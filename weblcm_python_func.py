import cherrypy
import dbus
import subprocess
import os
import uuid
import time
from systemd import journal
import weblcm_python_def

def in_session(value):
	if value in cherrypy.session:
		return True
	else:
		return False

@cherrypy.tools.register('before_request_body')
def check_session():
	if not in_session('SESSION'):
		cherrypy.session['SESSION'] = 1

def merge_secrets(proxy, config, setting_name):
	try:
		secrets = proxy.GetSecrets(setting_name)

		for setting in secrets:
			for key in secrets[setting]:
				config[setting_name][key] = secrets[setting][key]
	except Exception as e:
		pass

@cherrypy.expose
class Wifi_Status(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'strength':0,
			'channel':0,
		}
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_OBJ)
			manager = dbus.Interface(proxy, weblcm_python_def.NM_IFACE)

			wifi_device = manager.GetDeviceByIpIface(weblcm_python_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(weblcm_python_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)

			result['cardState'] = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "State")
			if result['cardState'] > weblcm_python_def.NM_DBUS_API_TYPES['NMDeviceState']['NM_DEVICE_STATE_UNAVAILABLE']:
				result['SDCERR'] = 0

			wifi_iface = dbus.Interface(dev_proxy, weblcm_python_def.NM_WIRELESS_IFACE)
			wifi_prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			result['client_MAC'] = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "PermHwAddress")

			active_connection = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "ActiveConnection")
			active_connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, active_connection)
			active_connection_prop_iface = dbus.Interface(active_connection_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			try:
				result['configName'] = active_connection_prop_iface.Get(weblcm_python_def.NM_CONNECTION_ACTIVE_IFACE, "Id")
			except Exception as e:
				print(e)
				return result

			ipv4_config_object = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "Ip4Config")
			ipv4_config_proxy = bus.get_object(weblcm_python_def.NM_IFACE, ipv4_config_object)
			ipv4_config_iface = dbus.Interface(ipv4_config_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			ipv4_config_addresses = ipv4_config_iface.Get(weblcm_python_def.NM_IP4_IFACE, "AddressData")
			result['client_IP'] = ipv4_config_addresses[0]['address']

			ipv6_config_object = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "Ip6Config")
			ipv6_config_proxy = bus.get_object(weblcm_python_def.NM_IFACE, ipv6_config_object)
			ipv6_config_iface = dbus.Interface(ipv6_config_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			result['IPv6'] = ipv6_config_iface.Get(weblcm_python_def.NM_IP6_IFACE, "AddressData")

			wireless_mode = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "Mode")
			# Due to some fluctuation in Bitrate identifier lets account for the change
			try:
				result['bitRate'] = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "Bitrate")
			except:
				result['bitRate'] = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "BitRate")

			wireless_active_access_point = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "ActiveAccessPoint")
			ap_proxy = bus.get_object(weblcm_python_def.NM_IFACE, wireless_active_access_point)
			ap_prop_iface = dbus.Interface(ap_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			result['ssid'] = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Ssid")
			result['AP_MAC'] = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "HwAddress")
			result['strength'] = int(ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Strength"))
			result['channel'] = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Frequency")

		except Exception as e:
			print(e)

		return result

@cherrypy.expose
@cherrypy.tools.check_session()
class Connections(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
			'SESSION': cherrypy.session['SESSION'],
			'profiles': {},
		}
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_OBJ)
			manager = dbus.Interface(proxy, weblcm_python_def.NM_IFACE)

			wifi_device = manager.GetDeviceByIpIface(weblcm_python_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(weblcm_python_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)

			if prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "State") > weblcm_python_def.NM_DBUS_API_TYPES['NMDeviceState']['NM_DEVICE_STATE_UNAVAILABLE']:
				result['SDCERR'] = 0

			#TODO - Handle case where no active connection exists.
			active_connection = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "ActiveConnection")
			active_connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, active_connection)
			active_connection_prop_iface = dbus.Interface(active_connection_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			try:
				result['currentConfig'] = active_connection_prop_iface.Get(weblcm_python_def.NM_CONNECTION_ACTIVE_IFACE, "Uuid")
			except Exception as e:
				print(e)

		except Exception as e:
			print(e)

		settings_proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_SETTINGS_OBJ)
		settings_manager = dbus.Interface(settings_proxy, weblcm_python_def.NM_SETTINGS_IFACE)
		connections = settings_manager.ListConnections()
		result['length'] = len(connections)
		for c in connections:
			connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, c)
			connection = dbus.Interface(connection_proxy, weblcm_python_def.NM_CONNECTION_IFACE)
			connection_settings = connection.GetSettings()
			if connection_settings['connection']['type'] == '802-11-wireless':
				result['profiles'][connection_settings['connection']['uuid']] = connection_settings['connection']['id']

		return result

@cherrypy.expose
class Activate_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
			'SESSION': cherrypy.session['SESSION'],
		}
		post_data = cherrypy.request.json
		try:
			bus = dbus.SystemBus()

			settings_proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_SETTINGS_OBJ)
			settings_manager = dbus.Interface(settings_proxy, weblcm_python_def.NM_SETTINGS_IFACE)
			conection_to_activate = settings_manager.GetConnectionByUuid(post_data['UUID'])

			nm_proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_OBJ)
			nm_manager = dbus.Interface(nm_proxy, weblcm_python_def.NM_IFACE)
			wifi_device = nm_manager.GetDeviceByIpIface(weblcm_python_def.WIFI_DEVICE_NAME)
			active_connection = nm_manager.ActivateConnection(conection_to_activate,wifi_device,"/")
			result['SDCERR'] = 0

		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Get_Certificates(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 0,
			'SESSION': cherrypy.session['SESSION'],
			"certs": {},
		}

		cert_directory = "/etc/ssl"
		supported_certs = ('.cer','.der','.pem','.pfx','.pac','.p7b')
		certs = []
		i = 1

		with os.scandir(cert_directory) as listOfEntries:
			for entry in listOfEntries:
				if entry.is_file():
					if entry.name.lower().endswith(supported_certs):
						certs.append(entry.name)

		certs.sort()
		for cert in certs:
			result['certs'][i] = cert
			i += 1

		return result

@cherrypy.expose
class Add_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		def path_to_cert(name):
			return [ dbus.Byte(ord(c)) for c in ("file:///etc/ssl/" + name) ] + [ dbus.Byte(0) ]

		result = {
			'SDCERR': 1,
			'SESSION': cherrypy.session['SESSION'],
		}
		post_data = cherrypy.request.json
		print(post_data)

		setting_connection = dbus.Dictionary({
			'type': '802-11-wireless',
			'id': bytearray(post_data['id']).decode("utf-8"),
			'autoconnect': True,
			'interface-name': 'wlan0',
		})

		if post_data['uuid'] == '':
			setting_connection['uuid'] = str(uuid.uuid4())
		else:
			setting_connection['uuid'] = post_data['uuid']

		settings_wireless = dbus.Dictionary({
			'mode': 'infrastructure',
			'ssid': dbus.ByteArray(post_data['ssid']),
		})

		settings_wireless_security = dbus.Dictionary({
			'key-mgmt': post_data['keymgmt'],
		})

		settings_ip4 = dbus.Dictionary({'method': 'auto'})
		settings_ip6 = dbus.Dictionary({'method': 'auto'})

		complete_connection = dbus.Dictionary({
			'connection': setting_connection,
			'802-11-wireless': settings_wireless,
			'ipv4': settings_ip4,
			'ipv6': settings_ip6,
		})

		if 'band' in post_data:
			if post_data['band'] != 'all':
				settings_wireless['band'] = post_data['band']

		if post_data['keymgmt'] != 'none':
			settings_wireless['security'] = '802-11-wireless-security'

			if post_data['keymgmt'] == 'static':
				# key-mgmt of 'static' is also 'none'
				settings_wireless_security['key-mgmt'] = 'none'
				if 'authalg' in post_data:
					settings_wireless_security['auth-alg'] = post_data['authalg']
				settings_wireless_security['wep-key-type'] = 1 # NM_WEP_KEY_TYPE_KEY
				if 'weptxkeyidx' in post_data:
					settings_wireless_security['wep-tx-keyidx'] = post_data['weptxkeyidx']
					if (len(post_data['wepkey0'])):
						settings_wireless_security['wep-key0'] = post_data['wepkey0']
					if (len(post_data['wepkey1'])):
						settings_wireless_security['wep-key1'] = post_data['wepkey1']
					if (len(post_data['wepkey2'])):
						settings_wireless_security['wep-key2'] = post_data['wepkey2']
					if (len(post_data['wepkey3'])):
						settings_wireless_security['wep-key3'] = post_data['wepkey3']

			elif post_data['keymgmt'] == 'wpa-psk':
				if 'psk' in post_data:
					settings_wireless_security['psk'] = bytearray(post_data['psk']).decode("utf-8")

			else:
				if post_data['keymgmt'] == 'ieee8021x':
					settings_wireless_security['auth-alg'] = post_data['authalg']
					if post_data['authalg'] == 'leap':
						settings_wireless_security['leap-username'] = post_data['leapusername']
						settings_wireless_security['leap-password'] = post_data['leappassword']

				settings_8021x = dbus.Dictionary({
					'eap':[post_data['eap']],
				})

				if 'identity' in post_data:
					settings_8021x['identity'] = post_data['identity']
				if 'password' in post_data:
					settings_8021x['password'] = post_data['password']
				if 'clientcert' in post_data:
					settings_8021x['client-cert'] = path_to_cert(post_data['clientcert'])
				if 'privatekey' in post_data:
					settings_8021x['private-key'] = path_to_cert(post_data['privatekey'])
				if 'cacert' in post_data:
					settings_8021x['ca-cert'] = path_to_cert(post_data['cacert'])
				if 'clientcertpassword' in post_data:
					if post_data['clientcertpassword'] != '':
						settings_8021x['client-cert-password'] = post_data['clientcertpassword']
				if 'privatekeypassword' in post_data:
					settings_8021x['private-key-password'] = post_data['privatekeypassword']
				if 'cacertpassword' in post_data:
					if post_data['cacertpassword'] != '':
						settings_8021x['ca-cert-password'] = post_data['cacertpassword']

				if post_data['eap'] == 'fast':
					settings_8021x['pac-file'] = post_data['pacfile']

				settings_8021x['phase2-auth'] = ['md5', 'mschapv2', 'otp', 'gtc', 'tls']
				if 'phase2auth' in post_data:
					if post_data['phase2auth'] != 'auto':
						settings_8021x['phase2-auth'] = [post_data['phase2auth']]

				complete_connection['802-1x'] = settings_8021x

			complete_connection['802-11-wireless-security'] = settings_wireless_security

		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_SETTINGS_OBJ)
			settings = dbus.Interface(proxy, weblcm_python_def.NM_SETTINGS_IFACE)

			try:
				settings.AddConnection(complete_connection)
			except:
				update_connection = settings.GetConnectionByUuid(setting_connection['uuid'])
				connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, update_connection)
				connection = dbus.Interface(connection_proxy, weblcm_python_def.NM_CONNECTION_IFACE)
				connection.Update(complete_connection)


			added_connection = settings.GetConnectionByUuid(setting_connection['uuid'])
			connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, added_connection)
			connection = dbus.Interface(connection_proxy, weblcm_python_def.NM_CONNECTION_IFACE)
			connection_settings = connection.GetSettings()
			print('Connection added:')
			print('Name: ' + connection_settings['connection']['id'])
			print('UUID: ' + connection_settings['connection']['uuid'])
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
			'SESSION': cherrypy.session['SESSION'],
		}
		post_data = cherrypy.request.json
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_SETTINGS_OBJ)
			manager = dbus.Interface(proxy, weblcm_python_def.NM_SETTINGS_IFACE)
			connection_for_deletion = manager.GetConnectionByUuid(post_data['UUID'])
			connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, connection_for_deletion)
			connection = dbus.Interface(connection_proxy, weblcm_python_def.NM_CONNECTION_IFACE)
			connection.Delete()
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
		result = {
			'SDCERR': 1,
			'SESSION': cherrypy.session['SESSION'],
		}
		post_data = cherrypy.request.json
		print(post_data)
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_SETTINGS_OBJ)
			settings = dbus.Interface(proxy, weblcm_python_def.NM_SETTINGS_IFACE)
			uuid_connection = settings.GetConnectionByUuid(post_data['UUID'])
			connection_proxy = bus.get_object(weblcm_python_def.NM_IFACE, uuid_connection)
			connection = dbus.Interface(connection_proxy, weblcm_python_def.NM_CONNECTION_IFACE)
			connection_settings = connection.GetSettings()
			merge_secrets(connection,connection_settings,'802-11-wireless')
			merge_secrets(connection,connection_settings,'802-11-wireless-security')
			merge_secrets(connection,connection_settings,'802-1x')

			if 'wep-tx-keyidx' in connection_settings['802-11-wireless-security']:
				if connection_settings['802-11-wireless-security']['key-mgmt'] == 'none':
					connection_settings['802-11-wireless-security']['key-mgmt'] = 'static'
			result['connection'] = connection_settings
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
			'SESSION': cherrypy.session['SESSION'],
			'accesspoints': {},
		}
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_OBJ)
			manager = dbus.Interface(proxy, weblcm_python_def.NM_IFACE)
			wifi_device = manager.GetDeviceByIpIface(weblcm_python_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(weblcm_python_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			wifi_iface = dbus.Interface(dev_proxy, weblcm_python_def.NM_WIRELESS_IFACE)
			wifi_prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)
			wireless_active_access_point = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "ActiveAccessPoint")
			wireless_hwaddress = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "HwAddress")
			wireless_permhwaddress = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "PermHwAddress")
			wireless_mode = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "Mode")
			wireless_bitrate = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "BitRate")
			wireless_lastscan = wifi_prop_iface.Get(weblcm_python_def.NM_WIRELESS_IFACE, "LastScan")
			print('Last scan:' + str(wireless_lastscan))
			scan_diff_in_seconds = ((time.clock_gettime(time.CLOCK_MONOTONIC) * 1000) - wireless_lastscan) / 1000
			print('Time difference since last scan: ' + str(scan_diff_in_seconds))
			try:
				options = []
				wifi_iface.RequestScan(options)
				print('Scan requested')
			except Exception as e:
				print(e)

			aps = wifi_iface.GetAllAccessPoints()
			i = 0
			for path in aps:
				ap_proxy = bus.get_object(weblcm_python_def.NM_IFACE, path)
				ap_prop_iface = dbus.Interface(ap_proxy, weblcm_python_def.DBUS_PROP_IFACE)
				ssid = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Ssid")
				bssid = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "HwAddress")
				strength = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Strength")
				maxbitrate = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "MaxBitrate")
				freq = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Frequency")
				flags = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "Flags")
				wpaflags = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "WpaFlags")
				rsnflags = ap_prop_iface.Get(weblcm_python_def.NM_ACCESSPOINT_IFACE, "RsnFlags")
				security_string = ""
				ssid_string = "%s" % ''.join([str(v) for v in ssid])
				keymgmt = 'none'
				if ((flags & weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApFlags']['NM_802_11_AP_FLAGS_PRIVACY']) and (wpaflags == weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']) and (rsnflags == weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE'])):
					security_string = security_string + 'WEP '
					keymgmt = 'static'

				if (wpaflags != weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']):
					security_string = security_string + 'WPA1 '

				if (rsnflags != weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_NONE']):
					security_string = security_string + 'WPA2 '

				if ((wpaflags & weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_802_1X']) or (rsnflags & weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_802_1X'])):
					security_string = security_string + '802.1X '
					keymgmt = 'wpa-eap'

				if ((wpaflags & weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_PSK']) or (rsnflags & weblcm_python_def.NM_DBUS_API_TYPES['NM80211ApSecurityFlags']['NM_802_11_AP_SEC_KEY_MGMT_PSK'])):
					security_string = security_string + 'PSK'
					keymgmt = 'wpa-psk'

				ap_data = {
					'ssid': ssid_string,
					'bssid': bssid,
					'strength': strength,
					'maxbitrate': maxbitrate,
					'freq': freq,
					'flags': flags,
					'wpaflags': wpaflags,
					'rsnflags': rsnflags,
					'security': security_string,
					'keymgmt': keymgmt,
				}

				result['accesspoints'][i] = ap_data
				result['last_scan'] = scan_diff_in_seconds
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
				'driver_version': "undefined",
				'build' : "undefined",
				'supplicant' : "undefined",
		}

		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(weblcm_python_def.NM_IFACE, weblcm_python_def.NM_OBJ)

			manager_iface = dbus.Interface(proxy, weblcm_python_def.DBUS_PROP_IFACE)

			manager = dbus.Interface(proxy, weblcm_python_def.NM_IFACE)
			wifi_device = manager.GetDeviceByIpIface(weblcm_python_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(weblcm_python_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, weblcm_python_def.DBUS_PROP_IFACE)

			result['nm_version'] = manager_iface.Get(weblcm_python_def.NM_IFACE, "Version")
			result['driver'] = prop_iface.Get(weblcm_python_def.NM_DEVICE_IFACE, "Driver")
			result['driver_version'] = subprocess.check_output(['modinfo','--field=version',result['driver']]).decode('ascii').rstrip()

		except Exception as e:
			print(e)

		result['build'] = subprocess.check_output(['cat','/etc/laird-release']).decode('ascii').rstrip()
		result['supplicant'] = subprocess.check_output(['sdcsupp','-v']).decode('ascii').rstrip()
		result['weblcm_python_webapp'] = weblcm_python_def.WEBLCM_PYTHON_BUILD + '-' + weblcm_python_def.WEBLCM_PYTHON_VERSION

		return result

class Log_Data():
	last_cursor = ''
	age_of_last_cursor = 0
	full_log = None
	journal_entries = ''

@cherrypy.expose
class Request_Log(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
		}

		current_time = time.time()
		age="--"

		# systemd journal
		if os.path.isfile(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME):
			st=os.stat(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME)
			age=round((current_time-st.st_mtime))

		result['systemd_age'] = str(age)

		log = []

		if (Log_Data.age_of_last_cursor  + weblcm_python_def.LOGGING_REGENERATE_LOG_TIMER ) < current_time:
			if type(Log_Data.full_log) is 'systemd.journal.Reader':
				Log_Data.full_log.close()
			buffer = journal.Reader()
			for service in weblcm_python_def.DEFAULT_LOG_SERVICES:
				buffer.add_match(_SYSTEMD_UNIT=service + ".service")
			if Log_Data.journal_entries:
				for service in Log_Data.journal_entries:
					buffer.add_match(_SYSTEMD_UNIT=service + ".service")
			buffer.this_boot()
			buffer.seek_head()
		else:
			buffer = Log_Data.full_log
			if buffer.test_cursor(Log_Data.last_cursor):
				buffer.seek_cursor(Log_Data.last_cursor)
				buffer.get_next()

		#loop for LOGGING_UPDATE_LOG_TIMER seconds.
		t_end = time.time() + weblcm_python_def.LOGGING_UPDATE_LOG_TIMER
		Log_Data.age_of_last_cursor = t_end
		while time.time() < t_end:
			entry = buffer.get_next()
			# See if at end of log
			try:
				data = [str(entry['__REALTIME_TIMESTAMP']),entry['SYSLOG_IDENTIFIER'],entry['MESSAGE']]
				log.append(data)
				Log_Data.last_cursor = entry['__CURSOR']
			except:
				time.sleep(1)

		Log_Data.full_log = buffer
		result['log'] = log
		result['SDCERR'] = 0

		return result

@cherrypy.expose
class Generate_Log(object):
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}

		post_data = cherrypy.request.json

		if os.path.isfile(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME):
			os.remove(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME)
		buffer = journal.Reader()
		buffer.this_boot()
		if not os.path.isdir(weblcm_python_def.LOGGING_STORAGE_PATH):
			try:
				os.mkdir(weblcm_python_def.LOGGING_STORAGE_PATH)
			except OSError:
				print("Creation of the directory %s failed" % weblcm_python_def.LOGGING_STORAGE_PATH)
		log_file = open(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME, "w")
		if log_file.mode == 'w':
			for entry in buffer:
				line = str(entry['__REALTIME_TIMESTAMP']) + " " + entry['SYSLOG_IDENTIFIER'] + ":" + entry['MESSAGE'] + "\n"
				log_file.write(line)
			log_file.close()
			result['SDCERR'] = 0

		return result

@cherrypy.expose
class Download_Log(object):

	def GET(self):
		from cherrypy.lib import static

		return static.serve_file(weblcm_python_def.LOGGING_STORAGE_PATH + weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME, 'application/x-download','attachment', weblcm_python_def.LOGGING_SYSD_JOURNAL_LOG_NAME)

@cherrypy.expose
class Set_Logging(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
		}

		post_data = cherrypy.request.json

		bus = dbus.SystemBus()
		proxy = bus.get_object(weblcm_python_def.WPA_IFACE, weblcm_python_def.WPA_OBJ)
		wpas = dbus.Interface(proxy, weblcm_python_def.DBUS_PROP_IFACE)
		wpas.Set(weblcm_python_def.WPA_IFACE, "DebugLevel", str(post_data['suppDebugLevel']))

		try:
			driver_debug_file = open(weblcm_python_def.WIFI_DRIVER_DEBUG_PARAM, "w")
			if driver_debug_file.mode == 'w':
				driver_debug_file.write(str(post_data['driverDebugLevel']))
		except Exception as e:
			print(e)

		result['SDCERR'] = 0

		return result

@cherrypy.expose
class Get_Logging(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
		}

		bus = dbus.SystemBus()
		proxy = bus.get_object(weblcm_python_def.WPA_IFACE, weblcm_python_def.WPA_OBJ)
		wpas = dbus.Interface(proxy, weblcm_python_def.DBUS_PROP_IFACE)
		debug_level = wpas.Get(weblcm_python_def.WPA_IFACE, "DebugLevel")

		result['suppDebugLevel'] = debug_level

		try:
			driver_debug_file = open(weblcm_python_def.WIFI_DRIVER_DEBUG_PARAM, "r")
			if driver_debug_file.mode == 'r':
				contents = driver_debug_file.read(1)
				result['driverDebugLevel'] = contents
		except Exception as e:
			print(e)

		result['SDCERR'] = 0

		return result
