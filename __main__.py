import os, os.path
import cherrypy
import configparser
import uuid
import hashlib
import weblcm_def
from weblcm_network import NetworkStatus, NetworkInterfaces, NetworkConnections, NetworkConnection, NetworkAccessPoints, Version
from weblcm_log import LogData, LogLevel
from weblcm_swupdate import SWUpdate
from weblcm_users import UserManage, LoginManage, LogoutManage
from weblcm_files import FileManage, TarFileManage

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

	webapp.login = LoginManage()
	webapp.logout = LogoutManage()

	webapp.networkStatus = NetworkStatus()
	webapp.connections = NetworkConnections()
	webapp.connection = NetworkConnection()
	webapp.accesspoints = NetworkAccessPoints()
	webapp.networkInterfaces = NetworkInterfaces()
	webapp.version = Version()

	webapp.logData = LogData()
	webapp.logLevel = LogLevel()

	webapp.users = UserManage()
	webapp.files = FileManage()
	webapp.tarfiles = TarFileManage()

	swu = SWUpdate()
	webapp.update_firmware = swu.update_firmware
	webapp.update_firmware_start = swu.update_firmware_start
	webapp.update_firmware_end = swu.update_firmware_end

	cherrypy.quickstart(webapp, '/', config=conf)
