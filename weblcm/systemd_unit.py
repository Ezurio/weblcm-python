from syslog import LOG_ERR, syslog
import dbus
from .definition import (
    SYSTEMD_BUS_NAME,
    SYSTEMD_MAIN_OBJ,
    SYSTEMD_MANAGER_IFACE,
    SYSTEMD_UNIT_ACTIVE_STATE_PROP,
    SYSTEMD_UNIT_IFACE,
    SYSTEMD_UNIT_UNIT_FILE_STATE_PROP,
    DBUS_PROP_IFACE,
)


class SystemdUnit(object):
    def __init__(self, unit_file: str) -> None:
        self.unit_file = unit_file

    @property
    def active_state(self) -> str:
        """
        The current 'ActiveState' value for the unit as a string. Possible values are:
        - active
        - reloading
        - inactive
        - failed
        - activating
        - deactivating
        - unknown (error state added by us)

        See below for more info:
        https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html
        """
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(
                bus.get_object(SYSTEMD_BUS_NAME, SYSTEMD_MAIN_OBJ),
                SYSTEMD_MANAGER_IFACE,
            )
            socket_unit_props = dbus.Interface(
                bus.get_object(
                    SYSTEMD_BUS_NAME,
                    manager.LoadUnit(self.unit_file),
                ),
                DBUS_PROP_IFACE,
            )
            active_state = socket_unit_props.Get(
                SYSTEMD_UNIT_IFACE, SYSTEMD_UNIT_ACTIVE_STATE_PROP
            )
            return active_state
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not read 'ActiveState' of {self.unit_file}: {str(e)}",
            )
            return "unknown"

    @property
    def unit_file_state(self) -> str:
        """
        The current 'UnitFileState' value for the unit as a string. Possible values are:
        - enabled
        - enabled-runtime
        - linked
        - linked-runtime
        - masked
        - masked-runtime
        - static
        - disabled
        - invalid
        - unknown (error state added by us)

        See below for more info:
        https://www.freedesktop.org/software/systemd/man/org.freedesktop.systemd1.html
        """
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(
                bus.get_object(SYSTEMD_BUS_NAME, SYSTEMD_MAIN_OBJ),
                SYSTEMD_MANAGER_IFACE,
            )
            socket_unit_props = dbus.Interface(
                bus.get_object(
                    SYSTEMD_BUS_NAME,
                    manager.LoadUnit(self.unit_file),
                ),
                DBUS_PROP_IFACE,
            )
            active_state = socket_unit_props.Get(
                SYSTEMD_UNIT_IFACE, SYSTEMD_UNIT_UNIT_FILE_STATE_PROP
            )
            return active_state
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not read 'UnitFileState' of {self.unit_file}: {str(e)}",
            )
            return "unknown"

    def activate(self) -> bool:
        """
        Activate the unit
        """
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(
                bus.get_object(SYSTEMD_BUS_NAME, SYSTEMD_MAIN_OBJ),
                SYSTEMD_MANAGER_IFACE,
            )
            manager.StartUnit(self.unit_file, "replace")
            return True
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not activate unit {str(self.unit_file)}: {str(e)}",
            )
            return False

    def deactivate(self) -> bool:
        """
        Deactivate the unit
        """
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(
                bus.get_object(SYSTEMD_BUS_NAME, SYSTEMD_MAIN_OBJ),
                SYSTEMD_MANAGER_IFACE,
            )
            manager.StopUnit(self.unit_file, "replace")
            return True
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Could not deactivate the unit {str(self.unit_file)}: {str(e)}",
            )
            return False
