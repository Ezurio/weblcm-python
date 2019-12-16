import cherrypy
import dbus
import subprocess
import os,errno
import uuid
import time
import swclient

def octet_stream_in(force=True, debug=False):
	request = cherrypy.serving.request
	def octet_stream_processor(entity):
		'''Read application/octet-stream data into request.json.'''
		global total_recv_bytes, SWUPDATE_FIFO_PATH
		if not entity.headers.get("Content-Length", ""):
			raise cherrypy.HTTPError(411)
		try:
			data = entity.read()
			swclient.do_fw_update(data)
		except OSError as err:
			raise err
	if force:
		request.body.processors.clear()
		request.body.default_proc = cherrypy.HTTPError(
			415, 'Expected an application/octet-stream content type')
	request.body.processors['application/octet-stream'] = octet_stream_processor

class SWUpdate:

	swupdate_states = ("IDLE", "START", "RUN", "SUCCESS", "FAILURE", "DOWNLOAD", "DONE", "SUBPROCESS")

	def __init__(self):
		cherrypy.tools.octet_stream_in = cherrypy.Tool('before_request_body', octet_stream_in)

	@cherrypy.expose
	@cherrypy.config(**{'tools.octet_stream_in.on': True})
	def update_firmware(self):
		pass

	@cherrypy.expose
	def update_firmware_start(self):
		dryrun = 0
		swclient.prepare_fw_update(dryrun)
		pass

	@cherrypy.expose
	def update_firmware_end(self):
		swclient.end_fw_update()
		pass
