import os, os.path
import cherrypy
import configparser
import uuid
import hashlib
import weblcm_python_def
import weblcm_python_func

config = configparser.ConfigParser()
config.read(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR + 'weblcm-python.ini')

passwords = configparser.ConfigParser()

PLUGINS = {
	'list':{},
}

def check_dict_value(value, dictionary):
	if value in dictionary:
		if dictionary[value] == 'true':
			return True
		elif dictionary[value] == 'false':
			return False
		else:
			return dictionary[value]
	else:
		return False

def rename_users_section(cp, section_from, section_to):
	items = cp.items(section_from)
	cp.add_section(section_to)
	for item in items:
		cp.set(section_to, item[0], item[1])
		cp.remove_section(section_from)

def update_users_username(update, current_username, new_username):
	result = 1
	if update:
		if current_username in passwords:
			rename_users_section(passwords,current_username,new_username)
			if new_username in passwords:
				cherrypy.session['USER'] = new_username
				result = 0
	else:
		result = 0

	return result

def update_users_password(update, current_password, new_password):
	result = 1
	username = cherrypy.session['USER']
	if update:
		attempted_password = hashlib.sha256(passwords[username]['salt'].encode() + current_password.encode()).hexdigest()
		if attempted_password == passwords[username]['password']:
			salt = uuid.uuid4().hex
			passwords[username]['salt'] = salt
			passwords[username]['password'] = hashlib.sha256(salt.encode() + new_password.encode()).hexdigest()
			result = 0
	else:
		result = 0

	return result

class Root(object):
	@cherrypy.expose
	def index(self):
		weblcm_python_func.check_session()
		return open(weblcm_python_def.WEBLCM_PYTHON_DOC_ROOT + 'webLCM.html')

@cherrypy.expose
class Login(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}
		post_data = cherrypy.request.json
		passwords.read(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		if post_data['username'] in passwords and post_data['password']:
			attempted_password = hashlib.sha256(passwords[post_data['username']]['salt'].encode() + post_data['password'].encode()).hexdigest()
			if attempted_password == passwords[post_data['username']]['password']:
				cherrypy.session['SESSION'] = 0
				cherrypy.session['USER'] = post_data['username']
				result['SDCERR'] = 0

		return result

@cherrypy.expose
class Logout(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 0,
		}
		cherrypy.session['SESSION'] = 1
		cherrypy.lib.sessions.expire()
		return result

@cherrypy.expose
class Update_Users(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}
		post_data = cherrypy.request.json
		passwords.read(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini')
		if ( not update_users_password(post_data['updatePassWord'], post_data['currentPassWord'], post_data['newPassWord']) and
			not update_users_username(post_data['updateUserName'],post_data['currentUserName'],post_data['newUserName'])):
			with open(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR + 'hash.ini', 'w') as configfile:
				passwords.write(configfile)
			result['SDCERR'] = 0


		return result

@cherrypy.expose
class Definitions(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
				'SDCERR': {
					'SDCERR_SUCCESS': 0, 'SDCERR_FAIL': 1
				},
				'PLUGINS': PLUGINS,
				'DEBUG': check_dict_value('debug',config['CORE']),
				'SESSION': cherrypy.session['SESSION'],
		}

		if check_dict_value('ignore_session',config['CORE']):
			result['IGNORE_SESSION'] = 0
			result['SESSION'] = 0
			cherrypy.session['SESSION'] = 0

		return result

if __name__ == '__main__':
	cherrypy_conf = {
		'global': {
			'server.socket_host': check_dict_value('socket_host',config['CORE']),
			'server.socket_port': int(check_dict_value('socket_port',config['CORE'])),
		},
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': weblcm_python_def.WEBLCM_PYTHON_DOC_ROOT,
			'tools.sessions.timeout': int(check_dict_value('session_timeout',config['CORE'])),
		},
		'/definitions': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/login': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/logout': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/update_app_users': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/assets': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'assets'
		},
		'/plugins': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'plugins'
		},
		'/html': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': 'html'
		}
	}

	webapp = Root()

	if check_dict_value('networking',config['PLUGINS']):
		PLUGINS['list']['networking'] = True
		PLUGINS['networking'] = weblcm_python_def.NM_DBUS_API_TYPES
		cherrypy_conf.update(weblcm_python_def.NETWORKING_CONF)
		webapp.networking_status = weblcm_python_func.Networking_Status()
		webapp.connections = weblcm_python_func.Connections()
		webapp.activate_connection = weblcm_python_func.Activate_Connection()
		webapp.get_certificates = weblcm_python_func.Get_Certificates()
		webapp.add_connection = weblcm_python_func.Add_Connection()
		webapp.remove_connection = weblcm_python_func.Remove_Connection()
		webapp.edit_connection = weblcm_python_func.Edit_Connection()
		webapp.wifi_scan = weblcm_python_func.Wifi_Scan()
		webapp.version = weblcm_python_func.Version()

	if check_dict_value('logging',config['PLUGINS']):
		PLUGINS['list']['logging'] = True
		weblcm_python_func.Log_Data.journal_entries = check_dict_value('journal',config['CORE'])
		cherrypy_conf.update(weblcm_python_def.LOGGING_CONF)
		webapp.request_log = weblcm_python_func.Request_Log()
		webapp.generate_log = weblcm_python_func.Generate_Log()
		webapp.download_log = weblcm_python_func.Download_Log()
		webapp.set_logging = weblcm_python_func.Set_Logging()
		webapp.get_logging = weblcm_python_func.Get_Logging()

	webapp.definitions = Definitions()
	webapp.login = Login()
	webapp.logout = Logout()
	webapp.update_users = Update_Users()

	cherrypy.quickstart(webapp, "/", cherrypy_conf)
