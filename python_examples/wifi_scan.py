import dbus
import socket, struct
import time

WIFI_DEVICE_NAME = 'wlan0'

# Standard DBUS Properties
DBUS_PROP_IFACE =		'org.freedesktop.DBus.Properties'
NM_OBJ =				'/org/freedesktop/NetworkManager'
NM_IFACE =				'org.freedesktop.NetworkManager'
NM_DEVICE_IFACE =		'org.freedesktop.NetworkManager.Device'
NM_WIRELESS_IFACE =		'org.freedesktop.NetworkManager.Device.Wireless'
NM_ACCESSPOINT_IFACE =	'org.freedesktop.NetworkManager.AccessPoint'

def ap_sec_to_str(sec):
	list = []

	if sec & (0x1 | 0x2 | 0x10 | 0x20):
		list.append("WEP")
	if sec & (0x4 | 0x40):
		list.append("WPA")
	if sec & (0x8 | 0x80):
		list.append("WPA2")
	if sec & 0x100:
		list.append("PSK")
	if sec & 0x200:
		list.append("802.1X")

	return list

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
wifi_device = manager.GetDeviceByIpIface(WIFI_DEVICE_NAME)
#Get device object
dev_proxy = bus.get_object(NM_IFACE, wifi_device)
prop_iface = dbus.Interface(dev_proxy, DBUS_PROP_IFACE)
#Get org.freedesktop.NetworkManager.Device properties
print('Interface Name: ' + str(prop_iface.Get(NM_DEVICE_IFACE, "Interface")))
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
print('Current Access Point:')
print('\tHardware Address:')
print('\t\t' + wireless_hwaddress)
print('\tPermanent Hardware Address:')
print('\t\t' + wireless_permhwaddress)
print('\tMode:')
print('\t\t' + str(int(wireless_mode)))
print('\tBitrate:')
print('\t\t' + str(wireless_bitrate/1000))

wireless_lastscan = wifi_prop_iface.Get(NM_WIRELESS_IFACE, "LastScan")
print('Last scan:' + str(wireless_lastscan))
difference_in_seconds = ((time.clock_gettime(time.CLOCK_MONOTONIC) * 1000) - wireless_lastscan) / 1000
print('Time difference since last scan: ' + str(difference_in_seconds))

#Request scan if last scan is finished
#Dont know how to check if last scan has completed or not
try:
	options = []
	wifi_iface.RequestScan(options)
	print('Scan requested')
except Exception as e:
	print(e)

print('List of all Access Points:')
# Get all APs the card can see
aps = wifi_iface.GetAllAccessPoints()
for path in aps:
	ap_proxy = bus.get_object(NM_IFACE, path)
	ap_prop_iface = dbus.Interface(ap_proxy, DBUS_PROP_IFACE)
	ssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Ssid")
	bssid = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "HwAddress")
	strength = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Strength")
	maxbitrate = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "MaxBitrate")
	freq = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Frequency")
	flags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "Flags")
	wpaflags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "WpaFlags")
	rsnflags = ap_prop_iface.Get(NM_ACCESSPOINT_IFACE, "RsnFlags")
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
	print('\tFlags:')
	print('\t\t' + str(int(flags)))
	print('\tWPA Flags:')
	print('\t\t' + str(ap_sec_to_str(wpaflags)))
	print('\tRSN Flags:')
	print('\t\t' + str(ap_sec_to_str(rsnflags)))
