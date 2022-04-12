import threading
import time
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
    DEVICE_IFACE,
)
from ..bluetooth.bt_plugin import BluetoothPlugin
from ..tcp_connection import (
    TcpConnection,
    TCP_SOCKET_HOST,
    firewalld_open_port,
    firewalld_close_port,
    SOCK_TIMEOUT,
)

MAX_TX_LEN = 16
""" Maximum bytes to transfer wrapped in one JSON packet over TCP. """


class VspConnectionPlugin(BluetoothPlugin):
    def __init__(self):
        self.vsp_connections: Dict[str, VspConnection] = {}
        """Dictionary of devices by UUID and their associated VspConnection, if any"""

    @property
    def device_commands(self) -> List[str]:
        return ["gattConnect", "gattDisconnect"]

    @property
    def adapter_commands(self) -> List[str]:
        return ["gattList"]

    def ProcessDeviceCommand(
        self, bus, command, device_uuid: str, device: dbus.ObjectPath, post_data
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
                vsp_connection = VspConnection()
                error_message = vsp_connection.gatt_connect(
                    bus, device_uuid, device, post_data
                )
                if not error_message:
                    self.vsp_connections[device_uuid] = vsp_connection
        elif command == "gattDisconnect":
            processed = True
            if not device_uuid in self.vsp_connections:
                error_message = f"device {device_uuid} has no vsp connection"
            else:
                vsp_connection = self.vsp_connections.pop(device_uuid)
                vsp_connection.vsp_close(bus, device_uuid, post_data)
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
            bus = dbus.SystemBus()
            vsp_connection = self.vsp_connections.pop(device_uuid)
            vsp_connection.vsp_close(bus, device_uuid)

    def ControllerRemovedNotify(
        self, controller_name: str, adapter_obj: dbus.ObjectPath
    ):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            vsp_connection.gatt_only_disconnect()

    def ControllerAddedNotify(self, controller_name: str, adapter_obj: dbus.ObjectPath):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            vsp_connection.gatt_only_reconnect()


class VspConnection(TcpConnection):
    """Represent a VSP connection with GATT read and write characteristics to a device, and an associated TCP socket
    connection.
    """

    def __init__(self):
        self.device: Optional[dbus.ObjectPath] = None
        self._waiting_for_services_resolved: bool = False
        self.recent_error: Optional[str] = None
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
        self.tx_wait_event = threading.Event()
        self.tx_complete = False
        self.tx_error = False
        super().__init__()

    def process_chrc(self, chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid):
        bus = dbus.SystemBus()
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
                if self._tcp_connection and self.socket_rx_type == "JSON":
                    self._tcp_connection.sendall(
                        f"{{\"Connected\": {changed_props['Connected']}}}\n".encode()
                    )
            except Exception as e:
                syslog(LOG_ERR, str(e))
        if "ServicesResolved" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"vsp device_prop_changed_cb: ServicesResolved: "
                    f"{changed_props['ServicesResolved']}",
                )
                if changed_props["ServicesResolved"] == True:
                    if self._waiting_for_services_resolved:
                        self._waiting_for_services_resolved = False
                        self.gatt_only_connected()
            except Exception as e:
                syslog(LOG_ERR, str(e))

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
        if self._tcp_connection:
            try:
                if self.socket_rx_type == "JSON":
                    self._tcp_connection.sendall(
                        f'{{"Received": "0x{python_value.hex()}"}}\n'.encode()
                    )
                else:
                    self._tcp_connection.sendall(python_value)
            except OSError as e:
                syslog("gatt_vsp_read_val_cb:" + str(e))

    def write_val_cb(self):
        self.tx_complete = True
        self.tx_wait_event.set()

    def generic_val_error_cb(self, error):
        self.recent_error = str(error)
        syslog("generic_val_error_cb: D-Bus call failed: " + str(error))
        if "Not connected" in error.args:
            self.bt_disconnected()

    def write_val_error_cb(self, error):
        self.tx_error = True
        self.tx_wait_event.set()
        self.generic_val_error_cb(error)

    def start_client(self):
        if not self.vsp_read_chrc:
            return

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

    def bt_disconnected(self):
        syslog("vsp bt_disconnected: Connected: 0")
        if self._tcp_connection and self.socket_rx_type == "JSON":
            self._tcp_connection.sendall('{"Connected": 0}\n'.encode())

    def gatt_send_data(self, data) -> bool:
        if self.vsp_write_chrc and len(self.vsp_write_chrc):
            self.vsp_write_chrc[0].WriteValue(
                data,
                {},
                reply_handler=self.write_val_cb,
                error_handler=self.write_val_error_cb,
                dbus_interface=GATT_CHRC_IFACE,
            )
            return True
        else:
            self.tx_error = True
            return False

    def process_vsp_service(
        self,
        service_path,
        chrc_paths,
        vsp_svc_uuid,
        vsp_read_chr_uuid,
        vsp_write_chr_uuid,
    ):
        bus = dbus.SystemBus()
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
        self, bus, device_uuid: str, device: dbus.ObjectPath = None, params=None
    ):
        if not params:
            return "no params specified"
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
        if "socketRxType" in params:
            self.socket_rx_type = params["socketRxType"]

        vsp_service = self.create_vsp_service()
        if not vsp_service:
            return f"No VSP Service found for device {device_uuid}"

        # TODO: Enhance for simultaneous clients
        self.recent_error = None
        try:
            self.start_client()
            time.sleep(0.5)
            # For RESTful API, return BT connection errors if they occur within 0.5 seconds.
            if self.recent_error:
                self.stop_client()
                return self.recent_error

            if "tcpPort" in params:
                port = params["tcpPort"]
                if not self.validate_port(int(port)):
                    return f"port {port} not valid"
                host = TCP_SOCKET_HOST  # cherrypy.server.socket_host
                self.sock = self.tcp_server(host, params)
                if self.sock:
                    self.thread = threading.Thread(
                        target=self.vsp_tcp_server_thread,
                        name="vsp_tcp_server_thread",
                        daemon=True,
                        args=(self.sock,),
                    )
                    self.thread.start()
                device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
                device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
                self.signal_device_prop_changed = device_iface.connect_to_signal(
                    "PropertiesChanged", self.device_prop_changed_cb
                )
                if port:
                    firewalld_open_port(port)
        except Exception:
            self.stop_client()
            raise

    def gatt_only_disconnect(self):
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        if self.signal_device_prop_changed:
            try:
                self.signal_device_prop_changed.remove()
                self.signal_device_prop_changed = None
            except Exception as e:
                syslog(LOG_ERR, "gatt_only_disconnect: " + str(e))
        self.stop_client()

    def vsp_close(self, bus, device_uuid: str = "", params=None):
        """Close the VSP connection down, including the REST host connection."""
        self.gatt_only_disconnect()
        self.stop_tcp_server(self.sock)
        if self.thread:
            self.thread.join()
        if self.port:
            firewalld_close_port(self.port)

    def gatt_only_reconnect(self):
        """
        Reconnect VSP gatt connection, assuming it was prior connected and TCP server/
        websocket service is still running.
        Note: Services will NOT resolve if connect was not issued through LCM, as connect
        will not have been performed by controller_restore in that case.
        """
        bus = dbus.SystemBus()

        device_obj = bus.get_object(BLUEZ_SERVICE_NAME, self.device)
        device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
        self.signal_device_prop_changed = device_iface.connect_to_signal(
            "PropertiesChanged", self.device_prop_changed_cb
        )

        device_properties = dbus.Interface(
            device_obj, "org.freedesktop.DBus.Properties"
        )
        services_resolved = device_properties.Get(DEVICE_IFACE, "ServicesResolved")

        if services_resolved == True:
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
        self.start_client()

    def create_vsp_service(self):
        bus = dbus.SystemBus()
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

    def vsp_tcp_server_thread(self, sock):
        try:
            sock.settimeout(SOCK_TIMEOUT)
            while True:
                try:
                    tcp_connection, client_address = sock.accept()
                    with self._tcp_lock:
                        self._tcp_connection = tcp_connection
                    syslog(
                        "vsp_tcp_server_thread: tcp client connected:"
                        + str(client_address)
                    )
                    try:
                        while True:
                            data = self._tcp_connection.recv(MAX_TX_LEN)
                            if data:
                                # Convert string to array of DBus Bytes & send
                                val = [dbus.Byte(b) for b in bytearray(data)]
                                self.tx_complete = False
                                self.tx_error = False
                                self.tx_wait_event.clear()
                                # Use simple wait event rather than private queue, to inform network
                                # to wait for Bluetooth to consume stream and simplify buffer management.
                                if self.gatt_send_data(val):
                                    if not self.tx_wait_event.wait():
                                        syslog(
                                            "vsp_tcp_server_thread: ERROR: gatt tx no completion"
                                        )
                                if self.tx_error:
                                    syslog(f"vsp transmit failed, data: 0x{data.hex()}")
                                    if self.socket_rx_type == "JSON":
                                        self._tcp_connection.sendall(
                                            '{"Error": "Transmit failed"'
                                            f', "Data": "0x{data.hex()}'
                                            '"}\n'.encode()
                                        )
                            else:
                                break
                    except OSError as e:
                        # If sock is closed, exit.
                        if e.errno == socket.EBADF:
                            break
                        syslog("vsp_tcp_server_thread:" + str(e))
                    except Exception as e:
                        syslog(
                            "vsp_tcp_server_thread: non-OSError Exception: " + str(e)
                        )
                    finally:
                        with self._tcp_lock:
                            self.close_tcp_connection()
                            self._tcp_connection, client_address = None, None
                except socket.timeout:
                    continue
                except OSError as e:
                    # If the socket was closed by another thread, exit
                    if e.errno == socket.EBADF:
                        break
                    else:
                        raise
        finally:
            # TODO: Consider flagging to manager thread for vsp_connections.pop(device_uuid)
            sock.close()
            self._tcp_connection, client_address = None, None
