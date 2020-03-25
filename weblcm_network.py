import sys
import os
import uuid
import six
import time
import cherrypy
import subprocess
import NetworkManager
import weblcm_def

@cherrypy.expose
class NetworkConnections(object):
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'connections': {},
		}

		connections = NetworkManager.Settings.ListConnections()
		result['length'] = len(connections)
		for c in connections:

			connection = {}
			all_settings = c.GetSettings()
			settings = all_settings.get('connection')
			connection['id'] = settings['id']
			connection['activated'] = 0

			wifi_settings = all_settings.get('802-11-wireless')
			if wifi_settings and wifi_settings['mode'] == "ap":
				connection['type'] = "ap"

			result['connections'][settings['uuid']] = connection

		devices = NetworkManager.NetworkManager.GetDevices()
		for dev in devices:
			if dev.ActiveConnection:
				result['connections'][dev.ActiveConnection.Uuid]['activated'] = 1

		result['SDCERR'] = 0
		return result

@cherrypy.expose
class NetworkConnection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):
		result = {
			'SDCERR': 1,
		}
		try:
			uuid = cherrypy.request.json['UUID']
			if cherrypy.request.json['activate'] == 1:
				connections = NetworkManager.Settings.ListConnections()
				connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
				conn = connections[uuid]
				interface_name = conn.GetSettings()['connection']['interface-name']
				for dev in NetworkManager.Device.all():
					if dev.Interface == interface_name:
						NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")
						result['SDCERR'] = 0
						break;
			else:
				for conn in NetworkManager.NetworkManager.ActiveConnections:
					if uuid == conn.Connection.GetSettings()['connection']['uuid']:
						NetworkManager.NetworkManager.DeactivateConnection(conn)
						break;
				result['SDCERR'] = 0
		except Exception as e:
			print(e)

		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):

		result = {
			'SDCERR': 1,
		}

		try:
			new_settings = {};
			post_data = cherrypy.request.json

			if post_data.get('connection'):
				new_settings['connection'] = post_data.get('connection');
				if not new_settings['connection'].get('uuid'):
					new_settings['connection']['uuid'] = str(uuid.uuid4())

				if post_data.get('802-11-wireless'):
					new_settings['802-11-wireless'] = post_data.get('802-11-wireless');

					if post_data.get('802-11-wireless-security'):
						new_settings['802-11-wireless-security'] = post_data.get('802-11-wireless-security');

						if post_data.get('802-1x'):
							new_settings['802-1x'] = post_data.get('802-1x');
							"""
								Add path to certificates
							"""
							if new_settings['802-1x'].get('ca-cert'):
								new_settings['802-1x']['ca-cert'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('ca-cert');
							if new_settings['802-1x'].get('client-cert'):
								new_settings['802-1x']['client-cert'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('client-cert')
							if new_settings['802-1x'].get('private-key'):
								new_settings['802-1x']['private-key'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('private-key')
							if new_settings['802-1x'].get('phase2-ca-cert'):
								new_settings['802-1x']['phase2-ca-cert'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('phase2-ca-cert');
							if new_settings['802-1x'].get('phase2-client-cert'):
								new_settings['802-1x']['phase2-client-cert'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('phase2-client-cert');
							if new_settings['802-1x'].get('phase2-private-key'):
								new_settings['802-1x']['phase2-private-key'] = weblcm_def.FILEDIR_DICT.get('cert') + new_settings['802-1x'].get('phase2-private-key');

				new_settings['ipv4'] = post_data.get('ipv4');
				new_settings['ipv6'] = post_data.get('ipv6');

				connections = NetworkManager.Settings.ListConnections()
				connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
				if connections.get(new_settings['connection']['uuid']):
					connections[new_settings['connection']['uuid']].Update(new_settings)
				else:
					NetworkManager.Settings.AddConnection(new_settings)
				result['SDCERR'] = 0

		except Exception as e:
			print(e)

		return result

	@cherrypy.tools.json_out()
	def DELETE(self, uuid):
		result = {
			'SDCERR': 1,
		}
		try:
			connections = NetworkManager.Settings.ListConnections()
			connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
			connections[uuid].Delete();
			result['SDCERR'] = 0
		except Exception as e:
			print(e)

		return result

	@cherrypy.tools.json_out()
	def GET(self, uuid):

		def cert_to_filename(cert):
			"""
				Return base name only.
			"""
			if cert:
				return cert[len(weblcm_def.FILEDIR_DICT.get('cert')):]

		result = {
			'SDCERR': 1,
		}
		try:
			connections = NetworkManager.Settings.ListConnections()
			connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
			settings = connections[uuid].GetSettings()
			if settings.get('802-1x'):
				settings['802-1x']['ca-cert'] = cert_to_filename(settings['802-1x'].get('ca-cert'));
				settings['802-1x']['client-cert'] = cert_to_filename(settings['802-1x'].get('client-cert'));
				settings['802-1x']['private-key'] = cert_to_filename(settings['802-1x'].get('private-key'));
				settings['802-1x']['phase2-ca-cert'] = cert_to_filename(settings['802-1x'].get('phase2-ca-cert'));
				settings['802-1x']['phase2-client-cert'] = cert_to_filename(settings['802-1x'].get('phase2-client-cert'));
				settings['802-1x']['phase2-private-key'] = cert_to_filename(settings['802-1x'].get('phase2-private-key'));
			result['connection'] = settings
			result['SDCERR'] = 0
		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class NetworkAccessPoints(object):
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'accesspoints': {},
		}
		try:
			for dev in NetworkManager.Device.all():
				if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
					options = []
					dev.RequestScan(options)

			i = 0;
			for ap in NetworkManager.AccessPoint.all():
				security_string = ""
				keymgmt = 'none'
				if ((ap.Flags & NetworkManager.NM_802_11_AP_FLAGS_PRIVACY) and (ap.WpaFlags == NetworkManager.NM_802_11_AP_SEC_NONE) and (ap.RsnFlags == NetworkManager.NM_802_11_AP_SEC_NONE)):
					security_string = security_string + 'WEP '
					keymgmt = 'static'

				if (ap.WpaFlags != NetworkManager.NM_802_11_AP_SEC_NONE):
					security_string = security_string + 'WPA1 '

				if (ap.RsnFlags != NetworkManager.NM_802_11_AP_SEC_NONE):
					security_string = security_string + 'WPA2 '

				if ((ap.WpaFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X) or (ap.RsnFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_802_1X)):
					security_string = security_string + '802.1X '
					keymgmt = 'wpa-eap'

				if ((ap.WpaFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_PSK) or (ap.RsnFlags & NetworkManager.NM_802_11_AP_SEC_KEY_MGMT_PSK)):
					security_string = security_string + 'PSK'
					keymgmt = 'wpa-psk'

				ap_data = {
					'Ssid': ap.Ssid,
					'HwAddress': ap.HwAddress,
					'Strength': ap.Strength,
					'MaxBitrate': ap.MaxBitrate,
					'Frequency': ap.Frequency,
					'Flags': ap.Flags,
					'WpaFlags': ap.WpaFlags,
					'RsnFlags': ap.RsnFlags,
					'LastSeen': ap.LastSeen,
					'Security': security_string,
					'Keymgmt': keymgmt,
				}

				result['accesspoints'][i] = ap_data
				result['SDCERR'] = 0
				i += 1
		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Version(object):
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
				'SDCERR': 0,
				'sdk': "undefined",
				'chipset': "undefined",
				'driver': "undefined",
				'driver-version': "undefined",
				'build' : "undefined",
				'supplicant' : "undefined",
		}

		try:
			result['nm_version'] = NetworkManager.NetworkManager.Version
			for dev in NetworkManager.Device.all():
				if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
					result['driver'] = dev.Driver
					result['driver-version'] = dev.DriverVersion

		except Exception as e:
			print(e)

		result['build'] = subprocess.check_output(['cat','/etc/laird-release']).decode('ascii').rstrip()
		result['supplicant'] = subprocess.check_output(['sdcsupp','-v']).decode('ascii').rstrip()
		result['weblcm_python_webapp'] = weblcm_def.WEBLCM_PYTHON_BUILD + '-' + weblcm_def.WEBLCM_PYTHON_VERSION

		return result

@cherrypy.expose
class NetworkInterfaces(object):
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
		}
		try:
			interfaces = []
			for dev in NetworkManager.NetworkManager.GetDevices():
				interfaces.append(dev.Interface + " ")
			result['SDCERR'] = 0
			result['interfaces'] = interfaces
		except Exception as e:
			print(e)
		return result
