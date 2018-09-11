import dbus
import socket, struct

# Standard DBUS Properties
DBUS_PROP_IFACE =		'org.freedesktop.DBus.Properties'
NM_OBJ =				'/org/freedesktop/NetworkManager'
NM_IFACE =				'org.freedesktop.NetworkManager'
NM_DEVICE_IFACE =		'org.freedesktop.NetworkManager.Device'
NM_IP4_IFACE =			'org.freedesktop.NetworkManager.IP4Config'
NM_IP6_IFACE =			'org.freedesktop.NetworkManager.IP6Config'
NM_DHCP4_IFACE =		'org.freedesktop.NetworkManager.DHCP4Config'
NM_DHCP6_IFACE =		'org.freedesktop.NetworkManager.DHCP6Config'
NM_WIRED_IFACE =		'org.freedesktop.NetworkManager.Device.Wired'
NM_WIRELESS_IFACE =		'org.freedesktop.NetworkManager.Device.Wireless'
NM_ACCESSPOINT_IFACE =	'org.freedesktop.NetworkManager.AccessPoint'

bus = dbus.SystemBus()
proxy = bus.get_object(NM_IFACE, NM_OBJ)

#For org.freedesktop.NetworkManager
#Use standard DBUS Property on NetworkManager to
#Get NM version
manager_iface = dbus.Interface(proxy, DBUS_PROP_IFACE)
print('Network Manager Version:' + str(manager_iface.Get(NM_IFACE, "Version")))

#For org.freedesktop.NetworkManager
manager = dbus.Interface(proxy, NM_IFACE)
#Call a NM_IFACE's method
devices = manager.GetDevices()
for d in devices:
	#Get device object
	dev_proxy = bus.get_object(NM_IFACE, d)
	prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
	#Get org.freedesktop.NetworkManager.Device properties
	print('Interface Name: ' + str(prop_iface.Get(NM_DEVICE_IFACE, "Interface")))
	print('\tAutoconnect:')
	print('\t\t' + str(prop_iface.Get(NM_DEVICE_IFACE, "Autoconnect")))
	print('\tState:')
	print('\t\t' + str(prop_iface.Get(NM_DEVICE_IFACE, "State")))
	print('\tMtu:')
	print('\t\t' + str(prop_iface.Get(NM_DEVICE_IFACE, "Mtu")))

	device_type = prop_iface.Get(NM_DEVICE_IFACE, "DeviceType")
	print('\tDeviceType:')
	print('\t\t' + str(device_type))
	state = prop_iface.Get(NM_DEVICE_IFACE, "State")
	print('\tState:')
	print('\t\t' + str(state))

	# if NM_DEVICE_STATE_ACTIVATED get ipv4 address information
	if state == 100:
		#IPv4 device address information
		ipv4_config_object = prop_iface.Get(NM_DEVICE_IFACE, "Ip4Config")
		ipv4_config_proxy = bus.get_object(NM_IFACE, ipv4_config_object)
		ipv4_config_iface = dbus.Interface(ipv4_config_proxy, DBUS_PROP_IFACE)
		ipv4_config_addresses = ipv4_config_iface.Get(NM_IP4_IFACE, "AddressData")
		ipv4_config_routes= ipv4_config_iface.Get(NM_IP4_IFACE, "RouteData")
		ipv4_config_gateway = ipv4_config_iface.Get(NM_IP4_IFACE, "Gateway")
		ipv4_config_domains = ipv4_config_iface.Get(NM_IP4_IFACE, "Domains")
		print("\tIPv4 Info:")
		print("\t\tAdresses:")
		i = 0
		while i < len(ipv4_config_addresses):
			print("\t\t\t" + str(ipv4_config_addresses[i]['address']) + "/" + str(ipv4_config_addresses[0]['prefix']))
			i += 1
		print("\t\tRoutes:")
		i = 0
		while i < len(ipv4_config_routes):
			print("\t\t\t" + str(ipv4_config_routes[i]['dest']) + "/" + str(ipv4_config_routes[0]['prefix']) + " metric " + str(ipv4_config_routes[0]['metric']))
			i += 1
		print("\t\tGateway:")
		print("\t\t\t" + str(ipv4_config_gateway))
		print("\t\tDomains:")
		i = 0
		while i < len(ipv4_config_domains):
			print("\t\t\t" + str(ipv4_config_domains[i]))
			i += 1

		#IPv4 lease/config information
		ipv4_dhcp_object = prop_iface.Get(NM_DEVICE_IFACE, "Dhcp4Config")
		ipv4_dhcp_proxy = bus.get_object(NM_IFACE, ipv4_dhcp_object)
		ipv4_dhcp_iface = dbus.Interface(ipv4_dhcp_proxy, DBUS_PROP_IFACE)
		ipv4_dhcp_options = ipv4_dhcp_iface.Get(NM_DHCP4_IFACE, "Options")

		print("\tDHCPv4 Config Info:")
		for item in ipv4_dhcp_options:
			print("\t\t" + str(item))
			print("\t\t\t" + str(ipv4_dhcp_options[item]))

		#IPv6 device address information
		ipv6_config_object = prop_iface.Get(NM_DEVICE_IFACE, "Ip6Config")
		ipv6_config_proxy = bus.get_object(NM_IFACE, ipv6_config_object)
		ipv6_config_iface = dbus.Interface(ipv6_config_proxy, DBUS_PROP_IFACE)
		ipv6_config_addresses = ipv6_config_iface.Get(NM_IP6_IFACE, "AddressData")
		ipv6_config_routes= ipv6_config_iface.Get(NM_IP6_IFACE, "RouteData")
		ipv6_config_gateway = ipv6_config_iface.Get(NM_IP6_IFACE, "Gateway")
		ipv6_config_domains = ipv6_config_iface.Get(NM_IP6_IFACE, "Domains")
		print("\tIPv6 Info:")
		print("\t\tAdresses:")
		i = 0
		while i < len(ipv6_config_addresses):
			print("\t\t\t" + str(ipv6_config_addresses[i]['address']) + "/" + str(ipv6_config_addresses[0]['prefix']))
			i += 1
		print("\t\tRoutes:")
		i = 0
		while i < len(ipv6_config_routes):
			print("\t\t\t" + str(ipv6_config_routes[i]['dest']) + "/" + str(ipv6_config_routes[0]['prefix']) + " metric " + str(ipv6_config_routes[0]['metric']))
			i += 1
		print("\t\tGateway:")
		print("\t\t\t" + str(ipv6_config_gateway))
		print("\t\tDomains:")
		i = 0
		while i < len(ipv6_config_domains):
			print("\t\t\t" + str(ipv6_config_domains[i]))
			i += 1

		#IPv6 lease/config information
		ipv6_dhcp_object = prop_iface.Get(NM_DEVICE_IFACE, "Dhcp6Config")
		#Check if path is valid
		if ipv6_dhcp_object != "/":
			ipv6_dhcp_proxy = bus.get_object(NM_IFACE, ipv6_dhcp_object)
			ipv6_dhcp_iface = dbus.Interface(ipv6_dhcp_proxy, DBUS_PROP_IFACE)
			ipv6_dhcp_options = ipv6_dhcp_iface.Get(NM_DHCP6_IFACE, "Options")

			print("\tDHCPv6 Config Info:")
			for item in ipv6_dhcp_options:
				print("\t\t" + str(item))
				print("\t\t\t" + str(ipv6_dhcp_options[item]))

	#Get wired specific items
	if device_type == 1:
		wired_iface = dbus.Interface(dev_proxy, NM_WIRED_IFACE)
		wired_prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
		wired_hwaddress = wired_prop_iface.Get(NM_WIRED_IFACE, "HwAddress")
		wired_permhwaddress = wired_prop_iface.Get(NM_WIRED_IFACE, "PermHwAddress")
		wired_speed = wired_prop_iface.Get(NM_WIRED_IFACE, "Speed")
		wired_carrier = wired_prop_iface.Get(NM_WIRED_IFACE, "Carrier")
		print('\tHardware Address:')
		print('\t\t' + wired_hwaddress)
		print('\tPermanent Hardware Address:')
		print('\t\t' + wired_permhwaddress)
		print('\tSpeed:')
		print('\t\t' + str(int(wired_speed)))
		print('\tCarrier:')
		print('\t\t' + str(wired_speed))

	#Get Wifi specific items
	if device_type == 2:
		# Get a proxy for the wifi interface
		wifi_iface = dbus.Interface(dev_proxy, NM_WIRELESS_IFACE)
		wifi_prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
		# Get the associated AP's object path
		wireless_active_access_point = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "ActiveAccessPoint")
		wireless_hwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "HwAddress")
		wireless_permhwaddress = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "PermHwAddress")
		wireless_mode = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "Mode")
		# Bitrate identifier will change in next major NM release to "Bitrate"
		wireless_bitrate = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "BitRate")
		print('\tHardware Address:')
		print('\t\t' + wireless_hwaddress)
		print('\tPermanent Hardware Address:')
		print('\t\t' + wireless_permhwaddress)
		print('\tMode:')
		print('\t\t' + str(int(wireless_mode)))
		print('\tBitrate:')
		print('\t\t' + str(wireless_bitrate/1000))
		# Get all APs the card can see
		active_ap = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "ActiveAccessPoint")
		ap_proxy = bus.get_object(NM_IFACE, active_ap)
		ap_prop_iface = dbus.Interface(ap_proxy, DBUS_PROP_IFACE)
		ssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Ssid")
		bssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "HwAddress")
		strength = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Strength")
		maxbitrate = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "MaxBitrate")
		freq = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Frequency")
		print('\tSSID:')
		print("\t\t%s" % ''.join([str(v) for v in ssid]))
		print('\tBSSID:')
		print('\t\t' + bssid)
		print('\tStrength:')
		print('\t\t' + str(int(strength)))
		print('\tMax bit rate:')
		print('\t\t' + str(maxbitrate/1000))
		print('\tFrequency:')
		print('\t\t' + str(freq))
	print()