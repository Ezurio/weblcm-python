import os
from threading import Lock

import cherrypy

from .. import definition


@cherrypy.expose
class AWMCfgManage(object):

    _lock = Lock()

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):

        # Infinite geo-location checks by default
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "AWM configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        # check if there is a configuration file which contains a "scan_attempts:0" entry
        # if configuration file does not exist, scan_attempts is not disabled
        f = cherrypy.request.app.config["weblcm"].get("awm_cfg", None)
        if not f or not os.path.isfile(f):
            return result

        with AWMCfgManage._lock:
            config = {}
            with open(f, "r", encoding="utf-8") as fp:
                for line in fp.readlines():
                    line_split = line.strip().split("=")
                    if len(line_split) == 2:
                        config[line_split[0]] = line_split[1]
            if "scan_attempts" in config:
                result["geolocation_scanning_enable"] = config["scan_attempts"]
                result["InfoMsg"] = ""

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        # Enable/disable geolocation scanning
        # 0: disable geolocation scanning
        # others: enable geolocation scanning
        result = {
            "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "AWM's geolocation scanning configuration only supported in LITE mode",
            "geolocation_scanning_enable": 1,
        }

        # determine if in LITE mode
        litemode = False
        with open("/etc/default/adaptive_ww", "r") as file:
            if "lite" in file.read().lower():
                litemode = True

        if not litemode:
            return result

        # prep for next error condition
        result["InfoMsg"] = "No writable configuration file found"
        # check if there is a configuration file which contains a "scan_attempts:0" entry
        # if writable configuration file does not exist, scan_attempts can not be modified

        f = cherrypy.request.app.config["weblcm"].get("awm_cfg", None)
        if not f:
            return result

        os.makedirs(os.path.dirname(f), exist_ok=True)

        geolocation_scanning_enable = cherrypy.request.json.get(
            "geolocation_scanning_enable", 0
        )

        with AWMCfgManage._lock:
            try:
                config = {}
                with open(f, "r", encoding="utf-8") as fp:
                    for line in fp.readlines():
                        line_split = line.strip().split("=")
                        if len(line_split) == 2:
                            config[line_split[0]] = line_split[1]
            except:
                config = {}

            need_store = False
            if geolocation_scanning_enable:
                if "scan_attempts" in config:
                    del config["scan_attempts"]
                    need_store = True
            else:
                config["scan_attempts"] = geolocation_scanning_enable
                need_store = True

            if need_store:
                with open(f, "w", encoding="utf-8") as fp:
                    for key, value in config.items():
                        fp.write(f"{key}={value}\n")

        result["geolocation_scanning_enable"] = geolocation_scanning_enable
        result["SDCERR"] = definition.WEBLCM_ERRORS["SDCERR_SUCCESS"]
        result["InfoMsg"] = ""
        return result
