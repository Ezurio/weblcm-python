import sys
import os
import os.path
import six
import time
import cherrypy
from cherrypy.lib import static
import weblcm_def
import tarfile

def save_file(typ, fil):
	f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil.filename))
	with open(f, 'wb+') as out:
		while True:
			data = fil.file.read(8192)
			if not data:
				break
			out.write(data)
		out.close();
	return

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
class TarFileManage(object):
	"""
		Manage tared certificate/profile files.
	"""
	def POST(self, typ, fil):

		def extract_tarfile(output_filename, target_dir):
			with tarfile.open(output_filename, "r:gz") as tar:
				tar.extractall(target_dir)
				tar.close()

		for name in os.listdir(weblcm_def.FILEDIR_DICT.get(typ)):
			os.remove(weblcm_def.FILEDIR_DICT.get(typ) + name);

		save_file(typ, fil)

		f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil.filename))
		extract_tarfile(f, weblcm_def.FILEDIR_DICT.get(typ))
		os.unlink(f)
		return;

	def GET(self, typ):

		def make_tarfile(output_filename, source_dir):
			with tarfile.open(output_filename, "w:gz") as tar:
				for name in os.listdir(source_dir):
					tar.add(source_dir+name, arcname=os.path.basename(name))
				tar.close()

		fil = typ +".tgz"
		f = os.path.normpath(os.path.join("/tmp/", fil))
		if os.path.exists(f):
			os.remove(f)
		make_tarfile(f, weblcm_def.FILEDIR_DICT.get(typ))

		if os.path.exists(f):
			return static.serve_file(f, 'application/x-download', 'attachment', fil)
