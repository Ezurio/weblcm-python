"""Module to support log forwarding functionality"""

import os
from syslog import LOG_ERR, syslog
import cherrypy
from weblcm.systemd_unit import SystemdUnit
from weblcm.definition import (
    LOG_FORWARDING_ENABLED_FLAG_FILE,
    WEBLCM_ERRORS,
    SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE,
)


@cherrypy.expose
class LogForwarding(SystemdUnit):
    """CherryPy-exposed class to handle log forwarding functionality"""

    def __init__(self) -> None:
        super().__init__(SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE)

    @cherrypy.tools.json_out()
    def GET(self):
        """GET handler for the /logForwarding endpoint"""
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
        except Exception as exception:
            syslog(
                LOG_ERR, f"Could not retrieve log forwarding state: {str(exception)}"
            )

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        """PUT handler for the /logForwarding endpoint"""
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
        except Exception as exception:
            syslog(LOG_ERR, f"Could not set log forwarding state: {str(exception)}")
            result = {
                "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": "Could not set log forwarding state",
            }

        return result
