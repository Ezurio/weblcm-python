import logging

import cherrypy
import dbus

DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
AGENT_IFACE = "org.bluez.Agent1"

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
BLUEZ_PATH_PREPEND = "/org/bluez/"


def python_to_dbus(data, datatype = None):
    # Convert python native data types to dbus data types
    if not datatype:
        datatype = type(data)

    if datatype is bool or datatype is dbus.Boolean:
        data = dbus.Boolean(data)
    elif datatype is int or datatype is dbus.Int64:
        data = dbus.Int64(data)

    return data

def controller_pretty_name(name: str):
    return name.replace("hci", "controller").replace("/org/bluez/", "")

def controller_bus_name(pretty_name: str):
    return pretty_name.replace("controller", "hci")

def find_controllers(bus):
    """
    Returns objects that have the bluez service and a GattManager1 interface
    """
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    controllers = []

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            controllers.append(o)

    return controllers

def find_controller(bus, name: str = None):
    """
    Returns the first object that has the bluez service and a GattManager1 interface and the provided name, if provided.
    """
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    controllers = []

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            if not name:
                return o

            controller_name = o.replace(BLUEZ_PATH_PREPEND, "")
            if controller_name.lower() == name.lower():
                return o

    return None

def find_devices(bus):
    """
    Returns the objects that have the bluez service and a DEVICE_IFACE interface
    """
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    devices = []

    for o, props in objects.items():
        if DEVICE_IFACE in props.keys():
            device = props[DEVICE_IFACE]
            devices.append(props[DEVICE_IFACE])

    return devices

def find_device(bus, uuid):
    """
    Returns the first object that has the bluez service and a DEVICE_IFACE interface.
    """
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if DEVICE_IFACE in props.keys():
            device = props[DEVICE_IFACE]
            if device['Address'].capitalize().lower() == uuid.lower():
                return o, props[DEVICE_IFACE]

    return None, None



def set_trusted(path):
    bus = dbus.SystemBus()
    props = dbus.Interface(
        bus.get_object("org.bluez", path), "org.freedesktop.DBus.Properties"
    )
    props.Set("org.bluez.Device1", "Trusted", True)


def dev_connect(path):
    bus = dbus.SystemBus()
    dev = dbus.Interface(bus.get_object("org.bluez", path), "org.bluez.Device1")
    dev.Connect()


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class Agent(dbus.service.Object):
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        cherrypy.log("Release")

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        cherrypy.log("AuthorizeService (%s, %s)" % (device, uuid))
        return

    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        cherrypy.log("RequestPinCode (%s)" % (device))
        set_trusted(device)
        return "000000"

    ''' TODO
    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        cherrypy.log("RequestPasskey (%s)" % (device))
        set_trusted(device)
        passkey = ask("Enter passkey: ")
        return dbus.UInt32(passkey)
    '''

    @dbus.service.method(AGENT_IFACE, in_signature="ouq", out_signature="")
    def DisplayPasskey(self, device, passkey, entered):
        cherrypy.log("DisplayPasskey (%s, %06u entered %u)" % (device, passkey, entered))

    @dbus.service.method(AGENT_IFACE, in_signature="os", out_signature="")
    def DisplayPinCode(self, device, pincode):
        cherrypy.log("DisplayPinCode (%s, %s)" % (device, pincode))

    @dbus.service.method(AGENT_IFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        cherrypy.log("RequestConfirmation (%s, %06d)" % (device, passkey))
        # TODO:  Check if provided passkey matches customer-preset passkey.
        set_trusted(device)
        return

    # Alcon Smart Remote utilizes RequestAuthorization
    @dbus.service.method(AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        cherrypy.log("RequestAuthorization (%s)" % (device))
        return

    @dbus.service.method(AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        cherrypy.log("Cancel")
