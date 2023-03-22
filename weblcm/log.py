import json
import os
from syslog import LOG_ERR, syslog
import cherrypy
import dbus
import time
from datetime import datetime
from .systemd_unit import SystemdUnit
from .settings import SystemSettingsManage
from subprocess import run
from .definition import (
    LOG_FORWARDING_ENABLED_FLAG_FILE,
    WEBLCM_ERRORS,
    WPA_IFACE,
    WPA_OBJ,
    WIFI_DRIVER_DEBUG_PARAM,
    DBUS_PROP_IFACE,
    SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE,
)
from .utils import DBusManager


@cherrypy.expose
class LogData(object):
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            priority = int(kwargs.get("priority", 7))
        except Exception as e:
            syslog(
                LOG_ERR, f"Error parsing 'priority' parameter as an integer: {str(e)}"
            )
            return {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
        if priority not in range(0, 8, 1):
            return {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
        # use .lower() to ensure incoming type has comparable case
        typ = kwargs.get("type", "All").lower()
        # TODO - documentation says 'python' is lower case while others are upper/mixed case.
        if typ == "networkmanager":
            typ = "NetworkManager"
        elif typ == "all":
            typ = "All"
        elif typ == "python":
            typ = "weblcm-python"
        types = {
            "kernel",
            "NetworkManager",
            "weblcm-python",
            "adaptive_ww",
            "All",
        }
        if typ not in types:
            return {
                "SDCERR": 1,
                "InfoMsg": f"supplied type parameter must be one of {str(types)}",
            }
        try:
            days = int(kwargs.get("days", 1))
        except Exception as e:
            syslog(LOG_ERR, f"Error parsing 'days' parameter as an integer: {str(e)}")
            return {"SDCERR": 1, "InfoMsg": "days must be an int"}

        try:
            journalctl_args = [
                "journalctl",
                f"--priority={str(priority)}",
                "--output=json",
            ]
            if typ != "All":
                journalctl_args.append(f"--identifier={str(typ)}")
            if days > 0:
                journalctl_args.append(
                    f"--since={datetime.fromtimestamp(time.time() - days * 86400).strftime('%Y-%m-%d %H:%M:%S')}"
                )

            proc = run(
                journalctl_args,
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if proc.returncode == 0:
                logs = []
                for line in str(proc.stdout.decode("utf-8")).split("\n"):
                    if line.strip() == "":
                        # The last line is empty, so break if we see it
                        break
                    entry = json.loads(line)
                    log = {}
                    timestamp = str(entry.get("__REALTIME_TIMESTAMP", "Undefined"))
                    log["time"] = (
                        datetime.fromtimestamp(float(timestamp) / 1000000).strftime(
                            "%Y-%m-%d %H:%M:%S.%f"
                        )
                        if timestamp != "Undefined"
                        else "Undefined"
                    )
                    log["priority"] = str(entry.get("PRIORITY", 7))
                    log["identifier"] = entry.get("SYSLOG_IDENTIFIER", "Undefined")
                    log["message"] = entry.get("MESSAGE", "Undefined")
                    logs.append(log)
                result["InfoMsg"] = f"type: {typ}; days: {days}; Priority: {priority}"
                result["count"] = len(logs)
                result["log"] = logs
                return result
            else:
                syslog(
                    LOG_ERR,
                    f"journalctl error - returncode: {str(proc.returncode)}, stderr: {str(proc.stderr.decode('utf-8'))}",
                )
                return {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}

        except Exception as e:
            syslog(LOG_ERR, f"Could not read journal logs: {str(e)}")
            return {"SDCERR": 1, "InfoMsg": "Could not read journal logs"}


@cherrypy.expose
class LogForwarding(SystemdUnit):
    def __init__(self) -> None:
        super().__init__(SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE)

    @cherrypy.tools.json_out()
    def GET(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not retrieve log forwarding state",
            "state": "unknown",
        }

        try:
            result["state"] = self.active_state
            if result["state"] != "unknown":
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
                result["InfoMsg"] = ""
        except Exception as e:
            syslog(LOG_ERR, f"Could not retrieve log forwarding state: {str(e)}")

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Could not set log forwarding state",
        }

        try:
            valid_states = ["active", "inactive"]

            post_data = cherrypy.request.json
            requested_state = post_data.get("state", None)
            if not requested_state:
                result["InfoMsg"] = f"Invalid state; valid states: {valid_states}"
                return result
            if requested_state not in valid_states:
                result[
                    "InfoMsg"
                ] = f"Invalid state: {requested_state}; valid states: {valid_states}"
                return result

            # Read the current 'ActiveState' of the log forwarding service
            current_state = self.active_state

            if requested_state == "active":
                # Create the 'flag file' which systemd uses to determine if it should start the
                # systemd-journal-gatewayd.socket unit.
                with open(LOG_FORWARDING_ENABLED_FLAG_FILE, "w"):
                    pass

                if current_state == "active":
                    # Service already active
                    result["InfoMsg"] = "Log forwarding already active"
                    result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
                else:
                    # Activate service
                    if self.activate():
                        result["InfoMsg"] = "Log forwarding activated"
                        result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
            elif requested_state == "inactive":
                # Remove the 'flag file' which systemd uses to determine if it should start the
                # systemd-journal-gatewayd.socket unit.
                try:
                    os.remove(LOG_FORWARDING_ENABLED_FLAG_FILE)
                except OSError:
                    # Handle the case where the file isn't already present
                    pass

                if current_state == "inactive":
                    # Service is already inactive
                    result["InfoMsg"] = "Log forwarding already inactive"
                    result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
                else:
                    # Deactivate service
                    if self.deactivate():
                        result["InfoMsg"] = "Log forwarding deactivated"
                        result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            syslog(LOG_ERR, f"Could not set log forwarding state: {str(e)}")
            result = {
                "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set log forwarding state",
            }

        return result


@cherrypy.expose
class LogSetting(object):
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        result = {"SDCERR": 1, "InfoMsg": ""}
        post_data = cherrypy.request.json

        if "suppDebugLevel" not in post_data:
            result["InfoMsg"] = "suppDebugLevel missing from JSON data"
            return result
        if "driverDebugLevel" not in post_data:
            result["InfoMsg"] = "driverDebugLevel missing from JSON data"
            return result

        levels = {"none", "error", "warning", "info", "debug", "msgdump", "excessive"}
        supp_level = post_data.get("suppDebugLevel").lower()
        if supp_level not in levels:
            result["InfoMsg"] = f"suppDebugLevel must be one of {levels}"
            return result

        try:
            bus = DBusManager().get_system_bus()
            proxy = bus.get_object(WPA_IFACE, WPA_OBJ)
            wpas = dbus.Interface(proxy, DBUS_PROP_IFACE)
            wpas.Set(WPA_IFACE, "DebugLevel", supp_level)
        except Exception as e:
            syslog(LOG_ERR, f"unable to set supplicant debug level: {str(e)}")
            result["InfoMsg"] = "unable to set supplicant debug level"
            return result

        drv_level = post_data.get("driverDebugLevel")
        try:
            drv_level = int(drv_level)
        except Exception:
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            return result

        if not (drv_level == 0 or drv_level == 1):
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            return result

        try:
            driver_debug_file = open(WIFI_DRIVER_DEBUG_PARAM, "w")
            if driver_debug_file.mode == "w":
                driver_debug_file.write(str(drv_level))
        except Exception as e:
            syslog(LOG_ERR, f"unable to set driver debug level: {str(e)}")
            result["InfoMsg"] = "unable to set driver debug level"
            return result

        result["SDCERR"] = 0
        result[
            "InfoMsg"
        ] = f"Supplicant debug level = {supp_level}; Driver debug level = {drv_level}"

        return result

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {"SDCERR": 0, "InfoMsg": ""}

        try:
            bus = DBusManager().get_system_bus()
            proxy = bus.get_object(WPA_IFACE, WPA_OBJ)
            wpas = dbus.Interface(proxy, DBUS_PROP_IFACE)
            debug_level = wpas.Get(WPA_IFACE, "DebugLevel")
            result["suppDebugLevel"] = debug_level
        except Exception as e:
            syslog(LOG_ERR, f"Unable to determine supplicant debug level: {str(e)}")
            result["Errormsg"] = "Unable to determine supplicant debug level"
            result["SDCERR"] = 1

        try:
            driver_debug_file = open(WIFI_DRIVER_DEBUG_PARAM, "r")
            if driver_debug_file.mode == "r":
                contents = driver_debug_file.read(1)
                result["driverDebugLevel"] = contents
        except Exception as e:
            syslog(LOG_ERR, f"Unable to determine driver debug level: {str(e)}")
            if result.get("SDCERR") == 0:
                result["Errormsg"] = "Unable to determine driver debug level"
            else:
                result[
                    "Errormsg"
                ] = "Unable to determine supplicant nor driver debug level"
            result["SDCERR"] = 1

        return result
