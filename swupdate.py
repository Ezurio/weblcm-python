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

	@cherrypy.expose
	@cherrypy.config(**{'tools.response_headers.on': True})
	@cherrypy.config(**{'tools.response_headers.headers': [('Content-Type', 'application/json')]})
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def get_progress_state(self):
		result = {
			'SDCERR': 1,
			'state': "",
			'nsteps': 1,
			'cur_step': 0,
			'cur_percent': 0,
			'cur_image': "",
		}
		try:
			state = swclient.get_fw_update_state()
			if(state is not None):
				result['SDCERR'] = 0
				result['state'] = self.swupdate_states[state[0]]
				result['nsteps'] = state[1]
				result['cur_step'] = state[2]
				result['cur_percent'] = state[3]
				result['cur_image'] = state[4]
		except Exception as e:
			print(e)
		return result

	@cherrypy.expose
	@cherrypy.config(**{'tools.response_headers.on': True})
	@cherrypy.config(**{'tools.response_headers.headers': [('Content-Type', 'application/json')]})
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def update_bootenv(self):
		env = cherrypy.request.json
		try:
			if(env):
				if(env['bootside'] == 'a' or env['bootside'] == 'b'):
					out = subprocess.Popen(['fw_setenv', 'bootside', env['bootside']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					result, err = out.communicate()
			else:
				env = {'bootside': 'unknow',}

			out = subprocess.Popen(['fw_printenv','bootside'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			result, err = out.communicate()
			env['bootside'] = result.decode().split('=')[1][0]
		except Exception as e:
			print(e)
		return env
