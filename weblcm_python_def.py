import cherrypy

WEBLCM_PYTHON_BUILD = '0.0.0.0'
WEBLCM_PYTHON_VERSION = '0.0.0.0'

WEBLCM_PYTHON_DOC_ROOT = '/var/www/'
WEBLCM_PYTHON_CONF_DIR = '/etc/weblcm-python/'

WIFI_DEVICE_NAME =				'wlan0'
WIFI_DRIVER_DEBUG_PARAM =		'/sys/module/lrdmwl/parameters/lrd_debug'

NETWORKING_CONF = {
		'/networking_status': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/connections': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/activate_connection': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/get_certificates': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/add_connection': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/remove_connection': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/edit_connection': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/wifi_scan': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/version': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
	}

DEFAULT_LOG_SERVICES =			['NetworkManager', 'wpa_supplicant']
LOGGING_REGENERATE_LOG_TIMER =	10
LOGGING_UPDATE_LOG_TIMER =		1
LOGGING_STORAGE_PATH =			"/tmp/weblcm_python/"
LOGGING_SYSD_JOURNAL_LOG_NAME =	"SOM60_SYSD_JOURNAL.txt"

LOGGING_CONF = {
		'/request_log': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/generate_log': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/download_log': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/set_logging': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
		'/get_logging': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.response_headers.on': True,
			'tools.response_headers.headers': [('Content-Type', 'application/json')],
		},
	}

DBUS_PROP_IFACE =				'org.freedesktop.DBus.Properties'

WPA_OBJ =						'/fi/w1/wpa_supplicant1'
WPA_IFACE =						'fi.w1.wpa_supplicant1'

NM_OBJ =						'/org/freedesktop/NetworkManager'
NM_SETTINGS_OBJ =				'/org/freedesktop/NetworkManager/Settings'

NM_IFACE =						'org.freedesktop.NetworkManager'
NM_DEVICE_IFACE =				'org.freedesktop.NetworkManager.Device'
NM_SETTINGS_IFACE =				'org.freedesktop.NetworkManager.Settings'
NM_CONNECTION_IFACE =			'org.freedesktop.NetworkManager.Settings.Connection'
NM_CONNECTION_ACTIVE_IFACE =	'org.freedesktop.NetworkManager.Connection.Active'
NM_IP4_IFACE =					'org.freedesktop.NetworkManager.IP4Config'
NM_IP6_IFACE =					'org.freedesktop.NetworkManager.IP6Config'
NM_DHCP4_IFACE =				'org.freedesktop.NetworkManager.DHCP4Config'
NM_DHCP6_IFACE =				'org.freedesktop.NetworkManager.DHCP6Config'
NM_WIRED_IFACE =				'org.freedesktop.NetworkManager.Device.Wired'
NM_WIRELESS_IFACE =				'org.freedesktop.NetworkManager.Device.Wireless'
NM_ACCESSPOINT_IFACE =			'org.freedesktop.NetworkManager.AccessPoint'

NM_DBUS_API_TYPES = {
	#https://developer.gnome.org/NetworkManager/stable/nm-dbus-types.html
	'NMCapability':{
		'NM_CAPABILITY_TEAM': 1
	},
	'NMState':{
		'NM_STATE_UNKNOWN':				0,
		'NM_STATE_ASLEEP':				10,
		'NM_STATE_DISCONNECTED':		20,
		'NM_STATE_DISCONNECTING':		30,
		'NM_STATE_CONNECTING':			40,
		'NM_STATE_CONNECTED_LOCAL':		50,
		'NM_STATE_CONNECTED_SITE':		60,
		'NM_STATE_CONNECTED_GLOBAL':	70,
	},
	'NMConnectivityState':{
		'NM_CONNECTIVITY_UNKNOWN':		0,
		'NM_CONNECTIVITY_NONE':			1,
		'NM_CONNECTIVITY_PORTAL':		2,
		'NM_CONNECTIVITY_LIMITED':		3,
		'NM_CONNECTIVITY_FULL':			4,
	},
	'NMDeviceType':{
		'NM_DEVICE_TYPE_UNKNOWN':		0,
		'NM_DEVICE_TYPE_ETHERNET':		1,
		'NM_DEVICE_TYPE_WIFI':			2,
		'NM_DEVICE_TYPE_UNUSED1':		3,
		'NM_DEVICE_TYPE_UNUSED2':		4,
		'NM_DEVICE_TYPE_BT':			5,
		'NM_DEVICE_TYPE_OLPC_MESH':		6,
		'NM_DEVICE_TYPE_WIMAX':			7,
		'NM_DEVICE_TYPE_MODEM':			8,
		'NM_DEVICE_TYPE_INFINIBAND':	9,
		'NM_DEVICE_TYPE_BOND':			10,
		'NM_DEVICE_TYPE_VLAN':			11,
		'NM_DEVICE_TYPE_ADSL':			12,
		'NM_DEVICE_TYPE_BRIDGE':		13,
		'NM_DEVICE_TYPE_GENERIC':		14,
		'NM_DEVICE_TYPE_TEAM':			15,
		'NM_DEVICE_TYPE_TUN':			16,
		'NM_DEVICE_TYPE_IP_TUNNEL':		17,
		'NM_DEVICE_TYPE_MACVLAN':		18,
		'NM_DEVICE_TYPE_VXLAN':			19,
		'NM_DEVICE_TYPE_VETH':			20,
		'NM_DEVICE_TYPE_MACSEC':		21,
		'NM_DEVICE_TYPE_DUMMY':			22,
		'NM_DEVICE_TYPE_PPP':			23,
		'NM_DEVICE_TYPE_OVS_INTERFACE':	24,
		'NM_DEVICE_TYPE_OVS_PORT':		25,
		'NM_DEVICE_TYPE_OVS_BRIDGE':	26,
		'NM_DEVICE_TYPE_WPAN':			27,
		'NM_DEVICE_TYPE_6LOWPAN':		28,
		'NM_DEVICE_TYPE_WIREGUARD':		29,
		'NM_DEVICE_TYPE_WIFI_P2P':		30,
	},
	'NMDeviceCapabilities':{
		'NM_DEVICE_CAP_NONE':			0x00000000,
		'NM_DEVICE_CAP_NM_SUPPORTED':	0x00000001,
		'NM_DEVICE_CAP_CARRIER_DETECT':	0x00000002,
		'NM_DEVICE_CAP_IS_SOFTWARE':	0x00000004,
		'NM_DEVICE_CAP_SRIOV':			0x00000008,
	},
	'NMDeviceWifiCapabilities':{
		'NM_WIFI_DEVICE_CAP_NONE':			0x00000000,
		'NM_WIFI_DEVICE_CAP_CIPHER_WEP40':	0x00000001,
		'NM_WIFI_DEVICE_CAP_CIPHER_WEP104':	0x00000002,
		'NM_WIFI_DEVICE_CAP_CIPHER_TKIP':	0x00000004,
		'NM_WIFI_DEVICE_CAP_CIPHER_CCMP':	0x00000008,
		'NM_WIFI_DEVICE_CAP_WPA':			0x00000010,
		'NM_WIFI_DEVICE_CAP_RSN':			0x00000020,
		'NM_WIFI_DEVICE_CAP_AP':			0x00000040,
		'NM_WIFI_DEVICE_CAP_ADHOC':			0x00000080,
		'NM_WIFI_DEVICE_CAP_FREQ_VALID':	0x00000100,
		'NM_WIFI_DEVICE_CAP_FREQ_2GHZ':		0x00000200,
		'NM_WIFI_DEVICE_CAP_FREQ_5GHZ':		0x00000400,
	},
	'NM80211ApFlags':{
		'NM_802_11_AP_FLAGS_NONE':		0x00000000,
		'NM_802_11_AP_FLAGS_PRIVACY':	0x00000001,
		'NM_802_11_AP_FLAGS_WPS':		0x00000002,
		'NM_802_11_AP_FLAGS_WPS_PBC':	0x00000004,
		'NM_802_11_AP_FLAGS_WPS_PIN':	0x00000008,
	},
	'NM80211ApSecurityFlags':{
		'NM_802_11_AP_SEC_NONE':			0x00000000,
		'NM_802_11_AP_SEC_PAIR_WEP40':		0x00000001,
		'NM_802_11_AP_SEC_PAIR_WEP104':		0x00000002,
		'NM_802_11_AP_SEC_PAIR_TKIP':		0x00000004,
		'NM_802_11_AP_SEC_PAIR_CCMP':		0x00000008,
		'NM_802_11_AP_SEC_GROUP_WEP40':		0x00000010,
		'NM_802_11_AP_SEC_GROUP_WEP104':	0x00000020,
		'NM_802_11_AP_SEC_GROUP_TKIP':		0x00000040,
		'NM_802_11_AP_SEC_GROUP_CCMP':		0x00000080,
		'NM_802_11_AP_SEC_KEY_MGMT_PSK':	0x00000100,
		'NM_802_11_AP_SEC_KEY_MGMT_802_1X':	0x00000200,
	},
	'NM80211Mode':{
		'NM_802_11_MODE_UNKNOWN':	0,
		'NM_802_11_MODE_ADHOC':		1,
		'NM_802_11_MODE_INFRA':		2,
		'NM_802_11_MODE_AP':		3,
	},
	'NMBluetoothCapabilities':{
		'NM_BT_CAPABILITY_NONE':	0x00000000,
		'NM_BT_CAPABILITY_DUN':		0x00000001,
		'NM_BT_CAPABILITY_NAP':		0x00000002,
	},
	'NMDeviceModemCapabilities':{
		'NM_DEVICE_MODEM_CAPABILITY_NONE':		0x00000000,
		'NM_DEVICE_MODEM_CAPABILITY_POTS':		0x00000001,
		'NM_DEVICE_MODEM_CAPABILITY_CDMA_EVDO':	0x00000002,
		'NM_DEVICE_MODEM_CAPABILITY_GSM_UMTS':	0x00000004,
		'NM_DEVICE_MODEM_CAPABILITY_LTE':		0x00000008,
	},
	'NMWimaxNspNetworkType':{
		'NM_WIMAX_NSP_NETWORK_TYPE_UNKNOWN':			0,
		'NM_WIMAX_NSP_NETWORK_TYPE_HOME':				1,
		'NM_WIMAX_NSP_NETWORK_TYPE_PARTNER':			2,
		'NM_WIMAX_NSP_NETWORK_TYPE_ROAMING_PARTNER':	3,
	},
	'NMDeviceState':{
		'NM_DEVICE_STATE_UNKNOWN':		0,
		'NM_DEVICE_STATE_UNMANAGED':	10,
		'NM_DEVICE_STATE_UNAVAILABLE':	20,
		'NM_DEVICE_STATE_DISCONNECTED':	30,
		'NM_DEVICE_STATE_PREPARE':		40,
		'NM_DEVICE_STATE_CONFIG':		50,
		'NM_DEVICE_STATE_NEED_AUTH':	60,
		'NM_DEVICE_STATE_IP_CONFIG':	70,
		'NM_DEVICE_STATE_IP_CHECK':		80,
		'NM_DEVICE_STATE_SECONDARIES':	90,
		'NM_DEVICE_STATE_ACTIVATED':	100,
		'NM_DEVICE_STATE_DEACTIVATING':	110,
		'NM_DEVICE_STATE_FAILED':		120,
	},
	'NMDeviceStateReason':{
		'NM_DEVICE_STATE_REASON_NONE':									0,
		'NM_DEVICE_STATE_REASON_UNKNOWN':								1,
		'NM_DEVICE_STATE_REASON_NOW_MANAGED':							2,
		'NM_DEVICE_STATE_REASON_NOW_UNMANAGED':							3,
		'NM_DEVICE_STATE_REASON_CONFIG_FAILED':							4,
		'NM_DEVICE_STATE_REASON_IP_CONFIG_UNAVAILABLE':					5,
		'NM_DEVICE_STATE_REASON_IP_CONFIG_EXPIRED':						6,
		'NM_DEVICE_STATE_REASON_NO_SECRETS':							7,
		'NM_DEVICE_STATE_REASON_SUPPLICANT_DISCONNECT':					8,
		'NM_DEVICE_STATE_REASON_SUPPLICANT_CONFIG_FAILED':				9,
		'NM_DEVICE_STATE_REASON_SUPPLICANT_FAILED':						10,
		'NM_DEVICE_STATE_REASON_SUPPLICANT_TIMEOUT':					11,
		'NM_DEVICE_STATE_REASON_PPP_START_FAILED':						12,
		'NM_DEVICE_STATE_REASON_PPP_DISCONNECT':						13,
		'NM_DEVICE_STATE_REASON_PPP_FAILED':							14,
		'NM_DEVICE_STATE_REASON_DHCP_START_FAILED':						15,
		'NM_DEVICE_STATE_REASON_DHCP_ERROR':							16,
		'NM_DEVICE_STATE_REASON_DHCP_FAILED':							17,
		'NM_DEVICE_STATE_REASON_SHARED_START_FAILED':					18,
		'NM_DEVICE_STATE_REASON_SHARED_FAILED':							19,
		'NM_DEVICE_STATE_REASON_AUTOIP_START_FAILED':					20,
		'NM_DEVICE_STATE_REASON_AUTOIP_ERROR':							21,
		'NM_DEVICE_STATE_REASON_AUTOIP_FAILED':							22,
		'NM_DEVICE_STATE_REASON_MODEM_BUSY':							23,
		'NM_DEVICE_STATE_REASON_MODEM_NO_DIAL_TONE':					24,
		'NM_DEVICE_STATE_REASON_MODEM_NO_CARRIER':						25,
		'NM_DEVICE_STATE_REASON_MODEM_DIAL_TIMEOUT':					26,
		'NM_DEVICE_STATE_REASON_MODEM_DIAL_FAILED':						27,
		'NM_DEVICE_STATE_REASON_MODEM_INIT_FAILED':						28,
		'NM_DEVICE_STATE_REASON_GSM_APN_FAILED':						29,
		'NM_DEVICE_STATE_REASON_GSM_REGISTRATION_NOT_SEARCHING':		30,
		'NM_DEVICE_STATE_REASON_GSM_REGISTRATION_DENIED':				31,
		'NM_DEVICE_STATE_REASON_GSM_REGISTRATION_TIMEOUT':				32,
		'NM_DEVICE_STATE_REASON_GSM_REGISTRATION_FAILED':				33,
		'NM_DEVICE_STATE_REASON_GSM_PIN_CHECK_FAILED':					34,
		'NM_DEVICE_STATE_REASON_FIRMWARE_MISSING':						35,
		'NM_DEVICE_STATE_REASON_REMOVED':								36,
		'NM_DEVICE_STATE_REASON_SLEEPING':								37,
		'NM_DEVICE_STATE_REASON_CONNECTION_REMOVED':					38,
		'NM_DEVICE_STATE_REASON_USER_REQUESTED':						39,
		'NM_DEVICE_STATE_REASON_CARRIER':								40,
		'NM_DEVICE_STATE_REASON_CONNECTION_ASSUMED':					41,
		'NM_DEVICE_STATE_REASON_SUPPLICANT_AVAILABLE':					42,
		'NM_DEVICE_STATE_REASON_MODEM_NOT_FOUND':						43,
		'NM_DEVICE_STATE_REASON_BT_FAILED':								44,
		'NM_DEVICE_STATE_REASON_GSM_SIM_NOT_INSERTED':					45,
		'NM_DEVICE_STATE_REASON_GSM_SIM_PIN_REQUIRED':					46,
		'NM_DEVICE_STATE_REASON_GSM_SIM_PUK_REQUIRED':					47,
		'NM_DEVICE_STATE_REASON_GSM_SIM_WRONG':							48,
		'NM_DEVICE_STATE_REASON_INFINIBAND_MODE':						49,
		'NM_DEVICE_STATE_REASON_DEPENDENCY_FAILED':						50,
		'NM_DEVICE_STATE_REASON_BR2684_FAILED':							51,
		'NM_DEVICE_STATE_REASON_MODEM_MANAGER_UNAVAILABLE':				52,
		'NM_DEVICE_STATE_REASON_SSID_NOT_FOUND':						53,
		'NM_DEVICE_STATE_REASON_SECONDARY_CONNECTION_FAILED':			54,
		'NM_DEVICE_STATE_REASON_DCB_FCOE_FAILED':						55,
		'NM_DEVICE_STATE_REASON_TEAMD_CONTROL_FAILED':					56,
		'NM_DEVICE_STATE_REASON_MODEM_FAILED':							57,
		'NM_DEVICE_STATE_REASON_MODEM_AVAILABLE':						58,
		'NM_DEVICE_STATE_REASON_SIM_PIN_INCORRECT':						59,
		'NM_DEVICE_STATE_REASON_NEW_ACTIVATION':						60,
		'NM_DEVICE_STATE_REASON_PARENT_CHANGED':						61,
		'NM_DEVICE_STATE_REASON_PARENT_MANAGED_CHANGED':				62,
		'NM_DEVICE_STATE_REASON_OVSDB_FAILED':							63,
		'NM_DEVICE_STATE_REASON_IP_ADDRESS_DUPLICATE':					64,
		'NM_DEVICE_STATE_REASON_IP_METHOD_UNSUPPORTED':					65,
	},
	'NMMetered':{
		'NM_METERED_UNKNOWN':	0,
		'NM_METERED_YES':		1,
		'NM_METERED_NO':		2,
		'NM_METERED_GUESS_YES':	3,
		'NM_METERED_GUESS_NO':	4,
	},
	'NMActiveConnectionState':{
		'NM_ACTIVE_CONNECTION_STATE_UNKNOWN':		0,
		'NM_ACTIVE_CONNECTION_STATE_ACTIVATING':	1,
		'NM_ACTIVE_CONNECTION_STATE_ACTIVATED':		2,
		'NM_ACTIVE_CONNECTION_STATE_DEACTIVATING':	3,
		'NM_ACTIVE_CONNECTION_STATE_DEACTIVATED':	4,
	},
	'NMActiveConnectionStateReason':{
		'NM_ACTIVE_CONNECTION_STATE_REASON_UNKNOWN':				0,
		'NM_ACTIVE_CONNECTION_STATE_REASON_NONE':					1,
		'NM_ACTIVE_CONNECTION_STATE_REASON_USER_DISCONNECTED':		2,
		'NM_ACTIVE_CONNECTION_STATE_REASON_DEVICE_DISCONNECTED':	3,
		'NM_ACTIVE_CONNECTION_STATE_REASON_SERVICE_STOPPED':		4,
		'NM_ACTIVE_CONNECTION_STATE_REASON_IP_CONFIG_INVALID':		5,
		'NM_ACTIVE_CONNECTION_STATE_REASON_CONNECT_TIMEOUT':		6,
		'NM_ACTIVE_CONNECTION_STATE_REASON_SERVICE_START_TIMEOUT':	7,
		'NM_ACTIVE_CONNECTION_STATE_REASON_SERVICE_START_FAILED':	8,
		'NM_ACTIVE_CONNECTION_STATE_REASON_NO_SECRETS':				9,
		'NM_ACTIVE_CONNECTION_STATE_REASON_LOGIN_FAILED':			10,
		'NM_ACTIVE_CONNECTION_STATE_REASON_CONNECTION_REMOVED':		11,
		'NM_ACTIVE_CONNECTION_STATE_REASON_DEPENDENCY_FAILED':		12,
		'NM_ACTIVE_CONNECTION_STATE_REASON_DEVICE_REALIZE_FAILED':	13,
		'NM_ACTIVE_CONNECTION_STATE_REASON_DEVICE_REMOVED':			14,
	},
	'NMSecretAgentGetSecretsFlags':{
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_NONE':				0x00000000,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_ALLOW_INTERACTION':	0x00000001,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_REQUEST_NEW':			0x00000002,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_USER_REQUESTED':		0x00000004,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_WPS_PBC_ACTIVE':		0x00000008,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_ONLY_SYSTEM':			0x80000000,
		'NM_SECRET_AGENT_GET_SECRETS_FLAG_NO_ERRORS':			0x40000000,
	},
	'NMSecretAgentCapabilities':{
		'NM_SECRET_AGENT_CAPABILITY_NONE':		0x0,
		'NM_SECRET_AGENT_CAPABILITY_VPN_HINTS':	0x1,
	},
	'NMIPTunnelMode':{
		'NM_IP_TUNNEL_MODE_UNKNOWN':	0,
		'NM_IP_TUNNEL_MODE_IPIP':		1,
		'NM_IP_TUNNEL_MODE_GRE':		2,
		'NM_IP_TUNNEL_MODE_SIT':		3,
		'NM_IP_TUNNEL_MODE_ISATAP':		4,
		'NM_IP_TUNNEL_MODE_VTI':		5,
		'NM_IP_TUNNEL_MODE_IP6IP6':		6,
		'NM_IP_TUNNEL_MODE_IPIP6':		7,
		'NM_IP_TUNNEL_MODE_IP6GRE':		8,
		'NM_IP_TUNNEL_MODE_VTI6':		9,
	},
	'NMCheckpointCreateFlags':{
		'NM_CHECKPOINT_CREATE_FLAG_NONE':						0,
		'NM_CHECKPOINT_CREATE_FLAG_DESTROY_ALL':				0x01,
		'NM_CHECKPOINT_CREATE_FLAG_DELETE_NEW_CONNECTIONS':		0x02,
		'NM_CHECKPOINT_CREATE_FLAG_DISCONNECT_NEW_DEVICES':		0x04,
		'NM_CHECKPOINT_CREATE_FLAG_ALLOW_OVERLAPPING':			0x08,
	},
	'NMRollbackResult':{
		'NM_ROLLBACK_RESULT_OK':					0,
		'NM_ROLLBACK_RESULT_ERR_NO_DEVICE':			1,
		'NM_ROLLBACK_RESULT_ERR_DEVICE_UNMANAGED':	2,
		'NM_ROLLBACK_RESULT_ERR_FAILED':			3,
	},
	'NMSettingsConnectionFlags':{
		'NM_SETTINGS_CONNECTION_FLAG_NONE':			0,
		'NM_SETTINGS_CONNECTION_FLAG_UNSAVED':		0x01,
		'NM_SETTINGS_CONNECTION_FLAG_NM_GENERATED':	0x02,
		'NM_SETTINGS_CONNECTION_FLAG_VOLATILE':		0x04,
	},
	#Unknown why docs have each enum = (1LL
	'NMActivationStateFlags':{
		'NM_ACTIVATION_STATE_FLAG_NONE':				0,
		'NM_ACTIVATION_STATE_FLAG_IS_MASTER':			0,
		'NM_ACTIVATION_STATE_FLAG_IS_SLAVE':			0,
		'NM_ACTIVATION_STATE_FLAG_LAYER2_READY':		0,
		'NM_ACTIVATION_STATE_FLAG_IP4_READY':			0,
		'NM_ACTIVATION_STATE_FLAG_IP6_READY':			0,
		'NM_ACTIVATION_STATE_FLAG_MASTER_HAS_SLAVES':	0,
	},
	#Unknown why docs have each enum = (1LL
	'NMSettingsUpdate2Flags':{
		'NM_SETTINGS_UPDATE2_FLAG_NONE':				0,
		'NM_SETTINGS_UPDATE2_FLAG_TO_DISK':				0,
		'NM_SETTINGS_UPDATE2_FLAG_IN_MEMORY':			0,
		'NM_SETTINGS_UPDATE2_FLAG_IN_MEMORY_DETACHED':	0,
		'NM_SETTINGS_UPDATE2_FLAG_IN_MEMORY_ONLY':		0,
		'NM_SETTINGS_UPDATE2_FLAG_VOLATILE':			0,
		'NM_SETTINGS_UPDATE2_FLAG_BLOCK_AUTOCONNECT':	0,
	},
}
