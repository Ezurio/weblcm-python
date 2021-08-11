from typing import List

import cherrypy
import dbus
import dbus.exceptions
import dbus.exceptions
import dbus.mainloop.glib
import dbus.mainloop.glib
import dbus.service
import dbus.service

import weblcm_def
from weblcm_ble import (
    find_controller, find_controllers, controller_pretty_name, find_device, find_devices, Agent,
    DEVICE_IFACE,
    ADAPTER_IFACE, python_to_dbus
)

#TODO: USER_PERMISSION_TYPES for Bluetooth

BLUEZ_SERVICE_NAME = "org.bluez"
AGENT_PATH = "/com/punchthrough/agent"

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [("Trusted", bool)]

# These controller properties can be directly set, without requiring any special-case logic.
PASS_ADAPTER_PROPS = ["Discovering", "Powered", "Discoverable"]


class AgentSingleton:
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if AgentSingleton.__instance is None:
            AgentSingleton()
        return AgentSingleton.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if AgentSingleton.__instance is None:
            AgentSingleton.__instance = self

            cherrypy.log("Registering agent for auto-pairing...")
            # get the system bus
            bus = dbus.SystemBus()
            agent = Agent(bus, AGENT_PATH)

            obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

            agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
            agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")


def GetControllerObj(name: str = None):
    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    controller = find_controller(bus, name)
    if not controller:
        cherrypy.log("GattManager1 interface not found")
        controller_obj = None
    else:
        controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

    return bus, controller_obj


@cherrypy.expose
@cherrypy.popargs('controller', 'device')
class Bluetooth(object):

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
        }

        filters: List[str] = None
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
                result['error_message'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result
        else:
            controllers = find_controllers(bus)

        for controller in controllers:
            controller_friendly_name: str = controller.replace("hci", "controller").replace("/org/bluez/", "")
            controller_result = {
            }
            controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

            if not controller_obj:
                result['error_message'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result

            try:
                if not device_uuid:
                    if not filters or 'bluetoothdevices' in filters:
                        controller_result['bluetoothdevices'] = find_devices(bus)

                    adapter_props = dbus.Interface(controller_obj, "org.freedesktop.DBus.Properties")
                    adapter_methods = dbus.Interface(controller_obj, "org.freedesktop.DBus.Methods")

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or pass_property.lower() in filters:
                            controller_result[pass_property.lower()] = adapter_props.Get(ADAPTER_IFACE, pass_property)

                    result[controller_friendly_name] = controller_result
                else:
                    result = {
                        'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
                    }

                    device, device_props = find_device(bus, device_uuid)
                    if not device:
                        result['error_message'] = 'Device not found'
                        return result

                    result.update(device_props)

                result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

            except Exception as e:
                result['error_message'] = str(e)
                cherrypy.log(str(e))

            return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
        }

        if 'controller' in cherrypy.request.params:
            controller_name = cherrypy.request.params['controller'].replace("controller", "hci")
        else:
            controller_name = None

        if 'device' in cherrypy.request.params:
            device_uuid = cherrypy.request.params['device'].upper()
        else:
            device_uuid = None

        # bus, controller_obj = GetControllerObj(controller_name)
        # get the system bus
        bus = dbus.SystemBus()
        # get the ble controller
        if controller_name is not None:
            controller = find_controller(bus, controller_name)
            if not controller:
                result['error_message'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result
        else:
            controller = find_controller(bus)

        post_data = cherrypy.request.json
        powered = post_data.get('powered', None)
        discovering = post_data.get('discovering', None)
        discoverable = post_data.get('discoverable', None)

        bus, adapter_obj = GetControllerObj()

        if not adapter_obj:
            return result

        try:
            adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
            adapter_methods = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Methods")

            if not device_uuid:
                if powered is not None:
                    status = adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(powered))
                    if status is not None:
                        return result

                if discoverable is not None:
                    status = adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(discoverable))
                    if status is not None:
                        return result

                if discovering is not None:
                    discovering_state = adapter_props.Get(ADAPTER_IFACE, "Discovering")
                    if discovering_state != discovering:
                        if discovering:
                            adapter_methods.get_dbus_method("StartDiscovery", ADAPTER_IFACE)()
                        else:
                            adapter_methods.get_dbus_method("StopDiscovery", ADAPTER_IFACE)()

                result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
            else:  # device_uuid specified
                device, device_props = find_device(bus, device_uuid)
                if device is None:
                    result['error_message'] = 'Device not found'
                    return result

                device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)

                device_methods = dbus.Interface(device_obj, "org.freedesktop.DBus.Methods")
                device_properties = dbus.Interface(device_obj, "org.freedesktop.DBus.Properties")

                for settable_property in SETTABLE_DEVICE_PROPS:
                    prop_name, prop_type = settable_property
                    value = post_data.get(prop_name.lower(), None)
                    if value is not None:
                        device_properties.Set(DEVICE_IFACE, prop_name, python_to_dbus(
                            value, prop_type))
                        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

                paired = post_data.get('paired', None)
                paired_state = device_properties.Get(DEVICE_IFACE, "Paired")
                if paired_state != paired:
                    if paired == 1:
                        # Note - device may need to be trusted prior to pairing
                        agent = AgentSingleton()
                        device_methods.get_dbus_method("Pair", DEVICE_IFACE)()

                        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
                    elif paired == 0:
                        adapter_methods.get_dbus_method("RemoveDevice", ADAPTER_IFACE)(device_obj)

                        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        except Exception as e:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['error_message'] = str(e)
            cherrypy.log(str(e))

        return result
