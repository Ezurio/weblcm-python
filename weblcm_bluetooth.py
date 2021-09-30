from typing import List, Optional

import cherrypy
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import weblcm_bluetooth_plugin
import weblcm_def
from weblcm_ble import (
    find_controller, find_controllers, controller_pretty_name, find_device, find_devices,
    DEVICE_IFACE, ADAPTER_IFACE, python_to_dbus, AgentSingleton, BLUEZ_SERVICE_NAME
)

# TODO: USER_PERMISSION_TYPES for Bluetooth

PAIR_TIMEOUT_SECONDS = 60

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [("Trusted", bool)]

# These controller properties can be directly set, without requiring any special-case logic.
PASS_ADAPTER_PROPS = ["Discovering", "Powered", "Discoverable"]

bluetooth_plugins: List[weblcm_bluetooth_plugin.BluetoothPlugin] = []

try:
    from weblcm_hid_barcode_scanner import HidBarcodeScannerPlugin
    bluetooth_plugins.append(HidBarcodeScannerPlugin())
    cherrypy.log("weblcm_bluetooth: HidBarcodeScannerPlugin loaded")
except ImportError:
    cherrypy.log("weblcm_bluetooth: HidBarcodeScannerPlugin NOT loaded")

try:
    from weblcm_vsp_connection import VspConnectionPlugin
    bluetooth_plugins.append(VspConnectionPlugin())
    cherrypy.log("weblcm_bluetooth: VspConnectionPlugin loaded")
except ImportError:
    cherrypy.log("weblcm_bluetooth: VspConnectionPlugin NOT loaded")


def GetControllerObj(name: str = None):
    result = {}
    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    controller = find_controller(bus, name)
    if not controller:
        result['ErrorMsg'] = f"Controller {controller_pretty_name(name)} not found."
        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
        controller_obj = None
    else:
        controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

    return bus, controller_obj, result


@cherrypy.expose
@cherrypy.popargs('controller', 'device')
class Bluetooth(object):
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
                matched_filter = False
                if not device_uuid:
                    if not filters or 'bluetoothDevices' in filters:
                        controller_result['bluetoothDevices'] = find_devices(bus)
                        matched_filter = True

                    adapter_props = dbus.Interface(controller_obj, "org.freedesktop.DBus.Properties")
                    adapter_methods = dbus.Interface(controller_obj, "org.freedesktop.DBus.Methods")

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or pass_property.lower() in filters:
                            controller_result[pass_property.lower()] = adapter_props.Get(ADAPTER_IFACE, pass_property)
                            matched_filter = True

                    result[controller_friendly_name] = controller_result
                    if filters and not matched_filter:
                        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
                        result['ErrorMsg'] = f"filters {filters} not matched"
                        return result
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

                if 'command' in post_data:
                    command = post_data['command']
                    result.update(self.execute_device_command(bus, command, device_uuid, device))
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

    def execute_device_command(self, bus, command, device_uuid: str, device: dbus.ObjectPath):
        result = {}
        error_message = None
        processed = False
        post_data = cherrypy.request.json
        for plugin in bluetooth_plugins:
            try:
                processed, error_message = plugin.ProcessDeviceCommand(bus, command, device_uuid,
                                                                      device, post_data)
            except Exception as e:
                processed = True
                error_message = f"Command {command} failed with {str(e)}"
                break
            if processed:
                break

        if not processed:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['ErrorMsg'] = f"Unrecognized command {command}"
        elif error_message:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['ErrorMsg'] = error_message
        else:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        return result

