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
		if os.path.exists(f):
			os.remove(f)
			result['SDCERR'] = 0;
		return result

	@cherrypy.tools.json_out()
	def GET(self, typ):

		files = []

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
	def POST(self, fil, typ, passwd):

		res = 1

		f = save_file(typ, fil)
		if os.path.exists(f):
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "config", "unzip",
				f, weblcm_def.FILEDIR_DICT.get(typ), passwd
			])
			res = p.wait()
			os.unlink(f)
		if res:
			raise cherrypy.HTTPError(500)

	def GET(self, typ, passwd):

		fil = typ + ".zip"
		f = "/tmp/" + fil
		if os.path.exists(f):
			os.remove(f)

		if typ == "config":
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "config", "zip",
				weblcm_def.FILEDIR_DICT.get(typ), f, passwd
			])
		elif typ == "log":
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "log", "zip",
				cherrypy.request.app.config['weblcm']['log_data_dir'], f, passwd
			])
		else:
			p = subprocess.Popen([
				'/usr/sbin/weblcm_file_import_export.sh', "debug", "zip",
				' '.join([cherrypy.request.app.config['weblcm']['log_data_dir'], weblcm_def.FILEDIR_DICT.get('config')]),
				f, cherrypy.request.app.config['weblcm']['cert_for_file_encryption']
			])
		p.wait()

		if os.path.exists(f):
			return static.serve_file(f, 'application/x-download', 'attachment', fil)

		raise cherrypy.HTTPError(500)

	def DELETE(self, typ):

		fil = typ + ".zip"
		f = "/tmp/" + fil
		if os.path.exists(f):
			os.remove(f)
