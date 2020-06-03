import cherrypy
import dbus
import subprocess
import os,errno
import uuid
import hashlib
import time
import weblcm_def
from weblcm_settings import WeblcmConfigManage, SystemSettingsManage

class UserManageHelper(object):

	@classmethod
	def verify(cls, username, password):
		if WeblcmConfigManage.get_key_from_section(username, 'salt', None):
			attempt = hashlib.sha256(WeblcmConfigManage.get_key_from_section(username, 'salt').encode() + password.encode()).hexdigest()
			return (attempt == WeblcmConfigManage.get_key_from_section(username, 'password', None))
		return False

	@classmethod
	def delUser(cls, username):
		if WeblcmConfigManage.remove_section(username):
			return WeblcmConfigManage.save()
		return False

	@classmethod
	def addUser(cls, username, password, permission=None):
		if WeblcmConfigManage.add_section(username):
			salt = uuid.uuid4().hex
			WeblcmConfigManage.upadte_key_from_section(username, 'salt', salt)
			WeblcmConfigManage.upadte_key_from_section(username, 'password', hashlib.sha256(salt.encode() + password.encode()).hexdigest())
			if permission:
				WeblcmConfigManage.upadte_key_from_section(username, 'permission', permission)
			return WeblcmConfigManage.save()
		return False

	@classmethod
	def updatePassword(cls, username, password):
		if WeblcmConfigManage.get_key_from_section(username, 'salt', None):
			salt = uuid.uuid4().hex
			WeblcmConfigManage.upadte_key_from_section(username, 'salt', salt)
			WeblcmConfigManage.upadte_key_from_section(username, 'password', hashlib.sha256(salt.encode() + password.encode()).hexdigest())
			return WeblcmConfigManage.save()
		return False

	@classmethod
	def getPermission(cls, username):
		return WeblcmConfigManage.get_key_from_section(username, 'permission', None)

	@classmethod
	def updatePermission(cls, username, permission):
		if permission and WeblcmConfigManage.get_key_from_section(username, 'permission', None):
			return WeblcmConfigManage.upadte_key_from_section(username, 'permission', permission)
		return False

	@classmethod
	def size(cls):
		''' All users including root '''
		return WeblcmConfigManage.get_section_size_by_key('password')

	@classmethod
	def getUserCount(cls):
		''' None root users'''
		return WeblcmConfigManage.get_section_size_by_key('permission')

	@classmethod
	def getUserList(cls):
		return WeblcmConfigManage.get_sections_and_key('permission')

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
		username = post_data.get('username', None)
		new_password = post_data.get('new_password', None)
		if new_password:
			current_password = post_data.get('current_password', None)
			if UserManageHelper.verify(username, current_password):
				if UserManageHelper.updatePassword(username, new_password):
					result['SDCERR'] = 0
					#Redirect is required when the default password is updated
					default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
					default_password = cherrypy.request.app.config['weblcm'].get('default_password', "summit")
					if current_password == default_password and username == default_username:
						result['REDIRECT'] = 1
		else:
			permission = post_data.get('permission', None)
			if permission:
				if UserManageHelper.updatePermission(username, permission):
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

		if UserManageHelper.getUserCount() < SystemSettingsManage.getInt('max_web_clients', 5):
			if UserManageHelper.addUser(username, password, permission):
				result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def DELETE(self, username):
		result = {
			'SDCERR': 1,
		}

		if UserManageHelper.delUser(username):
			result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		return UserManageHelper.getUserList()

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

		if UserManageHelper.size() == 0:
			default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
			default_password = cherrypy.request.app.config['weblcm'].get('default_password', "summit")
			if username != default_username or password != default_password:
				return result

			UserManageHelper.addUser(username, password)

			result['SDCERR'] = 0
			result['REDIRECT'] = 1
			return result

		if UserManageHelper.verify(username, password):
			result['SDCERR'] = 0
			default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
			if username == default_username:
				result['PERMISSION'] = " ".join(weblcm_def.USER_PERMISSION_TYPES['UserPermssionTypes'])
			else:
				result['PERMISSION'] = UserManageHelper.getPermission(username)

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
