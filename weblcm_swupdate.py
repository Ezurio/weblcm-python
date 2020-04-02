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
		'''Read application/octet-stream data into request.json.'''
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

class SWUpdate:

	_isUpdating = False
	_lock = threading.Lock()

	def __init__(self):
		cherrypy.tools.octet_stream_in = cherrypy.Tool('before_request_body', octet_stream_in)

	@cherrypy.expose
	@cherrypy.config(**{'tools.octet_stream_in.on': True})
	def update_firmware(self):
		pass

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def update_firmware_start(self):

		dryrun = 0

		result = {
			'SDCERR': 1,
			'message': "",
		}

		try:
			proc = Popen("/usr/sbin/weblcm_update_checking.sh", stdout=PIPE, stderr=PIPE)
			outs, errs = proc.communicate(timeout=cherrypy.request.app.config['weblcm'].get('swupdate_callback_timeout', 5))

			if proc.returncode:
				result['message'] = errs.decode("utf-8")
				result['SDCERR'] = proc.returncode
			else:
				self._lock.acquire()
				isupdating = self._isUpdating
				self._isUpdating = True
				self._lock.release()

				if isupdating == False:
					swclient.prepare_fw_update(dryrun)
					result['SDCERR'] = 0
				else:
					result['message'] = "Device is busy"

		except TimeoutExpired:
			proc.kill()
			outs, errs = proc.communicate()
			result['message'] = "Update checking timeout"
		except Exception as inst:
			result['message'] = "An Error happened during update checking"

		return result

	@cherrypy.expose
	def update_firmware_end(self):
		swclient.end_fw_update()
		self._isUpdating = False
