import itertools
import sys
import re
from syslog import syslog, LOG_ERR, LOG_INFO
from typing import List, Optional, Dict

import cherrypy
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import weblcm_bluetooth_plugin
import weblcm_def
from weblcm_ble import (
    find_controller, find_controllers, controller_pretty_name, controller_bus_name, find_device,
    find_devices, DEVICE_IFACE, ADAPTER_IFACE, DBUS_OM_IFACE, python_to_dbus, AgentSingleton,
    BLUEZ_SERVICE_NAME, uri_to_uuid
)
from weblcm_bluetooth_controller_state import BluetoothControllerState

# TODO: USER_PERMISSION_TYPES for Bluetooth

PAIR_TIMEOUT_SECONDS = 60

# These device properties can be directly set, without requiring any special-case logic.
SETTABLE_DEVICE_PROPS = [('Trusted', bool)]

CACHED_DEVICE_PROPS = ['connected']

# These controller properties can be directly set, without requiring any special-case logic.
PASS_ADAPTER_PROPS = ['Discovering', 'Powered', 'Discoverable']

CACHED_ADAPTER_PROPS = ['discovering', 'powered', 'discoverable', 'transportFilter']

ADAPTER_PATH_PATTERN = re.compile('^/org/bluez/hci\d+$')

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

try:
    # module dependencies, such as bt_logger.py, may be under /usr/lib
    sys.path.append('/usr/lib/igsdk')
    from weblcm_bluetooth_ble import BluetoothBlePlugin
    bluetooth_plugins.append(BluetoothBlePlugin())
    cherrypy.log("weblcm_bluetooth: BluetoothBlePlugin loaded")
except ImportError:
    cherrypy.log("weblcm_bluetooth: BluetoothBlePlugin NOT loaded")


def GetControllerObj(name: str = None):
    result = {}
    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    controller = find_controller(bus, name)
    if not controller:
        result['InfoMsg'] = f"Controller {controller_pretty_name(name)} not found."
        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
        controller_obj = None
    else:
        controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

    return bus, controller_obj, result


@cherrypy.expose
@cherrypy.popargs('controller', 'device')
class Bluetooth(object):
    _controller_callbacks_registered = False

    def __init__(self):
        self._controller_states: Dict[str, BluetoothControllerState] = {}
        """ Controller state tracking - indexed by friendly (REST API) name
        """

    @property
    def device_commands(self) -> List[str]:
        return list(itertools.chain.from_iterable(plugin.device_commands for plugin in
                                                  bluetooth_plugins))

    @property
    def adapter_commands(self) -> List[str]:
        return list(itertools.chain.from_iterable(plugin.adapter_commands for plugin in
                                                  bluetooth_plugins))

    def register_controller_callbacks(self):
        if not Bluetooth._controller_callbacks_registered:
            Bluetooth._controller_callbacks_registered = True

            bus = dbus.SystemBus()
            bus.add_signal_receiver(handler_function=self.interface_removed_cb,
                                    signal_name="InterfacesRemoved",
                                    dbus_interface=DBUS_OM_IFACE,
                                    path='/')
            bus.add_signal_receiver(handler_function=self.interface_added_cb,
                                    signal_name="InterfacesAdded",
                                    dbus_interface=DBUS_OM_IFACE,
                                    path='/')

    def interface_added_cb(self, interface: str, *args):
        try:
            if ADAPTER_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth interface added: {str(interface)}")
                # For now, assume the controller was previously removed and has been re-attached.
                self.controller_restore(interface)
        except Exception as e:
            syslog(LOG_ERR, str(e))

    def interface_removed_cb(self, interface: str, *args):
        try:
            if ADAPTER_PATH_PATTERN.match(interface):
                syslog(LOG_INFO, f"Bluetooth interface removed: {str(interface)}")
                bus, adapter_obj, get_controller_result = GetControllerObj(interface)
                for plugin in bluetooth_plugins:
                    try:
                        plugin.ControllerRemovedNotify(interface, adapter_obj)
                    except Exception as e:
                        syslog(LOG_ERR, str(e))
        except Exception as e:
            syslog(LOG_ERR, str(e))

    def controller_restore(self, controller_name: str = '/org/bluez/hci0'):
        """
        :param controller_name: controller whose state will be restored
        :return: None

        Call when the specified controller experienced a HW reset, for example, in case
        of a HW malfunction, or system power-save sleep.
        Attempts to re-establish previously commanded controller state.
        * Note the assumption is that this LCM process was used to establish controller state -
        assumption unsatisfied if prior run of LCM or another tool was used to alter controller
        state.
        """
        # we remove the bus path by convention, so the index names match that used by hosts
        # in REST API
        controller_friendly_name: str = controller_pretty_name(controller_name)
        controller_state = self.get_controller_state(controller_friendly_name)

        controller_name = controller_bus_name(controller_friendly_name)
        bus, adapter_obj, get_controller_result = GetControllerObj(controller_name)

        if not adapter_obj:
            syslog(LOG_ERR, f"Reset notification received for controller {controller_name}, " \
                   "but adapter_obj not found")
            return

        # First, set controller properties, powering it on if previously powered.
        adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
        adapter_methods = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Methods")
        try:
            self.set_adapter_properties(adapter_methods, adapter_props,
                                        controller_name, controller_state.properties)
        except Exception as e:
            syslog(str(e))

        # Second, set each device's properties, connecting if applicable.
        for device_uuid, properties in controller_state.device_properties_uuids.items():
            device, device_props = find_device(bus, device_uuid)
            if device is not None:
                device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)
                device_methods = dbus.Interface(device_obj, "org.freedesktop.DBus.Methods")
                device_properties = dbus.Interface(device_obj, "org.freedesktop.DBus.Properties")
                try:
                    self.set_device_properties(adapter_methods, device_methods, device_obj,
                                               device_properties, properties)
                except Exception as e:
                    syslog(str(e))
            else:
                syslog(LOG_ERR, f"couldn't find device {device_uuid} to restore properties")

        # Third, notify plugins, re-establishing protocol links.
        # We do not wait for BT connections to restore, so service discovery may not be complete
        # when plugins receive notification.
        for plugin in bluetooth_plugins:
            try:
                plugin.ControllerAddedNotify(controller_name, adapter_obj)
            except Exception as e:
                syslog(str(e))


    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
            'InfoMsg':'',
        }

        filters: Optional[List[str]] = None
        if 'filter' in cherrypy.request.params:
            filters = cherrypy.request.params['filter'].split(",")

        if 'controller' in cherrypy.request.params:
            controller_name = controller_bus_name(cherrypy.request.params['controller'])
        else:
            controller_name = None

        if 'device' in cherrypy.request.params:
            device_uuid = uri_to_uuid(cherrypy.request.params['device'])
        else:
            device_uuid = None

        # get the system bus
        bus = dbus.SystemBus()
        # get the ble controller
        if controller_name is not None:
            controller = find_controller(bus, controller_name)
            controllers = [controller]
            if not controller:
                result['InfoMsg'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result
        else:
            controllers = find_controllers(bus)

        for controller in controllers:
            controller_friendly_name: str = controller_pretty_name(controller)
            controller_result = {}
            controller_obj = bus.get_object(BLUEZ_SERVICE_NAME, controller)

            if not controller_obj:
                result['InfoMsg'] = f"Controller {controller_pretty_name(controller_name)} not found."
                return result

            try:
                matched_filter = False
                if not device_uuid:
                    if not filters or 'bluetoothDevices' in filters:
                        controller_result['bluetoothDevices'] = find_devices(bus)
                        matched_filter = True

                    adapter_props = dbus.Interface(controller_obj, "org.freedesktop.DBus.Properties")
                    adapter_methods = dbus.Interface(controller_obj, "org.freedesktop.DBus.Methods")

                    if not filters or 'transportFilter' in filters:
                        controller_result['transportFilter'] = self.get_adapter_transport_filter(
                            controller_name)
                        matched_filter = True

                    for pass_property in PASS_ADAPTER_PROPS:
                        if not filters or pass_property.lower() in filters:
                            controller_result[pass_property.lower()] = adapter_props.Get(ADAPTER_IFACE, pass_property)
                            matched_filter = True

                    result[controller_friendly_name] = controller_result
                    if filters and not matched_filter:
                        result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
                        result['InfoMsg'] = f"filters {filters} not matched"
                        return result
                else:
                    result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)

                    device, device_props = find_device(bus, device_uuid)
                    if not device:
                        result['InfoMsg'] = 'Device not found'
                        return result

                    result.update(device_props)

                result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

            except Exception as e:
                result['InfoMsg'] = str(e)
                syslog(str(e))

            return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {
            'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1),
            'InfoMsg': '',
        }

        if 'controller' in cherrypy.request.params:
            controller_name = controller_bus_name(cherrypy.request.params['controller'])
        else:
            controller_name = 'hci0'

        self.register_controller_callbacks()

        if 'device' in cherrypy.request.params:
            device_uuid = uri_to_uuid(cherrypy.request.params['device'])
        else:
            device_uuid = None

        post_data = cherrypy.request.json
        bus, adapter_obj, get_controller_result = GetControllerObj(controller_name)

        result.update(get_controller_result)

        if not adapter_obj:
            return result

        controller_friendly_name: str = controller_pretty_name(controller_name)
        controller_state = self.get_controller_state(controller_friendly_name)

        try:
            adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")
            adapter_methods = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Methods")

            command = post_data['command'] if 'command' in post_data else None
            if not device_uuid:
                # adapter-specific operation
                if command:
                    if not command in self.adapter_commands:
                        return '{"SDCERR":1, "InfoMsg": "supplied command parameter must be one ' \
                               'of %s"}' % self.adapter_commands
                    result.update(self.execute_adapter_command(bus, command, controller_name,
                                                               adapter_obj))
                    return result
                else:
                    for prop in CACHED_ADAPTER_PROPS:
                        if prop in post_data:
                            controller_state.properties[prop] = post_data.get(prop)
                    result.update(self.set_adapter_properties(adapter_methods, adapter_props,
                                                              controller_name, post_data))
            else:
                # device-specific operation
                if command and command not in self.device_commands:
                    return '{"SDCERR":1, "InfoMsg": "supplied command parameter must be one ' \
                           'of %s"}' % self.device_commands
                device, device_props = find_device(bus, device_uuid)
                if device is None:
                    result['InfoMsg'] = 'Device not found'
                    if command:
                        # Forward device-specific commands on to plugins even if device
                        # is not found:
                        result.update(
                            self.execute_device_command(bus, command, device_uuid, None))
                    return result

                device_obj = bus.get_object(BLUEZ_SERVICE_NAME, device)

                device_methods = dbus.Interface(device_obj, "org.freedesktop.DBus.Methods")
                device_properties = dbus.Interface(device_obj, "org.freedesktop.DBus.Properties")

                if command:
                    result.update(self.execute_device_command(bus, command, device_uuid, device))
                    return result
                else:
                    cached_device_properties = self.get_device_properties(controller_state,
                                                                          device_uuid)
                    for prop in CACHED_DEVICE_PROPS:
                        if prop in post_data:
                            cached_device_properties[prop] = post_data.get(prop)
                    result.update(self.set_device_properties(adapter_methods, device_methods,
                                                             device_obj, device_properties,
                                                             post_data))

        except Exception as e:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['InfoMsg'] = str(e)
            syslog(str(e))

        return result

    def get_controller_state(self, controller_friendly_name: str) -> BluetoothControllerState:
        controller_friendly_name = controller_pretty_name(controller_friendly_name)
        if not controller_friendly_name in self._controller_states:
            self._controller_states[controller_friendly_name] = BluetoothControllerState()
        return self._controller_states[controller_friendly_name]

    def get_device_properties(self, controller_state: BluetoothControllerState, device_uuid: str):
        """
        :param controller_state: controller device is on
        :param device_uuid: see uri_to_uuid()
        :return: dictionary map of device property names and values
        """
        if not device_uuid in controller_state.device_properties_uuids:
            controller_state.device_properties_uuids[device_uuid] = {}
        return controller_state.device_properties_uuids[device_uuid]

    def set_adapter_properties(self, adapter_methods, adapter_props, controller_name, post_data):
        """Set properties on an adapter (controller)"""
        result = {}
        powered = post_data.get('powered', None)
        discovering = post_data.get('discovering', None)
        discoverable = post_data.get('discoverable', None)
        transport_filter = post_data.get('transportFilter', None)
        if powered is not None:
            adapter_props.Set(ADAPTER_IFACE, "Powered", dbus.Boolean(powered))
            if not powered:
                # Do not attempt to set discoverable or discovering state if powering off
                discoverable = discoverable if discoverable else None
                discovering = discovering if discovering else None

        if transport_filter is not None:
            result.update(self.set_adapter_transport_filter(adapter_methods, controller_name,
                                                  transport_filter))
            if 'SDCERR' in result and result['SDCERR'] != weblcm_def.WEBLCM_ERRORS.get(
                    'SDCERR_SUCCESS'):
                return result
        if discoverable is not None:
            adapter_props.Set(ADAPTER_IFACE, "Discoverable", dbus.Boolean(discoverable))
        if discovering is not None:
            discovering_state = adapter_props.Get(ADAPTER_IFACE, "Discovering")
            if discovering_state != discovering:
                if discovering:
                    adapter_methods.get_dbus_method("StartDiscovery", ADAPTER_IFACE)()
                else:
                    adapter_methods.get_dbus_method("StopDiscovery", ADAPTER_IFACE)()

        if 'SDCERR' not in result:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')

        return result

    def get_adapter_transport_filter(self, controller_name):
        controller_state = self.get_controller_state(controller_name)
        return controller_state.properties.get('transportFilter', None)

    def set_adapter_transport_filter(self, adapter_methods, controller_name, transport_filter):
        """ Set a transport filter on the controller.  Note that "When multiple clients call
        SetDiscoveryFilter, their filters are internally merged" """
        result = {}
        discovery_filters = { 'Transport': transport_filter }
        discovery_filters_dbus = python_to_dbus(discovery_filters)
        try:
            adapter_methods.get_dbus_method("SetDiscoveryFilter", ADAPTER_IFACE)(discovery_filters_dbus)
        except dbus.DBusException as e:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['InfoMsg'] = f"Transport filter {transport_filter} not accepted"
            return result

        controller_state = self.get_controller_state(controller_name)
        controller_state.properties['transportFilter'] = transport_filter
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
            for plugin in bluetooth_plugins:
                try:
                    plugin.DeviceRemovedNotify(device_uuid, device_obj)
                except Exception as e:
                    syslog(str(e))
            return result
        connected = post_data.get('connected', None)
        connected_state = device_properties.Get(DEVICE_IFACE, "Connected")
        if connected_state != connected:
            if connected == 1:
                # Note - device may need to be paired prior to connecting
                # AgentSingleton can be registered to allow BlueZ to auto-pair (without bonding)
                agent = AgentSingleton()
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
            result['InfoMsg'] = f"Unrecognized command {command}"
        elif error_message:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['InfoMsg'] = error_message
        else:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
            result['InfoMsg'] = ''

        return result

    def execute_adapter_command(self, bus, command, controller_name: str, adapter_obj: dbus.ObjectPath):
        result = {}
        error_message = None
        processed = False
        post_data = cherrypy.request.json
        for plugin in bluetooth_plugins:
            try:
                processed, error_message, process_result = plugin.ProcessAdapterCommand(bus, command,
                                                                                        controller_name,
                                                                                        adapter_obj, post_data)
                if process_result:
                    result.update(process_result)
            except Exception as e:
                processed = True
                error_message = f"Command {command} failed with {str(e)}"
                break
            if processed:
                break

        if not processed:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['InfoMsg'] = f"Unrecognized command {command}"
        elif error_message:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL', 1)
            result['InfoMsg'] = error_message
        else:
            result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
            result['InfoMsg'] = ''

        return result
