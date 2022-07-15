from syslog import LOG_ERR, syslog
import cherrypy
import dbus
import time
from systemd import journal
from . import definition


@cherrypy.expose
class LogData(object):
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {"SDCERR": 0, "InfoMsg": ""}
        logs = []

        reader = journal.Reader()
        try:
            priority = int(kwargs.get("priority", 7))
        except Exception as e:
            syslog(
                LOG_ERR, f"Error parsing 'priority' parameter as an integer: {str(e)}"
            )
            return {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
        if priority not in range(0, 8, 1):
            return {"SDCERR": 1, "InfoMsg": "Priority must be an int between 0-7"}
        reader.log_level(priority)
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
        if typ != "All":
            reader.add_match(SYSLOG_IDENTIFIER=typ)
        try:
            days = int(kwargs.get("days", 1))
        except Exception as e:
            syslog(LOG_ERR, f"Error parsing 'days' parameter as an integer: {str(e)}")
            return {"SDCERR": 1, "InfoMsg": "days must be an int"}
        if days > 0:
            reader.seek_realtime(time.time() - days * 86400)

        for entry in reader:
            log = {}
            log["time"] = str(entry.get("__REALTIME_TIMESTAMP", "Undefined"))
            log["priority"] = str(entry.get("PRIORITY", 7))
            log["identifier"] = entry.get("SYSLOG_IDENTIFIER", "Undefined")
            log["message"] = entry.get("MESSAGE", "Undefined")
            logs.append(log)

        result["InfoMsg"] = f"type: {typ}; days: {days}; Priority: {priority}"
        result["count"] = len(logs)
        result["log"] = logs
        reader.close()
        return result


@cherrypy.expose
class LogSetting(object):
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        result = {"SDCERR": 1, "InfoMsg": ""}
        post_data = cherrypy.request.json

        if not "suppDebugLevel" in post_data:
            result["InfoMsg"] = "suppDebugLevel missing from JSON data"
            return result
        if not "driverDebugLevel" in post_data:
            result["InfoMsg"] = "driverDebugLevel missing from JSON data"
            return result

        levels = {"none", "error", "warning", "info", "debug", "msgdump", "excessive"}
        supp_level = post_data.get("suppDebugLevel").lower()
        if not supp_level in levels:
            result["InfoMsg"] = f"suppDebugLevel must be one of {levels}"
            return result

        try:
            bus = dbus.SystemBus()
            proxy = bus.get_object(definition.WPA_IFACE, definition.WPA_OBJ)
            wpas = dbus.Interface(proxy, definition.DBUS_PROP_IFACE)
            wpas.Set(definition.WPA_IFACE, "DebugLevel", supp_level)
        except Exception as e:
            result["InfoMsg"] = "unable to set supplicant debug level"
            return result

        drv_level = post_data.get("driverDebugLevel")
        try:
            drv_level = int(drv_level)
        except Exception as e:
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            return result

        if not (drv_level == 0 or drv_level == 1):
            result["InfoMsg"] = "driverDebugLevel must be 0 or 1"
            return result

        try:
            driver_debug_file = open(definition.WIFI_DRIVER_DEBUG_PARAM, "w")
            if driver_debug_file.mode == "w":
                driver_debug_file.write(str(drv_level))
        except Exception as e:
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
            bus = dbus.SystemBus()
            proxy = bus.get_object(definition.WPA_IFACE, definition.WPA_OBJ)
            wpas = dbus.Interface(proxy, definition.DBUS_PROP_IFACE)
            debug_level = wpas.Get(definition.WPA_IFACE, "DebugLevel")
            result["suppDebugLevel"] = debug_level
        except Exception as e:
            result["Errormsg"] = "Unable to determine supplicant debug level"
            result["SDCERR"] = 1

        try:
            driver_debug_file = open(definition.WIFI_DRIVER_DEBUG_PARAM, "r")
            if driver_debug_file.mode == "r":
                contents = driver_debug_file.read(1)
                result["driverDebugLevel"] = contents
        except Exception as e:
            if result.get("SDCERR") == 0:
                result["Errormsg"] = "Unable to determine driver debug level"
            else:
                result[
                    "Errormsg"
                ] = "Unable to determine supplicant nor driver debug level"
            result["SDCERR"] = 1

        return result
