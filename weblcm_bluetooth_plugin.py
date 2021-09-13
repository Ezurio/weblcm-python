import dbus


class BluetoothPlugin(object):
    def ProcessDeviceCommand(self, bus, command, device_uuid: str, device: dbus.ObjectPath,
                             post_data) \
            -> (bool, str):
        """ Process a device-specific command. """
        pass
