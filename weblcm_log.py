import cherrypy
import dbus
import os
import uuid
import time
import sys
from systemd import journal
import weblcm_def
from weblcm_settings import SystemSettingsManage

@cherrypy.expose
class LogData(object):

	@cherrypy.tools.accept(media='text/plain')
	@cherrypy.config(**{'response.stream': True})
	def GET(self,  *args, **kwargs):

		cherrypy.response.headers['Content-Type'] = 'text/plain'

		reader = journal.Reader()
		try:
			priority = int(kwargs.get('priority', 6))
		except Exception as e:
			return '{"SDCERR":1, "InfoMsg": "Priority must be an int between 0-7"}'
		if not priority in range(0, 7, 1):
			return '{"SDCERR":1, "InfoMsg": "Priority must be an int between 0-7"}'
		reader.log_level(priority)
		# use .title() to ensure incoming type has proper case
		typ = kwargs.get('type', "All").title()
		# TODO - documentation says 'python' is lower case while others are upper case.  Is that correct?
		if typ == 'Python':
			typ = 'python'
		types = {'Kernel', 'NetworkManager', 'python', 'All'}
		if not typ in types:
			return '{"SDCERR":1, "InfoMsg": "supplied type parameter must be one of %s"}' % types
		if typ != "All":
			reader.add_match(SYSLOG_IDENTIFIER=typ)
		try:
			days = int(kwargs.get('days', 1))
		except Exception as e:
			return '{"SDCERR":1, "InfoMsg": "days must be an int"}'
		if days > 0:
			reader.seek_realtime(time.time() - days * 86400)

		def streaming():
			logs = []
			log_data_streaming_size = SystemSettingsManage.get_log_data_streaming_size()
			for entry in reader:
				logs.append(str(entry.get('__REALTIME_TIMESTAMP', "Undefined")))
				logs.append(str(entry.get('PRIORITY', 7)))
				logs.append(entry.get('SYSLOG_IDENTIFIER', "Undefined"))
				logs.append(entry.get('MESSAGE', "Undefined"))
				if len(logs) == log_data_streaming_size:
					yield (":#:".join(logs) + ":#:")
					logs.clear()
			if len(logs) > 0:
				yield ":#:".join(logs)
				logs.clear()
			reader.close()

		return streaming()

@cherrypy.expose
class LogSetting(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
			'InfoMsg': ''
		}
		post_data = cherrypy.request.json

		if not 'suppDebugLevel' in post_data:
			result['InfoMsg'] = 'suppDebugLevel missing from JSON data'
			return result
		if not 'driverDebugLevel' in post_data:
			result['InfoMsg'] = 'driverDebugLevel missing from JSON data'
			return result

		levels = {'none', 'error', 'warning', 'info', 'debug', 'msgdump', 'excessive'}
		supp_level = post_data.get('suppDebugLevel').lower()
		if not supp_level in levels:
			result['InfoMsg'] = f'suppDebugLevel must be one of {levels}'
			return result

		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_def.WPA_IFACE, weblcm_def.WPA_OBJ)
			wpas = dbus.Interface(proxy, weblcm_def.DBUS_PROP_IFACE)
			wpas.Set(weblcm_def.WPA_IFACE, "DebugLevel", supp_level)
		except Exception as e:
			result['InfoMsg'] = 'unable to set supplicant debug level'
			return result

		drv_level=post_data.get('driverDebugLevel')
		try:
			drv_level=int(drv_level)
		except Exception as e:
			result['InfoMsg'] = 'driverDebugLevel must be 0 or 1'
			return result

		if not (drv_level == 0 or drv_level == 1):
			result['InfoMsg'] = 'driverDebugLevel must be 0 or 1'
			return result

		try:
			driver_debug_file = open(weblcm_def.WIFI_DRIVER_DEBUG_PARAM, "w")
			if driver_debug_file.mode == 'w':
				driver_debug_file.write(str(drv_level))
		except Exception as e:
			result['InfoMsg'] = 'unable to set driver debug level'
			return result

		result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		result = {
			'SDCERR': 0,
			'InfoMsg': ''
		}

		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_def.WPA_IFACE, weblcm_def.WPA_OBJ)
			wpas = dbus.Interface(proxy, weblcm_def.DBUS_PROP_IFACE)
			debug_level = wpas.Get(weblcm_def.WPA_IFACE, "DebugLevel")
			result['suppDebugLevel'] = debug_level
		except Exception as e:
			result['Errormsg'] = 'Unable to determine supplicant debug level'
			result['SDCERR'] = 1

		try:
			driver_debug_file = open(weblcm_def.WIFI_DRIVER_DEBUG_PARAM, "r")
			if driver_debug_file.mode == 'r':
				contents = driver_debug_file.read(1)
				result['driverDebugLevel'] = contents
		except Exception as e:
			print(e)
			if result['SDCERR'] == 0:
				result['Errormsg'] ='Unable to determine driver debug level'
			else:
				result['Errormsg'] ='Unable to determin supplicant nor driver debug level'
			result['SDCERR'] = 1

		return result
