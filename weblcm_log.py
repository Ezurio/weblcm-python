import cherrypy
import dbus
import subprocess
import os
import uuid
import time
import sys
from systemd import journal
import weblcm_def

@cherrypy.expose
class LogData(object):

	@cherrypy.tools.accept(media='text/plain')
	@cherrypy.tools.json_out()
	def GET(self, typ, priority, days):

		logs = []

		try:
			reader = journal.Reader()
			reader.log_level(int(priority))
			if typ != "All":
				reader.add_match(SYSLOG_IDENTIFIER=typ)
			if int(days) > 0:
				reader.seek_realtime(time.time() - int(days) * 86400)
			for entry in reader:
				log = {}
				log['time'] = str(entry.get('__REALTIME_TIMESTAMP', "None"))
				log['priority'] = entry.get('PRIORITY', 7)
				log['identifier'] = entry.get('SYSLOG_IDENTIFIER', "Unknown")
				log['message'] = entry.get('MESSAGE', "None")
				logs.append(log)

		except Exception as e:
			print(e)
		return logs

@cherrypy.expose
class LogLevel(object):

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

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
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
