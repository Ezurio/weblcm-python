import cherrypy
from syslog import syslog
from subprocess import Popen, PIPE
from weblcm_def import WEBLCM_ERRORS, USER_PERMISSION_TYPES
from weblcm_settings import SystemSettingsManage

@cherrypy.expose
class Reboot(object):

	@cherrypy.tools.json_out()
	def PUT(self):
		p = Popen(['systemctl', 'reboot'])
		p.wait()
		result = {
			'SDCERR': WEBLCM_ERRORS.get('SDCERR_SUCCESS'),
			'ErrorMsg': 'Reboot initiated',
		}
		syslog("reboot initiated")

		return result

@cherrypy.expose
class FactoryReset(object):
	FACTORY_RESET_SCRIPT='/usr/sbin/do_factory_reset.sh'

	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': WEBLCM_ERRORS.get('SDCERR_FAIL'),
		}
		p = Popen([FactoryReset.FACTORY_RESET_SCRIPT, 'reset'])
		result['SDCERR'] = p.wait()
		syslog("Factory Reset requested")
		if result.get('SDCERR') == 0:
			result['ErrorMsg'] = 'Reboot required'
		else:
			result['ErrorMsg'] = 'Error running factory reset'
			syslog("FactoryReset's p.wait() returned %s" % result.get('SDCERR'))

		return result

@cherrypy.expose
class Fips(object):

	FIPS_SCRIPT='/usr/bin/fips-set'

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': WEBLCM_ERRORS.get('SDCERR_FAIL'),
			'ErrorMsg': 'Reboot required',
		}

		setOptions = ['unset', 'fips', 'fips-wifi']

		post_data = cherrypy.request.json
		fips = post_data.get('fips', 'no option provided')
		if fips not in setOptions:
			result['ErrorMsg'] = 'Invalid option: {}'.format(fips)
			return result

		try:
			proc = Popen([Fips.FIPS_SCRIPT, fips], stdout=PIPE, stderr=PIPE)
		except Exception as e:
			syslog("FIPS SET exception: %s" % e)
			result['ErrorMsg'] = 'FIPS SET exception: {}'.format(e)
			return result

		try:
			outs, errs = proc.communicate(timeout=SystemSettingsManage.get_user_callback_timeout())
		except TimeoutExpired:
			proc.kill()
			outs, errs = proc.communicate()
			syslog("FIPS SET timeout: %s" % e)
			result['ErrorMsg'] = 'FIPS SET timeout'
		except Exception as e:
			syslog("FIPS set exception: %s" % e)
			result['ErrorMsg'] = 'FIPS SET exception: {}'.format(e)

		if not proc.returncode:
			result['SDCERR'] = WEBLCM_ERRORS.get('SDCERR_SUCCESS')
		else:
			syslog("FIPS set error: %s" % e)
			result['ErrorMsg'] = 'FIPS SET error'
		return result

	@cherrypy.tools.json_out()
	def GET(self,  *args, **kwargs):
		result = {
			'SDCERR': WEBLCM_ERRORS.get('SDCERR_SUCCESS'),
			'ErrorMsg': '',
			'status': "unset"
		}
		try:
			proc = Popen([Fips.FIPS_SCRIPT, 'status'], stdout=PIPE, stderr=PIPE)
		except Exception as e:
			syslog("FIPS get exception: %s" % e)
			result['ErrorMsg'] = 'FIPS GET exception: {}'.format(e)
			return result

		try:
			outs, errs = proc.communicate(timeout=SystemSettingsManage.get_user_callback_timeout())
		except TimeoutExpired:
			proc.kill()
			outs, errs = proc.communicate()
			syslog("FIPS get timeout: %s" % e)
			result['ErrorMsg'] = 'FIPS GET timeout'
		except Exception as e:
			syslog("FIPS get exception: %s" % e)
			result['ErrorMsg'] = 'FIPS GET exception: {}'.format(e)

		if not proc.returncode:
			try:
				result['status'] = outs.decode("utf-8").strip()
			except Exception as e:
				syslog('FIPS GET exception: %s' % e)
		else:
			syslog("FIPS GET error: %d" % proc.returncode)
			result['ErrorMsg'] = 'FIPS GET error'

		return result
