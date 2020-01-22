import sys
import os
import os.path
import six
import time
import cherrypy
from cherrypy.lib import static
import weblcm_def
import tarfile

class FileManage(object):
	"""
		Manage regular certificate/profile files, and .tgz files.
		Streaming is not required.
	"""

	@cherrypy.expose
	def upload_file(self, typ, fil):

		def extract_tarfile(output_filename, target_dir):
			with tarfile.open(output_filename, "r:gz") as tar:
				tar.extractall(target_dir)
				tar.close()

		f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil.filename))
		with open(f, 'wb+') as out:
			while True:
				data = fil.file.read(8192)
				if not data:
					break
				out.write(data)
			out.close();

		"""
			If it is a .tgz file, delete all the exsiting files and then extract.
		"""
		if ".tgz" == os.path.splitext(fil.filename)[1]:
			for name in os.listdir(weblcm_def.FILEDIR_DICT.get(typ)):
				if(name != fil.filename):
					os.remove(weblcm_def.FILEDIR_DICT.get(typ) + name);
			extract_tarfile(f, weblcm_def.FILEDIR_DICT.get(typ))
			os.unlink(f)
		return;

	@cherrypy.expose
	def download_file(self, typ, fil):

		def make_tarfile(output_filename, source_dir):
			with tarfile.open(output_filename, "w:gz") as tar:
				for name in os.listdir(source_dir):
					tar.add(source_dir+name, arcname=os.path.basename(name))
				tar.close()

		if fil:
			f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil))
		else:
			"""
				.tgz file needs to be generated first and then export
			"""
			fil = typ +".tgz"
			f = os.path.normpath(os.path.join("/tmp/", fil))
			if os.path.exists(f):
				os.remove(f)
			make_tarfile(f, weblcm_def.FILEDIR_DICT.get(typ))

		if os.path.exists(f):
			return static.serve_file(f, 'application/x-download', 'attachment', fil)

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def delete_file(self):
		result = {
			'SDCERR': 1,
		}

		post_data = cherrypy.request.json
		typ = post_data.get('type')
		fil = post_data.get('file')

		f = os.path.normpath(os.path.join(weblcm_def.FILEDIR_DICT.get(typ), fil))
		if os.path.exists(f):
			os.remove(f)
			result['SDCERR'] = 0;
		return result

	@cherrypy.expose
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def get_files(self):

		files = []

		post_data = cherrypy.request.json
		typ = post_data.get('type')

		with os.scandir(weblcm_def.FILEDIR_DICT.get(typ)) as listOfEntries:
			for entry in listOfEntries:
				if entry.is_file():
					if entry.name.lower().endswith(weblcm_def.FILEFMT_DICT.get(typ)):
						files.append(entry.name)

		files.sort()

		return files
