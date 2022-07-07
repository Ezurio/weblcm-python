import cherrypy
from threading import Lock
import swclient
from syslog import syslog
from subprocess import run, call, TimeoutExpired
from .settings import SystemSettingsManage


def octet_stream_in(force=True, debug=False):

    request = cherrypy.serving.request
    if not request.body:
        return

    def octet_stream_processor(entity):
        # Read application/octet-stream data into request.json.
        if not entity.headers.get("Content-Length", ""):
            raise cherrypy.HTTPError(411)
        try:
            data = entity.read()
            rc = swclient.do_fw_update(data)
            if rc < 0:
                syslog(
                    f"swclient.do_firmware_update returned {rc} while processing octect_stream"
                )
                raise cherrypy.HTTPError(
                    500, f"Software Update received error: {rc} while updating"
                )
        except OSError as err:
            raise err

    if force:
        request.body.processors.clear()
        request.body.default_proc = cherrypy.HTTPError(
            415, "Expected an application/octet-stream content type"
        )
    request.body.processors["application/octet-stream"] = octet_stream_processor


@cherrypy.expose
class SWUpdate:
    SWUPDATE_SCRIPT = "/etc/weblcm-python/scripts/weblcm_swupdate.sh"

    _lock = Lock()
    _isUpdating = False
    _mode = 0
    cherrypy.tools.octet_stream_in = cherrypy.Tool(
        "before_request_body", octet_stream_in
    )

    @cherrypy.config(**{"tools.octet_stream_in.on": True})
    def PUT(self):
        pass

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):

        result = {"SDCERR": 1, "InfoMsg": "Device is busy"}

        if not cherrypy.session.get("swupdate", None):
            result["SDCERR"] = 0
            result["InfoMsg"] = "No update in progress"
            return result

        try:
            proc = run(
                [SWUpdate.SWUPDATE_SCRIPT, "get-update", str(SWUpdate._mode)],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            result["SDCERR"] = proc.returncode
            if proc.returncode:
                result["InfoMsg"] = proc.stderr.decode("utf-8").replace("\n", "")
            else:
                result["InfoMsg"] = "Updated"

        except TimeoutExpired:
            result["InfoMsg"] = "Update checking timeout"
        except Exception as e:
            result["InfoMsg"] = "{}".format(e)

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        dryrun = 0

        result = {"SDCERR": 1, "InfoMsg": "Device is busy"}

        def get_imageset_for_update(image):
            """Parse /proc/cmdline to get bootside info"""

            imageset = None

            with open("/proc/cmdline", "r") as f:
                cmd = f.read()
                imageset = (
                    "stable," + image + "-b"
                    if "block=0,1" in cmd
                    else "stable," + image + "-a"
                )
                f.close()

            return imageset

        def do_swupdate(
            args,
            callback=None,
            timeout=SystemSettingsManage.get_user_callback_timeout(),
        ):

            try:
                proc = run(args, capture_output=True, timeout=timeout)
                if proc.returncode:
                    result["InfoMsg"] = proc.stderr.decode("utf-8").replace("\n", "")

                    result["SDCERR"] = proc.returncode
                elif not callback or callback(dryrun) > 0:
                    result["InfoMsg"] = ""
                    result["SDCERR"] = 0
            except TimeoutExpired:
                result["InfoMsg"] = "Update checking timeout"
            except Exception as e:
                result["InfoMsg"] = "{}".format(e)

        with SWUpdate._lock:
            if SWUpdate._isUpdating:
                return result
            SWUpdate._isUpdating = True

        url = cherrypy.request.json.get("url", None)
        image = cherrypy.request.json.get("image", "main")
        imageset = get_imageset_for_update(image)

        if imageset:
            if url:
                SWUpdate._mode = 1
                do_swupdate(args=[SWUpdate.SWUPDATE_SCRIPT, "do-update", imageset, url])
            else:
                SWUpdate._mode = 0
                do_swupdate(
                    args=[SWUpdate.SWUPDATE_SCRIPT, "pre-update", imageset],
                    callback=swclient.prepare_fw_update,
                )

        if result["SDCERR"]:
            SWUpdate._isUpdating = False

        cherrypy.session["swupdate"] = cherrypy.session.id
        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def DELETE(self):

        result = {"SDCERR": 0, "InfoMsg": ""}

        if cherrypy.session.get("swupdate", None) == cherrypy.session.id:
            swclient.end_fw_update()
            call([SWUpdate.SWUPDATE_SCRIPT, "post-update"])
            SWUpdate._isUpdating = False
            cherrypy.session.pop("swupdate", None)

        return result
