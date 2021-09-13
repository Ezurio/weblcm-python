import threading
import time
from typing import Optional, Tuple, Any, Dict

import cherrypy
import dbus

from weblcm_ble import BLUEZ_SERVICE_NAME, GATT_CHRC_IFACE, DBUS_PROP_IFACE, dbus_to_python_ex, \
    GATT_SERVICE_IFACE, DBUS_OM_IFACE
from weblcm_bluetooth_plugin import BluetoothPlugin
from weblcm_tcp_connection import TcpConnection, TCP_SOCKET_HOST, firewalld_open_port, \
    firewalld_close_port

MAX_TX_LEN = 16
""" Maximum bytes to transfer wrapped in one JSON packet over TCP. """


class VspConnectionPlugin(BluetoothPlugin):
    def __init__(self):
        self.vsp_connections: Dict[str, VspConnection] = {}
        """Dictionary of devices and their associated VspConnection, if any"""

    def ProcessDeviceCommand(self, bus, command, device_uuid, device, post_data):
        processed = False
        error_message = None
        if command == 'gattConnect':
            processed = True
            if str(device) in self.vsp_connections:
                error_message = f'device {str(device)} already has vsp connection on port ' \
                                f'{self.vsp_connections[device].port}'
            else:
                vsp_connection = VspConnection()
                error_message = vsp_connection.gatt_connect(bus, device, post_data)
                if not error_message:
                    self.vsp_connections[str(device)] = vsp_connection
        return processed, error_message


class VspConnection(TcpConnection):
    """Represent a VSP connection with GATT read and write characteristics to a device, and an associated TCP socket
    connection.
    """

    def __init__(self):
        self.recent_error: Optional[str] = None
        self.vsp_read_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None

        self.tx_wait_event = threading.Event()
        self.tx_complete = False
        self.tx_error = False
        super().__init__()

    def process_chrc(self, chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid):
        bus = dbus.SystemBus()
        chrc = bus.get_object(BLUEZ_SERVICE_NAME, chrc_path)
        chrc_props = chrc.GetAll(GATT_CHRC_IFACE,
                                 dbus_interface=DBUS_PROP_IFACE)

        uuid = chrc_props['UUID']

        if uuid == vsp_read_chr_uuid:
            self.vsp_read_chrc = (chrc, chrc_props)
        elif uuid == vsp_write_chr_uuid:
            self.vsp_write_chrc = (chrc, chrc_props)

        return True

    def device_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if 'Connected' in changed_props:
            if self._tcp_connection:
                self._tcp_connection.sendall(
                    f"{{\"Connected\": {changed_props['Connected']}}}\n".encode())

        if len(changed_props):
            cherrypy.log("device_prop_changed_cb: property changed " + str(changed_props))

    def vsp_read_prop_changed_cb(self, iface, changed_props, invalidated_props):
        if iface != GATT_CHRC_IFACE:
            cherrypy.log("vsp_read_prop_changed_cb: iface != GATT_CHRC_IFACE")

        if not len(changed_props):
            return

        value = changed_props.get('Value', None)

        # cherrypy.log("vsp_read_prop_changed_cb: property changed " + str(changed_props))
        if value:
            self.gatt_vsp_read_val_cb(value)

    @staticmethod
    def gatt_vsp_notify_cb():
        '''
        gatt_vsp_notify_cb performs no operation at present, but should be supplied to StartNotify,
        which is necessary to begin receiving PropertiesChanged signals on the VSP data read.
        '''
        return

    def gatt_vsp_read_val_cb(self, value):
        python_value = dbus_to_python_ex(value, bytearray)
        if self._tcp_connection:
            try:
                self._tcp_connection.sendall(
                    f"{{\"Received\": \"0x{python_value.hex()}\"}}\n".encode())
            except OSError as e:
                cherrypy.log("gatt_vsp_read_val_cb:" + str(e))

    def write_val_cb(self):
        self.tx_complete = True
        self.tx_wait_event.set()

    def generic_val_error_cb(self, error):
        self.recent_error = str(error)
        cherrypy.log("generic_val_error_cb: D-Bus call failed: " + str(error))
        if 'Not connected' in error.args:
            self.bt_disconnected()

    def write_val_error_cb(self, error):
        self.tx_error = True
        self.tx_wait_event.set()
        self.generic_val_error_cb(error)

    def start_client(self):
        # Subscribe to VSP read value notifications.
        self.vsp_read_chrc[0].StartNotify(reply_handler=self.gatt_vsp_notify_cb,
                                          error_handler=self.generic_val_error_cb,
                                          dbus_interface=GATT_CHRC_IFACE)

        # Listen to PropertiesChanged signals from the Read Value
        # Characteristic.
        vsp_read_prop_iface = dbus.Interface(self.vsp_read_chrc[0], DBUS_PROP_IFACE)
        vsp_read_prop_iface.connect_to_signal("PropertiesChanged", self.vsp_read_prop_changed_cb)

    def bt_disconnected(self):
        self._tcp_connection.sendall("{\"Connected\": 0}\n".encode())

    def gatt_send_data(self, data):
        self.vsp_write_chrc[0].WriteValue(data, {}, reply_handler=self.write_val_cb,
                                          error_handler=self.write_val_error_cb,
                                          dbus_interface=GATT_CHRC_IFACE)

    def process_vsp_service(self, service_path, chrc_paths, vsp_svc_uuid, vsp_read_chr_uuid, vsp_write_chr_uuid):
        bus = dbus.SystemBus()
        service = bus.get_object(BLUEZ_SERVICE_NAME, service_path)
        service_props = service.GetAll(GATT_SERVICE_IFACE,
                                       dbus_interface=DBUS_PROP_IFACE)

        uuid = service_props['UUID']

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

    def gatt_connect(self, bus, device: str = None, params=None):
        if 'vspSvcUuid' not in params:
            return 'vspSvcUuid param not specified'
        if 'vspReadChrUuid' not in params:
            return 'vspReachChrUuid param not specified'
        if 'vspWriteChrUuid' not in params:
            return 'vspWriteChrUuid param not specified'
        if 'tcpPort' not in params:
            return 'tcpPort param not specified'

        om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
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

            chrc_paths = [d for d in chrcs if d.startswith(path + '/')]

            if not device or path.startswith(device):
                vsp_service = self.process_vsp_service(path, chrc_paths, vsp_svc_uuid=params['vspSvcUuid'],
                                                       vsp_read_chr_uuid=params[
                                                           'vspReadChrUuid'],
                                                       vsp_write_chr_uuid=params['vspWriteChrUuid'])
                if vsp_service:
                    break

        if not vsp_service:
            return f"No VSP Service found for device {device}"

        # TODO: Fix for multithreaded use
        self.recent_error = None
        self.start_client()
        time.sleep(0.5)
        # For RESTful API, return BT connection errors if they occur within 0.5 seconds.
        if self.recent_error:
            return self.recent_error

        if 'tcpPort' in params:
            port = params['tcpPort']
            if not self.validate_port(int(port)):
                return f"port {port} not valid"
            host = TCP_SOCKET_HOST  # cherrypy.server.socket_host
            sock = self.tcp_server(host, params)
            if sock:
                threading.Thread(target=self.vsp_tcp_server_thread,
                                 name="vsp_tcp_server_thread", daemon=True,
                                 args=(sock, port)).start()
            device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
            device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
            device_iface.connect_to_signal("PropertiesChanged", self.device_prop_changed_cb)

    def vsp_tcp_server_thread(self, sock, port=None):
        if port:
            firewalld_open_port(port)
        try:
            while True:
                self._tcp_connection, client_address = sock.accept()
                cherrypy.log("vsp_tcp_server_thread: tcp client connected:" + str(client_address))
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
                            self.gatt_send_data(val)
                            if not self.tx_wait_event.wait():
                                cherrypy.log("vsp_tcp_server_thread: ERROR: gatt tx no completion")
                            if self.tx_error:
                                self._tcp_connection.sendall("{\"Error\": \"Transmit failed\""
                                                             f", \"Data\": \"0x{data.hex()}"
                                                             "\"}\n".encode())
                        else:
                            break
                except OSError as e:
                    cherrypy.log("vsp_tcp_server_thread:" + str(e))
                except Exception as e:
                    cherrypy.log("vsp_tcp_server_thread: non-OSError Exception: " + str(e))
                finally:
                    self._tcp_connection.close()
                    self._tcp_connection, client_address = None, None
        finally:
            # TODO: Consider flagging to manager thread for vsp_connections.pop(str(device))
            sock.close()
            if port:
                firewalld_close_port(port)