import sys
import os
import time
import cherrypy
from cherrypy.lib import static
import weblcm_def
import subprocess
from pathlib import Path
from pylibconfig import Config
from threading import Lock
from weblcm_settings import SystemSettingsManage

@cherrypy.expose
class FileManage(object):

	''' File Management '''

	_lock = Lock()
	FILE_MANAGE_SCRIPT='/etc/weblcm-python/scripts/weblcm_files.sh'

	#log will be saved in /var/run/log/journal/ for volatile mode, or /var/log/journal/ for persistent mode
	#If "/var/run/log/journal/" exists, it should be in volatile mode.
	_log_data_dir = "/var/run/log/journal/"
	if not os.path.exists("/var/run/log/journal/"):
		_log_data_dir = "/var/log/journal/"

	def save_file(self, typ, fil):
		path = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil.filename))
		with open(path, 'wb+') as out:
			while True:
				data = fil.file.read(8192)
				if not data:
					break
				out.write(data)
			out.close();
		return path

	def POST(self, *args, **kwargs):

		typ = kwargs.get('type', None)
		fil = kwargs.get('file', None)
		if not typ or not fil:
			raise cherrypy.HTTPError(400) #bad request

		with FileManage._lock:
			f = self.save_file(typ, fil)
			if os.path.isfile(f):
				if f.endswith(".zip"):
					password = kwargs.get('password', "")
					p = subprocess.Popen([
						FileManage.FILE_MANAGE_SCRIPT, typ, "unzip", f, weblcm_def.FILEDIR_DICT.get(typ), password
					])
					res = p.wait()
					os.remove(f)
					if res:
						raise cherrypy.HTTPError(500) #Internal server error
				return

		raise cherrypy.HTTPError(500) #Internal server error

	def GET(self, *args, **kwargs):

		typ = kwargs.get('type', None)
		if not typ:
			raise cherrypy.HTTPError(400)

		fil = '{0}{1}'.format(typ, ".zip")
		path = '{0}{1}'.format("/tmp/", fil)

		if typ == "config":

			password = kwargs.get('password', None)
			if not password:
				raise cherrypy.HTTPError(400)
			p = subprocess.Popen([
				FileManage.FILE_MANAGE_SCRIPT, "config", "zip",
				weblcm_def.FILEDIR_DICT.get(typ), path, password
			])

		elif typ == "log":

			password = kwargs.get('password', None)
			if not password:
				raise cherrypy.HTTPError(400)
			p = subprocess.Popen([
				FileManage.FILE_MANAGE_SCRIPT, "log", "zip",
				FileManage._log_data_dir, path, password
			])
			p.wait()

		else:
			p = subprocess.Popen([
				FileManage.FILE_MANAGE_SCRIPT, "debug", "zip",
				' '.join([FileManage._log_data_dir, weblcm_def.FILEDIR_DICT.get('config')]),
				path, SystemSettingsManage.get_cert_for_file_encryption()
			])
		p.wait()

		if os.path.isfile(path):
			objFile = static.serve_file(path, 'application/x-download', 'attachment', fil)
			os.unlink(path);
			return objFile;

		raise cherrypy.HTTPError(500)

	@cherrypy.tools.json_out()
	def DELETE(self, *args, **kwargs):
		result = { 'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL') }

		typ = kwargs.get('type', None)
		fil = kwargs.get('file', None)
		if not typ or not fil:
			raise cherrypy.HTTPError(400) #bad request

		path = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil))
		if os.path.isfile(path):
			os.remove(path);
		if not os.path.exists(path):
			result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
		return result

@cherrypy.expose
class FilesManage(object):

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		typ = kwargs.get('type', None)
		if not typ:
			raise cherrypy.HTTPError(400)

		files = []
		with os.scandir(weblcm_def.FILEDIR_DICT.get(typ)) as listOfEntries:
			for entry in listOfEntries:
				if entry.is_file():
					strs = entry.name.split('.')
					if len(strs) == 2 and strs[1] in weblcm_def.FILEFMT_DICT.get(typ):
						files.append(entry.name)
		files.sort()
		return files

@cherrypy.expose
class AWMCfgManage(object):

	_lock = Lock()

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		#Infinite geo-location checks by default
		result = { 'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS') }
		result['geolocation_scanning_enable'] = 1

		f = cherrypy.request.app.config['weblcm'].get('awm_cfg', None);
		if not f:
			return result

		if not os.path.isfile(f):
			return result

		config = Config()
		with AWMCfgManage._lock:
			config.readFile(f)
			if config.exists("scan_attempts"):
				result['geolocation_scanning_enable'] = config.value("scan_attempts")[0]

		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):

		#Enable/disable geolocation scanning
		#0: disable geolocation scanning
		#others: enable geolocation scanning

		result = { 'SDCERR': weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL') }
		result['geolocation_scanning_enable'] = 1

		f = cherrypy.request.app.config['weblcm'].get('awm_cfg', None);
		if not f:
			return result

		d = Path(os.path.dirname(f))
		d.mkdir(exist_ok=True)

		geolocation_scanning_enable = cherrypy.request.json.get('geolocation_scanning_enable', 0)

		config = Config()
		with AWMCfgManage._lock:
			if os.path.isfile(f):
				config.readFile(f)
			if geolocation_scanning_enable:
				if config.exists("scan_attempts"):
					config.remove("", "scan_attempts")
					config.writeFile(f)
			else:
				if not config.exists("scan_attempts"):
					config.addInteger("", "scan_attempts")
				config.setValue("scan_attempts", geolocation_scanning_enable)
				config.writeFile(f)

		result['geolocation_scanning_enable'] = geolocation_scanning_enable
		result['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
		return result
