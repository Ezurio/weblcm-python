import cherrypy
import os
from syslog import syslog, LOG_ERR
from subprocess import run, call, TimeoutExpired, CalledProcessError
from .definition import (
    WEBLCM_ERRORS,
    LOGIND_BUS_NAME,
    LOGIND_MAIN_OBJ,
    LOGIND_MAIN_IFACE,
    MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE,
)
from .settings import SystemSettingsManage
import dbus
from .utils import DBusManager


@cherrypy.expose
class PowerOff(object):
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Poweroff cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            return result

        try:
            bus = DBusManager().get_system_bus()
            manager = dbus.Interface(
                bus.get_object(LOGIND_BUS_NAME, LOGIND_MAIN_OBJ), LOGIND_MAIN_IFACE
            )

            # Call PowerOff() (non-interactive)
            manager.PowerOff(False)

            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Poweroff initiated"
        except Exception as e:
            syslog(LOG_ERR, f"Poweroff cannot be initiated: {str(e)}")

        return result


@cherrypy.expose
class Suspend(object):
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Suspend cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            return result

        try:
            bus = DBusManager().get_system_bus()
            manager = dbus.Interface(
                bus.get_object(LOGIND_BUS_NAME, LOGIND_MAIN_OBJ), LOGIND_MAIN_IFACE
            )

            # Call Suspend() (non-interactive)
            manager.Suspend(False)

            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Suspend initiated"

            cherrypy.lib.sessions.expire()
        except Exception as e:
            syslog(LOG_ERR, f"Suspend cannot be initiated: {str(e)}")

        return result


@cherrypy.expose
class Reboot(object):
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Reboot cannot be initiated",
        }

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            return result

        try:
            bus = DBusManager().get_system_bus()
            manager = dbus.Interface(
                bus.get_object(LOGIND_BUS_NAME, LOGIND_MAIN_OBJ), LOGIND_MAIN_IFACE
            )

            # Call Reboot() (non-interactive)
            manager.Reboot(False)

            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = "Reboot initiated"
        except Exception as e:
            syslog(LOG_ERR, f"Reboot cannot be initiated: {str(e)}")

        return result


@cherrypy.expose
class FactoryReset(object):
    FACTORY_RESET_SCRIPT = "/usr/sbin/do_factory_reset.sh"

    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "FactoryReset cannot be initiated",
        }

        if not os.path.exists(self.FACTORY_RESET_SCRIPT):
            result["InfoMsg"] += " - not available on non-encrypted file system images"
            return result

        if os.path.exists(MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE):
            result["InfoMsg"] += " - modem firmware update in progress"
            return result

        syslog("Factory Reset requested")
        try:
            returncode = call([self.FACTORY_RESET_SCRIPT, "reset"])
        except BaseException:
            returncode = -1
        result["SDCERR"] = returncode
        if returncode == 0:
            result["InfoMsg"] = "Reboot required"
        else:
            result["InfoMsg"] = "Error running factory reset"
            syslog("FactoryReset's returned % d" % returncode)

        return result


@cherrypy.expose
class Fips(object):

    FIPS_SCRIPT = "/usr/bin/fips-set"

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Reboot required",
        }

        setOptions = ["unset", "fips", "fips_wifi"]

        post_data = cherrypy.request.json
        fips = post_data.get("fips", None)
        if fips not in setOptions:
            result["InfoMsg"] = f"Invalid option: {fips}; valid options: {setOptions}"
            return result

        try:
            run(
                [Fips.FIPS_SCRIPT, fips],
                check=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result["InfoMsg"] = "FIPS SET error"

        except FileNotFoundError:
            result["InfoMsg"] = "Not a FIPS image"

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result["InfoMsg"] = "FIPS SET timeout"

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result["InfoMsg"] = "FIPS SET exception: {}".format(e)

        try:
            from .stunnel.stunnel import Stunnel

            if fips == "fips" or fips == "fips_wifi":
                Stunnel.configure_fips(enabled=True)
            elif fips == "unset":
                Stunnel.configure_fips(enabled=False)
        except ImportError:
            # stunnel module not loaded
            pass
        except Exception as e:
            syslog("FIPS stunnel set exception: %s" % e)
            result["InfoMsg"] = "FIPS stunnel SET exception: {}".format(e)

        return result

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
            "status": "unset",
        }

        try:
            p = run(
                [Fips.FIPS_SCRIPT, "status"],
                capture_output=True,
                check=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            result["status"] = p.stdout.decode("utf-8").strip()
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result["InfoMsg"] = "FIPS SET error"

        except FileNotFoundError:
            result["InfoMsg"] = "Not a FIPS image"
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result["InfoMsg"] = "FIPS SET timeout"

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result["InfoMsg"] = "FIPS SET exception: {}".format(e)

        return result
