from syslog import syslog, LOG_ERR
import time
from typing import Tuple, List
import cherrypy
from weblcm.definition import (
    TIMEDATE1_BUS_NAME,
    TIMEDATE1_MAIN_OBJ,
    WEBLCM_ERRORS,
    WEBLCM_PYTHON_TIME_FORMAT,
)
from weblcm.provisioning import CertificateProvisioning
import dbus
from weblcm.utils import DBusManager
from datetime import datetime, timezone

LOCALTIME = "/etc/localtime"
ZONEINFO = "/usr/share/zoneinfo/"
ETC_TIMEZONE = "/etc/timezone"


@cherrypy.expose
class DateTimeSetting(object):
    def __init__(self):
        self._zones: List[str] = []

    @property
    def zones(self) -> List[str]:
        """
        List of available time zones
        """
        return self._zones

    @property
    def local_zone(self) -> str:
        """
        Current local time zone
        """
        try:
            with open(ETC_TIMEZONE, "r") as etc_timezone_file:
                return etc_timezone_file.readline().strip()
        except Exception as e:
            syslog(LOG_ERR, f"Get local time zone failure: {str(e)}")
            return "Unable to determine timezone"

    @staticmethod
    def set_datetime(timestamp_usec: int):
        """
        Set the system time using the given timestamp (in microseconds) after first setting the
        validity period (also in microseconds, if provided) and verifying the new timestamp against
        the validity period.
        """
        if not CertificateProvisioning.validate_new_timestamp(int(timestamp_usec)):
            raise InvalidTimestampError()

        # Call the SetTime() method passing the provided timestamp (in usec_utc), set the 'relative'
        # parameter to False, and set the 'interactive' parameter to False. See below for more info:
        # https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
        dbus.Interface(
            DBusManager()
            .get_system_bus()
            .get_object(TIMEDATE1_BUS_NAME, TIMEDATE1_MAIN_OBJ),
            TIMEDATE1_BUS_NAME,
        ).SetTime(timestamp_usec, False, False)

        CertificateProvisioning.time_set_callback()

    def set_time_zone(self, new_zone: str):
        # Call the SetTimezone() method passing the provided time zone and set the
        # 'interactive' parameter to False.
        # See below for more info:
        # https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
        dbus.Interface(
            DBusManager()
            .get_system_bus()
            .get_object(TIMEDATE1_BUS_NAME, TIMEDATE1_MAIN_OBJ),
            TIMEDATE1_BUS_NAME,
        ).SetTimezone(new_zone, False)

        # Re-evaluate the timezone - this is necessary as the WebLCM Python process itself
        # doesn't automatically pick up on the timezone change.
        time.tzset()

    def populate_time_zone_list(self):
        """
        Populate the list of available time zones from systemd-timedated.
        """
        try:
            # Call the ListTimezones() method.
            # See below for more info:
            # https://www.freedesktop.org/software/systemd/man/org.freedesktop.timedate1.html
            zones_from_systemd = dbus.Interface(
                DBusManager()
                .get_system_bus()
                .get_object(TIMEDATE1_BUS_NAME, TIMEDATE1_MAIN_OBJ),
                TIMEDATE1_BUS_NAME,
            ).ListTimezones()

            zones_to_return = []
            for time_zone in zones_from_systemd:
                zones_to_return.append(str(time_zone))
            self._zones = zones_to_return
        except Exception as e:
            syslog(LOG_ERR, f"Could not populate time zone list: {str(e)}")
            self._zones = []

    def check_current_date_and_time(self) -> Tuple[bool, str]:
        """
        Retrieve the current date/time adjusted for the current time zone.

        The return value is a tuple containing a boolean indicating success/failure and a string
        (the current date and time for success, otherwise an error message).
        """
        try:
            # Re-evaluate the timezone - this is necessary as the WebLCM Python process itself
            # doesn't automatically pick up on the timezone change.
            time.tzset()

            return (
                True,
                datetime.now(timezone.utc)
                .astimezone()
                .strftime(WEBLCM_PYTHON_TIME_FORMAT),
            )
        except Exception as e:
            syslog(LOG_ERR, f"Get current date and time failure: {str(e)}")
            return (False, f"Get current date and time failure: {str(e)}")

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        result["zones"] = self.zones
        result["zone"] = self.local_zone

        success, msg = self.check_current_date_and_time()
        if success:
            result["method"] = "auto"
            result["time"] = msg.strip()
        else:
            result["method"] = "manual"
            result["time"] = ""

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        zone = cherrypy.request.json.get("zone", "")
        method = cherrypy.request.json.get("method", "")
        dt = cherrypy.request.json.get("datetime", "")

        # Setting the timezone was initially supported when 'zone' was not an empty string so
        # re-create that here.
        if zone != "":
            try:
                self.set_time_zone(zone)
            except Exception as e:
                syslog(LOG_ERR, f"Could not set timezone: {str(e)}")
                result["InfoMsg"] = f"Could not set timezone: {str(e)}"
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_FAIL"]
                return result
        # Setting the time was initially supported when 'method' is set to 'manual' so re-create
        # that here.
        elif method == "manual" and dt != "":
            try:
                self.set_datetime(int(dt))
            except InvalidTimestampError:
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = "Invalid timestamp"

                # Return current timestamp and validity period
                result["time"] = (
                    datetime.now(timezone.utc)
                    .astimezone()
                    .strftime(WEBLCM_PYTHON_TIME_FORMAT)
                )
                try:
                    (
                        not_before,
                        not_after,
                    ) = CertificateProvisioning.get_validity_period()
                    result["notBefore"] = not_before.strftime(WEBLCM_PYTHON_TIME_FORMAT)
                    result["notAfter"] = not_after.strftime(WEBLCM_PYTHON_TIME_FORMAT)
                except Exception as exception:
                    syslog(
                        LOG_ERR,
                        f"Could not retrieve validity period - {str(exception)}",
                    )

                return result
            except Exception as e:
                syslog(LOG_ERR, f"Could not set datetime: {str(e)}")
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = "Could not set datetime"
                return result

        # Unless we hit an error, the previous logic would return the current date and time (and
        # timezone), so re-create that here.
        success, msg = self.check_current_date_and_time()
        if success:
            result["time"] = msg
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = self.local_zone
        else:
            result["InfoMsg"] = msg
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_FAIL"]
        return result


class InvalidTimestampError(ValueError):
    """Custom error class for when an invalid timestamp is provided."""
