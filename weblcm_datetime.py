import os
import cherrypy
from datetime import datetime
import weblcm_def
from subprocess import Popen, PIPE
from weblcm_settings import SystemSettingsManage

@cherrypy.expose
class DateTimeSetting(object):

	def getZoneList(self):
		zones = []

		with open(weblcm_def.WEBLCM_PYTHON_TIMEZONE_CONF_FILE, 'r') as fp:
			line = fp.readline()
			while line:
				zones.append(line.strip())
				line = fp.readline()
			fp.close()

		return zones

	def __init__(self):

		self.localtime = "/etc/localtime"
		self.zoneinfo = "/usr/share/zoneinfo/"
		self.userZoneinfo = weblcm_def.WEBLCM_PYTHON_USER_ZONEINFO
		self.userLocaltime = self.userZoneinfo + "localtime"
		self.zones = self.getZoneList()

	def getLocalZone(self):

		localtime = os.readlink(self.userLocaltime)
		index = localtime.find(self.zoneinfo)
		if -1 != index:
			return localtime[index + len(self.zoneinfo):]

		index = localtime.find(self.userZoneinfo)
		if -1 != index:
			return localtime[index + len(self.userZoneinfo):]

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		result = { }

		if kwargs.get('zones'):
			result['zones'] = self.zones
			result['zone'] = self.getLocalZone()

		dt = datetime.now()
		result['time'] = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

		proc = Popen(['/usr/sbin/weblcm_datetime.sh', "check", "", ""], stdout=PIPE, stderr=PIPE)
		outs, errs = proc.communicate(timeout=SystemSettingsManage.getInt('user_callback_timeout', 5))

		if proc.returncode:
			result['method'] = "manual"
		else:
			result['method'] = "auto"

		result['SDCERR'] = 0
		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': 1,
		}

		zone = cherrypy.request.json['zone']
		method = cherrypy.request.json['method']
		dt = cherrypy.request.json['datetime']

		proc = Popen(['/usr/sbin/weblcm_datetime.sh', method, zone, dt], stdout=PIPE, stderr=PIPE)
		outs, errs = proc.communicate(timeout=SystemSettingsManage.getInt('user_callback_timeout', 5))

		if proc.returncode:
			result['message'] = errs.decode("utf-8")
			result['SDCERR'] = proc.returncode
		else:
			result['SDCERR'] = 0
		return result
