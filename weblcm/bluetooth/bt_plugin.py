from typing import Optional, Tuple, List

import dbus


class BluetoothPlugin(object):
    @property
    def device_commands(self) -> List[str]:
        return []

    @property
    def adapter_commands(self) -> List[str]:
        return []

    def ProcessDeviceCommand(
        self, bus, command, device_uuid: str, device: dbus.ObjectPath, post_data
    ) -> Tuple[bool, str]:
        """Process a device-specific command."""
        return False, ""

    def ProcessAdapterCommand(
        self,
        bus,
        command,
        controller_name: str,
        adapter_obj: dbus.ObjectPath,
        post_data,
    ) -> Tuple[bool, str, Optional[dict]]:
        """Process an adapter-specific command."""
        return False, "", None

    def DeviceRemovedNotify(self, device_uuid: str, device: dbus.ObjectPath):
        """Notify plugin that device was removed/unpaired."""
        return

    def ControllerResetNotify(self, controller_name: str, adapter_obj: dbus.ObjectPath):
        """Notify plugin that BT controller was reset, all state reset."""
        self.ControllerRemovedNotify(controller_name, adapter_obj)
        self.ControllerAddedNotify(controller_name, adapter_obj)

    def ControllerRemovedNotify(
        self, controller_name: str, adapter_obj: dbus.ObjectPath
    ):
        """Notify plugin that BT controller was removed, all state reset."""
        return

    def ControllerAddedNotify(self, controller_name: str, adapter_obj: dbus.ObjectPath):
        """Notify plugin that (probably previously removed) BT controller was added, all state
        reset."""
        return
