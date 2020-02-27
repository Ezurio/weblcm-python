import cherrypy
import subprocess

@cherrypy.expose
class Reboot(object):
	def PUT(self):
		subprocess.Popen(['systemctl', 'reboot'])
		return

@cherrypy.expose
class FactoryReset(object):

	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': 1,
		}
		p = subprocess.Popen(['/usr/sbin/do_factory_reset.sh', 'reset'])
		result['SDCERR'] = p.wait()
		return result
