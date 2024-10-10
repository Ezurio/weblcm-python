#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from syslog import syslog, LOG_ERR

import cherrypy

from .definition import WEBLCM_ERRORS
from .settings import SystemSettingsManage


@cherrypy.expose
class AllowUnauthenticatedResetReboot(object):
    @staticmethod
    def allow_unauthenticated_reset_reboot() -> bool:
        return cherrypy.request.app.config["weblcm"].get(
            "enable_allow_unauthenticated_reboot_reset", False
        ) and SystemSettingsManage.getBool("AllowUnauthenticatedRebootReset", False)

    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot set allow unauthenticated reset reboot",
        }

        try:
            if cherrypy.request.app.config["weblcm"].get(
                "enable_allow_unauthenticated_reboot_reset", False
            ) and SystemSettingsManage.update_persistent(
                "AllowUnauthenticatedRebootReset", str(True)
            ):
                result["InfoMsg"] = ""
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        return result

    @cherrypy.tools.json_out()
    def DELETE(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot clear allow unauthenticated reset reboot",
        }

        try:
            if SystemSettingsManage.update_persistent(
                "AllowUnauthenticatedRebootReset", str(False)
            ):
                result["InfoMsg"] = ""
                result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be set: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be set: {str(e)}"
            )
        return result

    @cherrypy.tools.json_out()
    def GET(self):
        result = {
            "SDCERR": WEBLCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "Cannot read allow unauthenticated reset reboot",
        }

        try:
            result[
                "allowUnauthenticatedRebootReset"
            ] = self.allow_unauthenticated_reset_reboot()
            result["InfoMsg"] = ""
            result["SDCERR"] = WEBLCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as e:
            result[
                "SDCERR"
            ] = f"AllowUnauthenticatedRebootReset cannot be read: {str(e)}"
            syslog(
                LOG_ERR, f"AllowUnauthenticatedRebootReset" f" cannot be read: {str(e)}"
            )
        return result
