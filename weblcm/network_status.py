import os
from typing import Any, Tuple
import cherrypy
from dbus.mainloop.glib import DBusGMainLoop
import gi

gi.require_version("NM", "1.0")
from gi.repository import GLib, NM
import NetworkManager
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
        except:
            syslog(LOG_ERR, "Call 'iw reg get' failed")

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
        except:
            syslog(LOG_ERR, "Call 'iw dev' failed")

        return frequency

    @classmethod
    def get_dev_status(cls, dev):
        status = {}
        status["State"] = dev.State
        try:
            status["StateText"] = definition.WEBLCM_STATE_TEXT.get(dev.State)
        except:
            status["StateText"] = "Unknown"
            syslog(
                "unknown device state value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % dev.State
            )
        status["Mtu"] = dev.Mtu
        status["DeviceType"] = dev.DeviceType
        try:
            status["DeviceTypeText"] = definition.WEBLCM_DEVTYPE_TEXT.get(
                dev.DeviceType
            )
        except:
            status["DeviceTypeText"] = "Unknown"
            syslog(
                "unknown device type value %d.  See https://developer-old.gnome.org/NetworkManager/stable/nm-dbus-types.html"
                % dev.DeviceType
            )
        return status

    @classmethod
    def get_ipv4_properties(cls, ipv4):

        ip4Properties = {}
        if not ipv4:
            return ip4Properties

        addresses = {}
        i = 0
        for addr in ipv4.Addresses:
            addresses[i] = str(addr[0]) + "/" + str(addr[1])
            i += 1
        ip4Properties["Addresses"] = addresses
        ip4Properties["AddressData"] = ipv4.AddressData

        routes = {}
        i = 0
        for rt in ipv4.Routes:
            routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
            i += 1
        ip4Properties["Routes"] = routes
        ip4Properties["RouteData"] = ipv4.RouteData
        ip4Properties["Gateway"] = ipv4.Gateway

        i = 0
        domains = {}
        for dns in ipv4.Domains:
            domains[i] = str(dns)
            i += 1
        ip4Properties["Domains"] = domains

        ip4Properties["NameserverData"] = ipv4.NameserverData
        ip4Properties["DnsOptions"] = ipv4.DnsOptions
        ip4Properties["DnsPriority"] = ipv4.DnsPriority
        ip4Properties["WinsServerData"] = ipv4.WinsServerData

        return ip4Properties

    @classmethod
    def get_ipv6_properties(cls, ipv6):

        ip6Properties = {}
        if not ipv6:
            return ip6Properties

        addresses = {}
        i = 0
        for addr in ipv6.Addresses:
            addresses[i] = str(addr[0]) + "/" + str(addr[1])
            i += 1
        ip6Properties["Addresses"] = addresses
        ip6Properties["AddressData"] = ipv6.AddressData

        routes = {}
        i = 0
        for rt in ipv6.Routes:
            routes[i] = str(rt[0]) + "/" + str(rt[1]) + " metric " + str(rt[3])
            i += 1
        ip6Properties["Routes"] = routes
        ip6Properties["RouteData"] = ipv6.RouteData

        ip6Properties["Gateway"] = ipv6.Gateway

        i = 0
        domains = {}
        for dns in ipv6.Domains:
            domains[i] = str(dns)
            i += 1
        ip6Properties["Domains"] = domains

        ip6Properties["Nameservers"] = ipv6.Nameservers
        ip6Properties["DnsOptions"] = ipv6.DnsOptions
        ip6Properties["DnsPriority"] = ipv6.DnsPriority

        return ip6Properties

    @classmethod
    def get_dhcp4_properties(cls, dhcp4):

        if not dhcp4:
            return {}

        return dhcp4.Options

    @classmethod
    def get_dhcp6_properties(cls, dhcp6):

        if not dhcp6:
            return {}

        return dhcp6.Options

    @classmethod
    def get_ap_properties(cls, ap, dev):

        apProperties = {}
        apProperties["Ssid"] = ap.Ssid
        apProperties["HwAddress"] = ap.HwAddress
        apProperties["Maxbitrate"] = ap.MaxBitrate
        apProperties["Flags"] = ap.Flags
        apProperties["Wpaflags"] = ap.WpaFlags
        apProperties["Rsnflags"] = ap.RsnFlags
        # Use iw dev to get channel/frequency info for AP mode
        if dev.Mode == NetworkManager.NM_802_11_MODE_AP:
            apProperties["Strength"] = 100
            apProperties["Frequency"] = cls.get_frequency_info(
                dev.Interface, ap.Frequency
            )
        else:
            apProperties["Strength"] = ap.Strength
            apProperties["Frequency"] = ap.Frequency
        return apProperties

    @classmethod
    def get_wifi_properties(cls, dev):
        wireless = {}
        wireless["Bitrate"] = dev.Bitrate
        wireless["HwAddress"] = dev.HwAddress
        wireless["PermHwAddress"] = dev.PermHwAddress
        wireless["Mode"] = dev.Mode
        wireless["LastScan"] = dev.LastScan
        return wireless

    @classmethod
    def get_wired_properties(cls, dev):
        wired = {}
        wired["HwAddress"] = dev.HwAddress
        wired["PermHwAddress"] = dev.PermHwAddress
        wired["Speed"] = dev.Speed
        wired["Carrier"] = dev.Carrier
        return wired

    @classmethod
    def get_available_connections(cls, available_connections):

        if not available_connections:
            return {}

        connections = []
        for connection in available_connections:
            connections.append(connection.GetSettings()["connection"])

        return connections

    @classmethod
    def get_active_connection(cls, dev):

        if not dev or not dev.ActiveConnection:
            return {}

        return dev.ActiveConnection.Connection.GetSettings()["connection"]

    @classmethod
    def gi_extract_properties_from_nm_setting(cls, nm_setting):
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
    def gi_extract_general_properties_from_active_connection(cls, active_connection):
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
    def gi_extract_ip_config_properties_from_active_connection(cls, ip_config):
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
    def gi_extract_dhcp_config_properties_from_active_connection(cls, dhcp_config):
        if not dhcp_config:
            return {}

        # Attempt to match output from:
        # 'nmcli connection show <target_profile>'
        properties = {}

        properties["options"] = dhcp_config.get_options()

        return properties

    @classmethod
    def gi_get_802_1x_settings(cls, settings):
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
    def gi_get_extended_connection_settings(cls, uuid) -> Tuple[int, Any, object]:
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
            ] = cls.gi_extract_properties_from_nm_setting(
                connection.get_setting_connection()
            )
            settings[
                definition.WEBLCM_NM_SETTING_IP4_CONFIG_TEXT
            ] = cls.gi_extract_properties_from_nm_setting(
                connection.get_setting_ip4_config()
            )
            settings[
                definition.WEBLCM_NM_SETTING_IP6_CONFIG_TEXT
            ] = cls.gi_extract_properties_from_nm_setting(
                connection.get_setting_ip6_config()
            )
            settings[
                definition.WEBLCM_NM_SETTING_PROXY_TEXT
            ] = cls.gi_extract_properties_from_nm_setting(
                connection.get_setting_proxy()
            )

            # Get settings only available if the requested connection is the active one
            for active_connection in cls._client.get_active_connections():
                if active_connection.get_uuid() == connection.get_uuid():
                    settings[
                        definition.WEBLCM_NM_SETTING_GENERAL_TEXT
                    ] = cls.gi_extract_general_properties_from_active_connection(
                        active_connection
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_IP4_TEXT
                    ] = cls.gi_extract_ip_config_properties_from_active_connection(
                        active_connection.get_ip4_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_IP6_TEXT
                    ] = cls.gi_extract_ip_config_properties_from_active_connection(
                        active_connection.get_ip6_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_DHCP4_TEXT
                    ] = cls.gi_extract_dhcp_config_properties_from_active_connection(
                        active_connection.get_dhcp4_config()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_DHCP6_TEXT
                    ] = cls.gi_extract_dhcp_config_properties_from_active_connection(
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
                    ] = cls.gi_extract_properties_from_nm_setting(
                        connection.get_setting_wired()
                    )

                if (
                    settings[definition.WEBLCM_NM_SETTING_CONNECTION_TEXT]["type"]
                    == definition.WEBLCM_NM_DEVICE_TYPE_WIRELESS_TEXT
                ):
                    settings[
                        definition.WEBLCM_NM_SETTING_WIRELESS_TEXT
                    ] = cls.gi_extract_properties_from_nm_setting(
                        connection.get_setting_wireless()
                    )
                    settings[
                        definition.WEBLCM_NM_SETTING_WIRELESS_SECURITY_TEXT
                    ] = cls.gi_extract_properties_from_nm_setting(
                        connection.get_setting_wireless_security()
                    )

            # Get 802.1x settings, if present
            enterprise_802_1x_settings = connection.get_setting_802_1x()
            if enterprise_802_1x_settings is not None:
                settings[
                    definition.WEBLCM_NM_SETTING_802_1X_TEXT
                ] = cls.gi_get_802_1x_settings(enterprise_802_1x_settings)

        return (0, "", settings)

    @classmethod
    def network_status_query(cls):
        cls._network_status = {}
        with cls._lock:
            devices = NetworkManager.NetworkManager.GetDevices()
            for dev in devices:

                # Dont add unmanaged devices
                if dev.State == NetworkManager.NM_DEVICE_STATE_UNMANAGED:
                    continue

                interface_name = dev.Interface
                cls._network_status[interface_name] = {}

                cls._network_status[interface_name]["status"] = cls.get_dev_status(dev)

                if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
                    settings = dev.ActiveConnection.Connection.GetSettings()
                    cls._network_status[interface_name]["connection_active"] = settings[
                        "connection"
                    ]
                    cls._network_status[interface_name][
                        "ip4config"
                    ] = cls.get_ipv4_properties(dev.Ip4Config)
                    cls._network_status[interface_name][
                        "ip6config"
                    ] = cls.get_ipv6_properties(dev.Ip6Config)
                    cls._network_status[interface_name][
                        "dhcp4config"
                    ] = cls.get_dhcp4_properties(dev.Dhcp4Config)
                    cls._network_status[interface_name][
                        "dhcp6config"
                    ] = cls.get_dhcp6_properties(dev.Dhcp6Config)

                # Get wired specific items
                if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
                    cls._network_status[interface_name][
                        "wired"
                    ] = cls.get_wired_properties(dev)

                # Get Wifi specific items
                if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                    cls._network_status[interface_name][
                        "wireless"
                    ] = cls.get_wifi_properties(dev)
                    if dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
                        cls._network_status[interface_name][
                            "activeaccesspoint"
                        ] = cls.get_ap_properties(dev.ActiveAccessPoint, dev)


def dev_added(nm, interface, signal, device_path):
    with NetworkStatusHelper._lock:
        NetworkStatusHelper._network_status[device_path.Interface] = {}
        NetworkStatusHelper._network_status[device_path.Interface][
            "status"
        ] = NetworkStatusHelper.get_dev_status(device_path)


def dev_removed(nm, interface, signal, device_path):
    with NetworkStatusHelper._lock:
        NetworkStatusHelper._network_status.pop(device_path.Interface, None)


def ap_propchange(ap, interface, signal, properties):
    if "Strength" in properties:
        for k in NetworkStatusHelper._network_status:
            if NetworkStatusHelper._network_status[k].get("activeaccesspoint", None):
                if (
                    NetworkStatusHelper._network_status[k]["activeaccesspoint"].get(
                        "Ssid"
                    )
                    == ap.Ssid
                ):
                    with NetworkStatusHelper._lock:
                        NetworkStatusHelper._network_status[k]["activeaccesspoint"][
                            "Strength"
                        ] = properties["Strength"]


def dev_statechange(dev, interface, signal, new_state, old_state, reason):
    if dev.Interface not in NetworkStatusHelper._network_status:
        NetworkStatusHelper._network_status[dev.Interface] = {}

    with NetworkStatusHelper._lock:
        if new_state == NetworkManager.NM_DEVICE_STATE_ACTIVATED:
            NetworkStatusHelper._network_status[dev.Interface][
                "status"
            ] = NetworkStatusHelper.get_dev_status(dev)
            settings = dev.ActiveConnection.Connection.GetSettings()
            NetworkStatusHelper._network_status[dev.Interface][
                "connection_active"
            ] = settings["connection"]
            NetworkStatusHelper._network_status[dev.Interface][
                "ip4config"
            ] = NetworkStatusHelper.get_ipv4_properties(dev.Ip4Config)
            NetworkStatusHelper._network_status[dev.Interface][
                "ip6config"
            ] = NetworkStatusHelper.get_ipv6_properties(dev.Ip6Config)
            NetworkStatusHelper._network_status[dev.Interface][
                "dhcp4config"
            ] = NetworkStatusHelper.get_dhcp4_properties(dev.Dhcp4Config)
            NetworkStatusHelper._network_status[dev.Interface][
                "dhcp6config"
            ] = NetworkStatusHelper.get_dhcp6_properties(dev.Dhcp6Config)
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_ETHERNET:
                NetworkStatusHelper._network_status[dev.Interface][
                    "wired"
                ] = NetworkStatusHelper.get_wired_properties(dev)
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                NetworkStatusHelper._network_status[dev.Interface][
                    "wireless"
                ] = NetworkStatusHelper.get_wifi_properties(dev)
                NetworkStatusHelper._network_status[dev.Interface][
                    "activeaccesspoint"
                ] = NetworkStatusHelper.get_ap_properties(dev.ActiveAccessPoint, dev)
        # 				dev.ActiveAccessPoint.OnPropertiesChanged(ap_propchange)
        elif new_state == NetworkManager.NM_DEVICE_STATE_DISCONNECTED:
            if "ip4config" in NetworkStatusHelper._network_status[dev.Interface]:
                NetworkStatusHelper._network_status[dev.Interface].pop(
                    "ip4config", None
                )
            if "ip6config" in NetworkStatusHelper._network_status[dev.Interface]:
                NetworkStatusHelper._network_status[dev.Interface].pop(
                    "ip6config", None
                )
            if (
                "activeaccesspoint"
                in NetworkStatusHelper._network_status[dev.Interface]
            ):
                NetworkStatusHelper._network_status[dev.Interface].pop(
                    "activeaccesspoint", None
                )
            if (
                "connection_active"
                in NetworkStatusHelper._network_status[dev.Interface]
            ):
                NetworkStatusHelper._network_status[dev.Interface].pop(
                    "connection_active", None
                )
        elif new_state == NetworkManager.NM_DEVICE_STATE_UNAVAILABLE:
            if "wired" in NetworkStatusHelper._network_status[dev.Interface]:
                NetworkStatusHelper._network_status[dev.Interface].pop("wired", None)
            if "wireless" in NetworkStatusHelper._network_status[dev.Interface]:
                NetworkStatusHelper._network_status[dev.Interface].pop("wireless", None)
        NetworkStatusHelper._network_status[dev.Interface]["status"][
            "State"
        ] = new_state


def run_event_listener():

    NetworkStatusHelper.network_status_query()

    NetworkManager.NetworkManager.OnDeviceAdded(dev_added)
    NetworkManager.NetworkManager.OnDeviceRemoved(dev_removed)

    for dev in NetworkManager.Device.all():
        if dev.DeviceType in (
            NetworkManager.NM_DEVICE_TYPE_ETHERNET,
            NetworkManager.NM_DEVICE_TYPE_WIFI,
            NetworkManager.NM_DEVICE_TYPE_MODEM,
        ):
            dev.OnStateChanged(dev_statechange)
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
        with NetworkStatusHelper._lock:
            result["status"] = NetworkStatusHelper._network_status

        devices = NetworkManager.NetworkManager.GetDevices()
        for dev in devices:
            if dev.DeviceType == NetworkManager.NM_DEVICE_TYPE_WIFI:
                result["status"][dev.Interface]["wireless"][
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
