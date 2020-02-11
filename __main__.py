import os, os.path
import cherrypy
import configparser
import uuid
import hashlib
import weblcm_def
import weblcm_log
import weblcm_network
from weblcm_swupdate import SWUpdate
from weblcm_users import UserManage, LoginManage
from weblcm_files import FileManage

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
		return result

conf = os.path.join(weblcm_def.WEBLCM_PYTHON_CONF_DIR, "weblcm-python.ini")


if not os.path.exists(weblcm_def.FILEDIR_DICT.get('profile')):
	"""Change default directories for som60sd"""
	weblcm_def.FILEDIR_DICT['profile']='/etc/NetworkManager/system-connections/'
	weblcm_def.FILEDIR_DICT['cert']='/etc/weblcm-python/ssl/'

"""create cert directory for certs"""
if not os.path.exists(weblcm_def.FILEDIR_DICT.get('cert')):
	os.makedirs(weblcm_def.FILEDIR_DICT.get('cert'), 0o666)

if __name__ == '__main__':

	webapp = Root()

	PLUGINS['networking'] = weblcm_def.NM_DBUS_API_TYPES

	login = LoginManage()
	webapp.login = login.login
	webapp.logout = login.logout

	webapp.networking_status = weblcm_network.Networking_Status()
	webapp.connections = weblcm_network.Connections()
	webapp.activate_connection = weblcm_network.Activate_Connection()
	webapp.add_connection = weblcm_network.Save_Connection()
	webapp.remove_connection = weblcm_network.Remove_Connection()
	webapp.edit_connection = weblcm_network.Edit_Connection()
	webapp.wifi_scan = weblcm_network.Wifi_Scan()
	webapp.get_interfaces = weblcm_network.Get_Interfaces()
	webapp.version = weblcm_network.Version()

	webapp.request_log = weblcm_log.Request_Log()
	webapp.set_logging_level = weblcm_log.Set_Logging_Level()
	webapp.get_logging_level = weblcm_log.Get_Logging_Level()

	swu = SWUpdate();
	webapp.update_firmware = swu.update_firmware
	webapp.update_firmware_start = swu.update_firmware_start
	webapp.update_firmware_end = swu.update_firmware_end

	um = UserManage()
	webapp.add_user = um.add_user
	webapp.get_user_list = um.get_user_list
	webapp.update_user = um.update_user
	webapp.delete_user = um.delete_user

	fm = FileManage()
	webapp.upload_file = fm.upload_file
	webapp.get_files = fm.get_files
	webapp.download_file = fm.download_file
	webapp.delete_file = fm.delete_file

	cherrypy.quickstart(webapp, '/', config=conf)
