import sys
import os
import uuid
import time
import cherrypy
import subprocess
import NetworkManager
import weblcm_def
from syslog import syslog

@cherrypy.expose
class NetworkConnections(object):

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		result = {
			'SDCERR': 0,
			'InfoMsg': '',
			'count': 0,
			'connections': {}
		}

		unmanaged_devices = cherrypy.request.app.config['weblcm'].get('unmanaged_hardware_devices', '').split()

		for conn in NetworkManager.Settings.ListConnections():
			s_all = conn.GetSettings()
			s_conn = s_all.get('connection')
			if unmanaged_devices and s_conn.get('interface-name') in unmanaged_devices:
				continue;

			t = {}
			t['id'] = s_conn.get('id')
			t['activated'] = 0

			s_wifi = s_all.get('802-11-wireless')
			if s_wifi and s_wifi.get('mode') == "ap":
				t['type'] = "ap"

			result['connections'][s_conn.get('uuid')] = t

		for conn in NetworkManager.NetworkManager.ActiveConnections:
			uuid = conn.Connection.GetSettings().get('connection').get('uuid')
			if result.get('connections') and result.get('connections').get(uuid):
				result['connections'][uuid]['activated'] = 1

		result['count'] = len(result['connections'])
		return result

@cherrypy.expose
class NetworkConnection(object):

	def get_connection_from_uuid(self, uuid):
		connections = NetworkManager.Settings.ListConnections()
		connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
		try:
			conn = connections[uuid]
		except Exception as e:
			conn = None
		return conn

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def PUT(self):

		result = { 'SDCERR': 1,
					'InfoMsg': 'unable to set connection'}
		try:
			uuid = cherrypy.request.json.get('uuid', None)
			if not uuid:
				result['InfoMsg'] = 'Missing UUID'
				return result

			conn = self.get_connection_from_uuid(uuid)
			if conn == None:
				result['InfoMsg']='UUID not found'
				return result

			if cherrypy.request.json['activate'] == 1 or cherrypy.request.json['activate'] == '1':
				if conn.GetSettings()['connection']['type'] == "bridge":
					if NetworkManager.NetworkManager.ActivateConnection(conn, "/", "/"):
						result['SDCERR'] = 0
						result['InfoMsg'] ='Bridge activated'
				else:
					interface_name = conn.GetSettings()['connection']['interface-name']
					for dev in NetworkManager.Device.all():
						if dev.Interface == interface_name:
							if NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/"):
								result['SDCERR'] = 0
								result['InfoMsg'] = 'Connection Activated'
								break;
			else:
				result['SDCERR'] = 0
				for conn in NetworkManager.NetworkManager.ActiveConnections:
					if uuid == conn.Connection.GetSettings()['connection']['uuid']:
						NetworkManager.NetworkManager.DeactivateConnection(conn)
						result['InfoMsg'] = 'Connection Deactivated'
						return result
				result['InfoMsg'] = 'Already inactive. No action taken'
		except Exception as e:
			syslog (f'exception during NetworkConnection PUT: {e}')
			result['InfoMsg'] = f'Internal error - exception from NeworkManger: {e}'
		return result

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):

		result = {
			'SDCERR': 1,
			'InfoMsg': ''
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

				if post_data.get('gsm'):
					new_settings['gsm'] = post_data.get('gsm');

				if post_data.get('ipv4'):
					new_settings['ipv4'] = post_data.get('ipv4');
				if post_data.get('ipv6'):
					new_settings['ipv6'] = post_data.get('ipv6');

				connections = NetworkManager.Settings.ListConnections()
				connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
				name = new_settings['connection'].get('id', '')
				if connections.get(new_settings['connection']['uuid']):
					connections[new_settings['connection']['uuid']].Update(new_settings)
					result['InfoMsg:'] = f'connection {name} updated'
				else:
					NetworkManager.Settings.AddConnection(new_settings)
					result['InfoMsg:'] = f'connection {name} created'
					result['SDCERR'] = 0

		except Exception as e:
			result['InfoMsg'] = f'Connection POST experienced an exception: {e}'

		return result

	@cherrypy.tools.json_out()
	def DELETE(self, uuid):
		result = {
			'SDCERR': 1,
			'InfoMsg': ''
		}
		try:
			connections = NetworkManager.Settings.ListConnections()
			connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
			connections[uuid].Delete();
			result['SDCERR'] = 0
		except Exception as e:
			result['InfoMsg'] = f'Unable to delete connection'

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		def cert_to_filename(cert):
			"""
				Return base name only.
			"""
			if cert:
				return cert[len(weblcm_def.FILEDIR_DICT.get('cert')):]

		result = {
			'SDCERR': 1,
			'InfoMsg': ''
		}
		try:
			uuid = kwargs.get('uuid', None)
			if not uuid:
				result['InfoMsg'] = 'no UUID provided'
				return result

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
			result['InfoMsg'] = 'Invalid UUID'

		return result

@cherrypy.expose
class NetworkAccessPoints(object):

	@cherrypy.tools.json_out()
	def PUT(self):
		"""
			Start a manual scan
		"""
		result = {
			'SDCERR': 1,
			'InfoMsg': ''
		}

		try:
			for dev in NetworkManager.Device.all():
				if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
					options = []
					dev.RequestScan(options)

			result['SDCERR'] = 0
			result['InfoMsg'] = 'Scan requested'

		except Exception as e:
			result['InfoMsg'] = 'Unable to start scan request'

		return result

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		'''Get Cached AP list'''

		result = {
			'SDCERR': 1,
			'InfoMsg': '',
			'count': 0,
			'accesspoints': [],
		}

		try:
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
					'SSID': ap.Ssid,
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
				result['accesspoints'].append(ap_data)

			if len(result['accesspoints']) > 0:
				result['SDCERR'] = 0
				result['count'] = len(result['accesspoints'])
			else:
				result['InfoMsg'] = 'No access points found'

		except Exception as e:
			result['InfoMsg'] = 'Unable to get access point list'
			syslog(f'NetworkAccessPoints GET exception: {e}')

		return result

@cherrypy.expose
class Version(object):

	_version = {}

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):
		try:
			if not Version._version:
				Version._version['SDCERR'] = weblcm_def.WEBLCM_ERRORS.get('SDCERR_SUCCESS')
				Version._version['InfoMsg'] = ''
				Version._version['nm_version'] = NetworkManager.NetworkManager.Version
				Version._version['weblcm_python_webapp'] = weblcm_def.WEBLCM_PYTHON_VERSION
				Version._version['build'] = subprocess.check_output("sed -n 's/^VERSION=//p' /etc/os-release", shell=True).decode('ascii').strip().strip('"')
				Version._version['supplicant'] = subprocess.check_output(['sdcsupp','-v']).decode('ascii').rstrip()
				Version._version['radio_stack'] = NetworkManager.NetworkManager.Version.partition("-")[0]
				for dev in NetworkManager.Device.all():
					if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
						Version._version['driver'] = dev.Driver
						Version._version['kernel_vermagic'] = dev.DriverVersion
						break
		except Exception as e:
			Version._version = {'SDCERR' : weblcm_def.WEBLCM_ERRORS.get('SDCERR_FAIL'), 'InfoMsg':f'An exception occurred while trying to get versioning info: {e}' }
		return Version._version

@cherrypy.expose
class NetworkInterfaces(object):

	@cherrypy.tools.json_out()
	def GET(self, *args, **kwargs):

		result = { 'SDCERR': 1,
				   'InfoMsg': '',}
		interfaces = []

		try:
			managed_devices = cherrypy.request.app.config['weblcm'].get('managed_software_devices', '').split()
			unmanaged_devices = cherrypy.request.app.config['weblcm'].get('unmanaged_hardware_devices', '').split()
			for dev in NetworkManager.NetworkManager.GetDevices():
				#Don't return connections with unmanaged interfaces
				if dev.State == NetworkManager.NM_DEVICE_STATE_UNMANAGED:
					continue
				if dev.Interface in unmanaged_devices:
					continue
				interfaces.append(dev.Interface)

			for dev in managed_devices:
				if dev not in interfaces:
					interfaces.append(dev)

			result['SDCERR'] = 0
			result['interfaces'] = interfaces
		except Exception as e:
			result['InfoMsg'] = 'Exception getting list of interfaces'
			syslog(f'NetworkInterfaces GET exception: {e}')

		return result
