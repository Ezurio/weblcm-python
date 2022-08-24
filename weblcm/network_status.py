import os
from typing import Any, Tuple
import cherrypy
from dbus.mainloop.glib import DBusGMainLoop
import gi

gi.require_version("NM", "1.0")
from gi.repository import GLib, NM
from threading import Thread, Lock
from .settings import SystemSettingsManage
from . import definition
from syslog import LOG_WARNING, syslog, LOG_ERR
from subprocess import run, TimeoutExpired
import re


class NetworkStatusHelper(object):

    _network_status = {}
    _lock = Lock()
    _IW_PATH = "/usr/sbin/iw"
    _client = NM.Client.new(None)

    @classmethod
    def get_reg_domain_info(cls):
        if not os.path.exists(cls._IW_PATH):
            return "WW"

        try:
            proc = run(
                [cls._IW_PATH, "reg", "get"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                s = re.split("phy#", proc.stdout.decode("utf-8"))
                # Return regulatory domain of phy#0
                m = re.search("country [A-Z][A-Z]", s[1] if len(s) > 1 else s[0])
                if m:
                    return m.group(0)[8:10]
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw reg get' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw reg get' failed: {str(e)}")

        return "WW"

    @classmethod
    def get_frequency_info(cls, interface, frequency):
        if not os.path.exists(cls._IW_PATH):
            return frequency

        try:
            proc = run(
                [cls._IW_PATH, "dev"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                ifces = re.split("Interface", proc.stdout.decode("utf-8"))
                for ifce in ifces:
                    lines = ifce.splitlines()
                    if (lines[0].strip() != interface) or (len(lines) < 7):
                        continue
                    m = re.search("[2|5][0-9]{3}", lines[6])
                    if m:
                        return m.group(0)
        except TimeoutExpired:
            syslog(LOG_ERR, "Call 'iw dev' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev' failed: {str(e)}")

        return frequency

    @classmethod
    def get_dev_status(cls, dev):
        status = {}
        status["State"] = int(dev.get_state())
        try:
            status["StateText"] = definition.WEBLCM_STATE_TEXT.get(status["State"])
        except Exception:
            status["StateText"] = "Unknown"
            syslog(
                "unknown device state value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % status["State"]
            )
        status["Mtu"] = dev.get_mtu()
        status["DeviceType"] = int(dev.get_device_type())
        try:
            status["DeviceTypeText"] = definition.WEBLCM_DEVTYPE_TEXT.get(
                status["DeviceType"]
            )
        except Exception:
            status["DeviceTypeText"] = "Unknown"
            syslog(
                "unknown device type value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % status["DeviceType"]
            )
        return status

    @classmethod
    def get_ipconfig_properties(cls, ipconfig):

        ipconfig_properties = {}
        if not ipconfig:
            return ipconfig_properties

        addresses = {}
        address_data = []
        i = 0
        for addr in ipconfig.get_addresses():
            data = {}
            data["address"] = addr.get_address()
            data["prefix"] = addr.get_prefix()
            address_data.append(data)
            addresses[i] = data["address"] + "/" + str(data["prefix"])
            i += 1
        ipconfig_properties["Addresses"] = addresses
        ipconfig_properties["AddressData"] = address_data

        routes = {}
        route_data = []
        i = 0
        for rt in ipconfig.get_routes():
            data = {}
            data["dest"] = rt.get_dest()
            data["prefix"] = rt.get_prefix()
            data["metric"] = rt.get_metric()
            route_data.append(data)
            routes[i] = (
                data["dest"]
                + "/"
                + str(data["prefix"])
                + " metric "
                + str(data["metric"])
            )
            i += 1
        ipconfig_properties["Routes"] = routes
        ipconfig_properties["RouteData"] = route_data
        ipconfig_properties["Gateway"] = ipconfig.get_gateway()
        ipconfig_properties["Domains"] = ipconfig.get_domains()

        ipconfig_properties["NameserverData"] = ipconfig.get_nameservers()
        ipconfig_properties["WinsServerData"] = ipconfig.get_wins_servers()

        return ipconfig_properties

    @classmethod
    def get_dhcp_config_properties(cls, dhcp_config):

        if not dhcp_config:
            return {}

        return dhcp_config.get_options()

    @classmethod
    def get_ap_properties(cls, dev):
        ap = dev.get_active_access_point()

        apProperties = {}
        ssid = ap.get_ssid()
        apProperties["Ssid"] = (
            ssid.get_data().decode("utf-8") if ssid is not None else ""
        )
        apProperties["HwAddress"] = ap.get_bssid()
        apProperties["Maxbitrate"] = ap.get_max_bitrate()
        apProperties["Flags"] = int(ap.get_flags())
        apProperties["Wpaflags"] = int(ap.get_wpa_flags())
        apProperties["Rsnflags"] = int(ap.get_rsn_flags())
        # Use iw dev to get channel/frequency info for AP mode
        if dev.get_mode() is getattr(NM, "80211Mode").AP:
            apProperties["Strength"] = 100
            apProperties["Frequency"] = cls.get_frequency_info(
                dev.get_iface(), ap.get_frequency()
            )
        else:
            apProperties["Strength"] = ap.get_strength()
            apProperties["Frequency"] = ap.get_frequency()
        return apProperties

    @classmethod
    def get_wifi_properties(cls, dev):
        wireless = {}
        wireless["Bitrate"] = dev.get_bitrate()
        wireless["HwAddress"] = dev.get_hw_address()
        wireless["PermHwAddress"] = dev.get_permanent_hw_address()
        wireless["Mode"] = int(dev.get_mode())
        wireless["LastScan"] = dev.get_last_scan()
        return wireless

    @classmethod
    def get_wired_properties(cls, dev):
        wired = {}
        wired["HwAddress"] = dev.get_hw_address()
        wired["PermHwAddress"] = dev.get_permanent_hw_address()
        wired["Speed"] = dev.get_speed()
        wired["Carrier"] = dev.get_carrier()
        return wired

    @classmethod
    def get_available_connections(cls, available_connections):

        if not available_connections:
            return {}

        connections = []
        for connection in available_connections:
            connections.append(
                connection.to_dbus(NM.ConnectionSerializationFlags.NO_SECRETS).unpack()[
                    "connection"
                ]
            )

        return connections

    @classmethod
    def get_active_connection(cls, dev):

        if not dev or not dev.get_active_connection():
            return {}

        return (
            dev.get_active_connection()
            .get_connection()
            .to_dbus(NM.ConnectionSerializationFlags.NO_SECRETS)
            .unpack()["connection"]
        )

    @classmethod
    def extract_properties_from_nm_setting(cls, nm_setting):
        if not nm_setting:
            return {}

        properties = {}

        if nm_setting.props is not None:
            for prop in nm_setting.props:
                # The 'name' property is the name of the setting itself so it isn't valuable here
                if prop.name == "name":
                    continue

                # Hide secret values
                if prop.name in [
                    "wep-key0",
                    "wep-key1",
                    "wep-key2",
                    "wep-key3",
                    "psk",
                    "leap-password",
                ]:
                    properties[prop.name] = "<hidden>"
                    continue

                # The data from a GBytes type can be converted to a 'bytes' type by calling
                # get_data()
                if prop.value_type.name == "GBytes":
                    properties[prop.name] = (
                        nm_setting.get_property(prop.name).get_data().decode("utf-8")
                    )
                    continue

                # Enum/flags values can be cast to an integer
                if (
                    prop.value_type.name == "GEnum"
                    or prop.value_type.fundamental.name == "GEnum"
                    or prop.value_type.fundamental.name == "GFlags"
                ):
                    properties[prop.name] = int(nm_setting.get_property(prop.name))
                    continue

                # IP address values can be printed as a string in CIDR notation
                if prop.name in ["addresses", "routes"]:
                    properties[prop.name] = []
                    for value in nm_setting.get_property(prop.name):
                        properties[prop.name].append(
                            f"{value.get_address()}/{value.get_prefix()}"
                        )
                    continue

                properties[prop.name] = nm_setting.get_property(prop.name)

        return properties

    @classmethod
    def extract_general_properties_from_active_connection(cls, active_connection):
        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["name"] = active_connection.get_id()
        properties["uuid"] = active_connection.get_uuid()

        properties["devices"] = []
        for device in active_connection.get_devices():
            device_props = {}
            device_props["interface"] = device.get_iface()
            device_props["ip-interface"] = device.get_ip_iface()
            properties["devices"].append(device_props)

        properties["state"] = definition.WEBLCM_NM_ACTIVE_CONNECTION_STATE_TEXT.get(
            int(active_connection.get_state())
        )

        properties["default"] = active_connection.get_default()
        properties["default6"] = active_connection.get_default6()
        properties[
            "specific-object-path"
        ] = active_connection.get_specific_object_path()
        properties["vpn"] = active_connection.get_vpn()
        properties["dbus-path"] = active_connection.get_path()

        connection = active_connection.get_connection()
        properties["con-path"] = connection.get_path()
        properties["zone"] = connection.get_setting_connection().get_zone()

        master = active_connection.get_master()
        if master:
            properties["master-path"] = master.get_path()
        else:
            properties["master-path"] = None

        return properties

    @classmethod
    def extract_ip_config_properties_from_active_connection(cls, ip_config):
        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["addresses"] = []
        for address in ip_config.get_addresses():
            properties["addresses"].append(
                f"{address.get_address()}/{address.get_prefix()}"
            )

        properties["domains"] = ip_config.get_domains()
        properties["gateway"] = ip_config.get_gateway()
        properties["dns"] = ip_config.get_nameservers()

        properties["routes"] = []
        for route in ip_config.get_routes():
            route_props = {}
            route_props["destination"] = f"{route.get_dest()}/{int(route.get_prefix())}"
            route_props["next_hop"] = route.get_next_hop()
            route_props["metric"] = int(route.get_metric())
            properties["routes"].append(route_props)

        return properties

    @classmethod
    def extract_dhcp_config_properties_from_active_connection(cls, dhcp_config):
        if not dhcp_config:
            return {}

        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["options"] = dhcp_config.get_options()

        return properties

    @classmethod
    def get_802_1x_settings(cls, settings):
        if not settings:
            return {}

        properties = {}

        # The following properties are omitted as they are binary blobs
        # - 'ca-cert'
        # - 'client-cert'
        # - 'phase2-ca-cert'
        # - 'phase2-client-cert'
        # - 'phase2-private-key' (also a secret)
        # - 'private-key' (also a secret)

        # The following properties are arrays of strings
        properties["altsubject-matches"] = settings.get_property("altsubject-matches")
        properties["eap"] = settings.get_property("eap")
        properties["phase2-altsubject-matches"] = settings.get_property(
            "phase2-altsubject-matches"
        )

        # The following properties are passwords/secrets and are therefore hidden
        properties["ca-cert-password"] = "<hidden>"
        properties["client-cert-password"] = "<hidden>"
        properties["password"] = "<hidden>"
        properties["password-raw"] = "<hidden>"
        properties["phase2-ca-cert-password"] = "<hidden>"
        properties["phase2-client-cert-password"] = "<hidden>"
        properties["phase2-private-key-password"] = "<hidden>"
        properties["pin"] = "<hidden>"
        properties["private-key-password"] = "<hidden>"

        # The following properties are flags (enums)
        properties["ca-cert-password-flags"] = int(
            settings.get_ca_cert_password_flags()
        )
        properties["client-cert-password-flags"] = int(
            settings.get_client_cert_password_flags()
        )
        properties["password-flags"] = int(settings.get_password_flags())
        properties["password-raw-flags"] = int(settings.get_password_raw_flags())
        properties["phase1-auth-flags"] = int(settings.get_phase1_auth_flags())
        properties["phase2-ca-cert-password-flags"] = int(
            settings.get_phase2_ca_cert_password_flags()
        )
        properties["phase2-client-cert-password-flags"] = int(
            settings.get_phase2_client_cert_password_flags()
        )
        properties["phase2-private-key-password-flags"] = int(
            settings.get_phase2_private_key_password_flags()
        )
        properties["pin-flags"] = int(settings.get_pin_flags())
        properties["private-key-password-flags"] = int(
            settings.get_private_key_password_flags()
        )

        # The following properties are standard Python types (strings, booleans, etc.)
        properties["anonymous-identity"] = settings.get_anonymous_identity()
        properties["auth-timeout"] = settings.get_auth_timeout()
        properties["ca-path"] = settings.get_ca_path()
        properties["domain-match"] = settings.get_domain_match()
        properties["domain-suffix-match"] = settings.get_domain_suffix_match()
        properties["identity"] = settings.get_identity()
        properties["optional"] = settings.get_optional()
        properties["pac-file"] = settings.get_pac_file()
        properties["phase1-fast-provisioning"] = settings.get_phase1_fast_provisioning()
        properties["phase1-peaplabel"] = settings.get_phase1_peaplabel()
        properties["phase1-peapver"] = settings.get_phase1_peapver()
        properties["phase2-auth"] = settings.get_property("phase2-auth")
        properties["phase2-autheap"] = settings.get_property("phase2-autheap")
        properties["phase2-ca-path"] = settings.get_phase2_ca_path()
        properties["phase2-domain-match"] = settings.get_phase2_domain_match()
        properties[
            "phase2-domain-suffix-match"
        ] = settings.get_phase2_domain_suffix_match()
        properties["phase2-subject-match"] = settings.get_phase2_subject_match()
        properties["subject-match"] = settings.get_subject_match()
        properties["system-ca-certs"] = settings.get_system_ca_certs()

        return properties

    @classmethod
    def get_extended_connection_settings(cls, uuid) -> Tuple[int, Any, object]:
        if not uuid or uuid == "":
            return (-1, "Invalid UUID", {})

        settings = {}

        with cls._lock:
            if not cls._client.reload_connections(None):
                syslog(
                    LOG_WARNING,
                    "Unable to reload connection settings, reported settings could be stale",
                )

            connection = cls._client.get_connection_by_uuid(str(uuid))
            if not connection:
                return (-1, "Invalid UUID", {})

            settings[
                definition.WEBLCM_NM_SETTING_CONNECTION_TEXT
            ] = cls.extract_properties_from_nm_setting(
                connection.get_setting_connection()
            )
            settings[
                definition.WEBLCM_NM_SETTING_IP4_CONFIG_TEXT
            ] = cls.extract_properties_from_nm_setting(
                connection.get_setting_ip4_config()
            )
            settings[
                definition.WEBLCM_NM_SETTING_IP6_CONFIG_TEXT
            ] = cls.extract_properties_from_nm_setting(
                connection.get_setting_ip6_config()
            )
            settings[
                definition.WEBLCM_NM_SETTING_PROXY_TEXT
            ] = cls.extract_properties_from_nm_setting(connection.get_setting_proxy())

            # Get settings only available if the requested connection is the active one
            for active_connection in cls._client.get_active_connections():
                if active_connection.get_uuid() == connection.get_uuid():
                    settings[
                        definition.WEBLCM_NM_SETTING_GENERAL_TEXT
                    ] = cls.extract_general_properties_from_active_connection(
                        active_connection
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_IP4_TEXT
                    ] = cls.extract_ip_config_properties_from_active_connection(
                        active_connection.get_ip4_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_IP6_TEXT
                    ] = cls.extract_ip_config_properties_from_active_connection(
                        active_connection.get_ip6_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_DHCP4_TEXT
                    ] = cls.extract_dhcp_config_properties_from_active_connection(
                        active_connection.get_dhcp4_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_DHCP6_TEXT
                    ] = cls.extract_dhcp_config_properties_from_active_connection(
                        active_connection.get_dhcp6_config()
                    )

                    break

            # Get type-specific connection settings (e.g., Wired, Wireless, etc.)
            if settings[definition.WEBLCM_NM_SETTING_CONNECTION_TEXT]["type"]:
                if (
                    settings[definition.WEBLCM_NM_SETTING_CONNECTION_TEXT]["type"]
                    == definition.WEBLCM_NM_DEVICE_TYPE_WIRED_TEXT
                ):
                    settings[
                        definition.WEBLCM_NM_SETTING_WIRED_TEXT
                    ] = cls.extract_properties_from_nm_setting(
                        connection.get_setting_wired()
                    )

                if (
                    settings[definition.WEBLCM_NM_SETTING_CONNECTION_TEXT]["type"]
                    == definition.WEBLCM_NM_DEVICE_TYPE_WIRELESS_TEXT
                ):
                    settings[
                        definition.WEBLCM_NM_SETTING_WIRELESS_TEXT
                    ] = cls.extract_properties_from_nm_setting(
                        connection.get_setting_wireless()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                    ] = cls.extract_properties_from_nm_setting(
                        connection.get_setting_wireless_security()
                    )

            # Get 802.1x settings, if present
            enterprise_802_1x_settings = connection.get_setting_802_1x()
            if enterprise_802_1x_settings is not None:
                settings[
                    definition.WEBLCM_NM_SETTING_802_1X_TEXT
                ] = cls.get_802_1x_settings(enterprise_802_1x_settings)

        return (0, "", settings)

    @classmethod
    def network_status_query(cls):
        cls._network_status = {}
        with cls._lock:
            devices = cls._client.get_all_devices()
            for dev in devices:
                # Don't add unmanaged devices
                if dev.get_state() is NM.DeviceState.UNMANAGED:
                    continue

                interface_name = dev.get_iface()
                cls._network_status[interface_name] = {}

                cls._network_status[interface_name]["status"] = cls.get_dev_status(dev)

                if dev.get_state() is NM.DeviceState.ACTIVATED:
                    active_connection = dev.get_active_connection().get_connection()
                    setting_connection = active_connection.get_setting_connection()

                    connection_active = {}
                    connection_active["id"] = setting_connection.get_id()
                    connection_active[
                        "interface-name"
                    ] = setting_connection.get_interface_name()
                    connection_active["permissions"] = setting_connection.get_property(
                        "permissions"
                    )
                    connection_active["type"] = setting_connection.get_property("type")
                    connection_active["uuid"] = setting_connection.get_uuid()
                    connection_active["zone"] = setting_connection.get_zone()
                    cls._network_status[interface_name][
                        "connection_active"
                    ] = connection_active

                    cls._network_status[interface_name][
                        "ip4config"
                    ] = cls.get_ipconfig_properties(dev.get_ip4_config())
                    cls._network_status[interface_name][
                        "ip6config"
                    ] = cls.get_ipconfig_properties(dev.get_ip6_config())
                    cls._network_status[interface_name][
                        "dhcp4config"
                    ] = cls.get_dhcp_config_properties(dev.get_dhcp4_config())
                    cls._network_status[interface_name][
                        "dhcp6config"
                    ] = cls.get_dhcp_config_properties(dev.get_dhcp6_config())

                # Get wired specific items
                if dev.get_device_type() is NM.DeviceType.ETHERNET:
                    cls._network_status[interface_name][
                        "wired"
                    ] = cls.get_wired_properties(dev)

                # Get Wifi specific items
                if dev.get_device_type() == NM.DeviceType.WIFI:
                    cls._network_status[interface_name][
                        "wireless"
                    ] = cls.get_wifi_properties(dev)
                    if dev.get_state() is NM.DeviceState.ACTIVATED:
                        cls._network_status[interface_name][
                            "activeaccesspoint"
                        ] = cls.get_ap_properties(dev)

    @classmethod
    def get_client(cls):
        return cls._client

    @classmethod
    def get_lock(cls):
        return cls._lock


def dev_added(client, device):
    with NetworkStatusHelper._lock:
        NetworkStatusHelper._network_status[device.get_iface()] = {}
        NetworkStatusHelper._network_status[device.get_iface()][
            "status"
        ] = NetworkStatusHelper.get_dev_status(device)


def dev_removed(client, device):
    with NetworkStatusHelper._lock:
        NetworkStatusHelper._network_status.pop(device.get_iface(), None)


# def ap_propchange(ap, interface, signal, properties):
#     if "Strength" in properties:
#         for k in NetworkStatusHelper._network_status:
#             if NetworkStatusHelper._network_status[k].get("activeaccesspoint", None):
#                 if (
#                     NetworkStatusHelper._network_status[k]["activeaccesspoint"].get(
#                         "Ssid"
#                     )
#                     == ap.Ssid
#                 ):
#                     with NetworkStatusHelper._lock:
#                         NetworkStatusHelper._network_status[k]["activeaccesspoint"][
#                             "Strength"
#                         ] = properties["Strength"]


def dev_statechange(dev, new_state, old_state, reason):
    interface_name = dev.get_iface()
    if interface_name not in NetworkStatusHelper._network_status:
        NetworkStatusHelper._network_status[interface_name] = {}

    with NetworkStatusHelper._lock:
        if new_state == int(NM.DeviceState.ACTIVATED):
            NetworkStatusHelper._network_status[interface_name][
                "status"
            ] = NetworkStatusHelper.get_dev_status(dev)

            active_connection = dev.get_active_connection().get_connection()
            setting_connection = active_connection.get_setting_connection()

            connection_active = {}
            connection_active["id"] = setting_connection.get_id()
            connection_active[
                "interface-name"
            ] = setting_connection.get_interface_name()
            connection_active["permissions"] = setting_connection.get_property(
                "permissions"
            )
            connection_active["type"] = setting_connection.get_property("type")
            connection_active["uuid"] = setting_connection.get_uuid()
            connection_active["zone"] = setting_connection.get_zone()
            NetworkStatusHelper._network_status[interface_name][
                "connection_active"
            ] = connection_active

            NetworkStatusHelper._network_status[interface_name][
                "ip4config"
            ] = NetworkStatusHelper.get_ipconfig_properties(dev.get_ip4_config())
            NetworkStatusHelper._network_status[interface_name][
                "ip6config"
            ] = NetworkStatusHelper.get_ipconfig_properties(dev.get_ip6_config())
            NetworkStatusHelper._network_status[interface_name][
                "dhcp4config"
            ] = NetworkStatusHelper.get_dhcp_config_properties(dev.get_dhcp4_config())
            NetworkStatusHelper._network_status[interface_name][
                "dhcp6config"
            ] = NetworkStatusHelper.get_dhcp_config_properties(dev.get_dhcp6_config())
        # 				dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)
        elif new_state == int(NM.DeviceState.DISCONNECTED):
            if "ip4config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "ip4config", None
                )
            if "ip6config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "ip6config", None
                )
            if "dhcp4config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "dhcp4config", None
                )
            if "dhcp6config" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "dhcp6config", None
                )
            if (
                "activeaccesspoint"
                in NetworkStatusHelper._network_status[interface_name]
            ):
                NetworkStatusHelper._network_status[interface_name].pop(
                    "activeaccesspoint", None
                )
            if (
                "connection_active"
                in NetworkStatusHelper._network_status[interface_name]
            ):
                NetworkStatusHelper._network_status[interface_name].pop(
                    "connection_active", None
                )
        elif new_state == int(NM.DeviceState.UNAVAILABLE):
            if "wired" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop("wired", None)
            if "wireless" in NetworkStatusHelper._network_status[interface_name]:
                NetworkStatusHelper._network_status[interface_name].pop(
                    "wireless", None
                )
        NetworkStatusHelper._network_status[interface_name]["status"][
            "State"
        ] = new_state


def run_event_listener():

    NetworkStatusHelper.network_status_query()

    NetworkStatusHelper.get_client().connect("device-added", dev_added)
    NetworkStatusHelper.get_client().connect("device-removed", dev_removed)

    with NetworkStatusHelper.get_lock():
        all_devices = NetworkStatusHelper.get_client().get_all_devices()
    for dev in all_devices:
        if dev.get_device_type() in (
            NM.DeviceType.ETHERNET,
            NM.DeviceType.WIFI,
            NM.DeviceType.MODEM,
        ):
            dev.connect("state-changed", dev_statechange)
        # In case wifi connection is already activated
    # 		if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI and dev.ActiveAccessPoint:
    # 			dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)

    GLib.MainLoop().run()


@cherrypy.expose
class NetworkStatus(object):

    DBusGMainLoop(set_as_default=True)

    def __init__(self):

        t = Thread(target=run_event_listener, daemon=True)
        t.start()

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        result = {"SDCERR": 0, "InfoMsg": ""}

        NetworkStatusHelper.network_status_query()
        with NetworkStatusHelper.get_lock():
            result["status"] = NetworkStatusHelper._network_status

        with NetworkStatusHelper.get_lock():
            devices = NetworkStatusHelper.get_client().get_devices()
        for dev in devices:
            if dev.get_device_type() is NM.DeviceType.WIFI:
                result["status"][dev.get_iface()]["wireless"][
                    "RegDomain"
                ] = NetworkStatusHelper.get_reg_domain_info()

        unmanaged_devices = (
            cherrypy.request.app.config["weblcm"]
            .get("unmanaged_hardware_devices", "")
            .split()
        )
        for dev in unmanaged_devices:
            if dev in result["status"]:
                del result["status"][dev]
        result["devices"] = len(result["status"])
        return result
