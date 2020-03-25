import os
import sys
import cherrypy
import dbus.mainloop.glib
from gi.repository import GLib
import NetworkManager
from threading import Thread
from time import sleep

network_status = {}

def get_dev_status(dev):
	status = {}
	status['State'] = dev.State
	status['Mtu'] = dev.Mtu
	status['DeviceType'] = dev.DeviceType
	return status

def get_ipv4_properties(ipv4):

	ip4Properties = {}

	addresses = {}
	i = 0
	for addr in ipv4.Addresses:
		addresses[i] = str(addr[0]) + "/" + str(addr[1])
		i += 1
	ip4Properties['Addresses'] = addresses

	routes = {}
	i = 0
	for rt in ipv4.Routes:
		routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
		i += 1
	ip4Properties['Routes'] = routes

	ip4Properties['Gateway'] = ipv4.Gateway

	i = 0
	domains = {}
	for dns in ipv4.Domains:
		domains[i] = str(dns)
		i += 1
	ip4Properties['Domains'] = domains

	return ip4Properties

def get_ipv6_properties(ipv6):

	ip6Properties = {}

	addresses = {}
	i = 0
	for addr in ipv6.Addresses:
		addresses[i] = str(addr[0]) + "/" + str(addr[1])
		i += 1
	ip6Properties['Addresses'] = addresses

	routes = {}
	i = 0
	for rt in ipv6.Routes:
		routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
		i += 1
	ip6Properties['Routes'] = routes

	ip6Properties['Gateway'] = ipv6.Gateway

	i = 0
	domains = {}
	for dns in ipv6.Domains:
		domains[i] = str(dns)
		i += 1
	ip6Properties['Domains'] = domains

	return ip6Properties

def get_ap_properties(ap, mode):
	apProperties = {}
	apProperties['Ssid'] = ap.Ssid
	apProperties['HwAddress'] = ap.HwAddress
	apProperties['Strength'] = 100 if mode == NetworkManager.NM_802_11_MODE_AP else ap.Strength
	apProperties['Maxbitrate'] = ap.MaxBitrate
	apProperties['Frequency'] = ap.Frequency
	apProperties['Flags'] = ap.Flags
	apProperties['Wpaflags'] = ap.WpaFlags
	apProperties['Rsnflags'] = ap.RsnFlags
	return apProperties

def get_wifi_properties(dev):
	wireless = {}
	wireless['Bitrate'] = dev.Bitrate
	wireless['HwAddress'] = dev.HwAddress
	wireless['PermHwAddress'] = dev.PermHwAddress
	wireless['Mode'] = dev.Mode
	wireless['LastScan'] = dev.LastScan
	return wireless

def get_wired_properties(dev):
	wired = {}
	wired['HwAddress'] = dev.HwAddress
	wired['PermHwAddress'] = dev.PermHwAddress
	wired['Speed'] = dev.Speed
	wired['Carrier'] = dev.Carrier
	return wired

def network_status_query():

	global network_status

	try:
		devices = NetworkManager.NetworkManager.GetDevices()
		for dev in devices:

			#Dont add unmanaged devices
			if(dev.State == NetworkManager.NM_DEVICE_STATE_UNMANAGED):
				continue;

			interface_name = dev.Interface
			network_status[interface_name] = {}

			network_status[interface_name]['status'] = get_dev_status(dev)

			if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:

				settings = dev.ActiveConnection.Connection.GetSettings();
				network_status[interface_name]['connection_active'] = settings['connection']

				network_status[interface_name]['ip4config'] = get_ipv4_properties(dev.Ip4Config)
				network_status[interface_name]['ip6config'] = get_ipv6_properties(dev.Ip6Config)

			#Get wired specific items
			if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
				network_status[interface_name]['wired'] = get_wired_properties(dev)

			#Get Wifi specific items
			if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
				network_status[interface_name]['wireless'] = get_wifi_properties(dev)

			if (dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI and dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED):
				network_status[interface_name]['activeaccesspoint'] = get_ap_properties(dev.ActiveAccessPoint, dev.Mode)

	except Exception as e:
		print(e)

	return

def dev_added(nm, interface, signal, device_path):
	global network_status
	network_status[device_path.Interface] = {}
	network_status[device_path.Interface]['status'] = get_dev_status(device_path)

def dev_removed(nm, interface, signal, device_path):
	global network_status
	network_status.pop(device_path.Interface)

def ap_propchange(ap, interface, signal, properties):
	global network_status
	if 'Strength' in properties:
		for k in network_status:
			if 'activeaccesspoint' in network_status[k]:
				if network_status[k]['activeaccesspoint']['Ssid'] == ap.Ssid:
					network_status[k]['activeaccesspoint']['Strength'] = properties['Strength']

def dev_statechange(dev, interface, signal, new_state, old_state, reason):
	global network_status

	if new_state == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
		network_status[dev.Interface]['status'] = get_dev_status(dev)
		settings = dev.ActiveConnection.Connection.GetSettings();
		network_status[dev.Interface]['connection_active'] = settings['connection']
		network_status[dev.Interface]['ip4config'] = get_ipv4_properties(dev.Ip4Config)
		network_status[dev.Interface]['ip6config'] = get_ipv6_properties(dev.Ip6Config)
		if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
			network_status[dev.Interface]['wired'] = get_wired_properties(dev)
		if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
			network_status[dev.Interface]['wireless'] = get_wifi_properties(dev)
			network_status[dev.Interface]['activeaccesspoint'] = get_ap_properties(dev.ActiveAccessPoint, dev.Mode)
			dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)

	elif new_state == NetworkManager.NM_DEVICE_STATE_DISCONNECTED:
		if 'ip4config' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('ip4config')
		if 'ip6config' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('ip6config')
		if 'activeaccesspoint' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('activeaccesspoint')
		if 'connection_active' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('connection_active')
	elif new_state == NetworkManager.NM_DEVICE_STATE_UNAVAILABLE:
		if 'wired' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('wired')
		if 'wireless' in network_status[dev.Interface]:
			network_status[dev.Interface].pop('wireless')

	network_status[dev.Interface]['status']['State'] = new_state

def run_event_listener():

	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	network_status_query()

	NetworkManager.NetworkManager.OnDeviceAdded(dev_added)
	NetworkManager.NetworkManager.OnDeviceRemoved(dev_removed)

	# Listen for added and removed access points
	for dev in NetworkManager.Device.all():
		if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET or dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
			dev.OnStateChanged(dev_statechange)

	GLib.MainLoop().run()

@cherrypy.expose
class NetworkStatus(object):

	def __init__(self):
		t = Thread(target=run_event_listener, daemon=True)
		t.start()

	@cherrypy.tools.json_out()
	def GET(self):
		global network_status
		return {
			'SDCERR': 0,
			'devices': len(network_status),
			'status': network_status,
		}
