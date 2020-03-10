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
from weblcm_files import FileManage, ArchiveFilesManage
from weblcm_advanced import Reboot, FactoryReset

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

if not os.path.exists(weblcm_def.FILEDIR_DICT.get('profile')):
	"""Change default directories for som60sd"""
	weblcm_def.FILEDIR_DICT['profile']='/etc/NetworkManager/system-connections/'
	weblcm_def.FILEDIR_DICT['cert']='/etc/weblcm-python/ssl/'
	weblcm_def.FILEDIR_DICT['config']='/etc/'

if not os.path.exists(weblcm_def.WEBLCM_PYTHON_CONF_DIR):
	weblcm_def.WEBLCM_PYTHON_CONF_DIR = '/etc/weblcm-python/'

conf = os.path.join(weblcm_def.WEBLCM_PYTHON_CONF_DIR, "weblcm-python.ini")

"""create cert directory for certs"""
if not os.path.exists(weblcm_def.FILEDIR_DICT.get('cert')):
	os.makedirs(weblcm_def.FILEDIR_DICT.get('cert'), 0o666)


"""Redirect http to https"""
def force_tls():
	if cherrypy.request.scheme == "http":
		raise cherrypy.HTTPRedirect(cherrypy.url().replace("http:", "https:"), status=301)

cherrypy.request.hooks.attach('on_start_resource', force_tls)

def setup_http_server():
    httpServer = cherrypy._cpserver.Server()
    httpServer.socket_host = "0.0.0.0"
    httpServer.socket_port = 80
    httpServer.subscribe()

if __name__ == '__main__':

	webapp = Root()

	PLUGINS['networking'] = weblcm_def.NM_DBUS_API_TYPES
	PLUGINS['usermanage'] = weblcm_def.USER_PERMISSION_TYPES

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
	webapp.archiveFiles = ArchiveFilesManage()

	swu = SWUpdate()
	webapp.update_firmware = swu.update_firmware
	webapp.update_firmware_start = swu.update_firmware_start
	webapp.update_firmware_end = swu.update_firmware_end

	webapp.reboot = Reboot()
	webapp.factoryReset = FactoryReset()

	setup_http_server()

	#Server config
	cherrypy.config.update({
			'server.socket_host': '0.0.0.0',
			'server.socket_port': 443,
			'server.ssl_module': 'builtin',
			'server.ssl_certificate': weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'ssl/server.crt',
			'server.ssl_private_key': weblcm_def.WEBLCM_PYTHON_CONF_DIR + 'ssl/server.key',
		})

	cherrypy.quickstart(webapp, '/', config=conf)
