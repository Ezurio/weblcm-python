#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
import configparser
from syslog import LOG_ERR, syslog
from typing import Optional
import functools
import threading
import dbus

from gi.repository import GLib
import dbus.mainloop.glib
from weblcm.definition import (
    SYSTEMD_BUS_NAME,
    SYSTEMD_MAIN_OBJ,
    SYSTEMD_MANAGER_IFACE,
    WEBLCM_PYTHON_SERVER_CONF_FILE,
)


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


def glib_idle_add_wait(function, *args, **kwargs):
    """
    Execute the target function in the main loop using GLib.idle_add() and block until it has
    completed.
    """
    TIMEOUT_S: float = 5.0

    gsource_completed = threading.Event()
    results = []

    @functools.wraps(function)
    def wrapper():
        results.append(function(*args, **kwargs))
        gsource_completed.set()
        return False

    GLib.idle_add(wrapper)
    if not gsource_completed.wait(timeout=TIMEOUT_S):
        raise TimeoutError()
    return results.pop()


def restart_weblcm() -> bool:
    """Restart the weblcm-python systemd service via D-Bus"""
    try:
        bus = DBusManager().get_system_bus()
        manager = dbus.Interface(
            bus.get_object(SYSTEMD_BUS_NAME, SYSTEMD_MAIN_OBJ),
            SYSTEMD_MANAGER_IFACE,
        )
        manager.RestartUnit("weblcm-python.service", "replace")
        return True
    except Exception as exception:
        syslog(
            LOG_ERR,
            f"Could not restart weblcm-python: {str(exception)}",
        )
        return False


class ServerConfig(metaclass=Singleton):
    """Singleton class to access WebLCM server config parser"""

    def __init__(self) -> None:
        self.parser = configparser.ConfigParser()
        self.parser.read(WEBLCM_PYTHON_SERVER_CONF_FILE)

    def get(self, *args, **kwargs) -> str:
        """Singleton wrapper around the WebCLM server config parser get() function"""
        return self.parser.get(*args, **kwargs)

    def getboolean(self, *args, **kwargs) -> bool:
        """Singleton wrapper around the WebCLM server config parser getboolean() function"""
        return self.parser.getboolean(*args, **kwargs)
