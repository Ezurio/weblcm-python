from socket import AF_INET, AF_INET6
from threading import Lock
import time
from typing import Any, Optional, Tuple
import cherrypy
import subprocess
from . import definition
from syslog import syslog, LOG_ERR, LOG_WARNING
from subprocess import run, TimeoutExpired
from .settings import SystemSettingsManage
from .network_status import NetworkStatusHelper
import gi
import os

gi.require_version("NM", "1.0")
from gi.repository import GLib, NM, Gio

try:
    from .bluetooth.bt import Bluetooth
except ImportError:
    Bluetooth = None


@cherrypy.expose
class NetworkConnections(object):
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        _client = NetworkStatusHelper.get_client()
        result = {"SDCERR": 0, "InfoMsg": "", "count": 0, "connections": {}}

        unmanaged_devices = (
            cherrypy.request.app.config["weblcm"]
            .get("unmanaged_hardware_devices", "")
            .split()
        )

        # Get a list of all known connections (profiles)
        with NetworkStatusHelper.get_lock():
            connections = _client.get_connections()

        # Loop through the connections and build a dictionary to return
        for conn in connections:
            if unmanaged_devices and conn.get_interface_name() in unmanaged_devices:
                continue

            entry = {}

            # Assume the connection is not in the 'Activated' state by default until we can check it
            # against the list of 'Active' connections later
            entry["activated"] = 0
            entry["id"] = conn.get_id()

            # Check if the connection is an AP
            try:
                entry["type"] = (
                    "ap" if conn.get_setting_wireless().get_mode() == "ap" else ""
                )
            except Exception:
                # Couldn't read the wireless settings, so assume it's not an AP
                pass

            # Add the connection to the dictionary
            result["connections"][conn.get_uuid()] = entry
        result["count"] = len(result["connections"])

        if result["count"] > 0:
            # Get a list of all active connections (profiles) so that we can mark which ones are in
            # the 'Activated' state
            with NetworkStatusHelper.get_lock():
                active_connections = _client.get_active_connections()
            for conn in active_connections:
                try:
                    if conn.get_state() == NM.ActiveConnectionState.ACTIVATED:
                        result["connections"][conn.get_uuid()]["activated"] = 1
                except Exception:
                    # Couldn't mark the connection as 'Activated', so just assume it's not
                    pass

        return result


@cherrypy.expose
class NetworkConnection(object):

    SUPPORTED_8021X_CERTS = [
        NM.SETTING_802_1X_CA_CERT,
        NM.SETTING_802_1X_CLIENT_CERT,
        NM.SETTING_802_1X_PRIVATE_KEY,
        NM.SETTING_802_1X_PHASE2_CA_CERT,
        NM.SETTING_802_1X_PHASE2_CLIENT_CERT,
        NM.SETTING_802_1X_PHASE2_PRIVATE_KEY,
    ]

    IPCONFIG_PROPERTIES = [
        (NM.SETTING_IP_CONFIG_DAD_TIMEOUT, int),
        (NM.SETTING_IP_CONFIG_DHCP_HOSTNAME, str),
        (NM.SETTING_IP_CONFIG_DHCP_SEND_HOSTNAME, bool),
        (NM.SETTING_IP_CONFIG_DHCP_TIMEOUT, int),
        (NM.SETTING_IP_CONFIG_DNS_PRIORITY, int),
        (NM.SETTING_IP_CONFIG_GATEWAY, str),
        (NM.SETTING_IP_CONFIG_IGNORE_AUTO_DNS, bool),
        (NM.SETTING_IP_CONFIG_IGNORE_AUTO_ROUTES, bool),
        (NM.SETTING_IP_CONFIG_MAY_FAIL, bool),
        (NM.SETTING_IP_CONFIG_METHOD, str),
        (NM.SETTING_IP_CONFIG_NEVER_DEFAULT, bool),
        (NM.SETTING_IP_CONFIG_ROUTE_METRIC, int),
        (NM.SETTING_IP_CONFIG_ROUTE_TABLE, int),
    ]

    IP4CONFIG_PROPERTIES = [
        (NM.SETTING_IP4_CONFIG_DHCP_CLIENT_ID, str),
        (NM.SETTING_IP4_CONFIG_DHCP_FQDN, str),
    ]

    IP6CONFIG_PROPERTIES = [
        (NM.SETTING_IP6_CONFIG_ADDR_GEN_MODE, int),
        (NM.SETTING_IP6_CONFIG_DHCP_DUID, str),
        (NM.SETTING_IP6_CONFIG_IP6_PRIVACY, NM.SettingIP6ConfigPrivacy),
        (NM.SETTING_IP6_CONFIG_TOKEN, str),
    ]

    ADD_CONNECTION_TIMEOUT_S: int = 10
    DELETE_CONNECTION_TIMEOUT_S: int = 10
    ACTIVATE_CONNECTION_TIMEOUT_S: int = 10

    def __init__(self):
        self.client = NetworkStatusHelper.get_client()

        # Determine if newer NM settings are supported
        self.nm_ip_config_dhcp_hostname_flags_supported = (
            getattr(NM, "SETTING_IP_CONFIG_DHCP_HOSTNAME_FLAGS", None) is not None
        )
        if self.nm_ip_config_dhcp_hostname_flags_supported:
            self.IPCONFIG_PROPERTIES.append(
                (NM.SETTING_IP_CONFIG_DHCP_HOSTNAME_FLAGS, int)
            )
        else:
            syslog(LOG_WARNING, "'dhcp-hostname-flags' setting not supported")
        self.nm_ip_config_dhcp_iaid_supported = (
            getattr(NM, "SETTING_IP_CONFIG_DHCP_IAID", None) is not None
        )
        if self.nm_ip_config_dhcp_iaid_supported:
            self.IPCONFIG_PROPERTIES.append((NM.SETTING_IP_CONFIG_DHCP_IAID, str))
        else:
            syslog(LOG_WARNING, "'dhcp-iaid' setting not supported")
        self.nm_ip_config_dhcp_reject_servers_supported = (
            getattr(NM, "SETTING_IP_CONFIG_DHCP_REJECT_SERVERS", None) is not None
        )
        if not self.nm_ip_config_dhcp_reject_servers_supported:
            syslog(LOG_WARNING, "'dhcp-reject-servers' setting not supported")

        self.nm_ip4_config_dhcp_vendor_class_identifier_supported = (
            getattr(NM, "SETTING_IP4_CONFIG_DHCP_VENDOR_CLASS_IDENTIFIER", None)
            is not None
        )
        if self.nm_ip4_config_dhcp_vendor_class_identifier_supported:
            self.IP4CONFIG_PROPERTIES.append(
                (NM.SETTING_IP4_CONFIG_DHCP_VENDOR_CLASS_IDENTIFIER, str)
            )
        else:
            syslog(LOG_WARNING, "'dhcp-vendor-class-identifier' setting not supported")

        self.nm_ip6_config_ra_timeout_supported = (
            getattr(NM, "SETTING_IP6_CONFIG_RA_TIMEOUT", None) is not None
        )
        if self.nm_ip6_config_ra_timeout_supported:
            self.IP6CONFIG_PROPERTIES.append((NM.SETTING_IP6_CONFIG_RA_TIMEOUT, int))
        else:
            syslog(LOG_WARNING, "'ra-timeout' setting not supported")

    def add_connection(self, new_connection: NM.SimpleConnection) -> bool:
        success = False
        callback_finished = False
        cancellable = Gio.Cancellable()
        lock = Lock()

        def connection_added_callback(source_object, res, user_data):
            nonlocal callback_finished
            nonlocal success
            nonlocal lock
            callback_finished = False
            success = False

            with lock:
                try:
                    # Finish the asynchronous operation (source_object is the client and the return
                    # type of add_connection_finish() is NM.RemoteConnection on success or None on
                    # failure)
                    with NetworkStatusHelper.get_lock():
                        success = source_object.add_connection_finish(res) is not None
                except Exception as e:
                    syslog(LOG_ERR, f"Could not finish adding new connection: {str(e)}")
                    success = False

                callback_finished = True

        try:
            with NetworkStatusHelper.get_lock():
                GLib.idle_add(
                    self.client.add_connection_async,
                    new_connection,
                    True,
                    cancellable,
                    connection_added_callback,
                    None,
                )
            start = time.time()
            while True:
                with lock:
                    if callback_finished:
                        break
                if time.time() - start > self.ADD_CONNECTION_TIMEOUT_S:
                    cancellable.cancel()
                    raise Exception("timeout")
                time.sleep(0.1)
        except Exception as e:
            syslog(LOG_ERR, f"Error adding connection: {str(e)}")
            success = False

        return success

    def delete_connection(self, connection_to_delete: NM.RemoteConnection) -> bool:
        success = False
        callback_finished = False
        cancellable = Gio.Cancellable()
        lock = Lock()

        def connection_deleted_callback(source_object, res, user_data):
            nonlocal callback_finished
            nonlocal success
            nonlocal lock
            callback_finished = False
            success = False

            with lock:
                try:
                    # Finish the asynchronous operation (source_object is an NM.RemoteConnection and
                    # the return type of delete_finish() is bool)
                    success = source_object.delete_finish(res)
                except Exception as e:
                    syslog(
                        LOG_ERR, f"Could not finish deleting the connection: {str(e)}"
                    )
                    success = False

                callback_finished = True

        try:
            GLib.idle_add(
                connection_to_delete.delete_async,
                cancellable,
                connection_deleted_callback,
                None,
            )
            start = time.time()
            while True:
                with lock:
                    if callback_finished:
                        break
                if time.time() - start > self.DELETE_CONNECTION_TIMEOUT_S:
                    cancellable.cancel()
                    raise Exception("timeout")
                time.sleep(0.1)
        except Exception as e:
            syslog(LOG_ERR, f"Error deleting connection: {str(e)}")
            success = False

        return success

    def activate_connection(
        self, connection: NM.Connection, dev: Optional[NM.Device] = None
    ) -> bool:
        success = False
        callback_finished = False
        cancellable = Gio.Cancellable()
        lock = Lock()

        def connection_activated_callback(source_object, res, user_data):
            nonlocal callback_finished
            nonlocal success
            callback_finished = False
            success = False
            nonlocal lock

            with lock:
                try:
                    # Finish the asynchronous operation (source_object is the client and the return
                    # type of activate_connection_finish() is NM.ActiveConnection on success or None
                    # on failure)
                    with NetworkStatusHelper.get_lock():
                        success = (
                            source_object.activate_connection_finish(res) is not None
                        )
                except Exception as e:
                    syslog(LOG_ERR, f"Could not finish activating connection: {str(e)}")
                    success = False

                callback_finished = True

        try:
            with NetworkStatusHelper.get_lock():
                GLib.idle_add(
                    self.client.activate_connection_async,
                    connection,
                    dev,
                    "/",
                    cancellable,
                    connection_activated_callback,
                    None,
                )
            start = time.time()
            while True:
                with lock:
                    if callback_finished:
                        break
                if time.time() - start > self.ACTIVATE_CONNECTION_TIMEOUT_S:
                    cancellable.cancel()
                    raise Exception("timeout")
                time.sleep(0.1)
        except Exception as e:
            syslog(LOG_ERR, f"Error activating connection: {str(e)}")
            success = False

        return success

    def get_connection_from_uuid(self, uuid):
        connections = NetworkStatusHelper._client.get_connections()
        connections = dict([(x.get_uuid(), x) for x in connections])
        try:
            conn = connections[uuid]
        except Exception as e:
            syslog(LOG_ERR, f"Could not find connection by UUID: {str(e)}")
            conn = None
        return conn

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self):

        result = {"SDCERR": 1, "InfoMsg": "unable to set connection"}
        try:
            uuid = cherrypy.request.json.get("uuid", None)
            if not uuid:
                result["InfoMsg"] = "Missing UUID"
                return result

            conn = self.get_connection_from_uuid(uuid)
            if conn is None:
                result["InfoMsg"] = "UUID not found"
                return result

            if (
                cherrypy.request.json["activate"] == 1
                or cherrypy.request.json["activate"] == "1"
            ):
                connection_setting_connection = conn.get_setting_connection()
                if connection_setting_connection is None:
                    result["InfoMsg"] = "Unable to read connection settings"
                    return result
                if connection_setting_connection.get_property("type") == "bridge":
                    if self.activate_connection(conn, None):
                        result["SDCERR"] = 0
                        result["InfoMsg"] = "Bridge activated"
                else:
                    interface_name = connection_setting_connection.get_interface_name()
                    with NetworkStatusHelper.get_lock():
                        all_devices = self.client.get_all_devices()
                    for dev in all_devices:
                        if dev.get_iface() == interface_name:
                            if self.activate_connection(conn, dev):
                                result["SDCERR"] = 0
                                result["InfoMsg"] = "Connection Activated"
                                break
            else:
                with NetworkStatusHelper.get_lock():
                    active_connections = self.client.get_active_connections()
                for conn in active_connections:
                    if uuid == conn.get_uuid():
                        if self.client.deactivate_connection(conn, None):
                            result["SDCERR"] = 0
                            result["InfoMsg"] = "Connection Deactivated"
                        else:
                            result["InfoMsg"] = "Unable to deactivate connection"
                        return result
                result["SDCERR"] = 0
                result["InfoMsg"] = "Already inactive. No action taken"
        except Exception as e:
            syslog(LOG_ERR, f"exception during NetworkConnection PUT: {e}")
            result["InfoMsg"] = f"Internal error - exception from NetworkManager: {e}"
        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        def get_variant(data: Any) -> GLib.Variant:
            """
            Builds a GLib.Variant from the given data.
            Based on:
            https://gitlab.gnome.org/nE0sIghT/gnome-browser-connector/-/blob/master/gnome_browser_connector/helpers.py#L8
            """
            if isinstance(data, str):
                return GLib.Variant.new_string(data)
            elif isinstance(data, int):
                return GLib.Variant.new_int32(data)
            elif isinstance(data, bytearray):
                return GLib.Variant.new_from_bytes(
                    GLib.VariantType.new("ay"), GLib.Bytes.new(list(data)), True
                )
            elif isinstance(data, (list, tuple, set)):
                if len(data) > 0 and isinstance(data[0], str):
                    variant_builder: GLib.VariantBuilder = GLib.VariantBuilder.new(
                        GLib.VariantType.new("as")
                    )

                    for value in data:
                        variant_builder.add_value(GLib.Variant.new_string(str(value)))
                else:
                    variant_builder: GLib.VariantBuilder = GLib.VariantBuilder.new(
                        GLib.VariantType.new("av")
                    )

                    for value in data:
                        variant_builder.add_value(
                            GLib.Variant.new_variant(get_variant(value))
                        )

                return variant_builder.end()
            elif isinstance(data, dict):
                variant_builder = GLib.VariantBuilder.new(GLib.VariantType.new("a{sv}"))

                for key in data:
                    if data[key] is None:
                        continue

                    key_string = str(key)

                    variant_builder.add_value(
                        GLib.Variant.new_dict_entry(
                            get_variant(key_string),
                            GLib.Variant.new_variant(get_variant(data[key])),
                        )
                    )

                return variant_builder.end()
            else:
                raise Exception(f"Unknown data type: {type(data)}")

        def build_connection_from_json(
            connection_json: dict, t_uuid: str = ""
        ) -> Tuple[NM.SimpleConnection, str]:
            """
            Build an NM connection (NM.SimpleConnection) from the given JSON object
            """

            try:
                if not connection_json.get(NM.SETTING_CONNECTION_SETTING_NAME):
                    return (None, "Invalid parameters")

                variant_builder = GLib.VariantBuilder.new(
                    GLib.VariantType.new("a{sa{sv}}")
                )

                # Build the 'Connection' section
                # Name constant:    NM.SETTING_CONNECTION_SETTING_NAME
                # Constant value:   connection
                if not connection_json[NM.SETTING_CONNECTION_SETTING_NAME].get(
                    NM.SETTING_CONNECTION_UUID
                ):
                    connection_json[NM.SETTING_CONNECTION_SETTING_NAME][
                        NM.SETTING_CONNECTION_UUID
                    ] = t_uuid

                # Remove the UUID if it's empty for compatibility with libnm
                if (
                    connection_json[NM.SETTING_CONNECTION_SETTING_NAME][
                        NM.SETTING_CONNECTION_UUID
                    ]
                    == ""
                ):
                    del connection_json[NM.SETTING_CONNECTION_SETTING_NAME][
                        NM.SETTING_CONNECTION_UUID
                    ]

                variant_builder.add_value(
                    GLib.Variant.new_dict_entry(
                        GLib.Variant.new_string(
                            str(NM.SETTING_CONNECTION_SETTING_NAME)
                        ),
                        get_variant(
                            connection_json[NM.SETTING_CONNECTION_SETTING_NAME]
                        ),
                    )
                )

                # Build the 'Wireless' section
                # Name constant:    NM.SETTING_WIRELESS_SETTING_NAME
                # Constant value:   802-11-wireless
                if connection_json.get(NM.SETTING_WIRELESS_SETTING_NAME):
                    if not connection_json[NM.SETTING_WIRELESS_SETTING_NAME].get(
                        NM.SETTING_WIRELESS_SSID
                    ):
                        syslog(LOG_ERR, "SSID required for Wi-Fi connection")
                        variant_builder.end()
                        return (None, "SSID required for Wi-Fi connection")
                    try:
                        connection_json[NM.SETTING_WIRELESS_SETTING_NAME][
                            NM.SETTING_WIRELESS_SSID
                        ] = bytearray(
                            str(
                                connection_json[NM.SETTING_WIRELESS_SETTING_NAME][
                                    NM.SETTING_WIRELESS_SSID
                                ]
                            ),
                            "utf-8",
                        )
                    except Exception as e:
                        syslog(LOG_ERR, f"Invalid SSID: {str(e)}")
                        variant_builder.end()
                        return (None, "Invalid SSID")

                    # if 'mode' is not provided, assume 'infrastructure'
                    if not connection_json[NM.SETTING_WIRELESS_SETTING_NAME].get(
                        NM.SETTING_WIRELESS_MODE, None
                    ):
                        connection_json[NM.SETTING_WIRELESS_SETTING_NAME][
                            NM.SETTING_WIRELESS_MODE
                        ] = NM.SETTING_WIRELESS_MODE_INFRA

                    variant_builder.add_value(
                        GLib.Variant.new_dict_entry(
                            GLib.Variant.new_string(
                                str(NM.SETTING_WIRELESS_SETTING_NAME)
                            ),
                            get_variant(
                                connection_json[NM.SETTING_WIRELESS_SETTING_NAME]
                            ),
                        )
                    )

                    # Build the 'Wireless Security' section
                    # Name constant:    NM.SETTING_WIRELESS_SECURITY_SETTING_NAME
                    # Constant value:   802-11-wireless-security
                    if connection_json.get(NM.SETTING_WIRELESS_SECURITY_SETTING_NAME):
                        # libnm expects some 802-11-wireless-security properties to be an array of strings
                        for property in [
                            "pairwise",
                            "group",
                            "proto",
                        ]:
                            if connection_json["802-11-wireless-security"].get(
                                property
                            ):
                                if not isinstance(
                                    connection_json["802-11-wireless-security"][
                                        property
                                    ],
                                    list,
                                ):
                                    connection_json["802-11-wireless-security"][
                                        property
                                    ] = [
                                        str(
                                            connection_json["802-11-wireless-security"][
                                                property
                                            ]
                                        )
                                    ]

                        variant_builder.add_value(
                            GLib.Variant.new_dict_entry(
                                GLib.Variant.new_string(
                                    str(NM.SETTING_WIRELESS_SECURITY_SETTING_NAME)
                                ),
                                get_variant(
                                    connection_json[
                                        NM.SETTING_WIRELESS_SECURITY_SETTING_NAME
                                    ]
                                ),
                            )
                        )

                        # Build the '802-1x' section
                        # Name constant:    NM.SETTING_802_1X_SETTING_NAME
                        # Constant value:   802-1x
                        if connection_json.get(NM.SETTING_802_1X_SETTING_NAME):
                            # libnm expects some 802-1x properties to be an array of strings
                            for property in [
                                "eap",
                                "phase2-auth",
                                "phase2-autheap",
                                "altsubject-matches",
                                "phase2-altsubject-matches",
                            ]:
                                if connection_json["802-1x"].get(property):
                                    if not isinstance(
                                        connection_json["802-1x"][property], list
                                    ):
                                        connection_json["802-1x"][property] = [
                                            str(connection_json["802-1x"][property])
                                        ]

                            for cert in self.SUPPORTED_8021X_CERTS:
                                if connection_json["802-1x"].get(cert):
                                    connection_json["802-1x"][
                                        cert
                                    ] = convert_cert_to_nm_path_scheme(
                                        connection_json["802-1x"][cert]
                                    )

                            if connection_json["802-1x"].get("pac-file"):
                                # pac-file parameter provided, prepend path to certs
                                connection_json["802-1x"]["pac-file"] = str(
                                    "{0}{1}".format(
                                        definition.FILEDIR_DICT.get("pac"),
                                        connection_json["802-1x"]["pac-file"],
                                    ),
                                )

                            variant_builder.add_value(
                                GLib.Variant.new_dict_entry(
                                    GLib.Variant.new_string(
                                        str(NM.SETTING_802_1X_SETTING_NAME)
                                    ),
                                    get_variant(
                                        connection_json[NM.SETTING_802_1X_SETTING_NAME]
                                    ),
                                )
                            )

                # Build the 'GSM' section
                # Name constant:    NM.SETTING_GSM_SETTING_NAME
                # Constant value:   gsm
                if connection_json.get(NM.SETTING_GSM_SETTING_NAME):
                    variant_builder.add_value(
                        GLib.Variant.new_dict_entry(
                            GLib.Variant.new_string(str(NM.SETTING_GSM_SETTING_NAME)),
                            get_variant(connection_json[NM.SETTING_GSM_SETTING_NAME]),
                        )
                    )

                new_connection = NM.SimpleConnection.new_from_dbus(
                    variant_builder.end()
                )

                # Due to the complexity of the IPv4/v6 sections, it is simpler to add these
                # properties explicitly (i.e., do not attempt to convert them to D-Bus-compatible
                # GLib variants).

                # Build the 'IPv4' section
                # Name constant:    NM.SETTING_IP4_CONFIG_SETTING_NAME
                # Constant value:   ipv4
                if connection_json.get(NM.SETTING_IP4_CONFIG_SETTING_NAME):
                    # Check for the presence of possibly unsupported settings
                    if (
                        connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            "dhcp-hostname-flags"
                        )
                        and not self.nm_ip_config_dhcp_hostname_flags_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-hostname-flags' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            "dhcp-iaid"
                        )
                        and not self.nm_ip_config_dhcp_iaid_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-iaid' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            "dhcp-reject-servers"
                        )
                        and not self.nm_ip_config_dhcp_reject_servers_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-reject-servers' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            "dhcp-vendor-class-identifier"
                        )
                        and not self.nm_ip4_config_dhcp_vendor_class_identifier_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-vendor-class-identifier' setting not supported",
                        )

                    setting_ipv4 = NM.SettingIP4Config.new()

                    if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                        "address-data"
                    ):
                        # Found the 'address-data' property - this isn't technically the proper
                        # property name to use here (should be 'addresses'), but this is what was
                        # used in the past, so we need to support it.
                        for address in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ]["address-data"]:
                            setting_ipv4.add_address(
                                NM.IPAddress.new(
                                    AF_INET,
                                    str(address["address"]),
                                    int(address["prefix"]),
                                )
                            )

                    if (
                        self.nm_ip_config_dhcp_reject_servers_supported
                        and connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            NM.SETTING_IP_CONFIG_DHCP_REJECT_SERVERS
                        )
                    ):
                        for dhcp_reject_server in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DHCP_REJECT_SERVERS]:
                            setting_ipv4.add_dhcp_reject_server(str(dhcp_reject_server))

                    if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS
                    ):
                        for dns_entry in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS]:
                            setting_ipv4.add_dns(str(dns_entry))

                    if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS_OPTIONS
                    ):
                        for dns_option in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS_OPTIONS]:
                            setting_ipv4.add_dns_option(str(dns_option))

                    if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS_SEARCH
                    ):
                        for dns_search in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS_SEARCH]:
                            setting_ipv4.add_dns_search(str(dns_search))

                    if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_ROUTES
                    ):
                        for route in connection_json[
                            NM.SETTING_IP4_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_ROUTES]:
                            setting_ipv4.add_route(
                                NM.IPAddress.new(
                                    AF_INET,
                                    str(route["dest"]),
                                    int(route["prefix"]),
                                    str(route["next_hop"])
                                    if route.get("next_hop")
                                    else None,
                                    int(route["metric"]) if route.get("metric") else -1,
                                )
                            )

                    # Loop through SettingIPConfig and SettingIP4Config properties and apply them,
                    # if present
                    for property in (
                        self.IPCONFIG_PROPERTIES + self.IP4CONFIG_PROPERTIES
                    ):
                        if connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME].get(
                            property[0]
                        ):
                            setting_ipv4.set_property(
                                property[0],
                                property[1](
                                    connection_json[NM.SETTING_IP4_CONFIG_SETTING_NAME][
                                        property[0]
                                    ]
                                ),
                            )

                    new_connection.add_setting(setting_ipv4)

                # Build the 'IPv6' section
                # Name constant:    NM.SETTING_IP6_CONFIG_SETTING_NAME
                # Constant value:   ipv6
                if connection_json.get(NM.SETTING_IP6_CONFIG_SETTING_NAME):
                    # Check for the presence of possibly unsupported settings
                    if (
                        connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            "dhcp-hostname-flags"
                        )
                        and not self.nm_ip_config_dhcp_hostname_flags_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-hostname-flags' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            "dhcp-iaid"
                        )
                        and not self.nm_ip_config_dhcp_iaid_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-iaid' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            "dhcp-reject-servers"
                        )
                        and not self.nm_ip_config_dhcp_reject_servers_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'dhcp-reject-servers' setting not supported",
                        )
                    if (
                        connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            "ra-timeout"
                        )
                        and not self.nm_ip6_config_ra_timeout_supported
                    ):
                        return (
                            None,
                            "Invalid configuration, 'ra-timeout' setting not supported",
                        )

                    setting_ipv6 = NM.SettingIP6Config.new()

                    if connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                        "address-data"
                    ):
                        # Found the 'address-data' property - this isn't technically the proper
                        # property name to use here (should be 'addresses'), but this is what was
                        # used in the past, so we need to support it.
                        for address in connection_json[
                            NM.SETTING_IP6_CONFIG_SETTING_NAME
                        ]["address-data"]:
                            setting_ipv6.add_address(
                                NM.IPAddress.new(
                                    AF_INET6,
                                    str(address["address"]),
                                    int(address["prefix"]),
                                )
                            )

                    if (
                        self.nm_ip_config_dhcp_reject_servers_supported
                        and connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            NM.SETTING_IP_CONFIG_DHCP_REJECT_SERVERS
                        )
                    ):
                        for dhcp_reject_server in connection_json[
                            NM.SETTING_IP6_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DHCP_REJECT_SERVERS]:
                            setting_ipv6.add_dhcp_reject_server(str(dhcp_reject_server))

                    if connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS
                    ):
                        for dns_entry in connection_json[
                            NM.SETTING_IP6_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS]:
                            setting_ipv6.add_dns(str(dns_entry))

                    if connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS_OPTIONS
                    ):
                        for dns_option in connection_json[
                            NM.SETTING_IP6_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS_OPTIONS]:
                            setting_ipv6.add_dns_option(str(dns_option))

                    if connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                        NM.SETTING_IP_CONFIG_DNS_SEARCH
                    ):
                        for dns_search in connection_json[
                            NM.SETTING_IP6_CONFIG_SETTING_NAME
                        ][NM.SETTING_IP_CONFIG_DNS_SEARCH]:
                            setting_ipv6.add_dns_search(str(dns_search))

                    # Loop through SettingIPConfig and SettingIP6Config properties and apply them,
                    # if present
                    for property in (
                        self.IPCONFIG_PROPERTIES + self.IP6CONFIG_PROPERTIES
                    ):
                        if connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME].get(
                            property[0]
                        ):
                            setting_ipv6.set_property(
                                property[0],
                                property[1](
                                    connection_json[NM.SETTING_IP6_CONFIG_SETTING_NAME][
                                        property[0]
                                    ]
                                ),
                            )

                    new_connection.add_setting(setting_ipv6)

                return (new_connection, "")
            except Exception as e:
                syslog(
                    LOG_ERR,
                    f"Could not build connection from the given parameters: {str(e)}",
                )
                return (None, str(e))

        def remove_empty_lists(dictionary: dict) -> dict:
            """
            Recursively walks through the given dictionary, removes any key/value pairs whose
            value is an empty list, and returns a new copy without the empty lists.
            """
            new_dictionary = {}
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    new_dictionary[key] = remove_empty_lists(value)
                else:
                    if isinstance(value, list) and len(value) == 0:
                        continue
                    new_dictionary[key] = value

            return new_dictionary

        def convert_cert_to_nm_path_scheme(cert_name: str) -> bytearray:
            """
            For certain certs, NM supports specifying the path to the cert prefixed with "file://"
            and NUL terminated
            """
            return bytearray(
                str(
                    "file://{0}{1}\x00".format(
                        definition.FILEDIR_DICT.get("cert"), cert_name
                    )
                ),
                "utf-8",
            )

        result = {"SDCERR": 1, "InfoMsg": ""}

        post_data = cherrypy.request.json
        if not post_data.get("connection"):
            result["InfoMsg"] = "Missing connection section"
            return result

        t_uuid = post_data["connection"].get("uuid", None)
        id = post_data["connection"].get("id", None)

        if not id:
            result["InfoMsg"] = "connection section must have an id element"
            return result

        with NetworkStatusHelper.get_lock():
            nm_connection_objs = self.client.get_connections()
        connections = dict([(x.get_id(), x) for x in nm_connection_objs])
        if id in connections:
            con_uuid = connections.get(id).get_uuid()
            if t_uuid and con_uuid:
                if not con_uuid == t_uuid:
                    result["InfoMsg"] = "Provided uuid does not match uuid of given id"
                    return result
            t_uuid = con_uuid

        connections = dict([(x.get_uuid(), x) for x in nm_connection_objs])

        try:
            if not post_data.get("connection"):
                result["InfoMsg"] = "Invalid parameters"
                return result

            existing_connection = (
                connections.get(post_data.get("connection")["uuid"], None)
                if post_data.get("connection").get("uuid")
                else None
            )

            (new_connection, error_msg) = build_connection_from_json(
                remove_empty_lists(post_data), t_uuid
            )
            if not new_connection:
                result["InfoMsg"] = f"Unable to create connection: {error_msg}"
                return result

            name = post_data["connection"].get("id", "")
            if existing_connection:
                # Connection already exists, delete it
                saved_profile = NM.SimpleConnection.new_clone(existing_connection)

                if self.delete_connection(existing_connection):
                    # Successfully removed the existing connection, now add the new one
                    if self.add_connection(new_connection):
                        # Connection updated successfully
                        result["InfoMsg"] = f"connection {name} updated"
                        result["SDCERR"] = 0
                        return result
                    else:
                        # Could not add new connnection, restore existing connection
                        syslog(
                            LOG_ERR,
                            "An error occurred trying to save config, restoring original",
                        )
                        if self.add_connection(saved_profile):
                            result[
                                "InfoMsg"
                            ] = "An error occurred trying to save config: Original config restored"
                        else:
                            # Could not restore existing connection
                            syslog(LOG_ERR, "Unable to restore origin config")
                            result[
                                "InfoMsg"
                            ] = "An error occurred trying to save config: Unable to restore original config"
                else:
                    # Could not remove the existing connection
                    syslog(LOG_ERR, f"Could not update connection {name}")
                    result["InfoMsg"] = f"Could not update connection {name}"
            else:
                if self.add_connection(new_connection):
                    result["InfoMsg"] = f"connection {name} created"
                    result["SDCERR"] = 0
                    return result
                else:
                    result["InfoMsg"] = "Unable to create connection"

        except Exception as e:
            syslog(LOG_ERR, f"Connection POST experienced an exception: {str(e)}")
            result["InfoMsg"] = f"Connection POST experienced an exception: {str(e)}"

        return result

    @cherrypy.tools.json_out()
    def DELETE(self, uuid):
        result = {"SDCERR": 1, "InfoMsg": ""}
        try:
            with NetworkStatusHelper.get_lock():
                connection = self.client.get_connection_by_uuid(str(uuid))
            if connection is not None:
                if self.delete_connection(connection):
                    result["InfoMsg"] = "Connection deleted"
                    result["SDCERR"] = 0
                    return result
                else:
                    result["InfoMsg"] = "Unable to delete connection"
            else:
                result["InfoMsg"] = "Unable to delete connection, not found"
        except Exception as e:
            syslog(LOG_ERR, f"Unable to delete connection : {str(e)}")
            result["InfoMsg"] = "Unable to delete connection"

        return result

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        def cert_to_filename(cert):
            """
            Return base name only.
            """
            if cert:
                return cert[len(definition.FILEDIR_DICT["cert"]) :]

        result = {"SDCERR": 1, "InfoMsg": ""}
        try:
            uuid = kwargs.get("uuid", None)
            if not uuid:
                result["InfoMsg"] = "no UUID provided"
                return result

            extended_test = -1
            try:
                extended = kwargs.get("extended", None)
                if extended is not None:
                    extended = extended.lower()
                    if extended in ("y", "yes", "t", "true", "on", "1"):
                        extended_test = 1
                        extended = True
                    elif extended in ("n", "no", "f", "false", "off", "0"):
                        extended_test = 0
                        extended = False
                    if extended_test < 0:
                        raise ValueError("illegal value passed in")
                else:
                    # Default to 'non-extended' mode when 'extended' parameter is omitted
                    extended = False
            except Exception:
                result["SDCERR"] = definition.WEBLCM_ERRORS.get("SDCERR_FAIL")
                result["InfoMsg"] = (
                    "Unable to get extended connection info. Supplied extended parameter '%s' invalid."
                    % kwargs.get("extended")
                )
                return result

            if extended:
                try:
                    (
                        ret,
                        msg,
                        settings,
                    ) = NetworkStatusHelper.get_extended_connection_settings(uuid)

                    if ret < 0:
                        result["InfoMsg"] = msg
                    else:
                        result["connection"] = settings
                        result["SDCERR"] = ret
                except Exception as e_extended:
                    syslog(
                        LOG_ERR,
                        f"Unable to retrieve extended connection settings: {str(e_extended)}",
                    )
                    result[
                        "InfoMsg"
                    ] = "Unable to retrieve extended connecting settings"

                return result
            else:
                with NetworkStatusHelper.get_lock():
                    connections = self.client.get_connections()
                connections = dict([(x.get_uuid(), x) for x in connections])
                settings = (
                    connections[uuid]
                    .to_dbus(NM.ConnectionSerializationFlags.NO_SECRETS)
                    .unpack()
                )
                if settings.get("802-11-wireless"):
                    # Convert SSID to a string
                    settings["802-11-wireless"]["ssid"] = bytearray(
                        settings["802-11-wireless"]["ssid"]
                    ).decode("utf-8")
                if settings.get("802-1x"):
                    settings["802-1x"]["ca-cert"] = cert_to_filename(
                        settings["802-1x"].get("ca-cert")
                    )
                    settings["802-1x"]["client-cert"] = cert_to_filename(
                        settings["802-1x"].get("client-cert")
                    )
                    settings["802-1x"]["private-key"] = cert_to_filename(
                        settings["802-1x"].get("private-key")
                    )
                    settings["802-1x"]["phase2-ca-cert"] = cert_to_filename(
                        settings["802-1x"].get("phase2-ca-cert")
                    )
                    settings["802-1x"]["phase2-client-cert"] = cert_to_filename(
                        settings["802-1x"].get("phase2-client-cert")
                    )
                    settings["802-1x"]["phase2-private-key"] = cert_to_filename(
                        settings["802-1x"].get("phase2-private-key")
                    )
            result["connection"] = settings
            result["SDCERR"] = 0
        except Exception as e:
            syslog(LOG_ERR, f"Invalid UUID: {str(e)}")
            result["InfoMsg"] = "Invalid UUID"

        return result


@cherrypy.expose
class NetworkAccessPoints(object):
    SCAN_REQUEST_TIMEOUT_S: int = 10

    def __init__(self):
        self.client = NetworkStatusHelper.get_client()

    def request_scan(self, dev: NM.Device) -> bool:
        success = False
        callback_finished = False
        cancellable = Gio.Cancellable()
        lock = Lock()

        def scan_requested_callback(source_object, res, user_data):
            nonlocal callback_finished
            nonlocal success
            nonlocal lock
            callback_finished = False
            success = False

            with lock:
                try:
                    # Finish the asynchronous operation (source_object is an NM.DeviceWifi and the
                    # return type of request_scan_finish() is bool)
                    success = source_object.request_scan_finish(res)
                except Exception as e:
                    syslog(LOG_ERR, f"Could not finish requesting scan: {str(e)}")
                    success = False

                callback_finished = True

        try:
            GLib.idle_add(
                dev.request_scan_async, cancellable, scan_requested_callback, None
            )
            start = time.time()
            while True:
                with lock:
                    if callback_finished:
                        break
                if time.time() - start > self.SCAN_REQUEST_TIMEOUT_S:
                    cancellable.cancel()
                    raise Exception("timeout")
                time.sleep(0.1)
        except Exception as e:
            syslog(LOG_ERR, f"Error requesting scan: {str(e)}")
            success = False

        return success

    @cherrypy.tools.json_out()
    def PUT(self):
        """
        Start a manual scan
        """
        result = {"SDCERR": 1, "InfoMsg": ""}

        try:
            with NetworkStatusHelper.get_lock():
                all_devices = self.client.get_all_devices()
            for dev in all_devices:
                if dev.get_device_type() == NM.DeviceType.WIFI:
                    if self.request_scan(dev):
                        result["SDCERR"] = 0
                        result["InfoMsg"] = "Scan complete"
                    else:
                        result["InfoMsg"] = "Could not request scan"
                    break
        except Exception as e:
            result["InfoMsg"] = f"Unable to start scan request: {str(e)}"

        return result

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        """Get Cached AP list"""

        result = {
            "SDCERR": 1,
            "InfoMsg": "",
            "count": 0,
            "accesspoints": [],
        }

        try:
            with NetworkStatusHelper.get_lock():
                all_devices = self.client.get_all_devices()
            for dev in all_devices:
                if dev.get_device_type() == NM.DeviceType.WIFI:
                    for ap in dev.get_access_points():
                        security_string = ""
                        keymgmt = "none"
                        if (
                            (ap.get_flags() & getattr(NM, "80211ApFlags").PRIVACY)
                            and (
                                ap.get_wpa_flags()
                                == getattr(NM, "80211ApSecurityFlags").NONE
                            )
                            and (
                                ap.get_rsn_flags()
                                == getattr(NM, "80211ApSecurityFlags").NONE
                            )
                        ):
                            security_string = security_string + "WEP "
                            keymgmt = "static"

                        if (
                            ap.get_wpa_flags()
                            != getattr(NM, "80211ApSecurityFlags").NONE
                        ):
                            security_string = security_string + "WPA1 "

                        if (
                            ap.get_rsn_flags()
                            != getattr(NM, "80211ApSecurityFlags").NONE
                        ):
                            security_string = security_string + "WPA2 "

                        if (
                            ap.get_wpa_flags()
                            & getattr(NM, "80211ApSecurityFlags").KEY_MGMT_802_1X
                        ) or (
                            ap.get_rsn_flags()
                            & getattr(NM, "80211ApSecurityFlags").KEY_MGMT_802_1X
                        ):
                            security_string = security_string + "802.1X "
                            keymgmt = "wpa-eap"

                        if (
                            ap.get_wpa_flags()
                            & getattr(NM, "80211ApSecurityFlags").KEY_MGMT_PSK
                        ) or (
                            ap.get_rsn_flags()
                            & getattr(NM, "80211ApSecurityFlags").KEY_MGMT_PSK
                        ):
                            security_string = security_string + "PSK"
                            keymgmt = "wpa-psk"

                        ssid = ap.get_ssid()
                        ap_data = {
                            "SSID": ssid.get_data().decode("utf-8")
                            if ssid is not None
                            else "",
                            "HwAddress": ap.get_bssid(),
                            "Strength": ap.get_strength(),
                            "MaxBitrate": ap.get_max_bitrate(),
                            "Frequency": ap.get_frequency(),
                            "Flags": int(ap.get_flags()),
                            "WpaFlags": int(ap.get_wpa_flags()),
                            "RsnFlags": int(ap.get_rsn_flags()),
                            "LastSeen": int(ap.get_last_seen()),
                            "Security": security_string,
                            "Keymgmt": keymgmt,
                        }
                        result["accesspoints"].append(ap_data)

                    if len(result["accesspoints"]) > 0:
                        result["SDCERR"] = 0
                        result["count"] = len(result["accesspoints"])
                    else:
                        result["InfoMsg"] = "No access points found"

        except Exception as e:
            result["InfoMsg"] = "Unable to get access point list"
            syslog(f"NetworkAccessPoints GET exception: {e}")

        return result


@cherrypy.expose
class Version(object):

    _version = {}

    def get_u_boot_version(self) -> str:
        """
        Read and return the U-Boot 'version' environment variable
        """
        try:
            return (
                subprocess.check_output("fw_printenv -n version", shell=True)
                .decode("ascii")
                .strip()
                .strip('"')
            )
        except Exception:
            return ""

    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        try:
            if not Version._version:
                _client = NetworkStatusHelper.get_client()
                with NetworkStatusHelper.get_lock():
                    Version._version["SDCERR"] = definition.WEBLCM_ERRORS[
                        "SDCERR_SUCCESS"
                    ]
                    Version._version["InfoMsg"] = ""
                    Version._version["nm_version"] = str(_client.get_version())
                    Version._version[
                        "weblcm_python_webapp"
                    ] = definition.WEBLCM_PYTHON_VERSION
                    Version._version["build"] = (
                        subprocess.check_output(
                            "sed -n 's/^VERSION=//p' /etc/os-release", shell=True
                        )
                        .decode("ascii")
                        .strip()
                        .strip('"')
                    )
                    Version._version["supplicant"] = (
                        subprocess.check_output(["sdcsupp", "-v"])
                        .decode("ascii")
                        .rstrip()
                    )
                    Version._version["radio_stack"] = str(
                        _client.get_version()
                    ).partition("-")[0]
                    for dev in _client.get_all_devices():
                        if dev.get_device_type() == NM.DeviceType.WIFI:
                            Version._version["driver"] = dev.get_driver()
                            Version._version[
                                "kernel_vermagic"
                            ] = dev.get_driver_version()
                            break
                    Version._version["bluez"] = (
                        Bluetooth.get_bluez_version()
                        if Bluetooth is not None
                        else "n/a"
                    )
                    Version._version["u-boot"] = self.get_u_boot_version()
        except Exception as e:
            Version._version = {
                "SDCERR": definition.WEBLCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": f"An exception occurred while trying to get versioning info: {e}",
            }
        return Version._version


@cherrypy.expose
class NetworkInterfaces(object):
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):

        result = {
            "SDCERR": 1,
            "InfoMsg": "",
        }
        interfaces = []

        try:
            managed_devices = (
                cherrypy.request.app.config["weblcm"]
                .get("managed_software_devices", "")
                .split()
            )
            unmanaged_devices = (
                cherrypy.request.app.config["weblcm"]
                .get("unmanaged_hardware_devices", "")
                .split()
            )
            with NetworkStatusHelper.get_lock():
                all_devices = NetworkStatusHelper.get_client().get_all_devices()
            for dev in all_devices:
                # Don't return connections with unmanaged interfaces
                if dev.get_state() == NM.DeviceState.UNMANAGED:
                    continue
                if dev.get_iface() in unmanaged_devices:
                    continue
                interfaces.append(dev.get_iface())

            if os.path.exists(definition.MODEM_ENABLE_FILE):
                for dev in managed_devices:
                    if dev not in interfaces:
                        interfaces.append(dev)

            result["SDCERR"] = 0
            result["interfaces"] = interfaces
        except Exception as e:
            result["InfoMsg"] = "Exception getting list of interfaces"
            syslog(f"NetworkInterfaces GET exception: {e}")

        return result

    """
            Add virtual interface
    """

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        result = {"SDCERR": 1, "InfoMsg": ""}

        post_data = cherrypy.request.json
        if not post_data.get("interface"):
            result["InfoMsg"] = "Missing interface section"
            return result
        interface = post_data.get("interface")
        if not post_data.get("type"):
            result["InfoMsg"] = "Missing type section"
            return result
        int_type = post_data.get("type")
        if int_type == "STA":
            int_type = "managed"

        if interface != "wlan1":
            result[
                "InfoMsg"
            ] = f"Invalid interface {interface}. Supported interface wlan1"
            return result

        if int_type != "managed":
            result["InfoMsg"] = f"Invalid type {int_type}. Supported type: STA"
            return result

        """
            Currently only support wlan1/managed
        """
        result["InfoMsg"] = f"Unable to add virtual interface {interface}."
        try:
            proc = run(
                ["iw", "dev", "wlan0", "interface", "add", interface, "type", int_type],
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                result["SDCERR"] = 0
                result["InfoMsg"] = f"Virtual interface {interface} added"
        except TimeoutExpired:
            syslog(
                LOG_ERR,
                f"Call 'iw dev wlan0 interface add {interface} type {int_type}' timeout",
            )
        except Exception as e:
            syslog(
                LOG_ERR,
                f"Call 'iw dev wlan0 interface add {interface} type {int_type}' failed: {str(e)}",
            )

        return result

    @cherrypy.tools.json_out()
    def DELETE(self, interface):
        result = {"SDCERR": 1, "InfoMsg": f"Unable to remove interface {interface}"}

        if interface != "wlan1":
            return result

        try:
            proc = run(
                ["iw", "dev", interface, "del"],
                timeout=SystemSettingsManage.get_user_callback_timeout(),
            )
            if not proc.returncode:
                result["SDCERR"] = 0
                result["InfoMsg"] = f"Virtual interface {interface} removed"
        except TimeoutExpired:
            syslog(LOG_ERR, f"Call 'iw dev {interface} del' timeout")
        except Exception as e:
            syslog(LOG_ERR, f"Call 'iw dev {interface} del' failed: {str(e)}")

        return result


@cherrypy.expose
class NetworkInterface(object):
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):

        result = {"SDCERR": 1, "InfoMsg": ""}
        try:
            name = kwargs.get("name", None)
            if not name:
                result["InfoMsg"] = "no interface name provided"
                return result

            unmanaged_devices = (
                cherrypy.request.app.config["weblcm"]
                .get("unmanaged_hardware_devices", "")
                .split()
            )
            if name in unmanaged_devices:
                result["InfoMsg"] = "invalid interface name provided"
                return result

            with NetworkStatusHelper.get_lock():
                devices = NetworkStatusHelper.get_client().get_all_devices()
            for dev in devices:
                if name == dev.get_iface():
                    # Read all NM device properties
                    dev_properties = {}
                    dev_properties["udi"] = dev.get_udi()
                    dev_properties["path"] = dev.get_path()
                    dev_properties["interface"] = dev.get_iface()
                    dev_properties["ip_interface"] = dev.get_ip_iface()
                    dev_properties["driver"] = dev.get_driver()
                    dev_properties["driver_version"] = dev.get_driver_version()
                    dev_properties["firmware_version"] = dev.get_firmware_version()
                    dev_properties["capabilities"] = int(dev.get_capabilities())
                    dev_properties["state_reason"] = int(dev.get_state_reason())
                    dev_properties[
                        "connection_active"
                    ] = NetworkStatusHelper.get_active_connection(dev)
                    dev_properties[
                        "ip4config"
                    ] = NetworkStatusHelper.get_ipconfig_properties(
                        dev.get_ip4_config()
                    )
                    dev_properties[
                        "ip6config"
                    ] = NetworkStatusHelper.get_ipconfig_properties(
                        dev.get_ip6_config()
                    )
                    dev_properties[
                        "dhcp4config"
                    ] = NetworkStatusHelper.get_dhcp_config_properties(
                        dev.get_dhcp4_config()
                    )
                    dev_properties[
                        "dhcp6config"
                    ] = NetworkStatusHelper.get_dhcp_config_properties(
                        dev.get_dhcp6_config()
                    )
                    dev_properties["managed"] = bool(dev.get_managed())
                    dev_properties["autoconnect"] = bool(dev.get_autoconnect())
                    dev_properties["firmware_missing"] = bool(
                        dev.get_firmware_missing()
                    )
                    dev_properties["nm_plugin_missing"] = bool(
                        dev.get_nm_plugin_missing()
                    )
                    dev_properties["status"] = NetworkStatusHelper.get_dev_status(dev)
                    dev_properties[
                        "available_connections"
                    ] = NetworkStatusHelper.get_available_connections(
                        dev.get_available_connections()
                    )
                    dev_properties["physical_port_id"] = dev.get_physical_port_id()
                    dev_properties["metered"] = int(dev.get_metered())
                    dev_properties["metered_text"] = definition.WEBLCM_METERED_TEXT.get(
                        int(dev.get_metered())
                    )
                    lldp_neighbors = []
                    for neighbor in dev.get_lldp_neighbors():
                        attrs = {}
                        for attr_name in neighbor.get_attr_names():
                            attrs[attr_name] = str(neighbor.get_attr_value(attr_name))
                        lldp_neighbors.append(attrs)
                    dev_properties["lldp_neighbors"] = lldp_neighbors
                    dev_properties["real"] = dev.is_real()
                    dev_properties["ip4connectivity"] = int(
                        dev.get_connectivity(int(AF_INET))
                    )
                    dev_properties[
                        "ip4connectivity_text"
                    ] = definition.WEBLCM_CONNECTIVITY_STATE_TEXT.get(
                        int(dev.get_connectivity(int(AF_INET)))
                    )
                    dev_properties["ip6connectivity"] = int(
                        dev.get_connectivity(int(AF_INET6))
                    )
                    dev_properties[
                        "ip6connectivity_text"
                    ] = definition.WEBLCM_CONNECTIVITY_STATE_TEXT.get(
                        int(dev.get_connectivity(int(AF_INET6)))
                    )
                    dev_properties["interface_flags"] = int(dev.get_interface_flags())

                    # Get wired specific items
                    if dev.get_device_type() == NM.DeviceType.ETHERNET:
                        dev_properties[
                            "wired"
                        ] = NetworkStatusHelper.get_wired_properties(dev)

                    # Get Wi-Fi specific items
                    if dev.get_device_type() == NM.DeviceType.WIFI:
                        dev_properties[
                            "wireless"
                        ] = NetworkStatusHelper.get_wifi_properties(dev)
                        if dev.get_state() == NM.DeviceState.ACTIVATED:
                            dev_properties[
                                "activeaccesspoint"
                            ] = NetworkStatusHelper.get_ap_properties(dev)

                    result["properties"] = dev_properties
                    result["SDCERR"] = 0

                    return result

            # Target interface wasn't found, so throw an error
            result["InfoMsg"] = "invalid interface name provided"

        except Exception as e:
            syslog(
                LOG_ERR,
                f"Unable to retrieve detailed network interface configuration: {str(e)}",
            )

        return result


@cherrypy.expose
class NetworkInterfaceStatistics(object):
    @cherrypy.tools.json_out()
    def GET(self, *args, **kwargs):
        """
        Retrieve receive/transmit statistics for the requested interface
        """

        result = {
            "SDCERR": 1,
            "InfoMsg": "",
            "statistics": {
                "rx_bytes": -1,
                "rx_packets": -1,
                "rx_errors": -1,
                "rx_dropped": -1,
                "multicast": -1,
                "tx_bytes": -1,
                "tx_packets": -1,
                "tx_errors": -1,
                "tx_dropped": -1,
            },
        }

        try:
            name = kwargs.get("name", None)
            if not name:
                result["InfoMsg"] = "No interface name provided"
                return result

            path_to_stats_dir = f"/sys/class/net/{name}/statistics"
            stats = {
                "rx_bytes": f"{path_to_stats_dir}/rx_bytes",
                "rx_packets": f"{path_to_stats_dir}/rx_packets",
                "rx_errors": f"{path_to_stats_dir}/rx_errors",
                "rx_dropped": f"{path_to_stats_dir}/rx_dropped",
                "multicast": f"{path_to_stats_dir}/multicast",
                "tx_bytes": f"{path_to_stats_dir}/tx_bytes",
                "tx_packets": f"{path_to_stats_dir}/tx_packets",
                "tx_errors": f"{path_to_stats_dir}/tx_errors",
                "tx_dropped": f"{path_to_stats_dir}/tx_dropped",
            }
            outputstats = {}
            for key in stats:
                with open(stats[key]) as f:
                    output = int(f.readline().strip())
                    outputstats[key] = output

            result["SDCERR"] = 0
            result["statistics"] = outputstats
            return result
        except FileNotFoundError as e:
            syslog(f"Invalid interface name - {str(e)}")
            result["InfoMsg"] = f"Invalid interface name - {str(e)}"
            return result
        except Exception as e:
            result["InfoMsg"] = f"Could not read interface statistics - {str(e)}"
            return result


@cherrypy.expose
class WifiEnable(object):
    _client = NetworkStatusHelper.get_client()

    @cherrypy.tools.json_out()
    def GET(self):

        result = {"SDCERR": definition.WEBLCM_ERRORS.get("SDCERR_SUCCESS")}

        with NetworkStatusHelper.get_lock():
            result["wifi_radio_software_enabled"] = self._client.wireless_get_enabled()
            result[
                "wifi_radio_hardware_enabled"
            ] = self._client.wireless_hardware_get_enabled()

        result["InfoMsg"] = "wifi enable results"

        return result

    @cherrypy.tools.accept(media="application/json")
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs):
        result = {}
        enable_test = -1
        try:
            enable = kwargs.get("enable")
            enable = enable.lower()
            if enable in ("y", "yes", "t", "true", "on", "1"):
                enable_test = 1
            elif enable in ("n", "no", "f", "false", "off", "0"):
                enable_test = 0
            if enable_test < 0:
                raise ValueError("illegal value passed in")
        except Exception:
            result["SDCERR"] = definition.WEBLCM_ERRORS.get("SDCERR_FAIL")
            result["InfoMsg"] = (
                "unable to set wireless_set_enable. Supplied enable parameter '%s' invalid."
                % kwargs.get("enable")
            )

            return result

        with NetworkStatusHelper.get_lock():
            self._client.wireless_set_enabled(enable_test)
        result["SDCERR"] = definition.WEBLCM_ERRORS.get("SDCERR_SUCCESS")
        result["InfoMsg"] = "wireless_radio_software_enabled: %s" % (
            "true" if enable else "false"
        )
        with NetworkStatusHelper.get_lock():
            result["wifi_radio_software_enabled"] = self._client.wireless_get_enabled()
        return result
