import os
import cherrypy
import logging
from typing import List

from . import definition
from .network_status import NetworkStatus
from .network import (
    NetworkInterfaces,
    NetworkConnections,
    NetworkConnection,
    NetworkAccessPoints,
    Version,
)
from .log import LogData, LogSetting
from .swupdate import SWUpdate
from .users import UserManage, LoginManage
from .files import FileManage, FilesManage, AWMCfgManage
from .advanced import Reboot, FactoryReset
from .datetime import DateTimeSetting
from .settings import SystemSettingsManage
from .modem import PositioningSwitch, Positioning
from .advanced import Fips

weblcm_plugins: List[str] = []
websockets_auth_by_header_token: bool = False

"""
Note: Authenticating websocket users by header token is non-standard; an alternative method
may be required for Javascript browser clients.
"""

try:
    from .bluetooth.bt import Bluetooth

    weblcm_plugins.append("bluetooth")
    websockets_auth_by_header_token = True
    cherrypy.log("__main__: Bluetooth loaded")
except ImportError:
    Bluetooth = None
    cherrypy.log("__main__: Bluetooth NOT loaded")


class WebApp(object):
    def __init__(self):
        self._firewalld_disabled = os.system("systemctl is-active --quiet firewalld")

        self.login = LoginManage()
        self.networkStatus = NetworkStatus()
        self.connections = NetworkConnections()
        self.connection = NetworkConnection()
        self.accesspoints = NetworkAccessPoints()
        self.networkInterfaces = NetworkInterfaces()
        self.version = Version()

        self.logData = LogData()
        self.logSetting = LogSetting()

        self.users = UserManage()
        self.file = FileManage()
        self.files = FilesManage()
        self.awm = AWMCfgManage()

        self.firmware = SWUpdate()

        self.reboot = Reboot()
        self.factoryReset = FactoryReset()
        self.datetime = DateTimeSetting()

        self.positioningSwitch = PositioningSwitch()
        self.positioning = Positioning()
        self.fips = Fips()

        if Bluetooth:
            self.bluetooth = Bluetooth()
        else:
            self.bluetooth = None

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def definitions(self, *args, **kwargs):

        plugins = []
        for k in cherrypy.request.app.config["plugins"]:
            plugins.append(k)

        settings = {}
        # Whether to display 'zone' on the 'edit connection' page
        settings["firewalld_disabled"] = self._firewalld_disabled
        settings["session_timeout"] = SystemSettingsManage.get_session_timeout()

        return {
            "SDCERR": definition.WEBLCM_ERRORS.get("SDCERR_SUCCESS"),
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


# Redirect http to https
def force_tls():

    if cherrypy.request.scheme == "http":
        raise cherrypy.HTTPRedirect(
            cherrypy.url().replace("http:", "https:"), status=301
        )


def setup_http_server():

    httpServer = cherrypy._cpserver.Server()
    httpServer.socket_host = "::"
    httpServer.socket_port = 80
    httpServer.thread_pool = 0
    httpServer.subscribe()

    cherrypy.request.hooks.attach("on_start_resource", force_tls)


def force_session_checking():
    """
    Raise HTTP 401 Unauthorized client error if a session with invalid id tries to assess following resources.
    HTMLs still can be loaded to keep consistency, i.e. loaded from local cache or remotely.
    """

    paths = [
        "connections",
        "connection",
        "accesspoints",
        "networkInterfaces",
        "file",
        "users",
        "firmware",
        "logData",
        "awm",
        "positioning",
        "positioningSwitch",
        "logSetting",
        "factoryReset",
        "reboot",
        "files",
        "datetime",
        "fips",
    ] + weblcm_plugins

    if websockets_auth_by_header_token:
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


def main(args=None):
    setup_http_server()

    logging.getLogger("cherrypy").propagate = False

    cherrypy.request.hooks.attach("before_handler", force_session_checking)

    # Server config
    cherrypy.config.update(
        {
            "tools.sessions.timeout": SystemSettingsManage.get_session_timeout(),
        }
    )

    cherrypy.quickstart(WebApp(), "/", config=definition.WEBLCM_PYTHON_SERVER_CONF_FILE)
