import sys
import os
import time
import cherrypy
from cherrypy.lib import static
import weblcm_def
import subprocess
from weblcm_settings import SystemSettingsManage

def save_file(typ, fil):
	f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil.filename))
	with open(f, 'wb+') as out:
		while True:
			data = fil.file.read(8192)
			if not data:
				break
			out.write(data)
		out.close();
	return f

@cherrypy.expose
class FileManage(object):
	"""
		Manage regular config/timezone files.
	"""
	def POST(self, *args, **kwargs):
		typ = kwargs.get('typ')
		fil = kwargs.get('fil')
		save_file(typ, fil)
		return;


	@cherrypy.tools.json_out()
	def DELETE(self, *args, **kwargs):
		result = {
			'SDCERR': 1,
		}

		typ = kwargs.get('typ')
		fil = kwargs.get('fil')
		f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil))
		if os.path.isfile(f):
			os.remove(f)
			result['SDCERR'] = 0;
		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		files = []
		typ = kwargs.get('typ')
		with os.scandir(weblcm_def.FILEDIR_DICT.get(typ)) as listOfEntries:
			for entry in listOfEntries:
				if entry.is_file():
					if entry.name.lower().endswith(weblcm_def.FILEFMT_DICT.get(typ)):
						files.append(entry.name)

		files.sort()

		return files

@cherrypy.expose
class ArchiveFilesManage(object):
	"""
		Manage archive files.
	"""
	def POST(self, *args, **kwargs):

		res = 1

		typ = kwargs.get('typ')
		fil = kwargs.get('fil')
		password = kwargs.get('Password', "Don't care")

		f = save_file(typ, fil)

		if os.path.isfile(f):
			p = subprocess.Popen([
				'/usr/sbin/weblcm_files.sh', typ, "unzip",
				f, weblcm_def.FILEDIR_DICT.get(typ), password
			])
			res = p.wait()
			os.unlink(f)

		if res:
			raise cherrypy.HTTPError()

	def GET(self, *args, **kwargs):

		typ = kwargs.get('typ')
		password = kwargs.get('Password')

		fil = '{0}{1}'.format(typ, ".zip")
		f = '{0}{1}'.format("/tmp/", fil)
		if typ == "config":
			p = subprocess.Popen([
				'/usr/sbin/weblcm_files.sh', "config", "zip",
				weblcm_def.FILEDIR_DICT.get(typ), f, password
			])
		elif typ == "log":
			p = subprocess.Popen([
				'/usr/sbin/weblcm_files.sh', "log", "zip",
				SystemSettingsManage.get_log_data_dir(), f, password
			])
		else:
			p = subprocess.Popen([
				'/usr/sbin/weblcm_files.sh', "debug", "zip",
				' '.join([SystemSettingsManage.get_log_data_dir(), weblcm_def.FILEDIR_DICT.get('config')]),
				f, SystemSettingsManage.get_cert_for_file_encryption()
			])
		p.wait()

		if os.path.isfile(f):
			objFile = static.serve_file(f, 'application/x-download', 'attachment', fil)
			os.unlink(f);
			return objFile;

		raise cherrypy.HTTPError()

	def DELETE(self, typ):
		return
