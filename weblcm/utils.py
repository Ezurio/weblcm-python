from syslog import LOG_ERR, syslog
from typing import Optional
import dbus

from gi.repository import GLib
import dbus.mainloop.glib


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DBusManager(object, metaclass=Singleton):
    def __init__(self) -> None:
        self._bus = None
        self._dbus_mainloop = None
        self._glib_mainloop = None

    def start(self):
        # Initialize the DBus/GLib main loops
        dbus.mainloop.glib.threads_init()
        self._dbus_mainloop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self._glib_mainloop = GLib.MainLoop()

    def get_glib_mainloop(self):
        return self._glib_mainloop

    def get_system_bus(self) -> Optional[dbus.SystemBus]:
        if self._bus is None:
            if self._dbus_mainloop is None:
                return None
            try:
                self._bus = dbus.SystemBus(mainloop=self._dbus_mainloop)
            except Exception as e:
                syslog(LOG_ERR, f"Could not connect to DBus system bus: {str(e)}")
                self._bus = None
        return self._bus
