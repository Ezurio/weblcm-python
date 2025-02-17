#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
import os
from pathlib import Path
import time
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse
import cherrypy
import gi

gi.require_version("NM", "1.0")
from gi.repository import NM, GLib, Gio
from threading import Lock
from .settings import SystemSettingsManage
from . import definition
from syslog import syslog, LOG_ERR
from subprocess import run, TimeoutExpired
import re


class NetworkStatusHelper(object):

    _network_status = {}
    _lock = Lock()
    _IW_PATH = "/usr/sbin/iw"
    _client = NM.Client.new(None)
    RELOAD_CONNECTIONS_TIMEOUT_S: int = 10

    @staticmethod
    def reload_connections() -> bool:
        success = False
        callback_finished = False
        cancellable = Gio.Cancellable()
        lock = Lock()

        @staticmethod
        def connections_reloaded_callback(source_object, res, user_data):
            nonlocal callback_finished
            nonlocal success
            nonlocal lock
            callback_finished = False
            success = False

            with lock:
                try:
                    # Finish the asynchronous operation (source_object is the client and the return
                    # type of reload_connections_finish() is bool)
                    with NetworkStatusHelper.get_lock():
                        success = source_object.reload_connections_finish(res)
                except Exception as e:
                    syslog(LOG_ERR, f"Could not finish reloading connections: {str(e)}")
                    success = False

                callback_finished = True

        try:
            with NetworkStatusHelper.get_lock():
                GLib.idle_add(
                    NetworkStatusHelper.get_client().reload_connections_async,
                    cancellable,
                    connections_reloaded_callback,
                    None,
                )
            start = time.time()
            while True:
                with lock:
                    if callback_finished:
                        break
                if time.time() - start > NetworkStatusHelper.RELOAD_CONNECTIONS_TIMEOUT_S:
                    cancellable.cancel()
                    raise Exception("timeout")
                time.sleep(0.1)
        except Exception as e:
            syslog(LOG_ERR, f"Error reloading connections: {str(e)}")
            success = False

        return success

    @classmethod
    def get_active_ap_rssi(cls, ifname: Optional[str] = "wlan0") -> Tuple[bool, float]:
        """
        Retrieve the signal strength in dBm for the active accesspoint on the specified interface
        (default is wlan0).

        The return value is a tuple in the form of: (success, rssi)
        """
        _RSSI_RE = r"signal: (?P<RSSI>.*) dBm"

        if not os.path.exists(cls._IW_PATH):
            return (False, definition.INVALID_RSSI)

        try:
            proc = run(
                [cls._IW_PATH, "dev", ifname, "link"],
                capture_output=True,
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )

            if not proc.returncode:
                for line in proc.stdout.decode("utf-8").splitlines():
                    line = line.strip()
                    match = re.match(_RSSI_RE, line)
                    if match:
                        return (True, float(match.group("RSSI")))
        except TimeoutExpired:
            syslog(LOG_ERR, f"Call 'iw dev {str(ifname)} link' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev {str(ifname)} link' failed: {str(e)}")

        return (False, definition.INVALID_RSSI)

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
    def gflags_to_list(cls, flags_type, value) -> List[str]:
        """
        Convert an NM 80211ApFlags or 80211ApSecurityFlags GFlags value to a list of strings
        representing the flags that are set.

        Adapted from the NetworkManager Python examples:
        https://github.com/NetworkManager/NetworkManager/blob/main/examples/python/gi/show-wifi-networks.py
        """
        if value == 0:
            return []
        list_of_flags = []
        for n in sorted(dir(flags_type)):
            if not re.search("^[A-Z0-9_]+$", n):
                continue
            flag_value = getattr(flags_type, n)
            if value & flag_value:
                value &= ~flag_value
                list_of_flags.append(n)
                if value == 0:
                    break
        if value:
            list_of_flags.append("(0x%0x)" % (value,))
        return list_of_flags

    @classmethod
    def get_ap_properties(cls, dev):
        ap = dev.get_active_access_point()
        if not ap:
            return {}

        apProperties = {}
        ssid = ap.get_ssid()
        apProperties["Ssid"] = (
            ssid.get_data().decode("utf-8") if ssid is not None else ""
        )
        apProperties["HwAddress"] = ap.get_bssid()
        apProperties["Maxbitrate"] = ap.get_max_bitrate()
        flags = int(ap.get_flags())
        wpa_flags = int(ap.get_wpa_flags())
        rsn_flags = int(ap.get_rsn_flags())
        apProperties["Flags"] = flags
        apProperties["FlagsList"] = cls.gflags_to_list(
            getattr(NM, "80211ApFlags"), flags
        )
        apProperties["Wpaflags"] = wpa_flags
        apProperties["WpaFlagsList"] = cls.gflags_to_list(
            getattr(NM, "80211ApSecurityFlags"), wpa_flags
        )
        apProperties["Rsnflags"] = rsn_flags
        apProperties["RsnFlagsList"] = cls.gflags_to_list(
            getattr(NM, "80211ApSecurityFlags"), rsn_flags
        )
        # Use iw dev to get channel/frequency/rssi info for AP mode
        if dev.get_mode() is getattr(NM, "80211Mode").AP:
            apProperties["Strength"] = 100
            apProperties["Frequency"] = cls.get_frequency_info(
                dev.get_iface(), ap.get_frequency()
            )
            apProperties["Signal"] = definition.INVALID_RSSI
        else:
            apProperties["Strength"] = ap.get_strength()
            apProperties["Frequency"] = ap.get_frequency()
            (success, signal) = NetworkStatusHelper.get_active_ap_rssi(dev.get_iface())
            apProperties["Signal"] = signal if success else definition.INVALID_RSSI
        return apProperties

    @classmethod
    def get_wifi_properties(cls, dev):
        wireless = {}
        wireless["Bitrate"] = dev.get_bitrate()
        wireless["HwAddress"] = dev.get_hw_address()
        wireless["PermHwAddress"] = dev.get_permanent_hw_address()
        wireless["Mode"] = int(dev.get_mode())
        wireless["LastScan"] = dev.get_last_scan()
        wireless["RegDomain"] = NetworkStatusHelper.get_reg_domain_info()
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
        connection_setting_connection = connection.get_setting_connection()
        properties["zone"] = (
            connection_setting_connection.get_zone()
            if connection_setting_connection
            else NM.SettingConnection.props.zone.default_value
        )

        master = active_connection.get_master()
        properties["master-path"] = (
            master.get_path()
            if master
            else NM.ActiveConnection.props.master.default_value
        )

        return properties

    @classmethod
    def extract_ip_config_properties_from_active_connection(cls, ip_config):
        if not ip_config:
            return {}

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

        # The following properties are presented as a GLib.Bytes object containing "file://"
        # followed by the path to the target file and a terminating null byte
        # See below for more info:
        # https://lazka.github.io/pgi-docs/#NM-1.0/classes/Setting8021x.html#NM.Setting8021x.props.ca_cert
        properties["ca-cert"] = cls.cert_to_filename(settings.get_property("ca-cert"))
        properties["client-cert"] = cls.cert_to_filename(
            settings.get_property("client-cert")
        )
        properties["private-key"] = cls.cert_to_filename(
            settings.get_property("private-key")
        )
        properties["phase2-ca-cert"] = cls.cert_to_filename(
            settings.get_property("phase2-ca-cert")
        )
        properties["phase2-client-cert"] = cls.cert_to_filename(
            settings.get_property("phase2-client-cert")
        )
        properties["phase2-private-key"] = cls.cert_to_filename(
            settings.get_property("phase2-private-key")
        )

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

            # Get settings only available if the requested connection is active
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
                    settings[definition.WEBLCM_NM_SETTING_WIRELESS_TEXT][
                        "RegDomain"
                    ] = NetworkStatusHelper.get_reg_domain_info()
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
                    dev_active_connection = dev.get_active_connection()
                    if dev_active_connection:
                        active_connection = dev_active_connection.get_connection()
                        setting_connection = active_connection.get_setting_connection()

                        if setting_connection:
                            connection_active = {}
                            connection_active["id"] = setting_connection.get_id()
                            connection_active[
                                "interface-name"
                            ] = setting_connection.get_interface_name()
                            connection_active[
                                "permissions"
                            ] = setting_connection.get_property("permissions")
                            connection_active["type"] = setting_connection.get_property(
                                "type"
                            )
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

    @staticmethod
    def cert_to_filename(cert: bytearray | list | GLib.Bytes) -> Optional[str]:
        """
        Return base name only.
        """
        try:
            if not cert:
                return None

            if isinstance(cert, GLib.Bytes):
                cert = cert.get_data()
            elif isinstance(cert, list):
                cert = bytearray(cert)
            elif not isinstance(cert, bytearray):
                raise Exception("Invalid type")

            return Path(urlparse(cert.split(b"\0")[0].decode("utf-8")).path).name
        except Exception as exception:
            syslog(LOG_ERR, f"Could not decode certificate filename: {exception}")
            return None

    @staticmethod
    def get_access_point_security_description(
        flags: int, wpa_flags: int, rsn_flags: int
    ) -> Tuple[str, str]:
        """Analyze the provided AP flags and return the security and key management supported"""

        security_string = ""
        keymgmt = ""
        if (
            flags & int(getattr(NM, "80211ApFlags").PRIVACY)
            and wpa_flags == int(getattr(NM, "80211ApSecurityFlags").NONE)
            and rsn_flags == int(getattr(NM, "80211ApSecurityFlags").NONE)
        ):
            # WEP
            security_string += "WEP "
            keymgmt = "static"
        else:
            if wpa_flags != int(getattr(NM, "80211ApSecurityFlags").NONE):
                # WPA1
                security_string += "WPA1 "

            if (
                (rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_PSK))
                or (rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_CCKM))
                or (
                    rsn_flags
                    & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_SUITE_B)
                )
                or (
                    rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_802_1X)
                )
            ):
                # WPA2
                security_string += "WPA2 "

            if rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_SAE):
                # WPA3
                security_string += "WPA3 "
                keymgmt += "sae "

            if (wpa_flags == int(getattr(NM, "80211ApSecurityFlags").NONE)) and (
                rsn_flags
                == (
                    int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_EAP_SUITE_B_192)
                    | int(getattr(NM, "80211ApSecurityFlags").PAIR_GCMP_256)
                    | int(getattr(NM, "80211ApSecurityFlags").GROUP_GCMP_256)
                    | int(getattr(NM, "80211ApSecurityFlags").MGMT_GROUP_GMAC_256)
                )
            ):
                # WPA3
                security_string += "WPA3 "
                keymgmt = "wpa-eap-suite-b-192"

            if rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_OWE) != 0:
                # OWE
                security_string += "OWE "
                keymgmt = "owe"
            elif (
                rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_OWE_TM)
                != 0
            ):
                # OWE-TM
                security_string += "OWE-TM "
                keymgmt = "owe"

            if (
                (wpa_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_802_1X))
                or (rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_CCKM))
                or (
                    rsn_flags
                    & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_SUITE_B)
                )
                or (
                    rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_802_1X)
                )
            ):
                # 802.1X
                security_string += "802.1X "
                if rsn_flags & int(
                    getattr(NM, "80211ApSecurityFlags").KEY_MGMT_SUITE_B
                ):
                    keymgmt += "wpa-eap-suite-b "
                else:
                    keymgmt += "wpa-eap "

            if (
                wpa_flags
                & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_EAP_SUITE_B_192)
            ) or (
                rsn_flags
                & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_EAP_SUITE_B_192)
            ):
                # WPA-EAP-SUITE-B-192
                security_string += "WPA-EAP-SUITE-B-192 "
                keymgmt += "wpa-eap-suite-b-192 "

            if (wpa_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_PSK)) or (
                rsn_flags & int(getattr(NM, "80211ApSecurityFlags").KEY_MGMT_PSK)
            ):
                # PSK
                security_string += "PSK "
                keymgmt += "wpa-psk "

        if not keymgmt:
            # Open
            keymgmt = "none"

        return security_string.rstrip(" "), keymgmt.rstrip(" ")


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
    if not interface_name:
        return
    if interface_name not in NetworkStatusHelper._network_status:
        NetworkStatusHelper._network_status[interface_name] = {}

    with NetworkStatusHelper._lock:
        if new_state == int(NM.DeviceState.ACTIVATED):
            NetworkStatusHelper._network_status[interface_name][
                "status"
            ] = NetworkStatusHelper.get_dev_status(dev)

            dev_active_connection = dev.get_active_connection()
            if dev_active_connection:
                active_connection = dev_active_connection.get_connection()
                setting_connection = active_connection.get_setting_connection()

                if setting_connection:
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


@cherrypy.expose
class NetworkStatus(object):
    def __init__(self):
        run_event_listener()

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
