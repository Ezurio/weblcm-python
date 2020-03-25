// Copyright (c) 2018, Laird Connectivity
// Contact: support@lairdconnect.com

function networkingAUTORUN(retry){
  clickStatusPage(0);
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
      return "Unknown";
    case NMDeviceState.NM_DEVICE_STATE_UNMANAGED:
      return "Unmanaged";
    case NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE:
      return "Unavailable";
    case NMDeviceState.NM_DEVICE_STATE_DISCONNECTED:
      return "Disconnected";
    case NMDeviceState.NM_DEVICE_STATE_PREPARE:
      return "Preparing";
    case NMDeviceState.NM_DEVICE_STATE_CONFIG:
      return "Connecting";
    case NMDeviceState.NM_DEVICE_STATE_NEED_AUTH:
      return "Need Auth";
    case NMDeviceState.NM_DEVICE_STATE_IP_CONFIG:
      return "Requesting IP";
    case NMDeviceState.NM_DEVICE_STATE_IP_CHECK:
      return "IP Check";
    case NMDeviceState.NM_DEVICE_STATE_SECONDARIES:
      return "Secondaries";
    case NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
      return "Activated";
    case NMDeviceState.NM_DEVICE_STATE_DEACTIVATING:
      return "Deactivating";
    case NMDeviceState.NM_DEVICE_STATE_FAILED:
      return "Failed";
    default:
      return "Unknown State";
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

  $("#connection-wired-settings").addClass("hidden");
  $("#connection-wifi-settings").addClass("hidden");
  $("#connection-ppp-settings").addClass("hidden");
  $("#connection-modem-settings").addClass("hidden");
  $("#connection-wifi-p2p-settings").addClass("hidden");
  $("#connection-bridge-settings").addClass("hidden");
  $("#connection-bluetooth-settings").addClass("hidden");

  var ctype = $("#connection-type").val();
  switch(ctype){
    case "802-3-ethernet":
      $("#connection-wired-settings").removeClass("hidden");
      break;
    case "802-11-wireless":
      $("#connection-wifi-settings").removeClass("hidden");
      break;
    case "ppp":
      $("#connection-ppp-settings").removeClass("hidden");
      break;
    case "modem":
      $("#connection-modem-settings").removeClass("hidden");
      break;
    case "bluetooth":
      $("#connection-bluetooth-settings").removeClass("hidden");
      break;
    case "wifi-p2p":
      $("#connection-wifi-p2p-settings").removeClass("hidden");
      break;
    case "bridge":
      $("#connection-bridge-settings").removeClass("hidden");
      break;
    default:
      break;
  }
}

function clear8021xCredsDisplay(){

  $("#eap-method-display").addClass("hidden");
  $("#eap-method").val("peap");

  $("#eap-auth-timeout-display").addClass("hidden");
  $("#eap-auth-timeout").val("0");

  $("#eap-identity-display").addClass("hidden");
  $("#eap-identity").val("");

  $("#eap-password-display").addClass("hidden");
  $("#eap-password").val("");

  $("#eap-anonymous-identity-display").addClass("hidden");
  $("#eap-anonymous-identity").val("");

  $("#pac-file-display").addClass("hidden");
  $("#pac-file").val("");

  $("#pac-file-password-display").addClass("hidden");
  $("#pac-file-password").val("");

  $("#phase1-fast-provisioning-display").addClass("hidden");
  $("#phase1-fast-provisioning").val("0");

  $("#ca-cert-display").addClass("hidden");
  $("#ca-cert").val("");

  $("#ca-cert-password-display").addClass("hidden");
  $("#ca-cert-password").val("");

  $("#client-cert-display").addClass("hidden");
  $("#client-cert").val("");

  $("#client-cert-password-display").addClass("hidden");
  $("#client-cert-password").val("");

  $("#private-key-display").addClass("hidden");
  $("#private-key").val("");

  $("#private-key-password-display").addClass("hidden");
  $("#private-key-password").val();

  $("#phase2-auth-display").addClass("hidden");
  $("#phase2-auth").val("none");

  $("#phase2-autheap-display").addClass("hidden");
  $("#phase2-autheap").val("none");

  $("#phase2-ca-cert-display").addClass("hidden");
  $("#phase2-ca-cert").val("");

  $("#phase2-ca-cert-password-display").addClass("hidden");
  $("#phase2-ca-cert-password").val("");

  $("#phase2-client-cert-display").addClass("hidden");
  $("#phase2-client-cert").val("");

  $("#phase2-client-cert-password-display").addClass("hidden");
  $("#phase2-client-cert-password").val("");

  $("#phase2-private-key-display").addClass("hidden");
  $("#phase2-private-key").val("");

  $("#phase2-private-key-password-display").addClass("hidden");
  $("#phase2-private-key-password-display").val("");

  $("#tls-disable-time-checks-display").addClass("hidden");
  $("#tls-disable-time-checks").val("1");
}

function clearWifiSecurityCredsDisplay() {

  $("#auth-alg-display").addClass("hidden");
  $("#auth-alg").val("open");

  $("#wep-tx-keyidx-display").addClass("hidden");
  $("#wep-tx-keyidx").val("0");

  $("#wep-key-display").addClass("hidden");
  $("#wep-tx-key0").val("");
  $("#wep-tx-key1").val("");
  $("#wep-tx-key2").val("");
  $("#wep-tx-key3").val("");

  $("#psk-display").addClass("hidden");
  $("#psk").val("");

  $("#leap-username-display").addClass("hidden");
  $("#leap-username").val("");

  $("#leap-password-display").addClass("hidden");
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
    $("#phase2-ca-cert-display").removeClass("hidden");
    $("#phase2-ca-cert").val(parseSettingData(wxs, "phase2-ca-cert", ""));
    $("#phase2-client-cert-display").removeClass("hidden");
    $("#phase2-client-cert").val(parseSettingData(wxs, "phase2-client-cert", ""));
    $("#phase2-private-key-display").removeClass("hidden");
    $("#phase2-private-key").val(parseSettingData(wxs, "phase2-private-key", ""));
    $("#phase2-private-key-password-display").removeClass("hidden");
  }
  else
  {
    $("#phase2-ca-cert-display").addClass("hidden");
    $("#phase2-ca-cert").val("");

    $("#phase2-ca-cert-password-display").addClass("hidden");
    $("#phase2-ca-cert-password").val("");

    $("#phase2-client-cert-display").addClass("hidden");
    $("#phase2-client-cert").val("");

    $("#phase2-client-cert-password-display").addClass("hidden");
    $("#phase2-client-cert-password").val("");

    $("#phase2-private-key-display").addClass("hidden");
    $("#phase2-private-key").val("");

    $("#phase2-private-key-password-display").addClass("hidden");
    $("#phase2-private-key-password-display").val("");
  }
}

function onChangePhase2NoneEap() {
  resetPhase2AuthSetting(null, "phase2-auth", "phase2-autheap");
}

function onChangePhase2Eap() {
  resetPhase2AuthSetting(null, "phase2-autheap", "phase2-auth");
}

function resetEapSetting(wxs){

  var eap = $("#eap-method").val();
  if (eap == "fast"){
    $("#pac-file-display").removeClass("hidden");
    $("#pac-file").val(parseSettingData(wxs, "pac-file", ""));
    $("#pac-file-password-display").removeClass("hidden");
    $("#phase1-fast-provisioning-display").removeClass("hidden");
    $("#phase1-fast-provisioning").val(parseSettingData(wxs, "phase1-fast-provisioning", "0"));
  } else if (-1 !== eap.indexOf("tls")) {
    $("#ca-cert-display").removeClass("hidden");
    $("#ca-cert").val(parseSettingData(wxs, "ca-cert", ""));
    $("#client-cert-display").removeClass("hidden");
    $("#client-cert").val(parseSettingData(wxs, "client-cert", ""));
    $("#private-key-display").removeClass("hidden");
    $("#private-key").val(parseSettingData(wxs, "private-key", ""));
    $("#private-key-password-display").removeClass("hidden");
    $("#tls-disable-time-checks-display").removeClass("hidden");
    $("#tls-disable-time-checks").val(parseSettingData(wxs, "tls-disable-time-checks", "1"));
  } else if (-1 !== eap.indexOf("ttls")) {
    $("#ca-cert-display").removeClass("hidden");
    $("#ca-cert").val(parseSettingData(wxs, "ca-cert", ""));
    $("#client-cert-display").removeClass("hidden");
    $("#client-cert").val(parseSettingData(wxs, "client-cert", ""));
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
      $("#auth-alg-display").removeClass("hidden");
      $("#auth-alg").val(parseSettingData(wss, "auth-alg", "open"));
      $("#wep-tx-keyidx-display").removeClass("hidden");
      $("#wep-tx-keyidx").val(parseSettingData(wss, "wep-tx-keyidx", "0"));
      $("#wep-key-display").removeClass("hidden")
      break;
    case "ieee8021x":
      $("#leap-username-display").removeClass("hidden");
      $("#leap-password-display").removeClass("hidden");
      $("#auth-alg").val("leap");
      $("#leap-username").val(parseSettingData(wss, "leap-username", ""));
      break;
    case "wpa-psk":
      $("#psk-display").removeClass("hidden");
      $("#psk").val(parseSettingData(wss, "psk", ""));
      break;
    case "wpa-eap":
      $("#eap-method-display").removeClass("hidden");
      $("#eap-method").val(parseSettingData(wxs, "eap", "peap"));
      $("#eap-auth-timeout-display").removeClass("hidden");
      $("#eap-auth-timeout").val(parseSettingData(wxs, "auth-timeout", 0).toString());
      $("#eap-identity-display").removeClass("hidden");
      $("#eap-identity").val(parseSettingData(wxs, "identity", "").toString());
      $("#eap-password-display").removeClass("hidden");
      $("#eap-anonymous-identity-display").removeClass("hidden");
      $("#eap-anonymous-identity").val(parseSettingData(wxs, "anonymous-identity", ""));
      $("#phase2-autheap-display").removeClass("hidden");
      autheap = parseSettingData(wxs, "phase2-autheap", "none");
      $("#phase2-autheap").val(autheap.split(" "));
      $("#phase2-auth-display").removeClass("hidden");
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
function setIntervalUpdate(functionName){
  statusUpdateTimerId = setTimeout(functionName, 10000)
}


function updateStatus(){
  panel_collapse_id_prefix = "panel-collapse-";
  var getStatusJSON = $.getJSON( "networkStatus", function( data ) {
    if($("#panel-group").length > 0){
      $("#updateProgressDisplay").addClass("hidden");
      for (interfaceName in data.status){
        // Add new panels if they dont exist
        if($("#"+interfaceName).attr("id") == null){
          $("#root-interface").clone().attr("id", interfaceName).appendTo("#panel-group");
        }

        $("#"+interfaceName).removeClass("hidden");

        panel_collapse_id = panel_collapse_id_prefix + interfaceName;

        panel_button = $("#"+interfaceName + " > .panel-heading > .panel-title > .row > .panel-button");
        panel_button.attr("href", "#" + panel_collapse_id);
        panel_button.attr("aria-controls", panel_collapse_id);
        panel_button.text(interfaceName);

        panel_collapse = $("#"+interfaceName + " > .panel-collapse").attr("id", panel_collapse_id);
        // Device Type
        $("#"+interfaceName + " > .panel-heading > .panel-title > .row > .devicetype").text(DeviceTypetoString(data.status[interfaceName].status.DeviceType));
        // State
        $("#"+interfaceName + " > .panel-heading > .panel-title > .row > .state").text(CARDSTATEtoString(data.status[interfaceName].status.State));

        // Active Connection
        connection_active = $("#"+interfaceName + " >.panel-collapse > .panel-body > .connection-active");
        if (data.status[interfaceName].connection_active){
          connection_active.removeClass("hidden");
          // ID
          connection_active.children(".id").text("ID: " + data.status[interfaceName].connection_active.id);
          // UUID
          connection_active.children(".uuid").text("UUID: " + data.status[interfaceName].connection_active.uuid);
        } else {
          connection_active.addClass("hidden");
        }
        // IPv4
        ipv4 = $("#"+interfaceName + " > .panel-collapse > .panel-body > .ip4config");
        if (data.status[interfaceName].ip4config){
          ipv4.removeClass("hidden");
          // IPv4 Address
          ipv4.children(".address").text("IPv4 Address: " + data.status[interfaceName].ip4config.Addresses[0]);
          // IPv4 Gateway
          ipv4.children(".gateway").text("IPv4 Gateway: " + data.status[interfaceName].ip4config.Gateway);
        } else {
          ipv4.addClass("hidden");
        }

        // IPv6
        ipv6 = $("#"+interfaceName + " > .panel-collapse > .panel-body > .ip6config");
        if (data.status[interfaceName].ip6config){
        // Add entries and Display IPv6 addresses
        if (data.status[interfaceName].ip6config.Addresses){
          if (data.status[interfaceName].ip6config.Addresses[0])
            ipv6.children(".address").text("IPv6 Address: " + data.status[interfaceName].ip6config.Addresses[0]);
          else
            ipv6.children(".address").text("IPv6 Address:");
          if (data.status[interfaceName].ip6config.Addresses[1])
            ipv6.children(".address-2").text("IPv6 Address 2: " + data.status[interfaceName].ip6config.Addresses[1]);
          else
            ipv6.children(".address-2").text("IPv6 Address 2:");
          if (data.status[interfaceName].ip6config.Addresses[2])
            ipv6.children(".address-3").text("IPv6 Address 3: " + data.status[interfaceName].ip6config.Addresses[2]);
          else
            ipv6.children(".address-3").text("IPv6 Address 3:");
        }
        // IPv6 Gateway
        panel_collapse.children(".gateway").text("IPv6 Gateway: " + data.status[interfaceName].ip6config.Gateway);
        } else {
          ipv6.addClass("hidden");
        }

        // Active Access Point
        activeaccesspoint = $("#"+interfaceName + " >.panel-collapse > .panel-body > .activeaccesspoint");
        if (data.status[interfaceName].activeaccesspoint){
          activeaccesspoint.removeClass("hidden");
          // SSID
          activeaccesspoint.children(".ssid").text("SSID: " + data.status[interfaceName].activeaccesspoint.Ssid);
          // BSSID
          activeaccesspoint.children(".bssid").text("BSSID:" + data.status[interfaceName].activeaccesspoint.HwAddress);
          // Frequency
          activeaccesspoint.children(".frequency").text("Frequency: " + data.status[interfaceName].activeaccesspoint.Frequency);
          // Signal Strength
          activeaccesspoint.children(".strength").text("Signal Strength: " + data.status[interfaceName].activeaccesspoint.Strength);
          // Progress Bar
          progress_bar = activeaccesspoint.children(".progress-bar");
          progress_bar.removeClass("hidden");
          progress_bar.removeClass("progress-bar-danger progress-bar-warning progress-bar-success hidden");
          if (data.status[interfaceName].activeaccesspoint.Strength == 0){ //Not connected
            progress_bar.addClass("progress-bar-danger");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else if (data.status[interfaceName].activeaccesspoint.Strength < 30){ //red
            progress_bar.addClass("progress-bar-danger");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else if (data.status[interfaceName].activeaccesspoint.Strength < 50){ //yellow
            progress_bar.addClass("progress-bar-warning");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          } else { //green
            progress_bar.addClass("progress-bar-success");
            progress_bar.css("width",data.status[interfaceName].activeaccesspoint.Strength.toString().concat("%"));
          }
          progress_bar.text(data.status[interfaceName].activeaccesspoint.Strength);
        } else {
          activeaccesspoint.addClass("hidden");
        }
        // Wireless
        wireless = $("#"+interfaceName + " >.panel-collapse > .panel-body > .wireless");
        if (data.status[interfaceName].wireless){
          wireless.removeClass("hidden");
          // HW Address
          wireless.children(".hwaddress").text("MAC Address: " + data.status[interfaceName].wireless.HwAddress);
          // Bit Rate
          wireless.children(".bitrate").text("Bit Rate: " + data.status[interfaceName].wireless.Bitrate);
        } else {
          wireless.addClass("hidden");
        }

        // Wired
        wired = $("#"+interfaceName + " >.panel-collapse > .panel-body > .wired");
        if (data.status[interfaceName].wired){
          wired.removeClass("hidden");
          // HW Address
          wired.children(".hwaddress").text("MAC Address: " + data.status[interfaceName].wired.HwAddress);
          // Speed
          wired.children(".speed").text("Speed: " + data.status[interfaceName].wired.Speed);
        } else {
          wired.addClass("hidden");
        }
      }
      setIntervalUpdate(updateStatus);
    }
  })
  .fail(function(data) {
    clearTimeout(statusUpdateTimerId);
    consoleLog("Failed to get status");
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
    $("li").removeClass("active");
    $("#networking_status_main_menu").addClass("active");
    $("#networking_status_mini_menu").addClass("active");
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("This page shows the current state of networking");
    $(".infoText").addClass("hidden");
    clearTimeout(statusUpdateTimerId);
    updateStatus();
  })
  .fail(function() {
    consoleLog("Failed to get status.html");
  });
}

function newWifiConnection(uuid, id, ssid, key_mgmt) {

  $("#connection-uuid").val(uuid);
  $("#connection-id").val(id);
  $("#ssid").val(ssid);

  $("#key-mgmt").val(key_mgmt);
  $("#key-mgmt").change();

  $("#connection-type").val("802-11-wireless");
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

function updateGetConnectionPage(uuid, id, ssid, key_mgmt){
  var data = {
    UUID: uuid,
  }
  $.ajax({
    url: "connection?uuid="+uuid,
    type: "GET",
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
      }
      else{
        newWifiConnection(uuid, id, ssid, key_mgmt);
      }
    }
  })
  .fail(function() {
    consoleLog("Failed to get connection settings");
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
    $("li").removeClass("active");
    $("#networking_edit_main_menu").addClass("active");
    $("#networking_edit_mini_menu").addClass("active");
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("Adjust connection settings.");
    $(".infoText").addClass("hidden");

    if(-1 == currUserPermission.indexOf("networking_ap_activate"))
      $("#radio-mode-display").addClass("hidden");

    $.when(getNetworkInterfaces(), getCerts()).done( function() {
      updateGetConnectionPage(uuid, id, ssid, key_mgmt);
    });
  })
  .fail(function() {
    consoleLog("Failed to get addConnection.html");
  });
}

function selectedConnection(){
  var uuid = $("#connectionSelect").val();
  editConnection(uuid, null, null, null);
}

function onChangeConnections(){
  var activated = $("#connectionSelect option:selected").attr("activated");
  if(activated == 1){
    $("#bt-connection-activate").attr("value", "Deactivate");
  }
  else {
    $("#bt-connection-activate").attr("value", "Activate");
  }
}

function updateConnectionsPage(){
  $.ajax({
    url: "connections",
    type: "GET",
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
  .fail(function() {
	consoleLog("Failed to update get connections");
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
  .fail(function() {
    consoleLog("Failed to activate connection");
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
    $("li").removeClass("active");
    $("#networking_connections_main_menu").addClass("active");
    $("#networking_connections_mini_menu").addClass("active");

    clearReturnData();

    $("#main_section").html(data);
    $("#helpText").html("These are the current networking connections.");
    $(".infoText").addClass("hidden");

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
  .fail(function() {
    consoleLog("Failed to get connections.html");
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
  ipv4 = {};
  ipv6 = {};
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
  if(v == "ap"){
    ipv4['method'] = "shared";
  }

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
  settings['ipv4'] = ipv4;
  settings['ipv6'] = ipv6;
  return settings;
}

function addConnection() {

  id = $("#connection-id").val();
  if (id != ""){
	var ctype = $("#connection-type").val();
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
	$.ajax({
	  url: "connection",
	  type: "POST",
	  data: JSON.stringify(new_connection),
	  contentType: "application/json",
	})
	.done(function( msg ) {
	  SDCERRtoString(msg.SDCERR);
	});
  } else {
	CustomMsg("Connection name can't be empty", true);
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

function drag(ev){
  var index = $(ev.currentTarget).index() + 1;
  if (index > 0){
	ev.dataTransfer.setData("ssid", $('#scanTable tr').eq(index).find("td:eq(0)").text());
	ev.dataTransfer.setData("security", $('#scanTable tr').eq(index).find("td:eq(4)").text());
	ev.dataTransfer.setData("key-mgmt",$('#scanTable tr').eq(index).attr("key-mgmt"));
  }
}

function drop(ev){
  ev.preventDefault();
  $("#newSSID").val(ev.dataTransfer.getData("ssid"));
  $("#security").val(ev.dataTransfer.getData("security"));
  $("#security").attr("key-mgmt",ev.dataTransfer.getData("key-mgmt"));
  $("#connectionNameDisplay").removeClass("has-error");
  $("#goToConnectionDisplay").removeClass("hidden");
}

function getScan(){
  $.ajax({
    url: "accesspoints",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(msg) {
    $("#updateProgressDisplay").addClass("hidden");
    if (msg.SDCERR == defines.SDCERR.SDCERR_NO_HARDWARE || msg.SDCERR == defines.SDCERR.SDCERR_FAIL){
      $("#status-hardware").removeClass("hidden");
    } else if($("#scanTable").length > 0){
      $("#scanTableDisplay").removeClass("hidden");

      for (var ap in msg["accesspoints"]){

        var markup =  "<tr><td>" + msg["accesspoints"][ap].Ssid +
                      "</td><td>" + msg["accesspoints"][ap].HwAddress +
                      "</td><td>" + msg["accesspoints"][ap].Frequency +
                      "</td><td>" + msg["accesspoints"][ap].Strength +
                      "</td><td>" + msg["accesspoints"][ap].Security + "</td></tr>";

        $('#scanTable tbody').append(markup);
        $("#scanTable tr:last").attr("draggable", true);
        $("#scanTable tr:last").attr("ondragstart", "drag(event)");
        $("#scanTable tr:last").attr("key-mgmt", msg["accesspoints"][ap].Keymgmt);
        $("#scanTable tr:last").on('click', function(){
          var row=$(this).closest("tr");
          $("#newSSID").val(row.find("td:eq(0)").text())
          $("#security").val(row.find("td:eq(4)").text());
          $("#security").attr("key-mgmt", row.attr("key-mgmt"));
          $("#connectionNameDisplay").removeClass("has-error");
          $("#goToConnectionDisplay").removeClass("hidden");
        });
        $("#emptyNode").remove();
      }
    }
  })
  .fail(function() {
    consoleLog("Failed to get AP list");
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
    $("li").removeClass("active");
    $("#networking_scan_main_menu").addClass("active");
    $("#networking_scan_mini_menu").addClass("active");
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("Scan for wireless networks");
    $(".infoText").addClass("hidden");

    if (-1 !== currUserPermission.indexOf("networking_edit")){
      $("#form-addWifiConnection").removeClass("hidden");
    }
    getScan(0);
  })
  .fail(function() {
    consoleLog("Failed to get scan.html");
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

  var data = {
    type: 'cert'
  };

  $.ajax({
    url: "files?typ=cert",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(msg) {
    createCertList(msg);
  })
  .fail(function() {
    consoleLog("Failed to get certificates.");
  });
}

function getVersion(){
  $.ajax({
    url: "version",
	type: "GET",
	contentType: "application/json",
  })
  .done(function(msg) {
    $("#sdk").text(msg['sdk'])
    $("#chipset").text(msg['chipset']);
    $("#driver").text(msg['driver']);
    $("#driver-version").text(msg['driver-version']);
    $("#supplicant").text(msg['supplicant']);
    $("#weblcm_python_webapp").text(msg['weblcm_python_webapp']);
    $("#build").text(msg['build']);
  })
  .fail(function() {
    consoleLog("Failed to get version information");
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
    $("li").removeClass("active");
    $("#networking_version_main_menu").addClass("active");
    $("#networking_version_mini_menu").addClass("active");
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("System version information");
    $(".infoText").addClass("hidden");
    getVersion(0);
  })
  .fail(function() {
    consoleLog("Failed to get version.html");
  });
}

function getNetworkInterfaces(){
  $.ajax({
    url: "networkInterfaces",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(data) {
    if (data.SDCERR == defines.SDCERR.SDCERR_FAIL)
      return;
    interfaces = data.interfaces;
    if($("#interface-name").length > 0){
      var sel = $("#interface-name");
      sel.empty();
      for (iface in interfaces){
        var option = "<option value=" + interfaces[iface] + ">" + interfaces[iface] + "</option>";
        sel.append(option);
      }
    }
  })
  .fail(function() {
    consoleLog("Failed to get interfaces");
  });
}

function onChangeRadioMode(){

  var mode = $("#radio-mode").val();

  switch(mode){
    case "infrastructure":
      $("#frequency-list-display").removeClass("hidden");
      $("#radio-channel-display").addClass("hidden");
      break;
    case "ap":
      $("#frequency-list-display").addClass("hidden");
      $("#radio-channel-display").removeClass("hidden");
      break;
    default:
      break;
  }
}
