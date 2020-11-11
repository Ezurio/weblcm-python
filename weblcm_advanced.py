import cherrypy
from subprocess import Popen, PIPE

@cherrypy.expose
class Reboot(object):

	def PUT(self):
		p = Popen(['systemctl', 'reboot'])
		p.wait()
		return

@cherrypy.expose
class FactoryReset(object):
	FACTORY_RESET_SCRIPT='/usr/sbin/do_factory_reset.sh'

	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': 1,
		}
		p = Popen([FactoryReset.FACTORY_RESET_SCRIPT, 'reset'])
		result['SDCERR'] = p.wait()
		return result
