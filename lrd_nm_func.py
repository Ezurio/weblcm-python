import cherrypy
import dbus
import subprocess
import os
import uuid
import lrd_nm_def

@cherrypy.expose
class Basic_Type_test(object):

	@cherrypy.tools.accept(media='text/plain')
	def GET(self):
		print("GET")
		return "GET"

	def POST(self):
		print("POST")
		return "POST"

	def PUT(self):
		print("PUT")
		return "PUT"

	def DELETE(self):
		print("AJAX_DELETE")
		return "AJAX_DELETE"

@cherrypy.expose
class Definitions(object):

	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
				'SDCERR': {
					'SDCERR_SUCCESS': 0, 'SDCERR_FAIL': 1
				},
				"PLUGINS": {
					'count': 1,
					'list': {
						'wifi': True, 'interfaces': False, 'remote_update': False,
					},
					'wifi': lrd_nm_def.NM_DBUS_API_TYPES,
				},
				"DEBUG": 3,
				"IGNORE_SESION": 0,
				"SESSION": 0,
		}

		#input_json = cherrypy.request.json
		#print(input_json)

		# Responses are serialized to JSON (because of the json_out decorator)
		return result

@cherrypy.expose
class Wifi_Status(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		result = {
			'SDCERR': 1,
		}
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_OBJ)
			manager = dbus.Interface(proxy, lrd_nm_def.NM_IFACE)

			wifi_device = manager.GetDeviceByIpIface(lrd_nm_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(lrd_nm_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, lrd_nm_def.DBUS_PROP_IFACE)

			result['cardState'] = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "State")
			if result['cardState'] > lrd_nm_def.NM_DBUS_API_TYPES['NMDeviceState']['NM_DEVICE_STATE_UNAVAILABLE']:
				result['SDCERR'] = 0

			active_connection = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "ActiveConnection")
			active_connection_proxy = bus.get_object(lrd_nm_def.NM_IFACE, active_connection)
			active_connection_prop_iface = dbus.Interface(active_connection_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			result['configName'] = active_connection_prop_iface.Get(lrd_nm_def.NM_CONNECTION_ACTIVE_IFACE, "Id")

			ipv4_config_object = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "Ip4Config")
			ipv4_config_proxy = bus.get_object(lrd_nm_def.NM_IFACE, ipv4_config_object)
			ipv4_config_iface = dbus.Interface(ipv4_config_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			ipv4_config_addresses = ipv4_config_iface.Get(lrd_nm_def.NM_IP4_IFACE, "AddressData")
			result['client_IP'] = ipv4_config_addresses[0]['address']

			ipv6_config_object = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "Ip6Config")
			ipv6_config_proxy = bus.get_object(lrd_nm_def.NM_IFACE, ipv6_config_object)
			ipv6_config_iface = dbus.Interface(ipv6_config_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			result['IPv6'] = ipv6_config_iface.Get(lrd_nm_def.NM_IP6_IFACE, "AddressData")

			wifi_iface = dbus.Interface(dev_proxy, lrd_nm_def.NM_WIRELESS_IFACE)
			wifi_prop_iface = dbus.Interface(dev_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			result['client_MAC'] = wifi_prop_iface.Get(lrd_nm_def.NM_WIRELESS_IFACE, "PermHwAddress")
			wireless_mode = wifi_prop_iface.Get(lrd_nm_def.NM_WIRELESS_IFACE, "Mode")
			# Due to some fluctuation in Bitrate identifier lets account for the change
			try:
				result['bitRate'] = wifi_prop_iface.Get(lrd_nm_def.NM_WIRELESS_IFACE, "Bitrate")
			except:
				result['bitRate'] = wifi_prop_iface.Get(lrd_nm_def.NM_WIRELESS_IFACE, "BitRate")

			wireless_active_access_point = wifi_prop_iface.Get(lrd_nm_def.NM_WIRELESS_IFACE, "ActiveAccessPoint")
			ap_proxy = bus.get_object(lrd_nm_def.NM_IFACE, wireless_active_access_point)
			ap_prop_iface = dbus.Interface(ap_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			result['ssid'] = ap_prop_iface.Get(lrd_nm_def.NM_ACCESSPOINT_IFACE, "Ssid")
			result['AP_MAC'] = ap_prop_iface.Get(lrd_nm_def.NM_ACCESSPOINT_IFACE, "HwAddress")
			result['strength'] = int(ap_prop_iface.Get(lrd_nm_def.NM_ACCESSPOINT_IFACE, "Strength"))
			result['channel'] = ap_prop_iface.Get(lrd_nm_def.NM_ACCESSPOINT_IFACE, "Frequency")

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
			"SESSION": 0,
			'profiles': {},
		}
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_OBJ)
			manager = dbus.Interface(proxy, lrd_nm_def.NM_IFACE)

			wifi_device = manager.GetDeviceByIpIface(lrd_nm_def.WIFI_DEVICE_NAME)
			dev_proxy = bus.get_object(lrd_nm_def.NM_IFACE, wifi_device)
			prop_iface = dbus.Interface(dev_proxy, lrd_nm_def.DBUS_PROP_IFACE)

			if prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "State") > lrd_nm_def.NM_DBUS_API_TYPES['NMDeviceState']['NM_DEVICE_STATE_UNAVAILABLE']:
				result['SDCERR'] = 0

			active_connection = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "ActiveConnection")
			active_connection_proxy = bus.get_object(lrd_nm_def.NM_IFACE, active_connection)
			active_connection_prop_iface = dbus.Interface(active_connection_proxy, lrd_nm_def.DBUS_PROP_IFACE)
			result['currentConfig'] = active_connection_prop_iface.Get(lrd_nm_def.NM_CONNECTION_ACTIVE_IFACE, "Uuid")

			settings_proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_SETTINGS_OBJ)
			settings_manager = dbus.Interface(settings_proxy, lrd_nm_def.NM_SETTINGS_IFACE)
			connections = settings_manager.ListConnections()
			result['length'] = len(connections)
			for c in connections:
				connection_proxy = bus.get_object(lrd_nm_def.NM_IFACE, c)
				connection = dbus.Interface(connection_proxy, lrd_nm_def.NM_CONNECTION_IFACE)
				connection_settings = connection.GetSettings()
				if connection_settings['connection']['type'] == '802-11-wireless':
					result['profiles'][connection_settings['connection']['uuid']] = connection_settings['connection']['id']

		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Activate_Connection(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_in()
	@cherrypy.tools.json_out()
	def POST(self):
		result = {
			'SDCERR': 1,
			"SESSION": 0,
		}
		post_data = cherrypy.request.json
		try:
			bus = dbus.SystemBus()

			settings_proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_SETTINGS_OBJ)
			settings_manager = dbus.Interface(settings_proxy, lrd_nm_def.NM_SETTINGS_IFACE)
			conection_to_activate = settings_manager.GetConnectionByUuid(post_data['UUID'])

			nm_proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_OBJ)
			nm_manager = dbus.Interface(nm_proxy, lrd_nm_def.NM_IFACE)
			wifi_device = nm_manager.GetDeviceByIpIface(lrd_nm_def.WIFI_DEVICE_NAME)
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
			"SESSION": 0,
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
			"SESSION": 0,
		}
		post_data = cherrypy.request.json
		print(post_data)

		setting_connection = dbus.Dictionary({
			'type': '802-11-wireless',
			'uuid': str(uuid.uuid4()),
			'id': bytearray(post_data['id']).decode("utf-8"),
			'autoconnect': True,
			'interface-name': 'wlan0',
		})

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

		if post_data['band'] != 'all':
			settings_wireless['band'] = post_data['band']

		if post_data['keymgmt'] != 'none':
			settings_wireless['security'] = '802-11-wireless-security'

			if post_data['keymgmt'] == 'static':
				# key-mgmt of 'static' is also 'none'
				settings_wireless_security['key-mgmt'] = 'none'
				settings_wireless_security['auth-alg'] = post_data['authalg']
				settings_wireless_security['wep-key-type'] = 1 # NM_WEP_KEY_TYPE_KEY
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
				settings_wireless_security['psk'] = bytearray(post_data['psk']).decode("utf-8")

			else:
				if post_data['keymgmt'] == 'ieee8021x':
					settings_wireless_security['auth-alg'] = post_data['authalg']
					if post_data['authalg'] == 'leap':
						settings_wireless_security['leap-username'] = post_data['leapusername']
						settings_wireless_security['leap-password'] = post_data['leappassword']

				settings_8021x = dbus.Dictionary({
					'eap':[post_data['eap']],
					'identity': post_data['identity'],
					'password': post_data['password'],
					'client-cert': path_to_cert(post_data['clientcert']),
					'private-key': path_to_cert(post_data['privatekey']),
					'ca-cert': path_to_cert(post_data['cacert']),
				})

				if post_data['clientcertpassword'] != '':
					settings_8021x['client-cert-password'] = post_data['clientcertpassword']
				if post_data['privatekeypassword'] != '':
					settings_8021x['private-key-password'] = post_data['privatekeypassword']
				if post_data['cacertpassword'] != '':
					settings_8021x['ca-cert-password'] = post_data['cacertpassword']

				if post_data['eap'] == 'fast':
					settings_8021x['pac-file'] = post_data['pacfile']

				if post_data['phase2auth'] != 'auto':
					settings_8021x['phase2-auth'] = [post_data['phase2auth']]

				complete_connection['802-1x'] = settings_8021x

			complete_connection['802-11-wireless-security'] = settings_wireless_security

		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_SETTINGS_OBJ)
			settings = dbus.Interface(proxy, lrd_nm_def.NM_SETTINGS_IFACE)

			settings.AddConnection(complete_connection)

			added_connection = settings.GetConnectionByUuid(setting_connection['uuid'])
			connection_proxy = bus.get_object(lrd_nm_def.NM_IFACE, added_connection)
			connection = dbus.Interface(connection_proxy, lrd_nm_def.NM_CONNECTION_IFACE)
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
			"SESSION": 0,
		}
		post_data = cherrypy.request.json
		try:
			bus = dbus.SystemBus()
			proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_SETTINGS_OBJ)
			manager = dbus.Interface(proxy, lrd_nm_def.NM_SETTINGS_IFACE)
			connection_for_deletion = manager.GetConnectionByUuid(post_data['UUID'])
			connection_proxy = bus.get_object(lrd_nm_def.NM_IFACE, connection_for_deletion)
			connection = dbus.Interface(connection_proxy, lrd_nm_def.NM_CONNECTION_IFACE)
			connection.Delete()
			result['SDCERR'] = 0

		except Exception as e:
			print(e)

		return result

@cherrypy.expose
class Version(object):
	@cherrypy.tools.accept(media='application/json')
	@cherrypy.tools.json_out()
	def GET(self):
		bus = dbus.SystemBus()
		proxy = bus.get_object(lrd_nm_def.NM_IFACE, lrd_nm_def.NM_OBJ)

		manager_iface = dbus.Interface(proxy, lrd_nm_def.DBUS_PROP_IFACE)
		nm_version = manager_iface.Get(lrd_nm_def.NM_IFACE, "Version")

		manager = dbus.Interface(proxy, lrd_nm_def.NM_IFACE)
		wifi_device = manager.GetDeviceByIpIface(lrd_nm_def.WIFI_DEVICE_NAME)
		dev_proxy = bus.get_object(lrd_nm_def.NM_IFACE, wifi_device)
		prop_iface = dbus.Interface(dev_proxy, lrd_nm_def.DBUS_PROP_IFACE)

		driver = prop_iface.Get(lrd_nm_def.NM_DEVICE_IFACE, "Driver")

		build = subprocess.check_output(['cat','/etc/laird-release']).decode('ascii').rstrip()
		supplicant = subprocess.check_output(['sdcsupp','-v']).decode('ascii').rstrip()
		driver_version = subprocess.check_output(['modinfo','--field=version',driver]).decode('ascii').rstrip()

		result = {
				'SDCERR': 0,
				'sdk': nm_version,
				'chipset': driver,
				'driver': driver_version,
				'build' : build,
				'supplicant' : supplicant,
				'lrd_nm_webapp' : lrd_nm_def.LRD_NM_WEBAPP_BUILD + '-' + lrd_nm_def.LRD_NM_WEBAPP_VERSION,

		}

		return result