// Copyright (c) 2020 Ezurio
// Contact: support@ezurio.com

function statusAUTORUN(retry){

  $(document).on("click", "#status_networking_mini_menu, #status_networking_main_menu", function(){
    clickStatusPage();
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
      return g_i18nData['Unknown'];
    case NMDeviceState.NM_DEVICE_STATE_UNMANAGED:
      return g_i18nData['Unmanaged'];
    case NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE:
      return g_i18nData['Unavailable'];
    case NMDeviceState.NM_DEVICE_STATE_DISCONNECTED:
      return g_i18nData['Disconnected'];
    case NMDeviceState.NM_DEVICE_STATE_PREPARE:
      return g_i18nData['Preparing'];
    case NMDeviceState.NM_DEVICE_STATE_CONFIG:
      return g_i18nData['Connecting'];
    case NMDeviceState.NM_DEVICE_STATE_NEED_AUTH:
      return g_i18nData['Need Auth'];
    case NMDeviceState.NM_DEVICE_STATE_IP_CONFIG:
      return g_i18nData['Requesting IP'];
    case NMDeviceState.NM_DEVICE_STATE_IP_CHECK:
      return g_i18nData['IP Check'];
    case NMDeviceState.NM_DEVICE_STATE_SECONDARIES:
      return g_i18nData['Secondaries'];
    case NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
      return g_i18nData['Activated'];
    case NMDeviceState.NM_DEVICE_STATE_DEACTIVATING:
      return g_i18nData['Deactivating'];
    case NMDeviceState.NM_DEVICE_STATE_FAILED:
      return g_i18nData['Failed'];
    default:
      return g_i18nData['Unknown State'];
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
      return "GSM";
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

var statusUpdateTimerId;

function updateStatus(){
  $.ajax({
    url: "networkStatus",
    type: "GET",
    cache: false,
  })
  .done(function( data ) {
    let card_id_prefix = "status-networking-accordion-";
    if($("#status-networking-accordion").length > 0){
      $("#status-update-progress-Display").addClass("d-none");
      for (interfaceName in data.status){
        let button, card_id;

        card_id = card_id_prefix + interfaceName;
        // Add new cards if they dont exist
        if($("#" + card_id).attr("id") == null){
          $("#status-networking-accordion-root").clone().attr("id", card_id).appendTo("#status-networking-accordion");
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
          ipv4.children(".address").text(g_i18nData['IPv4 Address'] + ": " + data.status[interfaceName].ip4config.Addresses[0]);
          // IPv4 Gateway
          ipv4.children(".gateway").text(g_i18nData['IPv4 Gateway'] + ": " + data.status[interfaceName].ip4config.Gateway);
        } else {
          ipv4.addClass("d-none");
        }

        // IPv6
        ipv6 = $("#" + card_id + "-body" + " >.card-body >.ip6config");
        ipv6.empty();
        if (data.status[interfaceName].ip6config){
          let i = 0;
          let addresses = data.status[interfaceName].ip6config.Addresses;
          // Add entries and display IPv6 addresses
          for (let key in addresses) {
            ipv6.append('<div class="col-6 text-left mb-3">' + g_i18nData['IPv6 Address'] + ' ' + i + ': <span>' + addresses[key] + '</span></div>');
            i += 1;
          }
          // IPv6 Gateway
          if (data.status[interfaceName].ip6config.Gateway){
            ipv6.append('<div class="col-6 text-left mb-3">' + g_i18nData['IPv6 Gateway'] + ': <span>' + data.status[interfaceName].ip6config.Gateway + '</span></div>');
          }
          ipv6.removeClass("d-none");
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
          activeaccesspoint.children(".channel").text(g_i18nData['Channel'] + ": " + wifi_freq_to_channel(data.status[interfaceName].activeaccesspoint.Frequency));
          // Signal Strength
          var rssi = data.status[interfaceName].activeaccesspoint.Signal
          if (rssi < -9000) {
            // RSSI value is invalid, so don't display it
            activeaccesspoint.children(".strength").text(g_i18nData['Signal Strength'] + ": " + data.status[interfaceName].activeaccesspoint.Strength + "%");
          } else {
            activeaccesspoint.children(".strength").text(g_i18nData['Signal Strength'] + ": " + data.status[interfaceName].activeaccesspoint.Strength + "% (" + rssi + " dBm)");
          }
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
          wireless.children(".hwaddress").text(g_i18nData['MAC Address'] + ": " + data.status[interfaceName].wireless.HwAddress);
          // Bit Rate
          wireless.children(".bitrate").text(g_i18nData['Bit Rate'] + ": " + data.status[interfaceName].wireless.Bitrate/1000 + "Mbit/s");
          // Regulatory Domain
          wireless.children(".regdomain").text(g_i18nData['Regulatory Domain'] + ": " + data.status[interfaceName].wireless.RegDomain);
        } else {
          wireless.addClass("d-none");
        }

        // Wired
        wired = $("#" + card_id + "-body" + " >.card-body >.wired");
        if (data.status[interfaceName].wired){
          wired.removeClass("d-none");
          // HW Address
          wired.children(".hwaddress").text(g_i18nData['MAC Address'] + ": " + data.status[interfaceName].wired.HwAddress);
          // Speed
          wired.children(".speed").text(g_i18nData['Speed'] + ": "  + data.status[interfaceName].wired.Speed + "Mbit/s");
        } else {
          wired.addClass("d-none");
        }
      }
      statusUpdateTimerId = setTimeout(updateStatus, 10000);
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickStatusPage() {

  $.ajax({
    url: "plugins/status/html/status.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#status_networking_main_menu").addClass("active");
    $("#status_networking_mini_menu").addClass("active");
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

