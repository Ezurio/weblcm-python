import os, os.path
import cherrypy
import configparser
import uuid
import hashlib
import weblcm_python_def
import weblcm_python_func
from swupdate import SWUpdate
from users import UserManage, LoginManage

PLUGINS = {
       'list':{},
}

class Root(object):

	@cherrypy.expose
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def definitions(self):
		result = {
			'SDCERR': {
				'SDCERR_SUCCESS': 0, 'SDCERR_FAIL': 1
			},
			'PLUGINS': PLUGINS,
		}
		weblcm_python_func.check_session()
		return result

conf = os.path.join(weblcm_python_def.WEBLCM_PYTHON_CONF_DIR, "weblcm-python.ini")

if __name__ == '__main__':

	webapp = Root()

	PLUGINS['networking'] = weblcm_python_def.NM_DBUS_API_TYPES

	login = LoginManage()
	webapp.login = login.login
	webapp.logout = login.logout

	webapp.networking_status = weblcm_python_func.Networking_Status()
	webapp.connections = weblcm_python_func.Connections()
	webapp.activate_connection = weblcm_python_func.Activate_Connection()
	webapp.get_certificates = weblcm_python_func.Get_Certificates()
	webapp.add_connection = weblcm_python_func.Add_Connection()
	webapp.remove_connection = weblcm_python_func.Remove_Connection()
	webapp.edit_connection = weblcm_python_func.Edit_Connection()
	webapp.wifi_scan = weblcm_python_func.Wifi_Scan()
	webapp.version = weblcm_python_func.Version()

	webapp.request_log = weblcm_python_func.Request_Log()
	webapp.generate_log = weblcm_python_func.Generate_Log()
	webapp.download_log = weblcm_python_func.Download_Log()
	webapp.set_logging = weblcm_python_func.Set_Logging()
	webapp.get_logging = weblcm_python_func.Get_Logging()

	swu = SWUpdate();
	webapp.update_firmware = swu.update_firmware
	webapp.update_firmware_start = swu.update_firmware_start
	webapp.update_firmware_end = swu.update_firmware_end

	um = UserManage()
	webapp.add_user = um.add_user
	webapp.get_user_list = um.get_user_list
	webapp.update_user = um.update_user
	webapp.delete_user = um.delete_user

	cherrypy.quickstart(webapp, '/', config=conf)
