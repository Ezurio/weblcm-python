from typing import List

import dbus


class BluetoothPlugin(object):
    @property
    def device_commands(self) -> List[str]:
        return []

    @property
    def adapter_commands(self) -> List[str]:
        return []

    def ProcessDeviceCommand(self, bus, command, device_uuid: str, device: dbus.ObjectPath,
                             post_data) \
            -> (bool, str):
        """ Process a device-specific command. """
        return False, None

    def ProcessAdapterCommand(self, bus, command, controller_name: str, adapter_obj:
                              dbus.ObjectPath, post_data) \
            -> (bool, str, dict):
        """ Process an adapter-specific command. """
        return False, None, None
