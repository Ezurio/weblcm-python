import sys
import os
import os.path
import six
import time
import cherrypy
from cherrypy.lib import static
import weblcm_def
import subprocess

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
		Manage regular certificate/profile files.
	"""
	def POST(self, typ, fil):
		save_file(typ, fil)
		return;


	@cherrypy.tools.json_out()
	def DELETE(self, typ, fil):
		result = {
			'SDCERR': 1,
		}

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
		password = kwargs.get('Password')

		f = save_file(typ, fil)

		if os.path.isfile(f):
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "config", "unzip",
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
				'/usr/sbin/weblcm_file_import_export.sh', "config", "zip",
				weblcm_def.FILEDIR_DICT.get(typ), f, password
			])
		elif typ == "log":
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "log", "zip",
				cherrypy.request.app.config['weblcm'].get('log_data_dir', "/run/log/journal/"), f, password
			])
		else:
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "debug", "zip",
				' '.join([cherrypy.request.app.config['weblcm'].get('log_data_dir', "/run/log/journal/"), weblcm_def.FILEDIR_DICT.get('config')]),
				f, cherrypy.request.app.config['weblcm'].get('cert_for_file_encryption', "/etc/weblcm-python/ssl/ca.crt")
			])
		p.wait()

		if os.path.isfile(f):
			return static.serve_file(f, 'application/x-download', 'attachment', fil)

		raise cherrypy.HTTPError()

	def DELETE(self, typ):

		fil = '{0}{1}'.format(typ, ".zip")
		f = '{0}{1}'.format("/tmp/", fil)
		if os.path.isfile(f):
			os.remove(f)
