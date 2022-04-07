import cherrypy
from syslog import syslog
from subprocess import run, call, TimeoutExpired, CalledProcessError
from .definition import WEBLCM_ERRORS
from .settings import SystemSettingsManage


@cherrypy.expose
class Reboot(object):

    @cherrypy.tools.json_out()
    def PUT(self):
        try:
            call(['systemctl', 'reboot'])
        except:
            pass
        result = {
            'SDCERR': WEBLCM_ERRORS.get('SDCERR_SUCCESS'),
            'InfoMsg': 'Reboot initiated',
        }
        syslog("reboot initiated")

        return result


@cherrypy.expose
class FactoryReset(object):
    FACTORY_RESET_SCRIPT = '/usr/sbin/do_factory_reset.sh'

    @cherrypy.tools.json_out()
    def PUT(self):
        result = {}
        syslog("Factory Reset requested")
        try:
            returncode = call([self.FACTORY_RESET_SCRIPT, 'reset'])
        except:
            returncode = -1
        result['SDCERR'] = returncode
        if returncode == 0:
            result['InfoMsg'] = 'Reboot required'
        else:
            result['InfoMsg'] = 'Error running factory reset'
            syslog("FactoryReset's returned %d" % returncode)

        return result


@cherrypy.expose
class Fips(object):

    FIPS_SCRIPT = '/usr/bin/fips-set'

    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):
        result = {
            'SDCERR': WEBLCM_ERRORS['SDCERR_FAIL'],
            'InfoMsg': 'Reboot required',
        }

        setOptions = ['unset', 'fips', 'fips-wifi']

        post_data = cherrypy.request.json
        fips = post_data.get('fips', 'no option provided')
        if fips not in setOptions:
            result['InfoMsg'] = 'Invalid option: %s' % fips
            return result

        try:
            run([Fips.FIPS_SCRIPT, fips], check=True, timeout=SystemSettingsManage.get_user_callback_timeout())
            result['SDCERR'] = WEBLCM_ERRORS['SDCERR_SUCCESS']

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result['InfoMsg'] = 'FIPS SET error'

        except FileNotFoundError:
            result['InfoMsg'] = 'Not a FIPS image'

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result['InfoMsg'] = 'FIPS SET timeout'

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result['InfoMsg'] = 'FIPS SET exception: {}'.format(e)

        return result

    @cherrypy.tools.json_out()
    def GET(self,  *args, **kwargs):
        result = {
            'SDCERR': WEBLCM_ERRORS['SDCERR_FAIL'],
            'InfoMsg': '',
        }

        try:
            p = run([Fips.FIPS_SCRIPT, 'status'], capture_output=True, check=True,
                    timeout=SystemSettingsManage.get_user_callback_timeout())
            result['status'] = p.stdout.decode("utf-8").strip()
            result['SDCERR'] = WEBLCM_ERRORS['SDCERR_SUCCESS']

        except CalledProcessError as e:
            syslog("FIPS set error: %d" % e.returncode)
            result['InfoMsg'] = 'FIPS SET error'

        except FileNotFoundError:
            result['InfoMsg'] = 'Not a FIPS image'

        except TimeoutExpired as e:
            syslog("FIPS SET timeout: %s" % e)
            result['InfoMsg'] = 'FIPS SET timeout'

        except Exception as e:
            syslog("FIPS set exception: %s" % e)
            result['InfoMsg'] = 'FIPS SET exception: {}'.format(e)

        return result
