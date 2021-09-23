import socket
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import cherrypy
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import weblcm_def
from weblcm_ble import (
    find_controller, find_controllers, controller_pretty_name, find_device, find_devices, DEVICE_IFACE,
    ADAPTER_IFACE, python_to_dbus, dbus_to_python_ex, AgentSingleton, DBUS_OM_IFACE, GATT_CHRC_IFACE, DBUS_PROP_IFACE,
    GATT_SERVICE_IFACE, BLUEZ_SERVICE_NAME
)

# TODO: USER_PERMISSION_TYPES for Bluetooth
VSP_PORT_MIN: int = 1000
# Keep away from dynamic ports, 49152 to 65535
VSP_PORT_MAX: int = 49152 - 1
FIREWALLD_TIMEOUT_SECONDS = 20
FIREWALLD_SERVICE_NAME = 'org.fedoraproject.FirewallD1'
FIREWALLD_OBJECT_PATH = '/org/fedoraproject/FirewallD1'
FIREWALLD_ZONE_INTERFACE = 'org.fedoraproject.FirewallD1.zone'
FIREWALLD_ZONE = 'internal'

PAIR_TIMEOUT_SECONDS = 60

GATT_TCP_SOCKET_HOST = "0.0.0.0"
MAX_TX_LEN = 16

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [("Trusted", bool)]

# These controller properties can be directly set, without requiring any special-case logic.
PASS_ADAPTER_PROPS = ["Discovering", "Powered", "Discoverable"]


def GetControllerObj(name: str = None):
    result = {}
    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    controller = find_controller(bus, name)
    if not controller:
        result['error_message'] = f"Controller {controller_pretty_name(name)} not found."
        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
        controller_obj = None
    else:
        controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

    return bus, controller_obj, result


def firewalld_open_port(port):
    try:
        bus = dbus.SystemBus()
        bus.call_blocking(bus_name=FIREWALLD_SERVICE_NAME, object_path=FIREWALLD_OBJECT_PATH,
                          dbus_interface=FIREWALLD_ZONE_INTERFACE,
                          method='addPort', signature='sssi', args=[dbus.String(FIREWALLD_ZONE), dbus.String(port),
                                                                    dbus.String('tcp'), dbus.Int32(0)],
                          timeout=FIREWALLD_TIMEOUT_SECONDS)
    except dbus.exceptions.DBusException as e:
        cherrypy.log("firewalld_open_port: Exception: " + str(e))


def firewalld_close_port(port):
    try:
        bus = dbus.SystemBus()
        bus.call_blocking(bus_name=FIREWALLD_SERVICE_NAME, object_path=FIREWALLD_OBJECT_PATH,
                          dbus_interface=FIREWALLD_ZONE_INTERFACE,
                          method='removePort', signature='sss', args=[dbus.String(FIREWALLD_ZONE), dbus.String(port),
                                                                      dbus.String('tcp')],
                          timeout=FIREWALLD_TIMEOUT_SECONDS)
    except dbus.exceptions.DBusException as e:
        cherrypy.log("firewalld_close_port: Exception: " + str(e))


class VspConnection(object):
    """Represent a VSP connection with GATT read and write characteristics to a device, and an associated TCP socket
    connection.
    """

    def __init__(self):
        self._tcp_connection = None
        self.recent_error: Optional[str] = None

        self.vsp_read_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None
        self.vsp_write_chrc: Optional[Tuple[dbus.proxies.ProxyObject, Any]] = None

        self.tx_wait_event = threading.Event()
        self.tx_complete = False
        self.tx_error = False
        self.port: Optional[int] = None

    @staticmethod
    def validate_port(port: int) -> bool:
        """
        :rtype: bool
        :param port: port number to validate
        :return: true if port falls within valid range; false otherwise
        """
        return VSP_PORT_MIN <= int(port) <= VSP_PORT_MAX

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
                self._tcp_connection.sendall(f"{{\"Connected\": {changed_props['Connected']}}}\n".encode())

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
                self._tcp_connection.sendall("{\"Received\": \"0x".encode())
                self._tcp_connection.sendall(python_value.hex().encode())
                self._tcp_connection.sendall("\"}\n".encode())
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

    def vsp_tcp_server(self, host, params) -> socket.socket:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = int(params['tcpPort'])
        self.port = port
        server_address = (host, port)
        sock.bind(server_address)
        sock.listen()
        return sock

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
            return False

        # Process the characteristics.
        for chrc_path in chrc_paths:
            self.process_chrc(chrc_path, vsp_read_chr_uuid, vsp_write_chr_uuid)

        vsp_service = (service, service_props, service_path)

        return vsp_service

    def gatt_connect(self, bus, device: str = None, params=None):
        if 'vspSvcUuid' not in params:
            return 'vspSvcUuid param not specified'
        if 'vspReadChrUuid' not in params:
            return 'vspReachChrUuid param not specified'
        if 'vspWriteChrUuid' not in params:
            return 'vspWriteChrUuid param not specified'

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
                if vsp_service is not None:
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
            host = GATT_TCP_SOCKET_HOST  # cherrypy.server.socket_host
            sock = self.vsp_tcp_server(host, params)
            if sock:
                threading.Thread(target=self.vsp_tcp_server_thread, args=(sock, port)).start()
            device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
            device_iface = dbus.Interface(device_obj, DBUS_PROP_IFACE)
            device_iface.connect_to_signal("PropertiesChanged", self.device_prop_changed_cb)

    def vsp_tcp_server_thread(self, sock, port=None):
        if port:
            firewalld_open_port(port)
        try:
            while True:
                # Consider for easy service termination, https://stackoverflow.com/a/63265381
                self._tcp_connection, client_address = sock.accept()
                cherrypy.log("vsp_tcp_server_thread: tcp client connected:" + str(client_address))
                try:
                    while True:
                        data = self._tcp_connection.recv(16)
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
                                self._tcp_connection.sendall("{\"Error\": \"Transmit failed\"".encode())
                                self._tcp_connection.sendall(", \"Data\": \"0x".encode())
                                self._tcp_connection.sendall(data.hex().encode())
                                self._tcp_connection.sendall("\"}\n".encode())
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


@cherrypy.expose
@cherrypy.popargs('controller', 'device')
class Bluetooth(object):
    def __init__(self):
        self.vsp_connections: Dict[str, VspConnection] = {}
        """Dictionary of devices and their associated VspConnection, if any"""

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
            'ErrorMsg':'',
        }

        filters: Optional[List[str]] = None
        if 'filter' in cherrypy.request.params:
            filters = cherrypy.request.params['filter'].split(",")

        if 'controller' in cherrypy.request.params:
            controller_name = cherrypy.request.params['controller'].replace("controller", "hci")
        else:
            controller_name = None

        if 'device' in cherrypy.request.params:
            device_uuid = cherrypy.request.params['device'].upper()
        else:
            device_uuid = None

        # get the system bus
        bus = dbus.SystemBus()
        # get the ble controller
        if controller_name is not None:
            controller = find_controller(bus, controller_name)
            controllers = [controller]
            if not controller:
                result['ErrorMsg'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result
        else:
            controllers = find_controllers(bus)

        for controller in controllers:
            controller_friendly_name: str = controller.replace("hci", "controller").replace("/org/bluez/", "")
            controller_result = {}
            controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

            if not controller_obj:
                result['ErrorMsg'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result

            try:
                if not device_uuid:
                    if not filters or 'bluetoothDevices' in filters:
                        controller_result['bluetoothDevices'] = find_devices(bus)

                    adapter_props = dbus.Interface(controller_obj, "org.freedesktop.DBus.Properties")
                    adapter_methods = dbus.Interface(controller_obj, "org.freedesktop.DBus.Methods")

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or pass_property.lower() in filters:
                            controller_result[pass_property.lower()] = adapter_props.Get(ADAPTER_IFACE, pass_property)

                    result[controller_friendly_name] = controller_result
                else:
                    result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)

                    device, device_props = find_device(bus, device_uuid)
                    if not device:
                        result['ErrorMsg'] = 'Device not found'
                        return result

                    result.update(device_props)

                result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

            except Exception as e:
                result['ErrorMsg'] = str(e)
                cherrypy.log(str(e))

            return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
            'ErrorMsg': '',
        }

        if 'controller' in cherrypy.request.params:
            controller_name = cherrypy.request.params['controller'].replace("controller", "hci")
        else:
            controller_name = None

        if 'device' in cherrypy.request.params:
            device_uuid = cherrypy.request.params['device'].upper()
        else:
            device_uuid = None

        post_data = cherrypy.request.json
        bus, adapter_obj, get_controller_result = GetControllerObj(controller_name)

        result.update(get_controller_result)

        if not adapter_obj:
            return result

        try:
            adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
            adapter_methods = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Methods")

            if not device_uuid:
                result.update(self.set_adapter_properties(adapter_methods, adapter_props, post_data))
            else:
                # device_uuid specified
                device, device_props = find_device(bus, device_uuid)
                if device is None:
                    result['ErrorMsg'] = 'Device not found'
                    return result

                device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)

                device_methods = dbus.Interface(device_obj, "org.freedesktop.DBus.Methods")
                device_properties = dbus.Interface(device_obj, "org.freedesktop.DBus.Properties")

                if 'command' in cherrypy.request.params:
                    command = cherrypy.request.params['command']
                    result.update(self.execute_device_command(bus, command, device))
                    return result
                else:
                    result = self.set_device_properties(adapter_methods, device_methods, device_obj, device_properties,
                                                        post_data)

        except Exception as e:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['ErrorMsg'] = str(e)
            cherrypy.log(str(e))

        return result

    def set_adapter_properties(self, adapter_methods, adapter_props, post_data):
        """Set properties on an adapter (controller)"""
        result = {}
        powered = post_data.get('powered', None)
        discovering = post_data.get('discovering', None)
        discoverable = post_data.get('discoverable', None)
        if powered is not None:
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(powered))
        if discoverable is not None:
            adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(discoverable))
        if discovering is not None:
            discovering_state = adapter_props.Get(ADAPTER_IFACE, "Discovering")
            if discovering_state != discovering:
                if discovering:
                    adapter_methods.get_dbus_method("StartDiscovery", ADAPTER_IFACE)()
                else:
                    adapter_methods.get_dbus_method("StopDiscovery", ADAPTER_IFACE)()
        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        return result

    def set_device_properties(self, adapter_methods, device_methods, device_obj, device_properties, post_data):
        result = {}
        for settable_property in SETTABLE_DEVICE_PROPS:
            prop_name, prop_type = settable_property
            value = post_data.get(prop_name.lower(), None)
            if value is not None:
                device_properties.Set(DEVICE_IFACE, prop_name, python_to_dbus(
                    value, prop_type))
        paired = post_data.get('paired', None)
        if paired == 1:
            paired_state = device_properties.Get(DEVICE_IFACE, "Paired")
            if paired_state != paired:
                agent = AgentSingleton()
                bus = dbus.SystemBus()
                bus.call_blocking(bus_name=BLUEZ_SERVICE_NAME, object_path=device_obj.object_path,
                                  dbus_interface=DEVICE_IFACE,
                                  method="Pair", signature='', args=[],
                                  timeout=PAIR_TIMEOUT_SECONDS)
        elif paired == 0:
            adapter_methods.get_dbus_method("RemoveDevice", ADAPTER_IFACE)(device_obj)
            # If RemoveDevice is successful, further work on device will not be possible.
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
            return result
        connected = post_data.get('connected', None)
        connected_state = device_properties.Get(DEVICE_IFACE, "Connected")
        if connected_state != connected:
            if connected == 1:
                # Note - device may need to be paired prior to connecting
                device_methods.get_dbus_method("Connect", DEVICE_IFACE)()
            elif connected == 0:
                device_methods.get_dbus_method("Disconnect", DEVICE_IFACE)()
        passkey = post_data.get('passkey', None)
        if passkey is not None:
            agent_instance = AgentSingleton.get_instance()
            if agent_instance:
                agent_instance.passkeys[device_obj.object_path] = passkey
        # Found device, set any requested properties.  Assume success.
        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        return result

    def execute_device_command(self, bus, command, device):
        result = {}
        error_message = None
        if command == 'gatt_connect':
            if str(device) in self.vsp_connections:
                error_message = f'device {str(device)} already has vsp connection on port ' \
                                f'{self.vsp_connections[device].port}'
            else:
                vsp_connection = VspConnection()
                error_message = vsp_connection.gatt_connect(bus, device, cherrypy.request.params)
            if not error_message:
                self.vsp_connections[str(device)] = vsp_connection
        if error_message:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['ErrorMsg'] = error_message
        else:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        return result
