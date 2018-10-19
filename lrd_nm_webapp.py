import os, os.path
import cherrypy
import configparser
import lrd_nm_def
import lrd_nm_func

config = configparser.ConfigParser()
config.read('lrd_nm_webapp.ini')

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

def validate_password(username, password):
	if username in lrd_nm_def.USERS and lrd_nm_def.USERS[username] == password:
		return True
	return False

class Root(object):
	@cherrypy.expose
	def index(self):
		lrd_nm_func.check_session()
		return open('webLCM.html')

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
		if validate_password(post_data['username'],post_data['password']):
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
			'tools.staticdir.root': os.path.abspath(os.getcwd()),
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
		'/assets': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './assets'
		},
		'/plugins': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './plugins'
		}
	}

	webapp = Root()

	if check_dict_value('wifi',config['PLUGINS']):
		PLUGINS['list']['wifi'] = True
		PLUGINS['wifi'] = lrd_nm_def.NM_DBUS_API_TYPES
		cherrypy_conf.update(lrd_nm_def.WIFI_CONF)
		webapp.wifi_status = lrd_nm_func.Wifi_Status()
		webapp.connections = lrd_nm_func.Connections()
		webapp.activate_connection = lrd_nm_func.Activate_Connection()
		webapp.get_certificates = lrd_nm_func.Get_Certificates()
		webapp.add_connection = lrd_nm_func.Add_Connection()
		webapp.remove_connection = lrd_nm_func.Remove_Connection()
		webapp.edit_connection = lrd_nm_func.Edit_Connection()
		webapp.wifi_scan = lrd_nm_func.Wifi_Scan()
		webapp.version = lrd_nm_func.Version()

	webapp.definitions = Definitions()
	webapp.login = Login()
	webapp.logout = Logout()

	cherrypy.quickstart(webapp, "/", cherrypy_conf)

