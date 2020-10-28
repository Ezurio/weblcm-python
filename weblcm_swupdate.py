import cherrypy
import dbus
from threading import Lock
import os,errno
import uuid
import time
import swclient
from subprocess import Popen, PIPE, TimeoutExpired
from weblcm_settings import SystemSettingsManage

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

	_lock = Lock()
	_isUpdating = False
	cherrypy.tools.octet_stream_in = cherrypy.Tool('before_request_body', octet_stream_in)

	@cherrypy.config(**{'tools.octet_stream_in.on': True})
	def PUT(self):
		pass

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		result = {
			'SDCERR': 1,
			'message': "Device is busy"
		}

		if not cherrypy.session.get('swupdate', None):
			return result

		mode = kwargs.get('mode', 0)

		try:
			proc = Popen(["/usr/sbin/weblcm_swupdate.sh", "get-update", str(mode)], stdout=PIPE, stderr=PIPE)
			outs, errs = proc.communicate(timeout=SystemSettingsManage.get_user_callback_timeout())
			if proc.returncode:
				result['message'] = errs.decode("utf-8")
				result['SDCERR'] = proc.returncode
			else:
				result['message'] = "Updated"
				result['SDCERR'] = 0

		except TimeoutExpired:
			proc.kill()
			outs, errs = proc.communicate()
			result['message'] = "Update checking timeout"
		except Exception as e:
			result['message'] = "{}".format(e)

		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):

		dryrun = 0

		result = {
			'SDCERR': 1,
			'message': "Device is busy"
		}

		def get_imageset_for_update(image):

			'''Parse /proc/cmdline to get bootside info'''

			imageset = None

			with open('/proc/cmdline','r') as f:
				cmd = f.read()
				imageset = "stable,"+image+"-b" if "block=0,1" in cmd else "stable,"+image+"-a"
				f.close()

			return imageset

		def do_swupdate(args, callback=None, timeout=SystemSettingsManage.get_user_callback_timeout()):

			try:
				proc = Popen(args, stdout=PIPE, stderr=PIPE)
				outs, errs = proc.communicate(timeout=timeout)
				if proc.returncode:
					result['message'] = errs.decode("utf-8")
					result['SDCERR'] = proc.returncode
				else:
					if not callback or callback(dryrun) > 0:
						result['SDCERR'] = 0
			except TimeoutExpired:
				proc.kill()
				outs, errs = proc.communicate()
				result['message'] = "Update checking timeout"
			except Exception as e:
				result['message'] = "{}".format(e)
			return

		with SWUpdate._lock:
			if SWUpdate._isUpdating:
				return result
			SWUpdate._isUpdating = True

		url = cherrypy.request.json.get('url', None)
		image = cherrypy.request.json.get('image', "main")
		imageset = get_imageset_for_update(image)

		if imageset:
			if url:
				do_swupdate(args=["/usr/sbin/weblcm_swupdate.sh", "do-update", imageset, url])
			else:
				do_swupdate(args=["/usr/sbin/weblcm_swupdate.sh", "pre-update", imageset], callback=swclient.prepare_fw_update)

		if result['SDCERR']:
			SWUpdate._isUpdating = False

		cherrypy.session['swupdate'] = cherrypy.session.id
		return result

	def DELETE(self):

		if cherrypy.session.get('swupdate', None) == cherrypy.session.id:
			swclient.end_fw_update()
			proc = Popen(["/usr/sbin/weblcm_swupdate.sh", "post-update"], stdout=PIPE, stderr=PIPE)
			proc.wait()
			SWUpdate._isUpdating = False
			cherrypy.session.pop('swupdate', None)

		return
