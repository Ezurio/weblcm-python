#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
import logging
import shutil
from subprocess import Popen
from syslog import syslog, LOG_ERR
from typing import Tuple, Optional

import cherrypy
import swclient

from . import swuclient
from .somutil import get_current_side

swclient_fd: int = -1

FILE_STREAMING_BUFFER_SIZE = 128 * 1024


class StreamingUpdateFile:
    """File-like object to handle streaming data from a PUT request and forward it to swupdate."""

    def write(self, data):
        """Write a block of data to swupdate"""
        try:
            if swclient_fd < 0:
                syslog(
                    LOG_ERR, "swupdate.py: StreamingUpdateFile: no update in progress"
                )
                raise cherrypy.HTTPError(
                    500, "Software Update error: no update in progress"
                )
            rc = swclient.do_fw_update(data, swclient_fd)
            if rc < 0:
                syslog(
                    LOG_ERR,
                    f"swclient.do_firmware_update returned {rc} while processing octet stream",
                )
                raise cherrypy.HTTPError(
                    500, f"Software Update received error: {rc} while updating"
                )
        except Exception as exception:
            syslog(LOG_ERR, "StreamingUpdateFile: " + str(exception))
            raise exception


@cherrypy.expose
class SWUpdate:
    FW_UPDATE_SCRIPT = "fw_update"

    SWU_SDCERR_UPDATED = 0
    SWU_SDCERR_FAIL = 1
    SWU_SDCERR_NOT_UPDATING = 2
    SWU_SDCERR_UPDATING = 5

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.swupdate_client = None
        self.proc: Optional[Popen[str]] = None
        self.status = self.SWU_SDCERR_NOT_UPDATING

    def log_exception(self, e, message: str = ""):
        self._logger.exception(e)
        syslog(LOG_ERR, message + str(e))

    def get_running_mode_for_update(self, image):
        try:
            running_mode = image + "-b" if get_current_side() == "a" else image + "-a"
        except Exception as e:
            self.log_exception(e)
            raise e

        return running_mode

    def get_update_status(self) -> Tuple[int, str]:
        try:
            info = ""
            if self.status == self.SWU_SDCERR_UPDATED:
                info = "Updated"
            elif self.status == self.SWU_SDCERR_FAIL:
                info = "Failed"
            elif self.status == self.SWU_SDCERR_NOT_UPDATING:
                info = "No update in progress"
            elif self.status == self.SWU_SDCERR_UPDATING:
                info = "Updating..."
            return self.status, info

        except Exception as e:
            self.log_exception(e)
            return self.SWU_SDCERR_FAIL, f"Error: {str(e)}"

    def recv_handler(self, status, rcurr_img, msg):
        if status in [swuclient.SWU_STATUS_SUCCESS, swuclient.SWU_STATUS_FAILURE]:
            # See swupdate-progress.c
            # Latch success & failure messages, ignoring all others.
            if status == swuclient.SWU_STATUS_SUCCESS:
                self.status = self.SWU_SDCERR_UPDATED
            elif status == swuclient.SWU_STATUS_FAILURE:
                self.status = self.SWU_SDCERR_FAIL
            # Close down the thread after completion
            self.stop_progress_thread()

    def stop_progress_thread(self):
        """stop the progress thread"""
        if self.swupdate_client:
            self.swupdate_client.stop_progress_thread()

    def PUT(self):
        content_type = cherrypy.request.headers.get("Content-Type", None)
        if not content_type or content_type != "application/octet-stream":
            raise cherrypy.HTTPError(
                415, "Expected an application/octet-stream content type"
            )

        # In order to support chunked file streaming, we can use the copyfileobj() function which
        # supports reading from a file-like object (the request body) in chunks and writing each
        # chunk one-at-a-time to another file-like object (StreamingUpdateFile).
        shutil.copyfileobj(
            fsrc=cherrypy.request.body,
            fdst=StreamingUpdateFile(),
            length=FILE_STREAMING_BUFFER_SIZE,
        )

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):

        result = {"SDCERR": 1, "InfoMsg": "Device is busy"}

        try:
            (result["SDCERR"], result["InfoMsg"]) = self.get_update_status()
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = f"Error: {str(e)}"

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        global swclient_fd
        dryrun = 0

        result = {
            "SDCERR": 1,
            "InfoMsg": "Device is busy updating.",
        }

        def do_swupdate(
            args,
        ):
            try:
                # close_fds prevents hang on service stop
                self.proc = Popen(args, close_fds=True)
                result["InfoMsg"] = ""
                result["SDCERR"] = 0
            except Exception as e:
                self.log_exception(e)
                result["InfoMsg"] = "{}".format(e)

        if self.swupdate_client and self.swupdate_client.update_in_progress:
            return result

        url = cherrypy.request.json.get("url", None)
        if url and " " in url:
            result["InfoMsg"] = "Invalid URL"
            return result
        image = cherrypy.request.json.get("image", "main")
        running_mode = self.get_running_mode_for_update(image)

        try:
            if self.swupdate_client is None:
                self.swupdate_client = swuclient.SWUpdateClient(self.recv_handler)
            else:
                self.swupdate_client.state = None
            if self.swupdate_client.open_ipc() < 0:
                return
            if url:
                do_swupdate(
                    args=[SWUpdate.FW_UPDATE_SCRIPT, "-x", "r", "-m", image, url],
                )
            else:
                swclient_fd = swclient.prepare_fw_update(dryrun, "stable", running_mode)
                if swclient_fd > 0:
                    result["InfoMsg"] = ""
                    result["SDCERR"] = 0
            self.swupdate_client.start_progress_thread(swclient_fd)
        except Exception as e:
            self.log_exception(e)
            result["InfoMsg"] = "{}".format(e)

        if result["SDCERR"]:
            self.stop_progress_thread()
        else:
            # In order to avoid race condition between first update coming from swupdate_client and
            # external REST query, just assume update started unless/until a failure or completion
            # occurs.
            self.status = self.SWU_SDCERR_UPDATING

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def DELETE(self):
        result = {"SDCERR": 0, "InfoMsg": ""}
        try:
            self.stop_progress_thread()
        except Exception as e:
            self.log_exception(e)
            result["SDCERR"] = 1
            result["InfoMsg"] = "{}".format(e)
        return result
