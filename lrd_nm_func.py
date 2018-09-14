import cherrypy
import dbus
import subprocess
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