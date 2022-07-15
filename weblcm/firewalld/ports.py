import logging
from syslog import syslog, LOG_ERR
from typing import Optional, List

import cherrypy
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

from weblcm import definition

# TODO: USER_PERMISSION_TYPES for Ports

FIREWALLD_TIMEOUT_SECONDS = 20
FIREWALLD_SERVICE_NAME = "org.fedoraproject.FirewallD1"
FIREWALLD_OBJECT_PATH = "/org/fedoraproject/FirewallD1"
FIREWALLD_ZONE_INTERFACE = "org.fedoraproject.FirewallD1.zone"


def firewalld_forward_port(
    zone: str, port: str, protocol: str, toport: str, toaddr: str
):
    bus = dbus.SystemBus()
    bus.call_blocking(
        bus_name=FIREWALLD_SERVICE_NAME,
        object_path=FIREWALLD_OBJECT_PATH,
        dbus_interface=FIREWALLD_ZONE_INTERFACE,
        method="addForwardPort",
        signature="sssssi",
        args=[
            dbus.String(zone),
            dbus.String(port),
            dbus.String(protocol),
            dbus.String(toport),
            dbus.String(toaddr),
            dbus.Int32(0),
        ],
        timeout=FIREWALLD_TIMEOUT_SECONDS,
    )


def firewalld_remove_forward_port(
    zone: str, port: str, protocol: str, toport: str, toaddr: str
):
    bus = dbus.SystemBus()
    bus.call_blocking(
        bus_name=FIREWALLD_SERVICE_NAME,
        object_path=FIREWALLD_OBJECT_PATH,
        dbus_interface=FIREWALLD_ZONE_INTERFACE,
        method="removeForwardPort",
        signature="sssss",
        args=[
            dbus.String(zone),
            dbus.String(port),
            dbus.String(protocol),
            dbus.String(toport),
            dbus.String(toaddr),
        ],
        timeout=FIREWALLD_TIMEOUT_SECONDS,
    )


def firewalld_get_forward_ports(zone: str):
    bus = dbus.SystemBus()
    return bus.call_blocking(
        bus_name=FIREWALLD_SERVICE_NAME,
        object_path=FIREWALLD_OBJECT_PATH,
        dbus_interface=FIREWALLD_ZONE_INTERFACE,
        method="getForwardPorts",
        signature="s",
        args=[
            dbus.String(zone),
        ],
        timeout=FIREWALLD_TIMEOUT_SECONDS,
    )


def check_parameters(post_data, parameters: List[str]):
    for parameter in parameters:
        if parameter not in post_data:
            raise ValueError(f"required parameter '{parameter}' not specified")


@cherrypy.expose
@cherrypy.popargs("zone", "command")
class Ports(object):
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.port_commands = ["addForwardPort", "removeForwardPort"]

    def log_exception(self, e, message: str = ""):
        self._logger.exception(e)
        syslog(LOG_ERR, message + str(e))

    @staticmethod
    def result_parameter_not_one_of(parameter: str, supplied_value: str, not_one_of):
        return {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied parameter '{parameter}' value {supplied_value} must be one of"
            f" {not_one_of}, ",
        }

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            check_parameters(cherrypy.request.params, ["zone"])
            zone = cherrypy.request.params["zone"]

            filters: Optional[List[str]] = None
            if "filter" in cherrypy.request.params:
                filters = cherrypy.request.params["filter"].split(",")

            if not filters or "Forward" in filters:
                result["Forward"] = firewalld_get_forward_ports(zone)
                matched_filter = True

            if filters and not matched_filter:
                result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = f"filters {filters} not matched"
                return result
            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        return result

    @cherrypy.tools.json_in()
    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            check_parameters(cherrypy.request.params, ["zone"])
            zone = cherrypy.request.params["zone"]
            command = (
                cherrypy.request.params["command"]
                if "command" in cherrypy.request.params
                else None
            )

            post_data = cherrypy.request.json

            if command:
                if command not in self.port_commands:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, self.port_commands
                        )
                    )
                else:
                    if command == "addForwardPort":
                        check_parameters(
                            post_data, ["port", "protocol", "toport", "toaddr"]
                        )
                        port = post_data["port"]
                        protocol = post_data["protocol"]
                        toport = post_data["toport"]
                        toaddr = post_data["toaddr"]
                        firewalld_forward_port(zone, port, protocol, toport, toaddr)
                        result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
                    elif command == "removeForwardPort":
                        check_parameters(
                            post_data, ["port", "protocol", "toport", "toaddr"]
                        )
                        port = post_data["port"]
                        protocol = post_data["protocol"]
                        toport = post_data["toport"]
                        toaddr = post_data["toaddr"]
                        firewalld_remove_forward_port(
                            zone, port, protocol, toport, toaddr
                        )
                        result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"

                return result

        except Exception as e:
            result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_FAIL"]
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        return result
