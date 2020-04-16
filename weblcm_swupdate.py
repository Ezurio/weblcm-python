import cherrypy
import dbus
import threading
import os,errno
import uuid
import time
import swclient
from subprocess import Popen, PIPE, TimeoutExpired

def octet_stream_in(force=True, debug=False):
	request = cherrypy.serving.request
	def octet_stream_processor(entity):
		#Read application/octet-stream data into request.json.
		if not entity.headers.get("Content-Length", ""):
			raise cherrypy.HTTPError(411)
		try:
			data = entity.read()
			rc = swclient.do_fw_update(data)
			if rc < 0:
				raise cherrypy.HTTPError(500)
		except OSError as err:
			raise err
	if force:
		request.body.processors.clear()
		request.body.default_proc = cherrypy.HTTPError(
			415, 'Expected an application/octet-stream content type')
	request.body.processors['application/octet-stream'] = octet_stream_processor

@cherrypy.expose
class SWUpdate:

	_isUpdating = False
	_lock = threading.Lock()
	cherrypy.tools.octet_stream_in = cherrypy.Tool('before_request_body', octet_stream_in)

	@cherrypy.config(**{'tools.octet_stream_in.on': True})
	def PUT(self):
		pass

	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
			'message': "Device is busy"
		}

		dryrun = 0

		with SWUpdate._lock:
			if SWUpdate._isUpdating:
				return result
			SWUpdate._isUpdating = True

		try:
			proc = Popen("/usr/sbin/weblcm_update_checking.sh", stdout=PIPE, stderr=PIPE)
			outs, errs = proc.communicate(timeout=cherrypy.request.app.config['weblcm'].get('swupdate_callback_timeout', 5))

			if proc.returncode:
				result['message'] = errs.decode("utf-8")
				result['SDCERR'] = proc.returncode
			else:
				if swclient.prepare_fw_update(dryrun) > 0:
					result['SDCERR'] = 0

		except TimeoutExpired:
			proc.kill()
			outs, errs = proc.communicate()
			result['message'] = "Update checking timeout"
		except Exception as e:
			result['message'] = "{}".format(e)

		if result['SDCERR']:
			SWUpdate._isUpdating = False

		return result

	def DELETE(self):
		swclient.end_fw_update()
		SWUpdate._isUpdating = False
		return
