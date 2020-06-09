import os
import sys
import cherrypy
import dbus.mainloop.glib
from gi.repository import GLib
import NetworkManager
from threading import Thread, Lock


class NetworkStatusHelper(object):

	_network_status = {}
	_lock = Lock()

	@classmethod
	def get_dev_status(cls, dev):
		status = {}
		status['State'] = dev.State
		status['Mtu'] = dev.Mtu
		status['DeviceType'] = dev.DeviceType
		return status

	@classmethod
	def get_ipv4_properties(cls, ipv4):

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

	@classmethod
	def get_ipv6_properties(cls, ipv6):

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

	@classmethod
	def get_ap_properties(cls, ap, mode):
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

	@classmethod
	def get_wifi_properties(cls, dev):
		wireless = {}
		wireless['Bitrate'] = dev.Bitrate
		wireless['HwAddress'] = dev.HwAddress
		wireless['PermHwAddress'] = dev.PermHwAddress
		wireless['Mode'] = dev.Mode
		wireless['LastScan'] = dev.LastScan
		return wireless

	@classmethod
	def get_wired_properties(cls, dev):
		wired = {}
		wired['HwAddress'] = dev.HwAddress
		wired['PermHwAddress'] = dev.PermHwAddress
		wired['Speed'] = dev.Speed
		wired['Carrier'] = dev.Carrier
		return wired

	@classmethod
	def network_status_query(cls):

		with cls._lock:
			devices = NetworkManager.NetworkManager.GetDevices()
			for dev in devices:

				#Dont add unmanaged devices
				if(dev.State == NetworkManager.NM_DEVICE_STATE_UNMANAGED):
					continue;

				interface_name = dev.Interface
				cls._network_status[interface_name] = {}

				cls._network_status[interface_name]['status'] = cls.get_dev_status(dev)

				if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
					settings = dev.ActiveConnection.Connection.GetSettings();
					cls._network_status[interface_name]['connection_active'] = settings['connection']
					cls._network_status[interface_name]['ip4config'] = cls.get_ipv4_properties(dev.Ip4Config)
					cls._network_status[interface_name]['ip6config'] = cls.get_ipv6_properties(dev.Ip6Config)

				#Get wired specific items
				if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
					cls._network_status[interface_name]['wired'] = cls.get_wired_properties(dev)

				#Get Wifi specific items
				if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
					cls._network_status[interface_name]['wireless'] = cls.get_wifi_properties(dev)

				if (dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI and dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED):
					cls._network_status[interface_name]['activeaccesspoint'] = cls.get_ap_properties(dev.ActiveAccessPoint, dev.Mode)


def dev_added(nm, interface, signal, device_path):
	with NetworkStatusHelper._lock:
		NetworkStatusHelper._network_status[device_path.Interface] = {}
		NetworkStatusHelper._network_status[device_path.Interface]['status'] = NetworkStatusHelper.get_dev_status(device_path)

def dev_removed(nm, interface, signal, device_path):
	with NetworkStatusHelper._lock:
		NetworkStatusHelper._network_status.pop(device_path.Interface, None)

def ap_propchange(ap, interface, signal, properties):
		if 'Strength' in properties:
			for k in NetworkStatusHelper._network_status:
				if NetworkStatusHelper._network_status[k].get('activeaccesspoint', None):
					if NetworkStatusHelper._network_status[k]['activeaccesspoint'].get('Ssid') == ap.Ssid:
						with NetworkStatusHelper._lock:
							NetworkStatusHelper._network_status[k]['activeaccesspoint']['Strength'] = properties['Strength']

def dev_statechange(dev, interface, signal, new_state, old_state, reason):
	with NetworkStatusHelper._lock:
		if new_state == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
			NetworkStatusHelper._network_status[dev.Interface]['status'] = NetworkStatusHelper.get_dev_status(dev)
			settings = dev.ActiveConnection.Connection.GetSettings();
			NetworkStatusHelper._network_status[dev.Interface]['connection_active'] = settings['connection']
			NetworkStatusHelper._network_status[dev.Interface]['ip4config'] = NetworkStatusHelper.get_ipv4_properties(dev.Ip4Config)
			NetworkStatusHelper._network_status[dev.Interface]['ip6config'] = NetworkStatusHelper.get_ipv6_properties(dev.Ip6Config)
			if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
				NetworkStatusHelper._network_status[dev.Interface]['wired'] = NetworkStatusHelper.get_wired_properties(dev)
			if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
				NetworkStatusHelper._network_status[dev.Interface]['wireless'] = NetworkStatusHelper.get_wifi_properties(dev)
				NetworkStatusHelper._network_status[dev.Interface]['activeaccesspoint'] = NetworkStatusHelper.get_ap_properties(dev.ActiveAccessPoint, dev.Mode)
				dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)
		elif new_state == NetworkManager.NM_DEVICE_STATE_DISCONNECTED:
			if 'ip4config' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('ip4config', None)
			if 'ip6config' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('ip6config', None)
			if 'activeaccesspoint' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('activeaccesspoint', None)
			if 'connection_active' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('connection_active', None)
		elif new_state == NetworkManager.NM_DEVICE_STATE_UNAVAILABLE:
			if 'wired' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('wired', None)
			if 'wireless' in NetworkStatusHelper._network_status[dev.Interface]:
				NetworkStatusHelper._network_status[dev.Interface].pop('wireless', None)
		NetworkStatusHelper._network_status[dev.Interface]['status']['State'] = new_state

def run_event_listener():
	dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

	NetworkStatusHelper.network_status_query()

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
	def GET(self, *args, **kwargs):
		result = {}

		result['SDCERR'] = 1
		with NetworkStatusHelper._lock:
			result['devices'] = len(NetworkStatusHelper._network_status)
			result['status'] = NetworkStatusHelper._network_status
			result['SDCERR'] = 0

		return result
