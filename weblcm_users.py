import cherrypy
from cherrypy.lib import httputil
import subprocess
import os,errno
import uuid
import hashlib
from threading import Lock
from datetime import datetime
import time
from weblcm_def import WEBLCM_ERRORS, USER_PERMISSION_TYPES
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
	def getNumberOfUsers(cls):
		''' All users including root '''
		return WeblcmConfigManage.get_section_size_by_key('password')

	@classmethod
	def getUserList(cls):
		userlist = WeblcmConfigManage.get_sections_and_key('permission')
		if userlist:
			#Default user shouldn't be listed as its permission can't be updated by weblcm
			default_username = cherrypy.request.app.config['weblcm'].get('default_username', "root")
			userlist.pop(default_username, None)
		return userlist

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

		if UserManageHelper.getNumberOfUsers() < SystemSettingsManage.getInt('max_web_users', 1):
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

class LoginManageHelper(object):

	_lock = Lock()
	#Record logins with wrong credentials to protect against tamper
	_failed_logins = {}
	#Record successful logins and delete inactive sessions
	_sessions = {}

	@classmethod
	def is_blocked(cls, username):
		user = {}
		with cls._lock:
			user = cls._failed_logins.get(username)
			#Block username for 'login_block_timeout' seconds if failed consecutively for 'login_retry_times' times
			if user and user.get('failed', 0) >= SystemSettingsManage.getInt('login_retry_times', 3):
				dt = (datetime.now() - user['time']).total_seconds()
				if dt < SystemSettingsManage.getInt('tamper_protection_timeout', 120):
					return True
				cls._failed_logins.pop(username, None)
		return False

	@classmethod
	def login_failed(cls, username):
		with cls._lock:
			user = cls._failed_logins.get(username)
			if user:
				user['failed'] += 1
				user['time'] = datetime.now()
			else:
				user = {}
				user['failed'] = 1
				user['time'] = datetime.now()
				cls._failed_logins[username] = user

	@classmethod
	def login_reset(cls, username):
		with cls._lock:
			cls._failed_logins.pop(username, None)

	@classmethod
	def create(cls, username):

		def delete_session_by_id(session_id):
			if id:
				temp_id = cherrypy.session.id
				cherrypy.session.id = session_id
				#cherrypy.lib.sessions.expire()
				cherrypy.session._delete()
				cherrypy.session.id = temp_id

		with cls._lock:

			#Clean up inactive user session
			session = cls._sessions.get(username, None)
			if  session:
				dt = datetime.now() - session.get('time')
				if dt.total_seconds() < SystemSettingsManage.getInt('inactive_session_timeout', 300):
					return False

				delete_session_by_id(session.get('id', None))
				cls._sessions.pop(session.get('id'), None)

			#Clean up expired sessions
			temp_id = cherrypy.session.id
			for k, v in cls._sessions.copy().items():
				cherrypy.session.id = v.get('id')
				if not cherrypy.session._exists():
					cls._sessions.pop(v.get('id'), None)
			cherrypy.session.id = temp_id

			session = {}
			session['time'] = datetime.now()
			session['id'] = cherrypy.session.id
			cls._sessions[username] = session
		return True

	@classmethod
	def update_time(cls):
		with cls._lock:
			username = cherrypy.session.get('USERNAME', None)
			session = cls._sessions.get(username, None)
			if session:
				session['time'] = datetime.now()

	@classmethod
	def delete(cls):
		with cls._lock:
			user = cherrypy.session.pop('USERNAME', None)
			cls._sessions.pop(user, None)

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
		if UserManageHelper.getNumberOfUsers() == 0 and username == default_username and password == default_password:
			UserManageHelper.addUser(username, password, " ".join(USER_PERMISSION_TYPES['UserPermssionTypes']))
			result['SDCERR'] = 0
			result['REDIRECT'] = 1
			cherrypy.session['USERNAME'] = username
			return result
		elif UserManageHelper.getNumberOfUsers() == 1 and password == default_password and UserManageHelper.verify(username, password):
			result['SDCERR'] = 0
			result['REDIRECT'] = 1
			cherrypy.session['USERNAME'] = username
			return result

		if LoginManageHelper.is_blocked(username):
			result['SDCERR'] = WEBLCM_ERRORS.get('SDCERR_USER_BLOCKED')
			return result

		if not UserManageHelper.verify(username, password):
			LoginManageHelper.login_failed(username)
			return result

		LoginManageHelper.login_reset(username)

		#For each session, allow multiple logins with the same account
		sess_user = cherrypy.session.get('USERNAME', None)
		if sess_user and sess_user != username:
			result['SDCERR'] = WEBLCM_ERRORS.get('SDCERR_SESSION_CHECK_FAILED')
			return result

		if not sess_user and not LoginManageHelper.create(username):
			result['SDCERR'] = WEBLCM_ERRORS.get('SDCERR_USER_LOGGED')
			return result

		result['PERMISSION'] = UserManageHelper.getPermission(username)
		#Don't display "add_del_user" page for single user mode
		if SystemSettingsManage.getInt('max_web_users', 1) == 1:
			result['PERMISSION'] = result['PERMISSION'].replace("add_del_user", "")

		cherrypy.session['USERNAME'] = username
		result['SDCERR'] = 0
		return result

	@cherrypy.tools.json_in()
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def DELETE(self, *args, **kwargs):
		result = {
			'SDCERR': 0,
		}

		LoginManageHelper.delete()
		cherrypy.lib.sessions.expire()
		return result
