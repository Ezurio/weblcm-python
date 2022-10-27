from syslog import syslog
import threading
import cherrypy
import logging
from typing import List
from . import definition
from .network_status import NetworkStatus
from .network import (
    NetworkInterfaces,
    NetworkInterface,
    NetworkConnections,
    NetworkConnection,
    NetworkAccessPoints,
    Version,
    WifiEnable,
)
from .log import LogData, LogSetting, LogForwarding
from .swupdate import SWUpdate
from .unauthenticated import AllowUnauthenticatedResetReboot
from .users import UserManage, LoginManage
from .files import FileManage, FilesManage
from .certificates import Certificates
from .advanced import PowerOff, Suspend, Reboot, FactoryReset
from .date_time import DateTimeSetting
from .settings import SystemSettingsManage
from .advanced import Fips

from gi.repository import GLib
import dbus.mainloop.glib

weblcm_plugins: List[str] = []


"""
Note: Authenticating websocket users by header token is non-standard; an alternative method
may be required for Javascript browser clients.
"""

try:
    from .bluetooth.bt import Bluetooth
    from .bluetooth.bt_ble import websockets_auth_by_header_token

    weblcm_plugins.append("bluetooth")
    cherrypy.log("__main__: Bluetooth loaded")
except ImportError:
    Bluetooth = None
    cherrypy.log("__main__: Bluetooth NOT loaded")

try:
    from .awm.awm_cfg_manage import AWMCfgManage

    weblcm_plugins.append("awm")
    cherrypy.log("__main__: AWM loaded")
except ImportError:
    AWMCfgManage = None
    cherrypy.log("__main__: AWM NOT loaded")

try:
    from .stunnel.stunnel import Stunnel

    weblcm_plugins.append("stunnel")
    cherrypy.log("__main__: stunnel loaded")
except ImportError:
    Stunnel = None
    cherrypy.log("__main__: stunnel NOT loaded")

try:
    from .modem.modem import (
        PositioningSwitch,
        Positioning,
        ModemFirmwareUpdate,
        ModemEnable,
    )

    weblcm_plugins.append("positioning")
    weblcm_plugins.append("positioningSwitch")
    weblcm_plugins.append("modemFirmwareUpdate")
    weblcm_plugins.append("modemEnable")
    cherrypy.log("__main__: modem loaded")
except ImportError:
    PositioningSwitch = None
    cherrypy.log("__main__: modem NOT loaded")

try:
    from .iptables.firewall import Firewall

    weblcm_plugins.append("firewall")
    cherrypy.log("__main__: firewall loaded")
except ImportError:
    Firewall = None
    cherrypy.log("__main__: firewall NOT loaded")


class WebApp(object):
    def __init__(self):
        self.login = LoginManage()
        self.networkStatus = NetworkStatus()
        self.connections = NetworkConnections()
        self.connection = NetworkConnection()
        self.accesspoints = NetworkAccessPoints()
        self.networkInterfaces = NetworkInterfaces()
        self.networkInterface = NetworkInterface()
        self.version = Version()

        self.logData = LogData()
        self.logSetting = LogSetting()
        self.logForwarding = LogForwarding()

        self.users = UserManage()
        self.file = FileManage()
        self.files = FilesManage()
        self.certificates = Certificates()
        if AWMCfgManage:
            self.awm = AWMCfgManage()

        self.firmware = SWUpdate()

        self.poweroff = PowerOff()
        self.suspend = Suspend()
        self.reboot = Reboot()
        self.factoryReset = FactoryReset()
        self.allowUnauthenticatedResetReboot = AllowUnauthenticatedResetReboot()

        self.datetime = DateTimeSetting()
        self.wifiEnable = WifiEnable()

        if PositioningSwitch:
            self.positioningSwitch = PositioningSwitch()
            self.positioning = Positioning()
            self.modemFirmwareUpdate = ModemFirmwareUpdate()
            self.modemEnable = ModemEnable()
        self.fips = Fips()

        if Bluetooth:
            self.bluetooth = Bluetooth()
        else:
            self.bluetooth = None

        if Firewall:
            self.firewall = Firewall()
        else:
            self.firewall = None

        if Stunnel:
            self.stunnel = Stunnel()

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def definitions(self, *args, **kwargs):

        plugins = []
        for k in cherrypy.request.app.config["plugins"]:
            plugins.append(k)

        settings = {}
        settings["session_timeout"] = SystemSettingsManage.get_session_timeout()

        return {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "Definitions": {
                "SDCERR": definition.WEBLCM_ERRORS,
                "PERMISSIONS": definition.USER_PERMISSION_TYPES,
                "DEVICE_TYPES": definition.WEBLCM_DEVTYPE_TEXT,
                "DEVICE_STATES": definition.WEBLCM_STATE_TEXT,
                "PLUGINS": plugins,
                "SETTINGS": settings,
            },
        }


def force_session_checking():
    """
    Raise HTTP 401 Unauthorized client error if a session with invalid id tries to assess following resources.
    HTMLs still can be loaded to keep consistency, i.e. loaded from local cache or remotely.
    """

    paths = [
        "connections",
        "connection",
        "accesspoints",
        "allowUnauthenticatedResetReboot",
        "networkInterfaces",
        "networkInterface",
        "file",
        "users",
        "firmware",
        "logData",
        "logSetting",
        "logForwarding",
        "poweroff",
        "suspend",
        "files",
        "certificates",
        "datetime",
        "fips",
        "modemEnable",
    ] + weblcm_plugins

    if not AllowUnauthenticatedResetReboot.allow_unauthenticated_reset_reboot():
        paths += ["factoryReset", "reboot"]

    if Bluetooth and websockets_auth_by_header_token:
        paths.append("ws")

    # With the `get` method the session id will be saved which could result in session fixation vulnerability.
    # Session ids will be destroyed periodically so we have to check 'USERNAME' to make sure the session is not valid after logout.
    if not cherrypy.session._exists() or not cherrypy.session.get("USERNAME", None):
        url = cherrypy.url().split("/")[-1]
        path_root = cherrypy.request.path_info.split("/")[1]
        if url and ".html" not in url and ".js" not in url and path_root in paths:
            raise cherrypy.HTTPError(401)


@cherrypy.tools.register("before_finalize", priority=60)
def secureheaders():
    headers = cherrypy.response.headers
    headers["X-Frame-Options"] = "DENY"
    headers["X-XSS-Protection"] = "1; mode=block"
    headers["X-Content-Type-Options"] = "nosniff"
    headers["Content-Security-Policy"] = "default-src 'self'"
    # Add Strict-Transport headers
    headers["Strict-Transport-Security"] = "max-age=31536000"  # one year


def weblcm_cherrypy_start():
    """
    Configure and start CherryPy
    """

    logging.getLogger("cherrypy").propagate = False

    cherrypy.request.hooks.attach("before_handler", force_session_checking)

    # Server config
    cherrypy.config.update(
        {
            "tools.sessions.timeout": SystemSettingsManage.get_session_timeout(),
        }
    )

    web_app = WebApp()
    threading.Thread(target=web_app.datetime.populate_time_zone_list).start()
    cherrypy.quickstart(web_app, "/", config=definition.WEBLCM_PYTHON_SERVER_CONF_FILE)


def main(args=None):
    # Initialize the DBus/GLib main loop
    dbus.mainloop.glib.threads_init()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    dbus_mainloop = GLib.MainLoop()

    syslog("Starting webserver")
    threading.Thread(
        name="webserver_thread", target=weblcm_cherrypy_start, daemon=True
    ).start()

    syslog("Starting DBus mainloop")
    try:
        dbus_mainloop.run()
    except KeyboardInterrupt:
        syslog("Received signal, shutting down service.")
    except Exception as e:
        syslog(f"Unexpected exception occurred: {str(e)}")
    finally:
        cherrypy.engine.exit()
        dbus_mainloop.quit()
