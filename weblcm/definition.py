import os
import configparser
import cherrypy

WEBLCM_PYTHON_VERSION = "1.0.0.5"

# directory base when /data is not available
NON_ROOT_DATA_PATH = "/etc"

SYSTEM_CONF_DIR = "/data/"
NETWORKMANAGER_CONF_DIR = "/data/secret/NetworkManager/"
WEBLCM_PYTHON_CONF_DIR = "/data/secret/weblcm-python/"
# weblcm-python.ini is for server config. It should be updated only by software update.
WEBLCM_PYTHON_SERVER_CONF_FILE = "/etc/weblcm-python/weblcm-python.ini"
# system settings
WEBLCM_PYTHON_SETTINGS_FILE = "/data/secret/weblcm-python/weblcm-settings.ini"
# log forwarding
LOG_FORWARDING_ENABLED_FLAG_FILE = "/data/secret/weblcm-python/log_forwarding_enabled"

# timezone list
WEBLCM_PYTHON_ZONELIST_COMMAND = ["timedatectl", "list-timezones"]

# Default system timezone datebase can be readonly. Save customer files in /data/misc/.
WEBLCM_PYTHON_ZONEINFO = "/data/misc/zoneinfo/"

WIFI_DRIVER_DEBUG_PARAM = "/sys/module/lrdmwl/parameters/lrd_debug"
# Change to ath6kl driver for wb50n
if not os.path.exists(WIFI_DRIVER_DEBUG_PARAM):
    WIFI_DRIVER_DEBUG_PARAM = "/sys/module/ath6kl_core/parameters/debug_mask"

FILEDIR_DICT = {
    "cert": "{0}{1}".format(NETWORKMANAGER_CONF_DIR, "certs/"),
    "pac": "{0}{1}".format(NETWORKMANAGER_CONF_DIR, "certs/"),
    "config": SYSTEM_CONF_DIR,
    "timezone": WEBLCM_PYTHON_ZONEINFO,
}

FILEFMT_DICT = {
    "cert": ("crt", "key", "pem", "bin", "der", "p12", "pfx"),
    "pac": ("pac"),
}

DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
WPA_OBJ = "/fi/w1/wpa_supplicant1"
WPA_IFACE = "fi.w1.wpa_supplicant1"

LOGIND_BUS_NAME = "org.freedesktop.login1"
LOGIND_MAIN_OBJ = "/org/freedesktop/login1"
LOGIND_MAIN_IFACE = "org.freedesktop.login1.Manager"

SYSTEMD_BUS_NAME = "org.freedesktop.systemd1"
SYSTEMD_MAIN_OBJ = "/org/freedesktop/systemd1"
SYSTEMD_MANAGER_IFACE = "org.freedesktop.systemd1.Manager"
SYSTEMD_UNIT_IFACE = "org.freedesktop.systemd1.Unit"
SYSTEMD_UNIT_ACTIVE_STATE_PROP = "ActiveState"
SYSTEMD_UNIT_UNIT_FILE_STATE_PROP = "UnitFileState"
SYSTEMD_JOURNAL_GATEWAYD_SERVICE_FILE = "systemd-journal-gatewayd.service"
SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE = "systemd-journal-gatewayd.socket"

WEBLCM_ERRORS = {
    "SDCERR_SUCCESS": 0,
    "SDCERR_FAIL": 1,
    "SDCERR_USER_LOGGED": 2,
    "SDCERR_USER_BLOCKED": 3,
    "SDCERR_SESSION_CHECK_FAILED": 4,
    "SDCERR_FIRMWARE_UPDATING": 5,
}

USER_PERMISSION_TYPES = {
    "UserPermissionTypes": [
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
        # Root only permissions
        "system_user",
    ],
    # Attributes to be displayed on the web
    "UserPermissionAttrs": [
        ["Networking Status", "checked", "disabled"],
        ["View Connections", "checked", "disabled"],
        ["Edit Connection", "", ""],
        ["Activate Connection", "", ""],
        ["Activate AP", "", ""],
        ["Delete Connection", "", ""],
        ["Wifi Scan", "", ""],
        ["Manage Certs", "", ""],
        ["Logging", "", ""],
        ["Version", "checked", "disabled"],
        ["Date & time", "", ""],
        ["Firmware Update", "", ""],
        ["Update Password", "checked", "disabled"],
        ["Advance Setting", "", ""],
        ["Positioning", "", ""],
        ["Reboot", "", ""],
        # Don't need to display root only permissions
        ["", "", ""],
    ],
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_DEVTYPE_TEXT = {
    0: "Unknown",
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
    31: "VRF",
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_STATE_TEXT = {
    0: "Unknown",
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
    120: "Failed",
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_METERED_TEXT = {
    0: "Unknown",
    1: "Metered",
    2: "Not metered",
    3: "Metered (guessed)",
    4: "Not metered (guessed)",
}

# values from https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html
WEBLCM_CONNECTIVITY_STATE_TEXT = {
    0: "Unknown",
    1: "None",
    2: "Portal",
    3: "Limited",
    4: "Full",
}

# values from https://lazka.github.io/pgi-docs/#NM-1.0/enums.html
WEBLCM_NM_ACTIVE_CONNECTION_STATE_TEXT = {
    0: "Unknown",
    1: "Activating",
    2: "Activated",
    3: "Deactivating",
    4: "Deactivated",
}


WEBLCM_NM_DEVICE_TYPE_WIRED_TEXT = "802-3-ethernet"
WEBLCM_NM_DEVICE_TYPE_WIRELESS_TEXT = "802-11-wireless"

WEBLCM_NM_SETTING_CONNECTION_TEXT = "connection"
WEBLCM_NM_SETTING_IP4_CONFIG_TEXT = "ipv4"
WEBLCM_NM_SETTING_IP6_CONFIG_TEXT = "ipv6"
WEBLCM_NM_SETTING_WIRED_TEXT = "802-3-ethernet"
WEBLCM_NM_SETTING_WIRELESS_TEXT = "802-11-wireless"
WEBLCM_NM_SETTING_WIRELESS_SECURITY_TEXT = "802-11-wireless-security"
WEBLCM_NM_SETTING_802_1X_TEXT = "802-1x"
WEBLCM_NM_SETTING_PROXY_TEXT = "proxy"
WEBLCM_NM_SETTING_GENERAL_TEXT = "GENERAL"
WEBLCM_NM_SETTING_IP4_TEXT = "IP4"
WEBLCM_NM_SETTING_IP6_TEXT = "IP6"
WEBLCM_NM_SETTING_DHCP4_TEXT = "DHCP4"
WEBLCM_NM_SETTING_DHCP6_TEXT = "DHCP6"
# file names for firmware-update and in-progress in sync with names in
# /usr/bin/modem_check_firmware_update.sh script
MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE = "/data/modem/update-in-progress"
MODEM_FIRMWARE_UPDATE_FILE = "/data/modem/firmware-update"
MODEM_FIRMWARE_UPDATE_DST_DIR = "/data/modem"
MODEM_FIRMWARE_UPDATE_SRC_DIR = "/lib/firmware/modem"
# MODEM_ENABLE_FILE in sync with /usr/bin/modem_check_enable.sh
MODEM_ENABLE_FILE = "/data/modem/modem_enabled"

onlyonce = True


def adjust_data_paths():
    global onlyonce
    if onlyonce:
        onlyonce = False
        try:
            parser = configparser.ConfigParser()
            parser.read(WEBLCM_PYTHON_SERVER_CONF_FILE)

            data_available = (
                parser["weblcm"].get("root_data_is_available", "false").lower()
            )
        except Exception as e:
            data_available = "exception"
        if data_available == "false":
            cherrypy.log("/data not available.  Using /etc/data instead")
            global SYSTEM_CONF_DIR
            global NETWORKMANAGER_CONF_DIR
            global WEBLCM_PYTHON_CONF_DIR
            global WEBLCM_PYTHON_SETTINGS_FILE
            global WEBLCM_PYTHON_ZONEINFO
            global MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE
            global MODEM_FIRMWARE_UPDATE_FILE
            global MODEM_FIRMWARE_UPDATE_DST_DIR
            global MODEM_ENABLE_FILE

            SYSTEM_CONF_DIR = NON_ROOT_DATA_PATH + SYSTEM_CONF_DIR
            NETWORKMANAGER_CONF_DIR = NON_ROOT_DATA_PATH + NETWORKMANAGER_CONF_DIR
            WEBLCM_PYTHON_CONF_DIR = NON_ROOT_DATA_PATH + WEBLCM_PYTHON_CONF_DIR
            WEBLCM_PYTHON_SETTINGS_FILE = (
                NON_ROOT_DATA_PATH + WEBLCM_PYTHON_SETTINGS_FILE
            )
            WEBLCM_PYTHON_ZONEINFO = NON_ROOT_DATA_PATH + WEBLCM_PYTHON_ZONEINFO
            MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE = (
                NON_ROOT_DATA_PATH + MODEM_FIRMWARE_UPDATE_IN_PROGRESS_FILE
            )
            MODEM_FIRMWARE_UPDATE_FILE = NON_ROOT_DATA_PATH + MODEM_FIRMWARE_UPDATE_FILE
            MODEM_FIRMWARE_UPDATE_DST_DIR = (
                NON_ROOT_DATA_PATH + MODEM_FIRMWARE_UPDATE_DST_DIR
            )
            MODEM_ENABLE_FILE = NON_ROOT_DATA_PATH + MODEM_ENABLE_FILE
