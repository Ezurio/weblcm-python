import cherrypy
import dbus
import subprocess
import os,errno
import uuid
import time
import hashlib
import configparser
import weblcm_def
import threading

users = configparser.ConfigParser(defaults=None)

@cherrypy.expose
class UserManage(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': 1,
			'REDIRECT': 0,
		}

		post_data = cherrypy.request.json
		username = post_data.get('username')
		users.read(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')

		#Update password
		current_password = post_data.get('current_password')
		if current_password:
			new_password = post_data.get('new_password')
			attempted_password = hashlib.sha256(users[username]['salt'].encode() + current_password.encode()).hexdigest()
			if attempted_password == users[username]['password'] and new_password:
				salt = uuid.uuid4().hex
				users[username]['salt'] = salt
				users[username]['password'] = hashlib.sha256(salt.encode() + new_password.encode()).hexdigest()
				with open(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini', 'w') as configfile:
					users.write(configfile)
				if current_password == "summit" and username == "root":
					result['REDIRECT'] = 1
				result['SDCERR'] = 0
		else:
			#Update permission
			permission = post_data.get('permission')
			if permission and username in users:
				users[username]['permission'] = permission
				with open(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini', 'w') as configfile:
					users.write(configfile)
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
		users.read(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		if(len(users.sections()) < cherrypy.request.app.config['weblcm']['max_web_clients']):
			username = post_data.get('username')
			password = post_data.get('password')
			permission = post_data.get('permission')
			if username and password and username not in users:
				users.add_section(username);
				salt = uuid.uuid4().hex
				users[username]['salt'] = salt
				users[username]['password'] = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
				users[username]['permission'] = permission
				with open(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini', 'w') as configfile:
					users.write(configfile)
				result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def DELETE(self, username):
		result = {
			'SDCERR': 1,
		}
		users.read(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		if username in users:
			users.remove_section(username)
			with open(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini', 'w') as configfile:
				users.write(configfile)
			result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def GET(self):
		result = {}
		users.read(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		for k in users:
			if k != "root" and k != "DEFAULT":
				result[k] = users[k]['permission'];

		return result

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
		users.read(weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		if post_data.get('username') in users and post_data.get('password'):
			attempted_password = hashlib.sha256(users[post_data['username']]['salt'].encode() + post_data.get('password').encode()).hexdigest()
			if attempted_password == users[post_data['username']]['password']:
				result['SDCERR'] = 0
				if post_data.get('username') == "root":
					result['PERMISSION'] = weblcm_def.USER_PERMISSION_TYPES['UserPermssionTypes']
					"""Redirect to password update page"""
					if post_data.get('password') == "summit":
						result['REDIRECT'] = 1
				else:
					result['PERMISSION'] = users[post_data['username']]['permission']
		return result

@cherrypy.expose
class LogoutManage(object):

	@cherrypy.tools.json_in()
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 0,
		}
		cherrypy.lib.sessions.expire()
		return result
