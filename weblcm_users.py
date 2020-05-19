import cherrypy
import dbus
import subprocess
import os,errno
import uuid
import time
import hashlib
import configparser
import weblcm_def
from threading import Lock

class UserConfManage(object):

	_filename = None
	_lock = Lock()
	_parser = configparser.ConfigParser(defaults=None)

	@classmethod
	def init(cls, username, password):

		with cls._lock:
			if cls._filename:
				return
			cls._filename = weblcm_def.WEBLCM_PYTHON_USER_CONF_FILE

		if os.path.isfile(cls._filename):
			cls._parser.read(cls._filename)
			if username in cls._parser:
				return

		#Create users config file with default username and password if not exist
		cls._parser.clear()
		if cls.addUser(username, password, None):
			return

		cls._filename = None
		return

	@classmethod
	def verify(cls, username, password):
		res = False

		with cls._lock:
			if username in cls._parser:
				attempt = hashlib.sha256(cls._parser.get(username, 'salt').encode() + password.encode()).hexdigest()
				res = (attempt == cls._parser.get(username, 'password'))

		return res

	@classmethod
	def size(cls):

		with cls._lock:
			res = len(cls._parser.sections())

		return res

	@classmethod
	def delUser(cls, username):
		res = False

		with cls._lock:
			if username in cls._parser:
				cls._parser.remove_section(username)
				res = True

		return cls.save() if res else False

	@classmethod
	def addUser(cls, username, password, permission):
		res = False

		# Don't use any case-insensitive variants of "DEFAULT"
		if username.upper() == "DEFAULT":
			return res

		with cls._lock:
			if username not in cls._parser:
				salt = uuid.uuid4().hex
				cls._parser.add_section(username)
				cls._parser[username]['salt'] = salt
				cls._parser[username]['password'] = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
				if permission:
					cls._parser[username]['permission'] = permission
				res = True

		return cls.save() if res else False

	@classmethod
	def updatePassword(cls, username, password):
		res = False

		with cls._lock:
			if username in cls._parser:
				salt = uuid.uuid4().hex
				cls._parser[username]['salt'] = salt
				cls._parser[username]['password'] = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
				res = True

		return cls.save() if res else False

	@classmethod
	def getPermission(cls, username):
		permission = ""

		with cls._lock:
			if username in cls._parser:
				permission = cls._parser.get(username, 'permission')

		return permission

	@classmethod
	def updatePermission(cls, username, permission):
		res = False

		with cls._lock:
			if username in cls._parser and permission:
				cls._parser[username]['permission'] = permission
				res = True

		return cls.save() if res else False

	@classmethod
	def getUserList(cls):
		result = {}

		with cls._lock:
			for k in cls._parser:
				if cls._parser[k].get('permission'):
					result[k] = cls._parser[k].get('permission')

		return result

	@classmethod
	def save(cls):
		res = False

		with cls._lock:
			with open(cls._filename, 'w') as configfile:
				cls._parser.write(configfile)
				res = True

		return res


@cherrypy.expose
class UserManage(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):

		"""
			Update password/permission
		"""
		result = {
			'SDCERR': 1,
			'REDIRECT': 0,
		}

		post_data = cherrypy.request.json
		username = post_data.get('username')
		new_password = post_data.get('new_password')
		if new_password:
			current_password = post_data.get('current_password')
			if UserConfManage.verify(username, current_password):
				if UserConfManage.updatePassword(username, new_password):
					result['SDCERR'] = 0

					#Redirect is required when the default password is updated
					default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
					default_password = cherrypy.request.app.config['weblcm'].get('default_password', "summit")
					if current_password == default_password and username == default_username:
						result['REDIRECT'] = 1
		else:
			permission = post_data.get('permission')
			if permission:
				if UserConfManage.updatePermission(username, permission):
					result['SDCERR'] = 0

		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}

		post_data = cherrypy.request.json
		username = post_data.get('username')
		password = post_data.get('password')
		permission = post_data.get('permission')

		if not username or not password or not permission:
			return result

		if(UserConfManage.size() >= cherrypy.request.app.config['weblcm'].get('max_web_clients', 5)):
			return result

		if UserConfManage.addUser(username, password, permission):
			result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def DELETE(self, username):
		result = {
			'SDCERR': 1,
		}

		if UserConfManage.delUser(username):
			result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		return UserConfManage.getUserList()

@cherrypy.expose
class LoginManage(object):

	@cherrypy.tools.json_in()
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
			'REDIRECT': 0,
			'PERMISSION': "",
		}

		post_data = cherrypy.request.json
		username = post_data.get('username')
		password = post_data.get('password')

		if not username or not password:
			return result

		default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
		default_password = cherrypy.request.app.config['weblcm'].get('default_password', "summit")

		UserConfManage.init(default_username, default_password)

		if UserConfManage.verify(username, password):
			result['SDCERR'] = 0
			if username == default_username:
				"""Redirect to password update page"""
				if password == default_password:
					result['REDIRECT'] = 1
				result['PERMISSION'] = " ".join(weblcm_def.USER_PERMISSION_TYPES['UserPermssionTypes'])
			else:
				result['PERMISSION'] = UserConfManage.getPermission(username)
		return result

@cherrypy.expose
class LogoutManage(object):

	@cherrypy.tools.json_in()
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		result = {
			'SDCERR': 0,
		}
		cherrypy.lib.sessions.expire()
		return result
