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
class Networking_Status(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'devices':0,
		}
		try:
			devices = NetworkManager.NetworkManager.GetDevices()
			interface = {}
			for dev in devices:
				interface_name = dev.Interface
				interface_status = {}
				interface_status['Autoconnect'] = dev.Autoconnect;

				#Dont add unmanaged devices
				show_unmanaged = cherrypy.request.app.config['weblcm']['show_unmanaged']
				if(not show_unmanaged and dev.State == 10):
					continue;

				interface[interface_name] = {}
				result['devices'] = result['devices'] + 1

				interface_status['State'] = dev.State
				interface_status['Mtu'] = dev.Mtu
				interface_status['DeviceType'] = dev.DeviceType

				if dev.State == 100:
					settings = dev.ActiveConnection.Connection.GetSettings();
					interface[interface_name]['connection_active'] = settings['connection']

					ip4Config = {}

					addresses = {}
					i = 0
					for addr in dev.Ip4Config.Addresses:
						addresses[i] = str(addr[0]) + "/" + str(addr[1])
						i += 1
					ip4Config['Addresses'] = addresses

					routes = {}
					i = 0
					for rt in dev.Ip4Config.Routes:
						routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
						i += 1
					ip4Config['Routes'] = routes

					ip4Config['Gateway'] = dev.Ip4Config.Gateway

					i = 0
					domains = {}
					for dns in dev.Ip4Config.Domains:
						domains[i] = str(dns)
						i += 1
					ip4Config['Domains'] = domains

					interface[interface_name]['ip4config'] = ip4Config

					#IPv6 device address information
					ip6Config = {}

					addresses = {}
					i = 0
					for addr in dev.Ip6Config.Addresses:
						addresses[i] = str(addr[0]) + "/" + str(addr[1])
						i += 1
					ip6Config['Addresses'] = addresses

					routes = {}
					i = 0
					for rt in dev.Ip6Config.Routes:
						routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
						i += 1
					ip6Config['Routes'] = routes

					ip6Config['Gateway'] = dev.Ip6Config.Gateway

					i = 0
					domains = {}
					for dns in dev.Ip4Config.Domains:
						domains[i] = str(dns)
						i += 1
					ip6Config['Domains'] = domains

					interface[interface_name]['ip6config'] = ip6Config

					#IPv4 lease/config information
					if dev.Dhcp4Config:
						interface[interface_name]['dhcp4config'] = dev.Dhcp4Config.Options

					#IPv6 lease/config information
					if dev.Dhcp6Config:
						interface[interface_name]['dhcp6config'] = dev.Dhcp6Config.Options

				#Get wired specific items
				if dev.DeviceType == 1:
					wired = {};
					wired['HwAddress'] = dev.HwAddress
					wired['PermHwAddress'] = dev.PermHwAddress
					wired['Speed'] = dev.Speed
					wired['Carrier'] = dev.Carrier
					interface[interface_name]['wired'] = wired

				#Get Wifi specific items
				if dev.DeviceType == 2:
					wireless = {}
					wireless['Bitrate'] = dev.Bitrate
					wireless['HwAddress'] = dev.HwAddress
					wireless['PermHwAddress'] = dev.PermHwAddress
					wireless['Mode'] = dev.Mode
					wireless['LastScan'] = dev.LastScan
					interface[interface_name]['wireless'] = wireless

				if (dev.DeviceType == 2 and dev.State == 100):
					# Get access point info
					ap_data = {
						'Ssid': dev.ActiveAccessPoint.Ssid,
						'HwAddress': dev.ActiveAccessPoint.HwAddress,
						'Strength': dev.ActiveAccessPoint.Strength,
						'Maxbitrate': dev.ActiveAccessPoint.MaxBitrate,
						'Frequency': dev.ActiveAccessPoint.Frequency,
						'Flags': dev.ActiveAccessPoint.Flags,
						'Wpaflags': dev.ActiveAccessPoint.WpaFlags,
						'Rsnflags': dev.ActiveAccessPoint.RsnFlags
					}
					interface[interface_name]['activeaccesspoint'] = ap_data

				interface[interface_name]['status'] = interface_status

			result['status'] = interface
			result['SDCERR'] = 0

		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Connections(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'connections': {},
		}

		connections = NetworkManager.Settings.ListConnections()
		result['length'] = len(connections)
		for conn in connections:
			settings = conn.GetSettings()['connection']
			result['connections'][settings['uuid']] = [settings['id'], 0]

		devices = NetworkManager.NetworkManager.GetDevices()
		for dev in devices:
			if dev.ActiveConnection:
				result['connections'][dev.ActiveConnection.Uuid][1] = 1

		result['SDCERR'] = 0
		return result

@cherrypy.expose
class Activate_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
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
						result['SDCERR'] = 0
						break;
		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Save_Connection(object):

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
								new_settings['802-1x']['ca-cert'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('ca-cert');
							if new_settings['802-1x'].get('client-cert'):
								new_settings['802-1x']['client-cert'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('client-cert')
							if new_settings['802-1x'].get('private-key'):
								new_settings['802-1x']['private-key'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('private-key')
							if new_settings['802-1x'].get('phase2-ca-cert'):
								new_settings['802-1x']['phase2-ca-cert'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('phase2-ca-cert');
							if new_settings['802-1x'].get('phase2-client-cert'):
								new_settings['802-1x']['phase2-client-cert'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('phase2-client-cert');
							if new_settings['802-1x'].get('phase2-private-key'):
								new_settings['802-1x']['phase2-private-key'] = weblcm_def.CERT_DIRECTORY + new_settings['802-1x'].get('phase2-private-key');

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

@cherrypy.expose
class Remove_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}
		try:
			uuid = cherrypy.request.json['UUID']
			if uuid:
				connections = NetworkManager.Settings.ListConnections()
				connections = dict([(x.GetSettings()['connection']['uuid'], x) for x in connections])
				connections[uuid].Delete();
				result['SDCERR'] = 0
		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Edit_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):

		def cert_to_filename(cert):
			"""
				Return base name only.
			"""
			if cert:
				return cert[len(weblcm_def.CERT_DIRECTORY):]
			return

		result = {
			'SDCERR': 1,
		}
		try:
			uuid = cherrypy.request.json['UUID']
			if uuid:
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
class Wifi_Scan(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'accesspoints': {},
		}
		try:
			try:
				for dev in NetworkManager.Device.all():
					if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
						options = []
						dev.RequestScan(options)
			except Exception as e:
				print(e)

			i = 0;
			for ap in NetworkManager.AccessPoint.all():
				security_string = ""
				keymgmt = 'none'
				if ((ap.Flags & weblcm_def.NM_DBUS_API_TYPES['NM80211ApFlags']['NM_802_11_AP_FLAGS_PRIVACY']) and (ap.WpaFlags == weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']) and (ap.RsnFlags == weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE'])):
					security_string = security_string + 'WEP '
					keymgmt = 'static'

				if (ap.WpaFlags != weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']):
					security_string = security_string + 'WPA1 '

				if (ap.RsnFlags != weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']):
					security_string = security_string + 'WPA2 '

				if ((ap.WpaFlags & weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_802_1X']) or (ap.RsnFlags & weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_802_1X'])):
					security_string = security_string + '802.1X '
					keymgmt = 'wpa-eap'

				if ((ap.WpaFlags & weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_PSK']) or (ap.RsnFlags & weblcm_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_PSK'])):
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
	@cherrypy.tools.accept(media='application/json')
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
class Get_Interfaces(object):
	@cherrypy.tools.accept(media='application/json')
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
