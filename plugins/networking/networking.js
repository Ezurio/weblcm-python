// Copyright (c) 2018, Laird Connectivity
// Contact: support@lairdconnect.com

function networkingAUTORUN(retry){

  $(document).on("click", "#networking_status_mini_menu, #networking_status_main_menu", function(){
    clickStatusPage();
  });

  $(document).on("click", "#networking_connections_mini_menu, #networking_connections_main_menu", function(){
    clickConnectionsPage();
  });

  $(document).on("click", "#networking_edit_mini_menu, #networking_edit_main_menu", function(){
    clickEditConnectionPage();
  });

  $(document).on("click", "#networking_scan_mini_menu, #networking_scan_main_menu", function(){
    clickScanPage();
  });

  $(document).on("click", "#networking_version_mini_menu, #networking_version_main_menu", function(){
    clickVersionPage();
  });

  $(document).on("click", "#bt-connection-activate", function(){
    activateConnection();
  });

  $(document).on("click", "#bt-connection-edit", function(){
    selectedConnection();
  });

  $(document).on("click", "#bt-connection-delete", function(){
    removeConnection();
  });

  $(document).on("change", "#connectionSelect", function(){
    onChangeConnections();
  });

  $(document).on("click", "#goToConnection", function(){
    addScanConnection();
  });

  $(document).on("click", "#bt-manual-scan", function(){
    requestScan();
  });

  $(document).on("click", "#addNewConnection", function(){
    addConnection();
  });

  $(document).on("change", "#connection-type", function(){
    onChangeConnectionType();
  });

  $(document).on("change", "#ipv4-method", function(){
    onChangeIpv4Method();
  });

  $(document).on("change", "#ipv6-method", function(){
    onChangeIpv6Method();
  });

  $(document).on("change", "#radio-mode", function(){
    onChangeRadioMode();
  });

  $(document).on("change", "#key-mgmt", function(){
    onChangeKeymgmt();
  });

  $(document).on("change", "#eap-method", function(){
    onChangeEap();
  });

  $(document).on("change", "#phase2-auth", function(){
    onChangePhase2NoneEap();
  });

  $(document).on("change", "#phase2-autheap", function(){
    onChangePhase2Eap();
  });

  clickStatusPage();
}

const NMDeviceState = {
  NM_DEVICE_STATE_UNKNOWN:		0,
  NM_DEVICE_STATE_UNMANAGED:	10,
  NM_DEVICE_STATE_UNAVAILABLE:	20,
  NM_DEVICE_STATE_DISCONNECTED:	30,
  NM_DEVICE_STATE_PREPARE:		40,
  NM_DEVICE_STATE_CONFIG:		50,
  NM_DEVICE_STATE_NEED_AUTH:	60,
  NM_DEVICE_STATE_IP_CONFIG:	70,
  NM_DEVICE_STATE_IP_CHECK:		80,
  NM_DEVICE_STATE_SECONDARIES:	90,
  NM_DEVICE_STATE_ACTIVATED:	100,
  NM_DEVICE_STATE_DEACTIVATING:	110,
  NM_DEVICE_STATE_FAILED:		120,
};

function CARDSTATEtoString(state) {
  switch(state) {
    case NMDeviceState.NM_DEVICE_STATE_UNKNOWN:
      return i18nData['Unknown'];
    case NMDeviceState.NM_DEVICE_STATE_UNMANAGED:
      return i18nData['Unmanaged'];
    case NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE:
      return i18nData['Unavailable'];
    case NMDeviceState.NM_DEVICE_STATE_DISCONNECTED:
      return i18nData['Disconnected'];
    case NMDeviceState.NM_DEVICE_STATE_PREPARE:
      return i18nData['Preparing'];
    case NMDeviceState.NM_DEVICE_STATE_CONFIG:
      return i18nData['Connecting'];
    case NMDeviceState.NM_DEVICE_STATE_NEED_AUTH:
      return i18nData['Need Auth'];
    case NMDeviceState.NM_DEVICE_STATE_IP_CONFIG:
      return i18nData['Requesting IP'];
    case NMDeviceState.NM_DEVICE_STATE_IP_CHECK:
      return i18nData['IP Check'];
    case NMDeviceState.NM_DEVICE_STATE_SECONDARIES:
      return i18nData['Secondaries'];
    case NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
      return i18nData['Activated'];
    case NMDeviceState.NM_DEVICE_STATE_DEACTIVATING:
      return i18nData['Deactivating'];
    case NMDeviceState.NM_DEVICE_STATE_FAILED:
      return i18nData['Failed'];
    default:
      return i18nData['Unknown State'];
  }
}

const NMDeviceType = {
  NM_DEVICE_TYPE_UNKNOWN:		0,
  NM_DEVICE_TYPE_ETHERNET:		1,
  NM_DEVICE_TYPE_WIFI:			2,
  NM_DEVICE_TYPE_UNUSED1:		3,
  NM_DEVICE_TYPE_UNUSED2:		4,
  NM_DEVICE_TYPE_BT:			5,
  NM_DEVICE_TYPE_OLPC_MESH:		6,
  NM_DEVICE_TYPE_WIMAX:			7,
  NM_DEVICE_TYPE_MODEM:			8,
  NM_DEVICE_TYPE_INFINIBAND:	9,
  NM_DEVICE_TYPE_BOND:			10,
  NM_DEVICE_TYPE_VLAN:			11,
  NM_DEVICE_TYPE_ADSL:			12,
  NM_DEVICE_TYPE_BRIDGE:		13,
  NM_DEVICE_TYPE_GENERIC:		14,
  NM_DEVICE_TYPE_TEAM:			15,
  NM_DEVICE_TYPE_TUN:			16,
  NM_DEVICE_TYPE_IP_TUNNEL:		17,
  NM_DEVICE_TYPE_MACVLAN:		18,
  NM_DEVICE_TYPE_VXLAN:			19,
  NM_DEVICE_TYPE_VETH:			20,
  NM_DEVICE_TYPE_MACSEC:		21,
  NM_DEVICE_TYPE_DUMMY:			22,
  NM_DEVICE_TYPE_PPP:			23,
  NM_DEVICE_TYPE_OVS_INTERFACE:	24,
  NM_DEVICE_TYPE_OVS_PORT:		25,
  NM_DEVICE_TYPE_OVS_BRIDGE:	26,
  NM_DEVICE_TYPE_WPAN:			27,
  NM_DEVICE_TYPE_6LOWPAN:		28,
  NM_DEVICE_TYPE_WIREGUARD:		29,
  NM_DEVICE_TYPE_WIFI_P2P:		30,
};

function DeviceTypetoString(type) {
  switch(type) {
    case NMDeviceType.NM_DEVICE_TYPE_UNKNOWN:
      return "Unknown";
    case NMDeviceType.NM_DEVICE_TYPE_ETHERNET:
      return "Ethernet";
    case NMDeviceType.NM_DEVICE_TYPE_WIFI:
      return "WiFi";
    case NMDeviceType.NM_DEVICE_TYPE_UNUSED1:
      return "Unused 1";
    case NMDeviceType.NM_DEVICE_TYPE_UNUSED2:
      return "Unused 2";
    case NMDeviceType.NM_DEVICE_TYPE_BT:
      return "Bluetooth";
    case NMDeviceType.NM_DEVICE_TYPE_OLPC_MESH:
      return "OLPC Mesh";
    case NMDeviceType.NM_DEVICE_TYPE_WIMAX:
      return "WiMAX";
    case NMDeviceType.NM_DEVICE_TYPE_MODEM:
      return "Modem";
    case NMDeviceType.NM_DEVICE_TYPE_INFINIBAND:
      return "Infiniband";
    case NMDeviceType.NM_DEVICE_TYPE_BOND:
      return "Bond";
    case NMDeviceType.NM_DEVICE_TYPE_VLAN:
      return "VLAN";
    case NMDeviceType.NM_DEVICE_TYPE_ADSL:
      return "ADSL";
    case NMDeviceType.NM_DEVICE_TYPE_BRIDGE:
      return "Bridge";
    case NMDeviceType.NM_DEVICE_TYPE_GENERIC:
      return "Generic";
    case NMDeviceType.NM_DEVICE_TYPE_TEAM:
      return "Team";
    case NMDeviceType.NM_DEVICE_TYPE_TUN:
      return "Tunnel";
    case NMDeviceType.NM_DEVICE_TYPE_IP_TUNNEL:
      return "IP Tunnel";
    case NMDeviceType.NM_DEVICE_TYPE_MACVLAN:
      return "MAC VLAN";
    case NMDeviceType.NM_DEVICE_TYPE_VXLAN:
      return "VXLAN";
    case NMDeviceType.NM_DEVICE_TYPE_VETH:
      return "Virtual Ethernet";
    case NMDeviceType.NM_DEVICE_TYPE_MACSEC:
      return "MACSEC";
    case NMDeviceType.NM_DEVICE_TYPE_DUMMY:
      return "Dummy";
    case NMDeviceType.NM_DEVICE_TYPE_PPP:
      return "PPP";
    case NMDeviceType.NM_DEVICE_TYPE_OVS_INTERFACE:
      return "OVS Interface";
    case NMDeviceType.NM_DEVICE_TYPE_OVS_PORT:
      return "OVS Port";
    case NMDeviceType.NM_DEVICE_TYPE_OVS_BRIDGE:
      return "OVS Bridge";
    case NMDeviceType.NM_DEVICE_TYPE_WPAN:
      return "WPAN";
    case NMDeviceType.NM_DEVICE_TYPE_6LOWPAN:
      return "6LOWPAN";
    case NMDeviceType.NM_DEVICE_TYPE_WIREGUARD:
      return "Wire Guard";
    case NMDeviceType.NM_DEVICE_TYPE_WIFI_P2P:
      return "WiFi P2P";
    default:
      return "Unknown Type";
  }
}

function onChangeConnectionType(){

  $("#connection-wired-settings").addClass("d-none");
  $("#connection-wifi-settings").addClass("d-none");
  $("#connection-ppp-settings").addClass("d-none");
  $("#connection-modem-settings").addClass("d-none");
  $("#connection-wifi-p2p-settings").addClass("d-none");
  $("#connection-bridge-settings").addClass("d-none");
  $("#connection-bluetooth-settings").addClass("d-none");

  var ctype = $("#connection-type").val();
  switch(ctype){
    case "802-3-ethernet":
      $("#connection-wired-settings").removeClass("d-none");
      break;
    case "802-11-wireless":
      $("#connection-wifi-settings").removeClass("d-none");
      break;
    case "ppp":
      $("#connection-ppp-settings").removeClass("d-none");
      break;
    case "modem":
      $("#connection-modem-settings").removeClass("d-none");
      break;
    case "bluetooth":
      $("#connection-bluetooth-settings").removeClass("d-none");
      break;
    case "wifi-p2p":
      $("#connection-wifi-p2p-settings").removeClass("d-none");
      break;
    case "bridge":
      $("#connection-bridge-settings").removeClass("d-none");
      break;
    default:
      break;
  }
}

function clear8021xCredsDisplay(){

  $("#eap-method-display").addClass("d-none");
  $("#eap-method").val("peap");

  $("#eap-auth-timeout-display").addClass("d-none");
  $("#eap-auth-timeout").val("0");

  $("#eap-identity-display").addClass("d-none");
  $("#eap-identity").val("");

  $("#eap-password-display").addClass("d-none");
  $("#eap-password").val("");

  $("#eap-anonymous-identity-display").addClass("d-none");
  $("#eap-anonymous-identity").val("");

  $("#pac-file-display").addClass("d-none");
  $("#pac-file").val("");

  $("#pac-file-password-display").addClass("d-none");
  $("#pac-file-password").val("");

  $("#phase1-fast-provisioning-display").addClass("d-none");
  $("#phase1-fast-provisioning").val("0");

  $("#ca-cert-display").addClass("d-none");
  $("#ca-cert").val("");

  $("#ca-cert-password-display").addClass("d-none");
  $("#ca-cert-password").val("");

  $("#client-cert-display").addClass("d-none");
  $("#client-cert").val("");

  $("#client-cert-password-display").addClass("d-none");
  $("#client-cert-password").val("");

  $("#private-key-display").addClass("d-none");
  $("#private-key").val("");

  $("#private-key-password-display").addClass("d-none");
  $("#private-key-password").val();

  $("#phase2-auth-display").addClass("d-none");
  $("#phase2-auth").val("none");

  $("#phase2-autheap-display").addClass("d-none");
  $("#phase2-autheap").val("none");

  $("#phase2-ca-cert-display").addClass("d-none");
  $("#phase2-ca-cert").val("");

  $("#phase2-ca-cert-password-display").addClass("d-none");
  $("#phase2-ca-cert-password").val("");

  $("#phase2-client-cert-display").addClass("d-none");
  $("#phase2-client-cert").val("");

  $("#phase2-client-cert-password-display").addClass("d-none");
  $("#phase2-client-cert-password").val("");

  $("#phase2-private-key-display").addClass("d-none");
  $("#phase2-private-key").val("");

  $("#phase2-private-key-password-display").addClass("d-none");
  $("#phase2-private-key-password-display").val("");

  $("#tls-disable-time-checks-display").addClass("d-none");
  $("#tls-disable-time-checks").val("1");
}

function clearWifiSecurityCredsDisplay() {

  $("#auth-alg-display").addClass("d-none");
  $("#auth-alg").val("open");

  $("#wep-tx-keyidx-display").addClass("d-none");
  $("#wep-tx-keyidx").val("0");

  $("#wep-key-display").addClass("d-none");
  $("#wep-tx-key0").val("");
  $("#wep-tx-key1").val("");
  $("#wep-tx-key2").val("");
  $("#wep-tx-key3").val("");

  $("#psk-display").addClass("d-none");
  $("#psk").val("");

  $("#leap-username-display").addClass("d-none");
  $("#leap-username").val("");

  $("#leap-password-display").addClass("d-none");
  $("#leap-password").val("");
}

function parseSettingData(data, name, dVal){
  if(data && data.hasOwnProperty(name))
    return data[name];
  return dVal;
}

function resetPhase2AuthSetting(wxs, method, disabled) {
  $("#"+disabled).val(parseSettingData(wxs, disabled, "none"));

  var auth = $("#"+method).val();
  if (-1 !== auth.indexOf("tls")) {
    $("#phase2-ca-cert-display").removeClass("d-none");
    $("#phase2-ca-cert").val(parseSettingData(wxs, "phase2-ca-cert", ""));
    $("#phase2-ca-cert-password-display").removeClass("d-none");
    $("#phase2-ca-cert-password").val("");
    $("#phase2-client-cert-display").removeClass("d-none");
    $("#phase2-client-cert").val(parseSettingData(wxs, "phase2-client-cert", ""));
    $("#phase2-client-cert-password-display").removeClass("d-none");
    $("#phase2-client-cert-password").val("");
    $("#phase2-private-key-display").removeClass("d-none");
    $("#phase2-private-key").val(parseSettingData(wxs, "phase2-private-key", ""));
    $("#phase2-private-key-password-display").removeClass("d-none");
    $("#phase2-private-key-password").val("");
  }
  else
  {
    $("#phase2-ca-cert-display").addClass("d-none");
    $("#phase2-ca-cert").val("");

    $("#phase2-ca-cert-password-display").addClass("d-none");
    $("#phase2-ca-cert-password").val("");

    $("#phase2-client-cert-display").addClass("d-none");
    $("#phase2-client-cert").val("");

    $("#phase2-client-cert-password-display").addClass("d-none");
    $("#phase2-client-cert-password").val("");

    $("#phase2-private-key-display").addClass("d-none");
    $("#phase2-private-key").val("");

    $("#phase2-private-key-password-display").addClass("d-none");
    $("#phase2-private-key-password").val("");
  }
}

function onChangePhase2NoneEap() {
  resetPhase2AuthSetting(null, "phase2-auth", "phase2-autheap");
}

function onChangePhase2Eap() {
  resetPhase2AuthSetting(null, "phase2-autheap", "phase2-auth");
}

function resetEapSetting(wxs){

  $("#ca-cert-display").addClass("d-none");
  $("#ca-cert").val();
  $("#ca-cert-password-display").addClass("d-none");
  $("#ca-cert-password").val();
  $("#client-cert-display").addClass("d-none");
  $("#client-cert").val();
  $("#client-cert-password-display").addClass("d-none");
  $("#client-cert-password").val();
  $("#private-key-display").addClass("d-none");
  $("#private-key").val();
  $("#private-key-password-display").addClass("d-none");
  $("#tls-disable-time-checks-display").addClass("d-none");
  $("#tls-disable-time-checks").val();

  $("#pac-file-display").addClass("d-none");
  $("#pac-file").val();
  $("#pac-file-password-display").addClass("d-none");
  $("#phase1-fast-provisioning-display").addClass("d-none");
  $("#phase1-fast-provisioning").val();

  var eap = $("#eap-method").val();
  switch(eap){
    case "fast":
      $("#pac-file-display").removeClass("d-none");
      $("#pac-file").val(parseSettingData(wxs, "pac-file", ""));
      $("#pac-file-password-display").removeClass("d-none");
      $("#phase1-fast-provisioning-display").removeClass("d-none");
      $("#phase1-fast-provisioning").val(parseSettingData(wxs, "phase1-fast-provisioning", "0"));
      break;
    case "tls":
    case "ttls":
    case "peap":
      $("#ca-cert-display").removeClass("d-none");
      $("#ca-cert").val(parseSettingData(wxs, "ca-cert", ""));
      $("#ca-cert-password-display").removeClass("d-none");
      $("#client-cert-display").removeClass("d-none");
      $("#client-cert").val(parseSettingData(wxs, "client-cert", ""));
      $("#client-cert-password-display").removeClass("d-none");
      $("#private-key-display").removeClass("d-none");
      $("#private-key").val(parseSettingData(wxs, "private-key", ""));
      $("#private-key-password-display").removeClass("d-none");
      $("#tls-disable-time-checks-display").removeClass("d-none");
      $("#tls-disable-time-checks").val(parseSettingData(wxs, "tls-disable-time-checks", "1"));
      break;
    default:
      break;
  }
}

function onChangeEap() {
  resetEapSetting();
}

function resetWirelessSecuritySettings(wss, wxs){
  clear8021xCredsDisplay();
  clearWifiSecurityCredsDisplay();

  var keymgmt = $("#key-mgmt").val();
  switch (keymgmt){
    case "none":
      break;
   case "static":
      $("#auth-alg-display").removeClass("d-none");
      $("#auth-alg").val(parseSettingData(wss, "auth-alg", "open"));
      $("#wep-tx-keyidx-display").removeClass("d-none");
      $("#wep-tx-keyidx").val(parseSettingData(wss, "wep-tx-keyidx", "0"));
      $("#wep-key-display").removeClass("d-none")
      break;
    case "ieee8021x":
      $("#leap-username-display").removeClass("d-none");
      $("#leap-password-display").removeClass("d-none");
      $("#auth-alg").val("leap");
      $("#leap-username").val(parseSettingData(wss, "leap-username", ""));
      break;
    case "wpa-psk":
      $("#psk-display").removeClass("d-none");
      $("#psk").val(parseSettingData(wss, "psk", ""));
      break;
    case "wpa-eap":
      $("#eap-method-display").removeClass("d-none");
      $("#eap-method").val(parseSettingData(wxs, "eap", "peap"));
      resetEapSetting(wxs)
      $("#eap-auth-timeout-display").removeClass("d-none");
      $("#eap-auth-timeout").val(parseSettingData(wxs, "auth-timeout", 0).toString());
      $("#eap-identity-display").removeClass("d-none");
      $("#eap-identity").val(parseSettingData(wxs, "identity", "").toString());
      $("#eap-password-display").removeClass("d-none");
      $("#eap-anonymous-identity-display").removeClass("d-none");
      $("#eap-anonymous-identity").val(parseSettingData(wxs, "anonymous-identity", ""));
      $("#phase2-autheap-display").removeClass("d-none");
      autheap = parseSettingData(wxs, "phase2-autheap", "none");
      $("#phase2-autheap").val(autheap.split(" "));
      $("#phase2-auth-display").removeClass("d-none");
      auth = parseSettingData(wxs, "phase2-auth", "none");
      $("#phase2-auth").val(auth.split(" "));
      break;
    default:
      break;
  }
}

function onChangeKeymgmt(){
  resetWirelessSecuritySettings();
}

var statusUpdateTimerId;
function setIntervalUpdate(functionName, timeout, arg){
  statusUpdateTimerId = setTimeout(functionName, timeout, arg)
}

function updateStatus(){
  $.ajax({
    url: "networkStatus",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function( data ) {
    let card_id_prefix = "network-status-accordion-";
    if($("#network-status-accordion").length > 0){
      $("#updateProgressDisplay").addClass("d-none");
      for (interfaceName in data.status){
        let button, card_id;

        card_id = card_id_prefix + interfaceName;
        // Add new cards if they dont exist
        if($("#" + card_id).attr("id") == null){
          $("#network-status-accordion-root").clone().attr("id", card_id).appendTo("#network-status-accordion");
        }
        $("#" + card_id).removeClass("d-none");

        //Set card-header attributes
        $("#" + card_id + " > .card-header").attr("id", card_id + "-header");
        $("#" + card_id + " > .card-header").attr("data-target", "#" + card_id + "-body");

        $("#" + card_id + " >.card-header >.interface").text(interfaceName);

        // Device Type
        $("#" + card_id + " >.card-header >.devicetype").text(DeviceTypetoString(data.status[interfaceName].status.DeviceType));

        // State
        $("#" + card_id + " >.card-header >.state").text(CARDSTATEtoString(data.status[interfaceName].status.State));

        //Set card-body attributes
        $("#" + card_id + " >.collapse").attr("id", card_id + "-body");
        $("#" + card_id + " >.collapse").attr("aria-labelledby", card_id + "-header");

        // Active Connection
        connection_active = $("#" + card_id + "-body" + " >.card-body >.connection-active");
        if (data.status[interfaceName].connection_active){
          connection_active.removeClass("d-none");
          // ID
          connection_active.children(".id").text("ID: " + data.status[interfaceName].connection_active.id);
          // UUID
          connection_active.children(".uuid").text("UUID: " + data.status[interfaceName].connection_active.uuid);
        } else {
          connection_active.addClass("d-none");
        }

        // IPv4
        ipv4 = $("#" + card_id + "-body" + " >.card-body >.ip4config");
        if (data.status[interfaceName].ip4config){
          ipv4.removeClass("d-none");
          // IPv4 Address
          ipv4.children(".address").text(i18nData['IPv4 Address'] + ": " + data.status[interfaceName].ip4config.Addresses[0]);
          // IPv4 Gateway
          ipv4.children(".gateway").text(i18nData['IPv4 Gateway'] + ": " + data.status[interfaceName].ip4config.Gateway);
        } else {
          ipv4.addClass("d-none");
        }

        // IPv6
        ipv6 = $("#" + card_id + "-body" + " >.card-body >.ip6config");
        if (data.status[interfaceName].ip6config){
        // Add entries and Display IPv6 addresses
          if (data.status[interfaceName].ip6config.Addresses){
            if (data.status[interfaceName].ip6config.Addresses[0])
              ipv6.children(".address").text(i18nData['IPv6 Address'] + ": " + data.status[interfaceName].ip6config.Addresses[0]);
            else
              ipv6.children(".address").text(i18nData['IPv6 Address'] + ":");
            if (data.status[interfaceName].ip6config.Addresses[1])
              ipv6.children(".address-2").text(i18nData['IPv6 Address'] + " 2: "  + data.status[interfaceName].ip6config.Addresses[1]);
            else
              ipv6.children(".address-2").text(i18nData['IPv6 Address'] + " 2:");
            if (data.status[interfaceName].ip6config.Addresses[2])
              ipv6.children(".address-3").text(i18nData['IPv6 Address'] + " 3: " + data.status[interfaceName].ip6config.Addresses[2]);
            else
              ipv6.children(".address-3").text(i18nData['IPv6 Address'] + " 3:" );
          }
          // IPv6 Gateway
          ipv6.children(".gateway").text(i18nData['IPv6 Gateway'] + data.status[interfaceName].ip6config.Gateway);
        } else {
          ipv6.addClass("d-none");
        }

        // Active Access Point
        activeaccesspoint = $("#" + card_id + "-body" + " >.card-body >.activeaccesspoint");
        if (data.status[interfaceName].activeaccesspoint){
          activeaccesspoint.removeClass("d-none");
          // SSID
          activeaccesspoint.children(".ssid").text("SSID: " + data.status[interfaceName].activeaccesspoint.Ssid);
          // BSSID
          activeaccesspoint.children(".bssid").text("BSSID:" + data.status[interfaceName].activeaccesspoint.HwAddress);
          // Frequency
          activeaccesspoint.children(".frequency").text(i18nData['Frequency'] + ": " + data.status[interfaceName].activeaccesspoint.Frequency + "MHz");
          // Signal Strength
          activeaccesspoint.children(".strength").text(i18nData['Signal Strength'] + ": " + data.status[interfaceName].activeaccesspoint.Strength + "%");
          // Progress Bar
          progress_bar = activeaccesspoint.children(".progress-bar");
          progress_bar.removeClass("d-none");
          progress_bar.removeClass("bg-danger bg-warning bg-success d-none");
          if (data.status[interfaceName].activeaccesspoint.Strength == 0){ //Not connected
            progress_bar.addClass("bg-danger");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else if (data.status[interfaceName].activeaccesspoint.Strength < 30){ //red
            progress_bar.addClass("bg-danger");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else if (data.status[interfaceName].activeaccesspoint.Strength < 50){ //yellow
            progress_bar.addClass("bg-warning");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else { //green
            progress_bar.addClass("bg-success");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          }
          progress_bar.text(data.status[interfaceName].activeaccesspoint.Strength);
        } else {
          activeaccesspoint.addClass("d-none");
        }

        // Wireless
        wireless = $("#" + card_id + "-body" + " >.card-body >.wireless");
        if (data.status[interfaceName].wireless){
          wireless.removeClass("d-none");
          // HW Address
          wireless.children(".hwaddress").text(i18nData['MAC Address'] + ": " + data.status[interfaceName].wireless.HwAddress);
          // Bit Rate
          wireless.children(".bitrate").text(i18nData['Bit Rate'] + ": " + data.status[interfaceName].wireless.Bitrate + "Kb/s");
        } else {
          wireless.addClass("d-none");
        }

        // Wired
        wired = $("#" + card_id + "-body" + " >.card-body >.wired");
        if (data.status[interfaceName].wired){
          wired.removeClass("d-none");
          // HW Address
          wired.children(".hwaddress").text(i18nData['MAC Address'] + ": " + data.status[interfaceName].wired.HwAddress);
          // Speed
          wired.children(".speed").text(i18nData['Speed'] + ": "  + data.status[interfaceName].wired.Speed + "Mbit/s");
        } else {
          wired.addClass("d-none");
        }
      }
      setIntervalUpdate(updateStatus, 10000);
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    clearTimeout(statusUpdateTimerId);
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickStatusPage() {

  $.ajax({
    url: "plugins/networking/html/status.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#networking_status_main_menu").addClass("active");
    $("#networking_status_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
    clearTimeout(statusUpdateTimerId);
    updateStatus();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function newConnection(id, ssid, key_mgmt) {

  $("#connection-uuid").val("");
  $("#connection-id").val(id);

  $("#interface-name option:first").attr('selected','selected');
  $("#connection-type option:first").attr('selected','selected');

  if(ssid){
    $("#interface-name option").each(function(){
      if(-1 != $(this).val().indexOf("wlan")){
        $(this).attr('selected', 'selected');
        $("#connection-type").val("802-11-wireless");
        $("#ssid").val(ssid);
        $("#key-mgmt").val(key_mgmt);
        $("#key-mgmt").change();
        return false
      }
    });
  }

  $("#connection-type").change();
}
function getWifiConnection(settings){

  $("#connection-uuid").val(parseSettingData(settings['connection'], "uuid", ""));
  $("#connection-id").val(parseSettingData(settings['connection'], "id", ""));
  $("#interface-name").val(parseSettingData(settings['connection'], "interface-name", ""));

  $("#connection-type").val("802-11-wireless");
  $("#connection-type").change();

  $("#ssid").val(parseSettingData(settings['802-11-wireless'], "ssid", ""));
  $("#client-name").val(parseSettingData(settings['802-11-wireless'], "client-name", ""));

  txpower = parseSettingData(settings['802-11-wireless'], "tx-power", 0);
  if (txpower == 0){
    $("#tx-power").val("Auto");
  }
  else {
    $("#tx-power").val(txpower.toString());
  }

  $("#radio-band").val(parseSettingData(settings['802-11-wireless'], "band", "default"));
  $("#radio-channel").val(parseSettingData(settings['802-11-wireless'], "channel", ""));
  $("#radio-bgscan").val(parseSettingData(settings['802-11-wireless'], "bgscan", ""));
  $("#frequency-list").val(parseSettingData(settings['802-11-wireless'], "frequency-list", ""));
  $("#frequency-dfs").val(parseSettingData(settings['802-11-wireless'], "frequency-dfs", 1));
  $("#radio-mode").val(parseSettingData(settings['802-11-wireless'], "mode", "infrastructure"));
  $("#radio-mode").change();
  $("#powersave").val(parseSettingData(settings['802-11-wireless'], "powersave", "0"));

  keymgmt = parseSettingData(settings['802-11-wireless-security'], "key-mgmt", "undefined");
  if(keymgmt == "undefined") {
    $("#key-mgmt").val("none");
  }
  else if(keymgmt == "none") {
    $("#key-mgmt").val("static");
  }
  else {
    $("#key-mgmt").val(keymgmt);
  }

  if(keymgmt != "undefined") {
    resetWirelessSecuritySettings(settings['802-11-wireless-security'], settings['802-1x']);
  }

  if(keymgmt == "wpa-eap") {
    resetEapSetting(settings['802-1x']);
    if ( $("#phase2-autheap").val() != "none"){
      resetPhase2AuthSetting(settings['802-1x'], "phase2-autheap", "phase2-auth");
    }
    else {
      resetPhase2AuthSetting(settings['802-1x'], "phase2-auth", "phase2-autheap");
    }
  }
}

function getEthernetConnection(settings) {

  $("#connection-uuid").val(parseSettingData(settings['connection'], "uuid", ""));
  $("#connection-id").val(parseSettingData(settings['connection'], "id", ""));
  $("#interface-name").val(parseSettingData(settings['connection'], "interface-name", ""));

  $("#connection-type").val("802-3-ethernet");
  $("#connection-type").change();
}

function getIpv4Settings(settings){

  let ipv4 = [];
  let addresses=[];

  $("#ipv4-method").val(parseSettingData(settings['ipv4'], "method", "auto"));
  $.when($("#ipv4-method").change()).done( function() {
    addresses = parseSettingData(settings['ipv4'], "address-data", "");
    for(let i=0; i<addresses.length; i++){
      ipv4.push(addresses[i].address + '/' + addresses[i].prefix.toString());
    }
    $("#ipv4-addresses").val(ipv4.join(','));

    $("#ipv4-gateway").val(parseSettingData(settings['ipv4'], "gateway", ""));
    $("#ipv4-dns").val(parseSettingData(settings['ipv4'], "dns", ""));
  });
}

function getIpv6Settings(settings){

  let ipv6 = [];
  let addresses = [];

  $("#ipv6-method").val(parseSettingData(settings['ipv6'], "method", "auto"));
  $.when($("#ipv6-method").change()).done( function() {
    addresses = parseSettingData(settings['ipv6'], "address-data", "");
    for(let i=0; i<addresses.length; i++){
      ipv6.push(addresses[i].address + '/' + addresses[i].prefix.toString());
    }
    $("#ipv6-addresses").val(ipv6.join(','));

    $("#ipv6-gateway").val(parseSettingData(settings['ipv6'], "gateway", ""));
    $("#ipv6-dns").val(parseSettingData(settings['ipv6'], "dns", ""));
  });
}

function updateGetConnectionPage(uuid, id, ssid, key_mgmt){
  if(uuid == null){
    newConnection(id, ssid, key_mgmt);
    return;
  }

  $.ajax({
    url: "connection?uuid="+uuid,
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function( msg ) {
    if($("#connection-settings-accordion").length > 0){
      if (msg.SDCERR == defines.SDCERR.SDCERR_SUCCESS){
        switch(msg.connection.connection.type){
          case "802-3-ethernet":
            getEthernetConnection(msg.connection);
            break;
          case "802-11-wireless":
            getWifiConnection(msg.connection);
            break;
          case "ppp":
          case "bluetooth":
          case "modem":
          case "wifi-p2p":
          case "bridge":
          default:
            break;
        }
        getIpv4Settings(msg.connection);
        getIpv6Settings(msg.connection);
      }
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function editConnection(uuid, id, ssid, key_mgmt) {
  $.ajax({
    url: "plugins/networking/html/addConnection.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#networking_edit_main_menu").addClass("active");
    $("#networking_edit_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();

    if(-1 == currUserPermission.indexOf("networking_ap_activate"))
      $("#radio-mode-display").addClass("d-none");

    $.when(getNetworkInterfaces(), getCerts()).done( function() {
      updateGetConnectionPage(uuid, id, ssid, key_mgmt);
    });
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function selectedConnection(){
  var uuid = $("#connectionSelect").val();
  editConnection(uuid, null, null, null);
}

function onChangeConnections(){
  var activated = $("#connectionSelect option:selected").attr("activated");
  if(activated == 1){
    $("#bt-connection-activate").attr("value", i18nData['Deactivate-connection']);
  }
  else {
    $("#bt-connection-activate").attr("value", i18nData['Activate-connection']);
  }
}

function updateConnectionsPage(){
  $.ajax({
    url: "connections",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function( msg ) {
    if($("#connectionSelect").length > 0){
      var sel = $("#connectionSelect");
      sel.empty();
      for (var UUID in msg.connections) {
        if ((msg.connections[UUID]["type"] == "ap") && (-1 == currUserPermission.indexOf("networking_ap_activate")))
          continue;
        var activated = msg.connections[UUID]["activated"];
        var name = msg.connections[UUID]["id"] + "(" + UUID + ")";
        var option = "<option value=" + UUID + " activated=" + activated + ">" + name + "</option>";
        sel.append(option);
      }
      onChangeConnections();
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function activateConnection(){
  var data = {
    activate: $("#connectionSelect option:selected").attr("activated") != 1,
    UUID: $("#connectionSelect").val(),
  }
  $.ajax({
    url: "connection",
    type: "PUT",
    data: JSON.stringify(data),
    contentType: "application/json",
  })
  .done(function( msg ) {
    SDCERRtoString(msg.SDCERR);
    updateConnectionsPage();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function removeConnection(){

  $.ajax({
    url: "connection?uuid="+$("#connectionSelect").val(),
    type: "DELETE",
    contentType: "application/json",
  })
  .done(function( msg ) {
    SDCERRtoString(msg.SDCERR);
    updateConnectionsPage();
  });
}

function clickConnectionsPage() {
  $.ajax({
    url: "plugins/networking/html/connections.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done( function( data ){
    $(".active").removeClass("active");
    $("#networking_connections_main_menu").addClass("active");
    $("#networking_connections_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();

    updateConnectionsPage();

    if ((-1 !== currUserPermission.indexOf("networking_activate")) || (-1 !== currUserPermission.indexOf("networking_ap_activate"))){
      $("#bt-connection-activate").prop("disabled", false);
    }
    if (-1 !== currUserPermission.indexOf("networking_edit")){
      $("#bt-connection-edit").prop("disabled", false);
    }
    if (-1 !== currUserPermission.indexOf("networking_delete")){
      $("#bt-connection-delete").prop("disabled", false);
    }

  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickEditConnectionPage() {
  editConnection(null, null, null, "none")
}

function prepareEthernetConnection() {

  con = {};
  settings = {};

  con['uuid'] = $("#connection-uuid").val();
  con['id'] = $("#connection-id").val();
  con['type'] = "802-3-ethernet";
  con['interface-name'] = $("#interface-name").val();

  return settings = {'connection': con};
}

function prepareWirelessConnection() {

  con = {};
  ws = {};
  wss = {};
  wxs = {}
  settings = {};

  con['uuid'] = $("#connection-uuid").val();
  con['id'] = $("#connection-id").val();
  con['type'] = "802-11-wireless";
  con['interface-name'] = $("#interface-name").val();

  v = $("#ssid").val().trim();
  if(!v)
    return settings;
  ws['ssid'] = v;

  v = $("#radio-mode").val();
  ws['mode'] = v;

  v = $("#client-name").val().trim();
  if(v)
    ws['client-name'] = v;

  v = parseInt($("#tx-power").val().trim()) || 0;
  if(v)
    ws['tx-power'] = v;

  v = $("#radio-band").val();
  if(v != "default")
    ws['band'] = v;

  v = $("#radio-channel").val().trim();
  if(v)
    ws['channel'] = parseInt(v);

  v = $("#radio-bgscan").val().trim();
  if(v)
    ws['bgscan'] = v;

  v = $("#frequency-list").val().trim();
  if(v)
    ws['frequency-list'] = v;

  v = $("#frequency-dfs").val();
  ws['frequency-dfs'] = parseInt(v);

  v = parseInt($("#powersave").val()) || 0;
  if(v)
    ws['powersave'] = v;

  keymgmt = $("#key-mgmt").val();
  if(keymgmt == "static") {
    wss['key-mgmt'] = "none";
    wss['auth-alg'] = $("#auth-alg").val();
  }
  else if(keymgmt == "ieee8021x") {
    wss['auth-alg'] = $("#auth-alg").val();
    wss['key-mgmt'] = "ieee8021x";
  }
  else if(keymgmt != "none") {
    wss['key-mgmt'] = keymgmt;
  }

  if(keymgmt == "static") {
    v = parseInt($("#wep-tx-keyidx").val());
    wss['wep-tx-keyidx'] = v;

    v = $("#wep-key0").val();
    if(v)
      wss['wep-key0'] = v;

    v = $("#wep-key1").val();
    if(v)
      wss['wep-key1'] = v;

    v = $("#wep-key2").val();
    if(v)
      wss['wep-key2'] = v;

    v = $("#wep-key3").val();
    if(v)
      wss['wep-key3'] = v;
  }
  else if(keymgmt == "ieee8021x") {
    v = $("#leap-username").val();
    if(v)
      wss['leap-username'] = v;

    v = $("#leap-password").val();
    if(v)
      wss['leap-password'] = v;
  }
  else if (keymgmt == "wpa-psk") {
    v = $("#psk").val();
    if(v)
      wss['psk'] = v;
  }
  else if (keymgmt == "wpa-eap") {
    wxs['eap'] = $("#eap-method").val();
    wxs['auth-timeout'] = parseInt($("#eap-auth-timeout").val()) || 0;
    wxs['tls-disable-time-checks'] = $("#tls-disable-time-checks").val();
    wxs['phase1-fast-provisioning'] = parseInt($("#phase1-fast-provisioning").val());

    v = $("#eap-identity").val();
    if(v)
      wxs['identity'] = v;

    v = $("#eap-anonymous-identity").val();
    if (v)
      wxs['anonymous-identity'] = v;

    v = $("#eap-password").val();
    if(v)
      wxs['password'] = v;

    v = $("#ca-cert").val();
    if(v)
      wxs['ca-cert'] = v;

    v = $("#ca-cert-password").val();
    if(v)
      wxs['ca-cert-password'] = v;

    v = $("#client-cert").val();
    if(v)
      wxs['client-cert'] = v;

    v = $("#client-cert-password").val();
    if(v)
      wxs['client-cert-password'] = v;

    v = $("#private-key").val();
    if(v)
      wxs['private-key'] = v;

    v = $("#private-key-password").val();
    if(v)
      wxs['private-key-password'] = v;

    v = $("#phase2-auth").val().join(" ");
    if(v != "none")
      wxs['phase2-auth'] = v;

    v = $("#phase2-autheap").val().join(" ");
    if(v != "none")
      wxs['phase2-autheap'] = v;

    v = $("#phase2-ca-cert").val();
    if(v)
      wxs['phase2-ca-cert'] = v;

    v = $("#phase2-ca-cert-password").val();
    if(v)
      wxs['phase2-ca-cert-password'] = v;

    v = $("#phase2-client-cert").val();
    if(v)
      wxs['phase2-client-cert'] = v;

    v = $("#phase2-client-cert-password").val();
    if(v)
      wxs['phase2-client-cert-password'] = v;

    v = $("#phase2-private-key").val();
    if(v)
      wxs['phase2-private-key'] = v;

    v = $("#phase2-private-key-password").val();
    if(v)
      wxs['phase2-private-key-password'] = v;

    v = $("#pac-file").val();
    if(v)
      wxs['pac-file'] = v;

    v = $("#pac-file-password").val();
    if(v)
      wxs['pac-file-password'] = v;
  }
  settings['connection'] = con;
  settings['802-11-wireless'] = ws;
  settings['802-11-wireless-security'] = wss;
  settings['802-1x'] = wxs;
  return settings;
}

function prepareIPv4Addresses(){
  let result = {
    'error': true,
    'ipv4':{}
  };

  var ipFormat = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  var prefixFormat = /^(3[0-2]|[0-2]?[0-9])$/;

  result.ipv4['method'] = $("#ipv4-method").val();

  result.ipv4['address-data'] = [];
  if($("#ipv4-addresses").val()){
    let ips = $("#ipv4-addresses").val().split(',');
    for(let i=0; i<ips.length; i++){
      let data = ips[i].split('\/');
      if(data.length != 2)
        return result;
      if(!data[0].match(ipFormat))
        return result;
      if(!data[1].match(prefixFormat))
        return result;
      result.ipv4['address-data'].push({'address':data[0], 'prefix':data[1]});
    }
  }

  if ($("#ipv4-gateway").val()){
    if(!$("#ipv4-gateway").val().match(ipFormat))
      return result;
    result.ipv4['gateway'] = $("#ipv4-gateway").val();
  }

  result.ipv4['dns'] = [];
  if($("#ipv4-dns").val()){
    let ips = $("#ipv4-dns").val().split(',');
    for(let i=0; i<ips.length; i++){
      if(!ips[i].match(ipFormat))
        return result;
      result.ipv4['dns'].push(ips[i]);
    }
  }

  result.error = false;
  return result;
}

function prepareIPv6Addresses(){
  let result = {
    'error': true,
    'ipv6':{}
  };

  var ipFormat = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  var prefixFormat = /^(1[01][0-9]|12[0-8]|[0-9]?[0-9])$/;

  result.ipv6['method'] = $("#ipv6-method").val();

  if(result.ipv6['method'] == "manual" && $("#ipv6-addresses").val()=="")
    return result;

  result.ipv6['address-data'] = [];
  if($("#ipv6-addresses").val()){
    let ips = $("#ipv6-addresses").val().split(',');
    for(let i=0; i<ips.length; i++){
      let data = ips[0].split('\/');
      if(data.length != 2)
        return result;
      if(!data[0].match(ipFormat))
        return result;
      if(!data[1].match(prefixFormat))
        return result;
      result.ipv6['address-data'].push({'address':data[0], 'prefix':data[1]});
    }
  }

  if ($("#ipv6-gateway").val()){
    if(!$("#ipv6-gateway").val().match(ipFormat))
      return result;
    result.ipv6['gateway'] = $("#ipv6-gateway").val();
  }

  result.ipv6['dns'] = [];
  if($("#ipv6-dns").val()){
    let ips = $("#ipv6-dns").val().split(',');
    for(let i=0; i<ips.length; i++){
      if(ips[i].match(ipFormat))
        return result;
      result.ipv6['dns'].push(ips[i]);
    }
  }

  result.error = false;
  return result;
}

function addConnection() {

  let id = $("#connection-id").val();
  if (id != ""){
    let ctype = $("#connection-type").val();
    switch(ctype){
      case "802-3-ethernet":
        new_connection = prepareEthernetConnection();
        break;
      case "802-11-wireless":
        new_connection = prepareWirelessConnection();
        break;
      case "ppp":
      case "modem":
      case "bluetooth":
      case "wifi-p2p":
      case "bridge":
      default:
        break;
    }

    if (!new_connection){
      CustomMsg("Invalid Settings", true);
      return;
    }

    let result = prepareIPv4Addresses();
    if(result.error){
      CustomMsg("Invalid ipv4 Settings", true);
      return;
    }
    new_connection['ipv4'] = result.ipv4;

    result = prepareIPv6Addresses();
    if(result.error){
      CustomMsg("Invalid ipv6 Settings", true);
      return;
    }
    new_connection['ipv6'] = result.ipv6;

    $.ajax({
      url: "connection",
      type: "POST",
      data: JSON.stringify(new_connection),
      contentType: "application/json",
    })
    .done(function(msg) {
      SDCERRtoString(msg.SDCERR);
    })
    .fail(function( xhr, textStatus, errorThrown) {
      httpErrorResponseHandler(xhr, textStatus, errorThrown)
    });
  } else {
    CustomMsg("ID can not be empty", true);
  }
}

function addScanConnection(){
  id = $("#connectionName").val();
  ssid = $("#newSSID").val();
  key_mgmt = $("#security").attr("key-mgmt");
  editConnection(null, id, ssid, key_mgmt);
}

function allowDrop(ev){
  ev.preventDefault();
}

function clickScantableRow(row){
  $("#newSSID").val(row.find("td:eq(0)").text())
  $("#security").val(row.find("td:eq(4)").text());
  $("#security").attr("key-mgmt", row.attr("key-mgmt"));
  $("#connectionNameDisplay").removeClass("has-error");
  $("#goToConnectionDisplay").removeClass("d-none");
}

function dragStart(ev){
  let index = $(ev.currentTarget).index() + 1;
  if (index > 0){
    ev.originalEvent.dataTransfer.setData("ssid", $('#scanTable tr').eq(index).find("td:eq(0)").text());
    ev.originalEvent.dataTransfer.setData("security", $('#scanTable tr').eq(index).find("td:eq(4)").text());
    ev.originalEvent.dataTransfer.setData("key-mgmt",$('#scanTable tr').eq(index).attr("key-mgmt"));
  }
}

function drop(ev){
  ev.preventDefault();
  $("#newSSID").val(ev.originalEvent.dataTransfer.getData("ssid"));
  $("#security").val(ev.originalEvent.dataTransfer.getData("security"));
  $("#security").attr("key-mgmt",ev.originalEvent.dataTransfer.getData("key-mgmt"));
  $("#connectionNameDisplay").removeClass("has-error");
  $("#goToConnectionDisplay").removeClass("d-none");
}

function requestScan(){

  clearTimeout(statusUpdateTimerId);

  $("#bt-manual-scan").prop("disabled", true);
  $('#scanTable tbody').empty();
  $("#scanProgressDisplay").removeClass("d-none");
  $("#form-addWifiConnection").addClass("d-none");

  $.ajax({
    url: "accesspoints",
    type: "PUT",
    contentType: "application/json",
  })
  .done(function(msg) {
    setIntervalUpdate(getScan, 10000, 0);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    $("#bt-manual-scan").prop("disabled", false);
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function getScan(retry){

  $.ajax({
    url: "accesspoints",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function(msg) {

    if (msg.SDCERR == defines.SDCERR.SDCERR_FAIL){
      if(retry < 3){
        setIntervalUpdate(getScan, 10000, retry + 1);
      }
      else{
        $("#status-ap-scanning").removeClass("d-none");
        $("#scanProgressDisplay").addClass("d-none");
        $("#bt-manual-scan").prop("disabled", false);
      }
    }
    else if($("#scanTable").length > 0){

      $(document).off("drop", "#form-addWifiConnection");
      $(document).off("dragover", "#form-addWifiConnection");

      $("#scanProgressDisplay").addClass("d-none");

      $('#scanTable tbody').empty();
      for (let ap = 0; ap < msg["accesspoints"].length; ap++){

        var markup =  "<tr><td>" + msg["accesspoints"][ap].Ssid +
                      "</td><td>" + msg["accesspoints"][ap].HwAddress +
                      "</td><td>" + msg["accesspoints"][ap].Frequency +
                      "</td><td>" + msg["accesspoints"][ap].Strength +
                      "</td><td>" + msg["accesspoints"][ap].Security + "</td></tr>";
        $('#scanTable tbody').append(markup);
        $("#scanTable tr:last").attr("draggable", true);
        $("#scanTable tr:last").attr("key-mgmt", msg["accesspoints"][ap].Keymgmt);
      }

      $(document).on('dragstart', "#scanTable tbody tr", function(event){
        dragStart(event);
      });

      $("#scanTable tbody tr").on('click', function(){
        let row=$(this).closest("tr");
        clickScantableRow(row);
      });

      $(document).on("drop", "#form-addWifiConnection", function(event){
        drop(event);
      });

      $(document).on("dragover", "#form-addWifiConnection", function(event){
        allowDrop(event);
      });

      $("#bt-manual-scan").prop("disabled", false);

      if (-1 !== currUserPermission.indexOf("networking_edit")){
        $("#form-addWifiConnection").removeClass("d-none");
      }
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickScanPage(){
  $.ajax({
    url: "plugins/networking/html/scan.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#networking_scan_main_menu").addClass("active");
    $("#networking_scan_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
    clearTimeout(statusUpdateTimerId);

    getScan(0);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function getCerts(connection){

  function createCertList(data){
    var ca = $("#ca-cert");
    var client = $("#client-cert");
    var pri = $("#private-key");

    var phase2_ca = $("#phase2-ca-cert");
    var phase2_client = $("#phase2-client-cert");
    var phase2_pri = $("#phase2-private-key");

    var pac_file = $("#pac-file");

    ca.empty();
    client.empty();
    pri.empty();
    phase2_ca.empty();
    phase2_client.empty();
    phase2_pri.empty();

    for(i=0; i<data.length; i++) {
      var option = "<option value=" + data[i] + ">" + data[i] + "</option>";
      ca.append(option);
      client.append(option);
      pri.append(option);
      phase2_ca.append(option);
      phase2_client.append(option);
      phase2_pri.append(option);
      pac_file.append(option);
    }
  }

  return $.ajax({
    url: "files?typ=cert",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function(msg) {
    createCertList(msg);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function getVersion(){
  $.ajax({
    url: "version",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function(msg) {
    $("#driver").text(msg['driver']);
    $("#driver-version").text(msg['driver_version']);
    $("#supplicant").text(msg['supplicant']);
    $("#build").text(msg['build']);
    $("#nm-version").text(msg['nm_version']);
    $("#weblcm-python-webapp").text(msg['weblcm_python_webapp']);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickVersionPage(){
  $.ajax({
    url: "plugins/networking/html/version.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#networking_version_main_menu").addClass("active");
    $("#networking_version_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
    getVersion(0);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function getNetworkInterfaces(){
  return $.ajax({
    url: "networkInterfaces",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function(data) {
    if (data.SDCERR == defines.SDCERR.SDCERR_FAIL)
      return;
    interfaces = data.interfaces;
    if($("#interface-name").length > 0){
      let sel = $("#interface-name");
      sel.empty();
      for (iface in interfaces){
        let option = "<option value=" + interfaces[iface] + ">" + interfaces[iface] + "</option>";
        sel.append(option);
      }

      sel = $("#connection-type");
      sel.empty();
      for (iface in interfaces){
        if ((interfaces[iface].indexOf("eth") >= 0) || (interfaces[iface].indexOf("usb") >= 0)){
          let option = '<option value="802-3-ethernet">Ethernet</option>';
          sel.append(option);
          break;
        }
      }
      for (iface in interfaces){
        if (-1 != interfaces[iface].indexOf("wlan")){
          let option = '<option value="802-11-wireless">Wireless</option>';
          sel.append(option);
          break;
        }
      }
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function onChangeRadioMode(){

  var mode = $("#radio-mode").val();

  switch(mode){
    case "infrastructure":
      $("#frequency-list-display").removeClass("d-none");
      $("#radio-channel-display").addClass("d-none");
      break;
    case "ap":
      $("#frequency-list-display").addClass("d-none");
      $("#radio-channel-display").removeClass("d-none");
      break;
    default:
      break;
  }
}

function onChangeIpv4Method(){
  let method = $("#ipv4-method").val();
  switch(method){
    case "disabled":
    case "manual":
    case "shared":
      $("#ipv4-addresses").attr('readonly', false);
      $("#ipv4-gateway").attr('readonly', false);
      $("#ipv4-dns").attr('readonly', false);
      break;

    case "auto":
    case "link-local":
    default:
      $("#ipv4-addresses").val('');
      $("#ipv4-gateway").val('');
      $("#ipv4-dns").val('');
      $("#ipv4-addresses").attr('readonly', true);
      $("#ipv4-gateway").attr('readonly', true);
      $("#ipv4-dns").attr('readonly', true);
      break;
  }
}


function onChangeIpv6Method(){
  let method = $("#ipv6-method").val();
  switch(method){
    case "manual":
    case "shared":
    case "disabled":
      $("#ipv6-addresses").attr('readonly', false);
      $("#ipv6-gateway").attr('readonly', false);
      $("#ipv6-dns").attr('readonly', false);
      break;
    case "auto":
    case "dhcp":
    case "ignore":
    case "link-local":
    default:
      $("#ipv6-addresses").val('');
      $("#ipv6-gateway").val('');
      $("#ipv6-dns").val('');
      $("#ipv6-addresses").attr('readonly', true);
      $("#ipv6-gateway").attr('readonly', true);
      $("#ipv6-dns").attr('readonly', true);
      break;
  }
}
