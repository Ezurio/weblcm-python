import os

WEBLCM_PYTHON_BUILD = '0.0.0.0'
WEBLCM_PYTHON_VERSION = '0.0.0.0'

WEBLCM_PYTHON_CONF_DIR = '/data/secret/'
WEBLCM_PYTHON_USER_CONF_FILE = '/data/secret/weblcm-python/users.ini'
WEBLCM_PYTHON_SERVER_CONF_FILE = '/data/secret/weblcm-python/weblcm-python.ini'

WIFI_DRIVER_DEBUG_PARAM = '/sys/module/lrdmwl/parameters/lrd_debug'
"""Change to ath6kl driver for wb50n"""
if not os.path.exists(WIFI_DRIVER_DEBUG_PARAM):
	WIFI_DRIVER_DEBUG_PARAM = "/sys/module/ath6kl_core/parameters/debug_mask"

FILEDIR_DICT = {
	'cert': '{0}{1}'.format(WEBLCM_PYTHON_CONF_DIR, 'weblcm-python/ssl/'),
	'profile': '{0}{1}'.format(WEBLCM_PYTHON_CONF_DIR, 'NetworkManager/system-connections/'),
	'config': WEBLCM_PYTHON_CONF_DIR,
}

FILEFMT_DICT = {
	'cert' : ('.crt', '.key', '.pem', '.pac', '.bin'),
	'profile' : ('.nmconnection'),
}

DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
WPA_OBJ = '/fi/w1/wpa_supplicant1'
WPA_IFACE =	'fi.w1.wpa_supplicant1'

USER_PERMISSION_TYPES = {
	'UserPermssionTypes':[
		"networking_status",
		"networking_version",
		"networking_connections",
		"networking_edit",
		"networking_activate",
		"networking_ap_activate",
		"networking_delete",
		"networking_scan",
		"logging",
		"update_password",
		"swupdate",
		"advanced",
		#Root only permissions
		"add_del_user",
	],

	#Attributes to be displayed on the web
	'UserPermssionAttrs':[
		["Networking Status", "checked", "disabled"],
		["Version", "checked", "disabled"],
		["View Connections", "checked", "disabled"],
		["Edit Connection","", ""],
		["Activate Connection", "", ""],
		["Activate AP", "", ""],
		["Delete Connection", "", ""],
		["Wifi Scan","", ""],
		["Logging", "", ""],
		["Update Password", "checked", "disabled"],
		["Firmware Update", "", ""],
		["Advanced", "", ""],
		#Don't need to display root only permissions
		["", "", ""],
	],
}
