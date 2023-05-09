import logging
import socket
from syslog import LOG_WARNING, syslog, LOG_INFO, LOG_ERR
from typing import Optional, Any, Tuple, List, Dict

import dbus
from gi.repository import GLib

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

READ_ONLY = GLib.IOCondition.IN | GLib.IOCondition.ERR | GLib.IOCondition.HUP


class VspConnection(TcpConnection):
    """Represent a VSP connection with GATT read and write characteristics to a
    device, and an associated TCP socket connection.
    """

    def __init__(self, device_uuid: str, on_connection_closed=None):
        self.device: Optional[dbus.ObjectPath] = None
        self.adapter_obj: Optional[dbus.ObjectPath] = None
        self.remove_device_method = None
        self._waiting_for_services_resolved: bool = False
        self.vsp_svc_uuid = None
        self.vsp_read_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_read_chr_uuid = None
        self.signal_vsp_read_prop_changed = None
        self.signal_device_prop_changed = None
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_write_chr_uuid = None
        self.server_socket: Optional[socket.socket] = None
        self.socket_rx_type: str = "JSON"
        self._logger = logging.getLogger(__name__)
        self.auth_failure_unpair = False
        self.write_size: int = DEFAULT_WRITE_SIZE
        self.tcp_connection: Optional[socket.socket] = None
        self.client_address: Optional[socket._RetAddress] = None
        self.device_uuid = device_uuid
        self.on_connection_closed = on_connection_closed
        self.server_socket_channel: Optional[GLib.IOChannel] = None
        self.server_socket_channel_watch_id: int = 0
        self.tcp_connection_channel: Optional[GLib.IOChannel] = None
        self.tcp_connection_channel_watch_id: int = 0
        self.rx_buffer: list[dbus.Byte] = []
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
                    f"VSP device_prop_changed_cb: Connected: "
                    f"{changed_props['Connected']}",
                )
                if self.tcp_connection and self.socket_rx_type == "JSON":
                    self.tcp_connection.sendall(
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
                    "VSP device_prop_changed_cb: disconnect auth failure, auto-unpairing",
                )
                if self.remove_device_method:
                    self.remove_device_method(self.adapter_obj, self.device)
            except Exception as e:
                self.log_exception(e)
        if "ServicesResolved" in changed_props:
            try:
                syslog(
                    LOG_INFO,
                    f"VSP device_prop_changed_cb: ServicesResolved: "
                    f"{changed_props['ServicesResolved']}",
                )
                if changed_props["ServicesResolved"]:
                    if self._waiting_for_services_resolved:
                        self._waiting_for_services_resolved = False
                        self.gatt_only_connected()
            except Exception as e:
                self.log_exception(e)

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
        syslog("VSP: subscribed for GATT notifications")

    def gatt_vsp_read_val_cb(self, value):
        python_value = dbus_to_python_ex(value, bytearray)
        try:
            if self.tcp_connection:
                self.tcp_connection.sendall(
                    f'{{"Received": "0x{python_value.hex()}"}}\n'.encode()
                    if self.socket_rx_type == "JSON"
                    else python_value
                )
        except OSError as e:
            syslog("gatt_vsp_read_val_cb:" + str(e))

    def gatt_vsp_write_val_cb(self):
        if self.tcp_connection_channel:
            self.tcp_connection_channel_watch_id = GLib.io_add_watch(
                self.tcp_connection_channel,
                READ_ONLY,
                self.tcp_connection_event_handler,
            )

    def generic_val_error_cb(self, error):
        syslog("generic_val_error_cb: D-Bus call failed: " + str(error))
        if "Not connected" in error.args:
            if self.tcp_connection and self.socket_rx_type == "JSON":
                self.tcp_connection.sendall('{"Connected": 0}\n'.encode())

    def gatt_vsp_write_val_error_cb(self, error):
        self.gatt_vsp_write_val_cb()
        if self.socket_rx_type == "JSON" and self.tcp_connection:
            self.tcp_connection.sendall('{"Error": "Transmit failed"}\n'.encode())
        self.generic_val_error_cb(error)

    def start_client(self) -> bool:
        syslog("VSP: start_client")
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
        syslog("VSP: stop_client")
        if self.vsp_read_chrc and len(self.vsp_read_chrc):
            try:
                self.vsp_read_chrc[0].StopNotify(dbus_interface=GATT_CHRC_IFACE)
            except Exception as e:
                syslog(LOG_ERR, "stop_client: " + str(e))
            self.vsp_read_chrc = None
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
            return f"no VSP Service found for device {self.device_uuid}"

        if not self.start_client():
            return "could not start GATT client"

        self.server_socket = self.tcp_server(
            TCP_SOCKET_HOST, {"tcpPort": port}, backlog=1
        )
        if not self.server_socket:
            syslog("gatt_connect: Could not create TCP server socket")
            self.vsp_close()
            return "could not create TCP server socket"

        try:
            self.server_socket_channel = GLib.IOChannel.unix_new(
                self.server_socket.fileno()
            )
            self.server_socket_channel.set_encoding(None)
            self.server_socket_channel_watch_id = GLib.io_add_watch(
                self.server_socket_channel, READ_ONLY, self.server_socket_event_handler
            )
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"gatt_connect: server socket IO channel configuration error - {str(exception)}",
            )
            self.vsp_close()
            return "could not configure server socket IO channel"

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
        self.tcp_connection_channel_watch_id = GLib.io_add_watch(
            self.tcp_connection_channel, READ_ONLY, self.tcp_connection_event_handler
        )

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

    def cleanup_tcp_connection(self):
        """
        Close the TCP client connection and stop watching for events on the TCP client connection
        channel
        """
        try:
            if self.tcp_connection_channel_watch_id:
                GLib.source_remove(self.tcp_connection_channel_watch_id)
        except GLib.GError as glib_error:
            syslog(
                LOG_WARNING,
                f"VSP: error while cleaning up TCP client - {str(glib_error)}",
            )
        finally:
            self.tcp_connection_channel_watch_id = 0

        try:
            if self.tcp_connection_channel:
                self.tcp_connection_channel.shutdown(False)
        except GLib.GError as glib_error:
            syslog(
                LOG_WARNING,
                f"VSP: error while cleaning up TCP channel - {str(glib_error)}",
            )
        finally:
            self.tcp_connection_channel = None
            self.tcp_connection = None

    def cleanup_server_socket(self):
        """Close the server socket and stop watching for events on the server socket channel"""
        try:
            if self.server_socket_channel_watch_id:
                GLib.source_remove(self.server_socket_channel_watch_id)
        except GLib.GError as glib_error:
            syslog(
                LOG_WARNING,
                f"VSP: error while cleaning up server socket channel - {str(glib_error)}",
            )
        finally:
            self.server_socket_channel_watch_id = 0

        try:
            if self.server_socket_channel:
                self.server_socket_channel.shutdown(False)
        except GLib.GError as glib_error:
            syslog(
                LOG_WARNING,
                f"VSP: error while cleaning up server socket channel - {str(glib_error)}",
            )
        finally:
            self.server_socket_channel = None
            self.server_socket = None

    def vsp_close(self):
        """
        Close the VSP connection down, including the REST host connection, and perform any necessary
        cleanup
        """
        # Signal to the VspConnectionPlugin that this VspConnection instance is closing
        if self.on_connection_closed:
            self.on_connection_closed(self)

        # Cleanup TCP client connection and channel
        self.cleanup_tcp_connection()

        # Cleanup server socket and channel
        self.cleanup_server_socket()

        # Other cleanup
        self.gatt_only_disconnect()
        self.stop_tcp_server(self.server_socket)
        syslog(LOG_INFO, f"VSP: closed for device {self.device_uuid}")

    def tcp_connection_event_handler(self, _, condition):
        """
        Handler for IO events on the TCP client connection IO channel
        """
        if condition & GLib.IOCondition.IN:
            # IN event from the TCP client connection
            try:
                data = self.tcp_connection.recv(self.write_size)
                if not data:
                    # When recv() returns 0 bytes this indicates that the TCP client connection was
                    # closed
                    syslog(f"VSP: closing TCP client {str(self.client_address)}")
                    self.cleanup_tcp_connection()
                    return

                # Add the incoming data to the Rx buffer
                self.rx_buffer += [dbus.Byte(b) for b in bytearray(data)]
                if len(self.rx_buffer) < self.write_size:
                    # Not enough data to transmit
                    return

                # Unregister the TCP client connection as a source so we can queue up data in the
                # socket. The GATT Tx callbacks are responsible for re-registering it.
                if self.tcp_connection_channel_watch_id:
                    GLib.source_remove(self.tcp_connection_channel_watch_id)
                self.tcp_connection_channel_watch_id = 0

                # Convert bytes array to array of DBus Bytes and send
                self.gatt_send_data(self.rx_buffer[: self.write_size])

                # Update the Rx buffer to remove the now-sent chunk of data
                self.rx_buffer = self.rx_buffer[self.write_size :]
            except Exception as exception:
                syslog(
                    f"VSP: error - closing TCP client {str(self.client_address)} - {str(exception)}"
                )
                self.cleanup_tcp_connection()
        else:
            # HUP or ERR event from the TCP client connection
            syslog("VSP: client closed connection")
            if self.tcp_connection:
                self.cleanup_tcp_connection()

    def server_socket_event_handler(self, _, condition):
        """
        Handler for IO events on the main server socket IO channel
        """
        if condition & GLib.IOCondition.IN:
            # IO in event from the main server socket

            # Make sure the TCP client connection is in a good initial state
            self.cleanup_tcp_connection()
            self.rx_buffer = []

            # Accept an incoming TCP client connection
            (
                self.tcp_connection,
                self.client_address,
            ) = self.server_socket.accept()
            syslog("VSP: TCP client connected:" + str(self.client_address))
            self.tcp_connection.setblocking(0)

            # Setup the TCP client connection IO channel and watch for events
            self.tcp_connection_channel = GLib.IOChannel.unix_new(
                self.tcp_connection.fileno()
            )
            self.tcp_connection_channel.set_encoding(None)
            self.tcp_connection_channel_watch_id = GLib.io_add_watch(
                self.tcp_connection_channel,
                READ_ONLY,
                self.tcp_connection_event_handler,
            )
        else:
            # HUP or ERR event from the main server socket
            syslog("VSP: TCP server socket error")
            self.vsp_close()


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
        self,
        bus,
        command,
        device_uuid: str,
        device: dbus.ObjectPath,
        adapter_obj: dbus.ObjectPath,
        post_data,
        remove_device_method=None,
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
            syslog("Controller removed, removing GATT change subscriptions")
            vsp_connection.gatt_only_disconnect()

    def DeviceAddedNotify(
        self, device: str, device_uuid: str, device_obj: dbus.ObjectPath
    ):
        for vsp_uuid, vsp_connection in self.vsp_connections.items():
            if vsp_uuid == device_uuid:
                syslog(f"Re-connecting GATT subscriptions for device {device_uuid}")
                vsp_connection.gatt_only_reconnect()

    def on_connection_closed(self, connection: VspConnection) -> None:
        """
        Callback to be fired by the connection once it's closed
        """
        if connection.device_uuid in self.vsp_connections:
            self.vsp_connections.pop(connection.device_uuid)
