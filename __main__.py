import os, os.path
import cherrypy
import configparser
import uuid
import hashlib
import weblcm_python_def
import weblcm_python_func
from swupdate import SWUpdate
from users import UserManage, LoginManage

config = configparser.ConfigParser()
config.read(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR + 'weblcm-python.ini')


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

class Root(object):
	@cherrypy.expose
	def index(self):
		weblcm_python_func.check_session()
		return open(weblcm_python_def.WEBLCM_PYTHON_DOC_ROOT + 'webLCM.html')

	@cherrypy.expose
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def definitions(self):
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
		# Pass in ini setting
		weblcm_python_func.Networking_Data.show_unmanaged = check_dict_value('show_unmanaged',config['CORE'])
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


	if check_dict_value('swupdate',config['PLUGINS']):
		PLUGINS['list']['swupdate'] = True
		swu = SWUpdate();
		webapp.update_firmware = swu.update_firmware
		webapp.update_firmware_start = swu.update_firmware_start
		webapp.update_firmware_end = swu.update_firmware_end
		webapp.get_progress_state = swu.get_progress_state
		webapp.update_bootenv = swu.update_bootenv

	login = LoginManage()
	webapp.login = login.login
	webapp.logout = login.logout

	if check_dict_value('usermanage',config['PLUGINS']):
		PLUGINS['list']['usermanage'] = True
		um = UserManage()
		webapp.add_user = um.add_user
		webapp.get_user_list = um.get_user_list
		webapp.update_user = um.update_user
		webapp.delete_user = um.delete_user

	cherrypy.quickstart(webapp, "/", cherrypy_conf)
