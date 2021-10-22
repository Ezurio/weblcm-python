import os

WEBLCM_PYTHON_VERSION = '1.0.0.1'

SYSTEM_CONF_DIR = '/data/'
NETWORKMANAGER_CONF_DIR = '/data/secret/NetworkManager/'
WEBLCM_PYTHON_CONF_DIR = '/data/secret/weblcm-python/'
#weblcm-python.ini is for server config. It should be updated only by software update.
WEBLCM_PYTHON_SERVER_CONF_FILE = '/etc/weblcm-python/weblcm-python.ini'
#system settings
WEBLCM_PYTHON_SETTINGS_FILE = '/data/secret/weblcm-python/weblcm-settings.ini'

#timezone list
WEBLCM_PYTHON_ZONELIST = '/data/secret/weblcm-python/zonelist.db'

#Default system timezone datebase can be readonly. Save customer files in /data/misc/.
WEBLCM_PYTHON_ZONEINFO = '/data/misc/zoneinfo/'

WIFI_DRIVER_DEBUG_PARAM = '/sys/module/lrdmwl/parameters/lrd_debug'
#Change to ath6kl driver for wb50n
if not os.path.exists(WIFI_DRIVER_DEBUG_PARAM):
	WIFI_DRIVER_DEBUG_PARAM = "/sys/module/ath6kl_core/parameters/debug_mask"

FILEDIR_DICT = {
	'cert': '{0}{1}'.format(NETWORKMANAGER_CONF_DIR, 'certs/'),
	'pac': '{0}{1}'.format(NETWORKMANAGER_CONF_DIR, 'certs/'),
	'config': SYSTEM_CONF_DIR,
	'timezone': WEBLCM_PYTHON_ZONEINFO,
}

FILEFMT_DICT = {
	'cert' : ('crt', 'key', 'pem', 'bin'),
	'pac' : ('pac'),
}

DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
WPA_OBJ = '/fi/w1/wpa_supplicant1'
WPA_IFACE =	'fi.w1.wpa_supplicant1'

WEBLCM_ERRORS = {
	'SDCERR_SUCCESS': 0,
	'SDCERR_FAIL': 1,
	'SDCERR_USER_LOGGED': 2,
	'SDCERR_USER_BLOCKED': 3,
	'SDCERR_SESSION_CHECK_FAILED': 4,
	'SDCERR_FIRMWARE_UPDATING': 5,
}

USER_PERMISSION_TYPES = {
	'UserPermssionTypes':[
		"status_networking",
		"networking_connections",
		"networking_edit",
		"networking_activate",
		"networking_ap_activate",
		"networking_delete",
		"networking_scan",
		"networking_certs",
		"logging",
		"help_version",
		"system_datetime",
		"system_swupdate",
		"system_password",
		"system_advanced",
		"system_positioning",
		"system_reboot",
		#Root only permissions
		"system_user",
	],

	#Attributes to be displayed on the web
	'UserPermssionAttrs':[
		["Networking Status", "checked", "disabled"],
		["View Connections", "checked", "disabled"],
		["Edit Connection","", ""],
		["Activate Connection", "", ""],
		["Activate AP", "", ""],
		["Delete Connection", "", ""],
		["Wifi Scan","", ""],
		["Manage Certs","", ""],
		["Logging", "", ""],
		["Version", "checked", "disabled"],
		["Date & time","", ""],
		["Firmware Update", "", ""],
		["Update Password", "checked", "disabled"],
		["Advance Setting", "", ""],
		["Positioning", "", ""],
		["Reboot", "", ""],
		#Don't need to display root only permissions
		["", "", ""],
	],
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_DEVTYPE_TEXT = { 0: "Unknown",
             1: "Ethernet",
             2: "Wi-Fi",
             5: "Bluetooth",
             6: "OLPC",
             7: "WiMAX",
             8: "Modem",
             9: "InfiniBand",
             10: "Bond",
             11: "VLAN",
             12: "ADSL",
             13: "Bridge Master",
             14: "Generic",
             15: "Team Master",
             16: "TUN/TAP",
             17: "IP Tunnel",
             18: "MACVLAN",
             19: "VXLAN",
             20: "VETH",
             21: "MACsec",
             22: "dummy",
             23: "PPP",
             24: "Open vSwitch interface",
             25: "Open vSwitch port",
             26: "Open vSwitch bridge",
             27: "WPAN",
             28: "6LoWPAN",
             29: "WireGuard",
             30: "WiFi P2P",
             31: "VRF" }

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_STATE_TEXT = { 0: "Unknown",
           10: "Unmanaged",
           20: "Unavailable",
           30: "Disconnected",
           40: "Prepare",
           50: "Config",
           60: "Need Auth",
           70: "IP Config",
           80: "IP Check",
           90: "Secondaries",
           100: "Activated",
           110: "Deactivating",
           120: "Failed" }
