import logging
import select
import threading
import socket
from syslog import syslog, LOG_INFO, LOG_ERR
from typing import Optional, Any, Tuple, List, Dict

import dbus

from ..bluetooth.ble import (
    BLUEZ_SERVICE_NAME,
    GATT_CHRC_IFACE,
    DBUS_PROP_IFACE,
    dbus_to_python_ex,
    GATT_SERVICE_IFACE,
    DBUS_OM_IFACE,
    find_device,
)
from ..bluetooth.bt_plugin import BluetoothPlugin
from ..tcp_connection import (
    TcpConnection,
    TCP_SOCKET_HOST,
)

from ..utils import DBusManager

MAX_RECV_LEN = 512
""" Maximum bytes to read over TCP"""
DEFAULT_WRITE_SIZE = 1
""" Default GATT write size """

READ_ONLY = select.EPOLLIN | select.EPOLLERR


class VspConnection(TcpConnection):
    """Represent a VSP connection with GATT read and write characteristics to a
    device, and an associated TCP socket connection.
    """

    def __init__(self, device_uuid: str, on_connection_closed=None):
        self.device: Optional[dbus.ObjectPath] = None
        self._waiting_for_services_resolved: bool = False
        self.vsp_svc_uuid = None
        self.vsp_read_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_read_chr_uuid = None
        self.signal_vsp_read_prop_changed = None
        self.signal_device_prop_changed = None
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_write_chr_uuid = None
        self.sock: Optional[socket.socket] = None
        self.socket_rx_type: str = "JSON"
        self.thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)
        self.auth_failure_unpair = False
        self.write_size: int = DEFAULT_WRITE_SIZE
        self._producer: socket.socket = None
        self._consumer: socket.socket = None
        self.poller: Optional[select.epoll] = None
        self.tcp_connection: Optional[socket.socket] = None
        self._closing: bool = False
        self.device_uuid = device_uuid
        self.on_connection_closed = on_connection_closed
        super().__init__()

    def log_exception(self, e, message: str = ""):
        self._logger.exception(e)
        syslog(LOG_ERR, message + str(e))

    def process_chrc(self, chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid):
        bus = DBusManager().get_system_bus()
        chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)
        chrc_props = chrc.GetAll(GATT_CHRC_IFACE, dbus_interface=DBUS_PROP_IFACE)

        if not chrc_props:
            return False

        uuid = chrc_props["UUID"]

        if uuid == vsp_read_chr_uuid:
            self.vsp_read_chrc = (chrc, chrc_props)
        elif uuid == vsp_write_chr_uuid:
            self.vsp_write_chrc = (chrc, chrc_props)

        return True

    def device_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if "Connected" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"vsp device_prop_changed_cb: Connected: "
                    f"{changed_props['Connected']}",
                )
                if self._producer and self.socket_rx_type == "JSON":
                    self._producer.sendall(
                        f"{{\"Connected\": {changed_props['Connected']}}}\n".encode()
                    )
            except Exception as e:
                self.log_exception(e)
        if (
            self.auth_failure_unpair
            and "DisconnectReason" in changed_props
            and changed_props["DisconnectReason"] == "auth failure"
        ):
            try:
                syslog(
                    LOG_INFO,
                    "vsp device_prop_changed_cb: disconnect auth failure, auto-unpairing",
                )
                if self.remove_device_method:
                    self.remove_device_method(self.adapter_obj, self.device)
            except Exception as e:
                self.log_exception(e)
        if "ServicesResolved" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"vsp device_prop_changed_cb: ServicesResolved: "
                    f"{changed_props['ServicesResolved']}",
                )
                if changed_props["ServicesResolved"]:
                    if self._waiting_for_services_resolved:
                        self._waiting_for_services_resolved = False
                        self.gatt_only_connected()
            except Exception as e:
                self.log_exception(e)

        if len(changed_props):
            syslog(
                LOG_INFO,
                "device_prop_changed_cb: property changed " + str(changed_props),
            )

    def vsp_read_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if iface != GATT_CHRC_IFACE:
            syslog("vsp_read_prop_changed_cb: iface != GATT_CHRC_IFACE")

        if not len(changed_props):
            return

        value = changed_props.get("Value", None)

        # cherrypy.log("vsp_read_prop_changed_cb: property changed " + str(changed_props))
        if value:
            self.gatt_vsp_read_val_cb(value)

    @staticmethod
    def gatt_vsp_notify_cb():
        """
        gatt_vsp_notify_cb performs no operation at present, but should be supplied to StartNotify,
        which is necessary to begin receiving PropertiesChanged signals on the VSP data read.
        """
        return

    def gatt_vsp_read_val_cb(self, value):
        python_value = dbus_to_python_ex(value, bytearray)
        try:
            if self._producer and not self._closing:
                self._producer.sendall(
                    f'{{"Received": "0x{python_value.hex()}"}}\n'.encode()
                    if self.socket_rx_type == "JSON"
                    else python_value
                )
        except OSError as e:
            syslog("gatt_vsp_read_val_cb:" + str(e))

    def gatt_vsp_write_val_cb(self):
        if self.tcp_connection:
            self.poller.register(self.tcp_connection, READ_ONLY | select.EPOLLRDHUP)

    def generic_val_error_cb(self, error):
        syslog("generic_val_error_cb: D-Bus call failed: " + str(error))
        if "Not connected" in error.args:
            syslog("vsp bt_disconnected: Connected: 0")
            if self._producer and self.socket_rx_type == "JSON":
                self._producer.sendall('{"Connected": 0}\n'.encode())

    def gatt_vsp_write_val_error_cb(self, error):
        self.gatt_vsp_write_val_cb()
        if self.socket_rx_type == "JSON" and self._producer:
            self._producer.sendall('{"Error": "Transmit failed"}\n'.encode())
        self.generic_val_error_cb(error)

    def start_client(self) -> bool:
        syslog("vsp start_client: start")
        if not self.vsp_read_chrc:
            return False

        # Subscribe to VSP read value notifications.
        self.vsp_read_chrc[0].StartNotify(
            reply_handler=self.gatt_vsp_notify_cb,
            error_handler=self.generic_val_error_cb,
            dbus_interface=GATT_CHRC_IFACE,
        )

        # Listen to PropertiesChanged signals from the Read Value
        # Characteristic.
        vsp_read_prop_iface = dbus.Interface(self.vsp_read_chrc[0], DBUS_PROP_IFACE)
        self.signal_vsp_read_prop_changed = vsp_read_prop_iface.connect_to_signal(
            "PropertiesChanged", self.vsp_read_prop_changed_cb
        )

        return True

    def stop_client(self):
        # Stop client suppresses all errors, because it can be invoked during a failed startup,
        # in which case we want to focus attention on the startup error, not errors in
        # subsequently attempting to tear down.
        if self.vsp_read_chrc and len(self.vsp_read_chrc):
            try:
                self.vsp_read_chrc[0].StopNotify(dbus_interface=GATT_CHRC_IFACE)
                self.vsp_read_chrc = None
            except Exception as e:
                syslog(LOG_ERR, "stop_client: " + str(e))
        if self.signal_vsp_read_prop_changed:
            try:
                self.signal_vsp_read_prop_changed.remove()
                self.signal_vsp_read_prop_changed = None
            except Exception as e:
                syslog(LOG_ERR, "stop_client: " + str(e))

    def gatt_send_data(self, data) -> bool:
        if self.vsp_write_chrc and len(self.vsp_write_chrc):
            self.vsp_write_chrc[0].WriteValue(
                data,
                {},
                reply_handler=self.gatt_vsp_write_val_cb,
                error_handler=self.gatt_vsp_write_val_error_cb,
                dbus_interface=GATT_CHRC_IFACE,
            )
            return True
        return False

    def process_vsp_service(
        self,
        service_path,
        chrc_paths,
        vsp_svc_uuid,
        vsp_read_chr_uuid,
        vsp_write_chr_uuid,
    ):
        bus = DBusManager().get_system_bus()
        service = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
        service_props = service.GetAll(
            GATT_SERVICE_IFACE, dbus_interface=DBUS_PROP_IFACE
        )

        if not service_props:
            return None

        uuid = service_props["UUID"]

        if uuid != vsp_svc_uuid:
            return None

        # Process the characteristics.
        for chrc_path in chrc_paths:
            self.process_chrc(chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid)

        if self.vsp_read_chrc and self.vsp_write_chrc:
            vsp_service = (service, service_props, service_path)
            return vsp_service
        else:
            return None

    def gatt_connect(
        self,
        bus,
        adapter_obj: dbus.ObjectPath,
        device: dbus.ObjectPath,
        params=None,
        remove_device_method=None,
    ):
        if not params:
            return "no params specified"
        self.device = device
        self.adapter_obj = adapter_obj
        self.remove_device_method = remove_device_method
        port: int = 0
        if "authFailureUnpair" in params:
            self.auth_failure_unpair = params["authFailureUnpair"]
        if "vspSvcUuid" not in params:
            return "vspSvcUuid param not specified"
        self.vsp_svc_uuid = params["vspSvcUuid"]
        if "vspReadChrUuid" not in params:
            return "vspReachChrUuid param not specified"
        self.vsp_read_chr_uuid = params["vspReadChrUuid"]
        if "vspWriteChrUuid" not in params:
            return "vspWriteChrUuid param not specified"
        self.vsp_write_chr_uuid = params["vspWriteChrUuid"]
        if "tcpPort" not in params:
            return "tcpPort param not specified"
        try:
            port = int(params["tcpPort"])
            if not self.validate_port(port):
                raise ValueError
        except ValueError:
            return "invalid value for tcpPort param"
        if "socketRxType" in params:
            self.socket_rx_type = params["socketRxType"]
        if "vspWriteChrSize" in params:
            try:
                self.write_size = int(params["vspWriteChrSize"])
                if self.write_size < 1:
                    raise ValueError
            except ValueError:
                return "invalid value for vspWriteChrSize param"

        vsp_service = self.create_vsp_service()
        if not vsp_service:
            return f"No VSP Service found for device {self.device_uuid}"

        if not self.start_client():
            return "Could not start GATT client"

        self._closing = False
        self.thread = threading.Thread(
            target=self.vsp_tcp_server_thread,
            name="vsp_tcp_server_thread",
            daemon=True,
            args=(port,),
        )
        self.thread.start()
        device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
        device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
        self.signal_device_prop_changed = device_iface.connect_to_signal(
            "PropertiesChanged", self.device_prop_changed_cb
        )

    def gatt_only_disconnect(self):
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        if self.signal_device_prop_changed:
            try:
                self.signal_device_prop_changed.remove()
                self.signal_device_prop_changed = None
            except Exception as e:
                syslog(LOG_ERR, "gatt_only_disconnect: " + str(e))
        self.stop_client()

    def vsp_close(self):
        """Close the VSP connection down, including the REST host connection."""
        self._closing = True
        try:
            if self._producer:
                self._producer.sendall(b"")
        except Exception:
            pass
        syslog(LOG_INFO, f"vsp_close: closed for device {self.device_uuid}")

    def gatt_only_reconnect(self):
        """
        Reconnect VSP gatt connection, assuming it was prior connected and TCP server/
        websocket service is still running.
        Note: Services will NOT resolve if connect was not issued through LCM, as connect
        will not have been performed by controller_restore in that case.
        """
        bus = DBusManager().get_system_bus()
        self.device, device_props = find_device(bus, self.device_uuid)

        if not self.device:
            syslog(
                LOG_ERR,
                f"gatt_only_reconnect: device {self.device_uuid} not found on bus",
            )
            return

        device_obj = bus.get_object(BLUEZ_SERVICE_NAME, self.device)
        device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
        self.signal_device_prop_changed = device_iface.connect_to_signal(
            "PropertiesChanged", self.device_prop_changed_cb
        )

        services_resolved = device_props.get("ServicesResolved")

        if services_resolved:
            self.gatt_only_connected()
        else:
            syslog(
                LOG_INFO,
                f"services not resolved ({services_resolved}), schedule for "
                "later connection...",
            )
            self._waiting_for_services_resolved = True

    def gatt_only_connected(self):
        syslog(LOG_INFO, f"gatt_only_connected {self.device}")
        vsp_service = self.create_vsp_service()
        if not vsp_service:
            syslog(LOG_ERR, f"Failed to reconnect vsp_service for {str(self.device)}")
        if not self.start_client():
            syslog(LOG_ERR, f"Failed to restart GATT client for {str(self.device)}")

    def create_vsp_service(self):
        bus = DBusManager().get_system_bus()
        om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
        objects = om.GetManagedObjects()
        chrcs = []
        # List characteristics found
        for path, interfaces in objects.items():
            if GATT_CHRC_IFACE not in interfaces.keys():
                continue
            chrcs.append(path)
        # List sevices found
        vsp_service = None
        for path, interfaces in objects.items():
            if GATT_SERVICE_IFACE not in interfaces.keys():
                continue

            chrc_paths = [d for d in chrcs if d.startswith(path + "/")]

            if not self.device or path.startswith(self.device):
                vsp_service = self.process_vsp_service(
                    path,
                    chrc_paths,
                    self.vsp_svc_uuid,
                    self.vsp_read_chr_uuid,
                    self.vsp_write_chr_uuid,
                )
                if vsp_service:
                    break
        return vsp_service

    def vsp_tcp_server_thread(self, port: int):
        def cleanup_tcp_connection():
            nonlocal self

            if self.tcp_connection:
                try:
                    self.poller.unregister(self.tcp_connection)
                except FileNotFoundError:
                    # Ignore file not found errors while unregistering
                    pass
                self.tcp_connection.close()
                self.tcp_connection = None

        syslog("vsp_tcp_server_thread: start")
        try:
            self.sock = self.tcp_server(TCP_SOCKET_HOST, {"tcpPort": port}, backlog=1)
            if not self.sock:
                syslog("vsp_tcp_server_thread: Could not create TCP socket server")
                raise Exception("Could not create TCP socket server")

            (self._producer, self._consumer) = socket.socketpair(
                socket.AF_UNIX, socket.SOCK_SEQPACKET, 0
            )
            rx_buffer: list[dbus.Byte] = []
            with self.sock, self._consumer, self._producer:
                self.poller = select.epoll()
                self.poller.register(self.sock, READ_ONLY)
                self.poller.register(self._consumer, READ_ONLY)

                while not self._closing:
                    # Poll for events from the registered sockets
                    events = self.poller.poll()

                    # Check if we need to exit
                    if self._closing:
                        break

                    # Handle any incoming events
                    for fd, flag in events:
                        if flag & select.EPOLLIN:
                            if fd == self.sock.fileno():
                                # POLLIN event from the main server socket
                                (
                                    self.tcp_connection,
                                    client_address,
                                ) = self.sock.accept()
                                syslog(
                                    "vsp_tcp_server_thread: tcp client connected:"
                                    + str(client_address)
                                )
                                self.tcp_connection.setblocking(0)
                                rx_buffer = []
                                self.poller.register(
                                    self.tcp_connection, READ_ONLY | select.EPOLLRDHUP
                                )

                            elif fd == self._consumer.fileno():
                                # POLLIN event from the consumer socket
                                next_msg = self._consumer.recv(MAX_RECV_LEN)
                                if next_msg and self.tcp_connection:
                                    self.tcp_connection.sendall(next_msg)

                            elif (
                                self.tcp_connection
                                and fd == self.tcp_connection.fileno()
                            ):
                                # POLLIN event from the client TCP connection
                                try:
                                    data = self.tcp_connection.recv(self.write_size)
                                    if not data:
                                        # When recv() returns 0 bytes this indicates that the TCP
                                        # client connection was closed
                                        syslog(
                                            f"vsp_tcp_server_thread: closing {str(client_address)}"
                                        )
                                        cleanup_tcp_connection()
                                        continue

                                    # Add the incoming data to the Rx buffer
                                    rx_buffer += [dbus.Byte(b) for b in bytearray(data)]
                                    if len(rx_buffer) < self.write_size:
                                        # Not enough data to transmit
                                        continue

                                    # Unregister the TCP client connection from the poller so we can
                                    # queue up data in the socket. The GATT Tx callbacks are
                                    # responsible for re-registering it.
                                    self.poller.unregister(self.tcp_connection)

                                    # Convert bytes array to array of DBus Bytes and send
                                    self.gatt_send_data(rx_buffer[: self.write_size])

                                    # Update the Rx buffer to remove the now-sent chunk of data
                                    rx_buffer = rx_buffer[self.write_size :]
                                except Exception as e:
                                    syslog(
                                        f"vsp_tcp_server_thread: closing {str(client_address)} - "
                                        f"{str(e)}"
                                    )
                                    cleanup_tcp_connection()

                        elif flag & (select.EPOLLERR | select.EPOLLRDHUP):
                            # Handle error or hangup event
                            if fd == self.tcp_connection.fileno():
                                syslog(
                                    "vsp_tcp_server_thread: client closed connection"
                                )
                                if self.tcp_connection:
                                    cleanup_tcp_connection()
                            elif fd == self.sock.fileno():
                                syslog("vsp_tcp_server_thread: error")
                                self._closing = True

        except Exception as e:
            syslog(LOG_ERR, f"vsp_tcp_server_thread: exception - {str(e)}")
        finally:
            # Ensure we mark the VSP server connection as closing
            self._closing = True

            # Perform any necessary cleanup
            if self.on_connection_closed:
                self.on_connection_closed(self)
            if self.tcp_connection:
                cleanup_tcp_connection()
            self.gatt_only_disconnect()
            self.stop_tcp_server(self.sock)
            syslog("vsp_tcp_server_thread: tcp server stopped")


class VspConnectionPlugin(BluetoothPlugin):
    def __init__(self):
        self._vsp_connections: Dict[str, VspConnection] = {}
        """Dictionary of devices by UUID and their associated VspConnection, if any"""
        self.lock: threading.Lock = threading.Lock()

    @property
    def device_commands(self) -> List[str]:
        return ["gattConnect", "gattDisconnect"]

    @property
    def adapter_commands(self) -> List[str]:
        return ["gattList"]

    @property
    def vsp_connections(self) -> Dict[str, VspConnection]:
        with self.lock:
            return self._vsp_connections

    def ProcessDeviceCommand(
        self,
        bus,
        command,
        device_uuid: str,
        device: dbus.ObjectPath,
        adapter_obj: dbus.ObjectPath,
        post_data,
        remove_device_method,
    ):
        processed = False
        error_message = None
        if command == "gattConnect":
            processed = True
            if device_uuid in self.vsp_connections:
                error_message = (
                    f"device {device_uuid} already has vsp connection on port "
                    f"{self.vsp_connections[device_uuid].port}"
                )
            else:
                vsp_connection = VspConnection(device_uuid, self.on_connection_closed)
                error_message = vsp_connection.gatt_connect(
                    bus,
                    adapter_obj,
                    device,
                    post_data,
                    remove_device_method,
                )
                if not error_message:
                    self.vsp_connections[device_uuid] = vsp_connection
        elif command == "gattDisconnect":
            processed = True
            if device_uuid not in self.vsp_connections:
                error_message = f"device {device_uuid} has no vsp connection"
            else:
                syslog("Closing VSP due to gattDisconnect command")
                self.vsp_connections[device_uuid].vsp_close()
        return processed, error_message

    def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_obj: dbus.ObjectPath,
        post_data,
    ) -> Tuple[bool, str, dict]:
        processed = False
        error_message = ""
        result = {}
        if command == "gattList":
            processed = True
            result["GattConnections"] = [
                {"device": k, "port": self.vsp_connections[k].port}
                for k in self.vsp_connections.keys()
            ]
        return processed, error_message, result

    def DeviceRemovedNotify(self, device_uuid: str, device: dbus.ObjectPath):
        """Called when user has requested device be unpaired."""
        if device_uuid in self.vsp_connections:
            syslog("Closing VSP because the device was removed")
            self.vsp_connections[device_uuid].vsp_close()

    def ControllerRemovedNotify(
        self, controller_name: str, adapter_obj: dbus.ObjectPath
    ):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            syslog("Closing VSP because the controller was removed")
            vsp_connection.vsp_close()

    def DeviceAddedNotify(
        self, device: str, device_uuid: str, device_obj: dbus.ObjectPath
    ):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            if vsp_uuid == device_uuid:
                vsp_connection.gatt_only_reconnect()

    def on_connection_closed(self, connection: VspConnection) -> None:
        """
        Callback to be fired by the connection once it's closed
        """
        if connection.device_uuid in self.vsp_connections:
            self.vsp_connections.pop(connection.device_uuid)
