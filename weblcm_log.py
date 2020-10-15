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
		priority = int(kwargs.get('priority', 6))
		reader.log_level(priority)
		typ = kwargs.get('type', "All")
		if typ != "All":
			reader.add_match(SYSLOG_IDENTIFIER=typ)
		days = int(kwargs.get('days', 1))
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
		}

		post_data = cherrypy.request.json

		bus = dbus.SystemBus()
		proxy = bus.get_object(weblcm_def.WPA_IFACE, weblcm_def.WPA_OBJ)
		wpas = dbus.Interface(proxy, weblcm_def.DBUS_PROP_IFACE)
		wpas.Set(weblcm_def.WPA_IFACE, "DebugLevel", str(post_data['suppDebugLevel']))

		try:
			driver_debug_file = open(weblcm_def.WIFI_DRIVER_DEBUG_PARAM, "w")
			if driver_debug_file.mode == 'w':
				driver_debug_file.write(str(post_data['driverDebugLevel']))
		except Exception as e:
			print(e)

		result['SDCERR'] = 0

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		result = {
			'SDCERR': 1,
		}

		bus = dbus.SystemBus()
		proxy = bus.get_object(weblcm_def.WPA_IFACE, weblcm_def.WPA_OBJ)
		wpas = dbus.Interface(proxy, weblcm_def.DBUS_PROP_IFACE)
		debug_level = wpas.Get(weblcm_def.WPA_IFACE, "DebugLevel")
		result['suppDebugLevel'] = debug_level

		try:
			driver_debug_file = open(weblcm_def.WIFI_DRIVER_DEBUG_PARAM, "r")
			if driver_debug_file.mode == 'r':
				contents = driver_debug_file.read(1)
				result['driverDebugLevel'] = contents
		except Exception as e:
			print(e)

		result['SDCERR'] = 0

		return result
