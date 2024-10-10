#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from syslog import LOG_ERR, syslog
import threading
import cherrypy
import logging
from typing import List
from weblcm.provisioning import CertificateProvisioning, ProvisioningState
from . import definition
from .network_status import NetworkStatus
from .network import (
    NetworkInterfaces,
    NetworkInterface,
    NetworkInterfaceStatistics,
    NetworkInterfaceDriverInfo,
    NetworkConnections,
    NetworkConnection,
    NetworkAccessPoints,
    Version,
    WifiEnable,
)
from .log import LogData, LogSetting
from .swupdate import SWUpdate
from .unauthenticated import AllowUnauthenticatedResetReboot
from .users import UserManage, LoginManage
from .files import FileManage, FilesManage
from .certificates import Certificates
from .advanced import PowerOff, Suspend, Reboot, FactoryReset
from .date_time import DateTimeSetting
from .settings import SystemSettingsManage
from .advanced import Fips
from .utils import DBusManager, ServerConfig
from .ram_boot_time_session import RamBootTimeSession


weblcm_plugins: List[str] = []

PY_SSL_CERT_REQUIRED_NO_CHECK_TIME = 3
"""
Custom OpenSSL verify mode to disable time checking during certificate verification
"""

X509_V_FLAG_NO_CHECK_TIME = 0x200000
"""
Flags for OpenSSL 1.1.1 or newer to disable time checking during certificate verification
"""

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

try:
    from .radio_siso_mode.radio_siso_mode import RadioSISOMode

    weblcm_plugins.append("radioSISOMode")
    cherrypy.log("__main__: Radio SISO mode loaded")
except ImportError:
    RadioSISOMode = None
    cherrypy.log("__main__: Radio SISO mode NOT loaded")

try:
    from .chrony.ntp import NTP

    weblcm_plugins.append("ntp")
    cherrypy.log("__main__: chrony NTP loaded")
except ImportError:
    NTP = None
    cherrypy.log("__main__: chrony NTP NOT loaded")

try:
    from weblcm.log_forwarding.log_forwarding import LogForwarding

    weblcm_plugins.append("logForwarding")
    cherrypy.log("__main__: log forwarding loaded")
except ImportError:
    LogForwarding = None
    cherrypy.log("__main__: log forwarding NOT loaded")


class WebApp(object):
    def __init__(
        self,
        provisioning_state: ProvisioningState = ProvisioningState.FULLY_PROVISIONED,
    ):
        if provisioning_state != ProvisioningState.FULLY_PROVISIONED:
            self.datetime = DateTimeSetting()
            self.certificateProvisioning = CertificateProvisioning()
            self.networkStatus = NetworkStatus()
            self.version = Version()
            self.poweroff = PowerOff()
            self.reboot = Reboot()
            return

        self.login = LoginManage()
        self.networkStatus = NetworkStatus()
        self.connections = NetworkConnections()
        self.connection = NetworkConnection()
        self.accesspoints = NetworkAccessPoints()
        self.networkInterfaces = NetworkInterfaces()
        self.networkInterface = NetworkInterface()
        self.networkInterfaceStatistics = NetworkInterfaceStatistics()
        self.networkInterfaceDriverInfo = NetworkInterfaceDriverInfo()
        self.version = Version()

        self.logData = LogData()
        self.logSetting = LogSetting()
        if LogForwarding:
            self.logForwarding = LogForwarding()

        self.users = UserManage()
        self.file = FileManage()
        self.files = FilesManage()
        self.certificates = Certificates()
        self.certificateProvisioning = CertificateProvisioning()
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

        if RadioSISOMode:
            self.radioSISOMode = RadioSISOMode()
        else:
            self.radioSISOMode = None

        if NTP:
            self.ntp = NTP()
        else:
            self.ntp = None

    @cherrypy.expose
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def definitions(self, *args, **kwargs):
        plugins = []
        for k in cherrypy.request.app.config["plugins"]:
            plugins.append(k)

        settings = {}
        # If sessions aren't enabled, set the session_timeout to -1 to alert the frontend that we
        # don't need to auto log out.
        settings["session_timeout"] = (
            SystemSettingsManage.get_session_timeout()
            if cherrypy.request.app.config["/"].get("tools.sessions.on", True)
            else -1
        )

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


def get_ssl_files(provisioning_state: ProvisioningState) -> dict:
    """Retrieve a dictionary listing the key/certificates to use for HTTPS"""
    if provisioning_state == ProvisioningState.FULLY_PROVISIONED:
        return {
            "ssl_certificate": ServerConfig()
            .get(
                section="gobal",
                option="server.ssl_certificate",
                fallback="/etc/weblcm-python/ssl/server.crt",
            )
            .strip('"'),
            "ssl_private_key": ServerConfig()
            .get(
                section="global",
                option="server.ssl_private_key",
                fallback="/etc/weblcm-python/ssl/server.key",
            )
            .strip('"'),
            "ssl_certificate_chain": ServerConfig()
            .get(
                section="global",
                option="server.ssl_certificate_chain",
                fallback="/etc/weblcm-python/ssl/ca.crt",
            )
            .strip('"'),
        }

    if provisioning_state == ProvisioningState.UNPROVISIONED:
        return {
            "ssl_certificate": "/etc/weblcm-python/ssl/provisioning.crt",
            "ssl_private_key": "/etc/weblcm-python/ssl/provisioning.key",
            "ssl_certificate_chain": "",
        }

    if provisioning_state == ProvisioningState.PARTIALLY_PROVISIONED:
        return {
            "ssl_certificate": ServerConfig()
            .get(
                section="global",
                option="server.ssl_certificate",
                fallback="/etc/weblcm-python/ssl/server.crt",
            )
            .strip('"'),
            "ssl_private_key": ServerConfig()
            .get(
                section="global",
                option="server.ssl_private_key",
                fallback="/etc/weblcm-python/ssl/server.key",
            )
            .strip('"'),
            "ssl_certificate_chain": "",
        }

    return {
        "ssl_certificate": "",
        "ssl_private_key": "",
        "ssl_certificate_chain": "",
    }


def force_session_checking():
    """
    Raise HTTP 401 Unauthorized client error if a session with invalid id tries to assess following resources.
    HTMLs still can be loaded to keep consistency, i.e. loaded from local cache or remotely.
    """
    # Check if sessions are enabled
    if not cherrypy.request.app.config["/"].get("tools.sessions.on", True):
        return

    paths = [
        "connections",
        "connection",
        "accesspoints",
        "allowUnauthenticatedResetReboot",
        "networkInterfaces",
        "networkInterface",
        "networkInterfaceStatistics",
        "networkInterfaceDriverInfo",
        "file",
        "users",
        "firmware",
        "logData",
        "logSetting",
        "poweroff",
        "suspend",
        "files",
        "certificates",
        "datetime",
        "fips",
        "modemEnable",
        "wifiEnable",
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
            "tools.sessions.storage_class": RamBootTimeSession,
        }
    )

    # Configure SSL client authentication if enabled
    try:
        provisioning_state = CertificateProvisioning.get_provisioning_state()
        ssl_files = get_ssl_files(provisioning_state)

        if CertificateProvisioning.provisioning_enabled():
            if provisioning_state == ProvisioningState.UNPROVISIONED:
                # The device has not been provisioned yet, so enter restricted provisioning mode
                syslog("*** RESTRICTED PROVISIONING MODE ***")

                web_app = WebApp(provisioning_state=provisioning_state)
                config = definition.WEBLCM_PYTHON_SERVER_CONF_FILE
                cherrypy._global_conf_alias.update(config)

                cherrypy.tree.mount(web_app, "/", config)

                cherrypy.config.update(
                    {
                        "server.ssl_certificate": ssl_files["ssl_certificate"],
                        "server.ssl_private_key": ssl_files["ssl_private_key"],
                        "server.ssl_certificate_chain": ssl_files[
                            "ssl_certificate_chain"
                        ],
                    }
                )

                cherrypy.engine.signals.subscribe()
                cherrypy.engine.start()
                cherrypy.engine.block()
                return

        if ServerConfig().getboolean(
            section="weblcm", option="enable_client_auth", fallback=False
        ):
            from ssl import CERT_REQUIRED, OPENSSL_VERSION_NUMBER
            from cheroot.ssl.builtin import BuiltinSSLAdapter

            ssl_adapter = BuiltinSSLAdapter(
                certificate=ssl_files["ssl_certificate"],
                private_key=ssl_files["ssl_private_key"],
                certificate_chain=ssl_files["ssl_certificate_chain"],
            )
            if provisioning_state == ProvisioningState.FULLY_PROVISIONED:
                disable_certificate_expiry_verification = ServerConfig().getboolean(
                    section="weblcm",
                    option="disable_certificate_expiry_verification",
                    fallback=True,
                )

                if OPENSSL_VERSION_NUMBER >= 0x10101000:
                    # OpenSSL 1.1.1 or newer - we can use the built-in functionality to disable time
                    # checking during certificate verification, only if enabled
                    ssl_adapter.context.verify_mode = CERT_REQUIRED
                    if disable_certificate_expiry_verification:
                        ssl_adapter.context.verify_flags |= X509_V_FLAG_NO_CHECK_TIME
                else:
                    # OpenSSL 1.0.2 - we need to use the patched-in functionality to disable time
                    # checking during certificate verification, only if enabled
                    ssl_adapter.context.verify_mode = (
                        PY_SSL_CERT_REQUIRED_NO_CHECK_TIME
                        if disable_certificate_expiry_verification
                        else CERT_REQUIRED
                    )

                cherrypy.request.hooks.attach(
                    "before_handler", CertificateProvisioning.on_request_handler
                )
                syslog("SSL client authentication enabled")
            else:
                syslog("*** PARTIALLY PROVISIONED MODE ***")
            cherrypy.server.httpserver_from_self()[0].ssl_adapter = ssl_adapter
            cherrypy.server.ssl_context = ssl_adapter.context
        else:
            syslog("SSL client authentication NOT enabled")
    except Exception as e:
        syslog(LOG_ERR, f"Error configuring SSL client authentication - {str(e)}")

    web_app = WebApp(provisioning_state=provisioning_state)
    threading.Thread(target=web_app.datetime.populate_time_zone_list).start()
    cherrypy.quickstart(web_app, "/", config=definition.WEBLCM_PYTHON_SERVER_CONF_FILE)


def main(args=None):
    DBusManager().start()
    glib_mainloop = DBusManager().get_glib_mainloop()

    syslog("Starting webserver")
    threading.Thread(
        name="webserver_thread", target=weblcm_cherrypy_start, daemon=True
    ).start()

    syslog("Starting DBus mainloop")
    try:
        glib_mainloop.run()
    except KeyboardInterrupt:
        syslog("Received signal, shutting down service.")
    except Exception as e:
        syslog(f"Unexpected exception occurred: {str(e)}")
    finally:
        cherrypy.engine.exit()
        glib_mainloop.quit()
