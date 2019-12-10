// Copyright (c) 2018, Laird Connectivity
// Contact: support@lairdconnect.com

function networkingAUTORUN(retry){
	clickStatusPage(0);
}

function updateInfoText(option,retry){
	$.ajax({
		url: "plugins/networking/html/info.html",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function( data ) {
		$('#infoText').html(data);
		$("#" + option + "-text").removeClass("hidden");
	})
	.fail(function() {
		consoleLog("Error, couldn't get info.html.. retrying");
		if (retry < 5){
			retry++;
			$("#networking_status").removeClass("active");
			clickStatusPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function CARDSTATEtoString(CARDSTATE){
	switch(CARDSTATE) {
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_UNKNOWN:
			return "Unknown";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_UNMANAGED:
			return "Unmanaged";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE:
			return "Unavailable";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_DISCONNECTED:
			return "Disconnected";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_PREPARE:
			return "Preparing";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_CONFIG:
			return "Connecting";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_NEED_AUTH:
			return "Need Auth";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_IP_CONFIG:
			return "Requesting IP";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_IP_CHECK:
			return "IP Check";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_SECONDARIES:
			return "Secondaries";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
			return "Activated";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_DEACTIVATING:
			return "Deactivating";
		case defines.PLUGINS.networking.NMDeviceState.NM_DEVICE_STATE_FAILED:
			return "Failed";
		default:
			return "Unknown State";
	}
}

function DeviceTypetoString(NMDeviceType){
	switch(NMDeviceType) {
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_UNKNOWN:
			return "Unknown";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_ETHERNET:
			return "Ethernet";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_WIFI:
			return "WiFi";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_UNUSED1:
			return "Unused 1";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_UNUSED2:
			return "Unused 2";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_BT:
			return "Bluetooth";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_OLPC_MESH:
			return "OLPC Mesh";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_WIMAX:
			return "WiMAX";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_MODEM:
			return "Modem";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_INFINIBAND:
			return "Infiniband";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_BOND:
			return "Bond";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_VLAN:
			return "VLAN";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_ADSL:
			return "ADSL";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_BRIDGE:
			return "Bridge";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_GENERIC:
			return "Generic";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_TEAM:
			return "Team";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_TUN:
			return "Tunnel";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_IP_TUNNEL:
			return "IP Tunnel";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_MACVLAN:
			return "MAC VLAN";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_VXLAN:
			return "VXLAN";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_VETH:
			return "Virtual Ethernet";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_MACSEC:
			return "MACSEC";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_DUMMY:
			return "Dummy";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_PPP:
			return "PPP";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_OVS_INTERFACE:
			return "OVS Interface";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_OVS_PORT:
			return "OVS Port";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_OVS_BRIDGE:
			return "OVS Bridge";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_WPAN:
			return "WPAN";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_6LOWPAN:
			return "6LOWPAN";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_WIREGUARD:
			return "Wire Guard";
		case defines.PLUGINS.networking.NMDeviceType.NM_DEVICE_TYPE_WIFI_P2P:
			return "WiFi P2P";
		default:
			return "Unknown State";
	}
}

function onChangePowersave(){
	var powerSave = parseInt(document.getElementById("powerSave").value);
	switch (powerSave){
		case defines.PLUGINS.networking.POWERSAVE.POWERSAVE_OFF:
		case defines.PLUGINS.networking.POWERSAVE.POWERSAVE_MAX:
			$("#pspDelayDisplay").addClass("hidden");
			break;
		case defines.PLUGINS.networking.POWERSAVE.POWERSAVE_FAST:
			$("#pspDelayDisplay").removeClass("hidden");
			break;
		default:
			$("#pspDelayDisplay").removeClass("hidden");
			break;
	}
}

function onChangeSecurity(){
	var authalg = document.getElementById("auth-alg").value;
	var keymgmt = document.getElementById("key-mgmt").value;
	var eap = document.getElementById("eap").value;
	function clearCredsDisplay(){
		$("#certDisplay").addClass("hidden");
		$("#eapTypeDisplay").addClass("hidden");
		$("#phase2-auth-display").addClass("hidden");
		$("#wepIndexDisplay").addClass("hidden");
		$("#wepTypeOnDisplay").addClass("hidden");
		$("#pskDisplay").addClass("hidden");
		$("#leapUserNameDisplay").addClass("hidden");
		$("#leapPassWordDisplay").addClass("hidden");
		$("#identityDisplay").addClass("hidden");
		$("#passWordDisplay").addClass("hidden");
		$("#private-key-display").addClass("hidden");
		$("#private-key-password-display").addClass("hidden");
		$("#userCertDisplay").addClass("hidden");
		$("#userCertPasswordDisplay").addClass("hidden");
		$("#CACertDisplay").addClass("hidden");
		$("#CACertPasswordDisplay").addClass("hidden");
		$("#PACFilenameDisplay").addClass("hidden");
		$("#PACPasswordDisplay").addClass("hidden");
	}
	// FIXME Verify settings
	function displayProperEAPCreds(){
		$("#eapTypeDisplay").removeClass("hidden");
		// FIXME is this valid for all EAP types
		$("#phase2-auth-display").removeClass("hidden");

		if (eap == "fast"){
			$("#identityDisplay").removeClass("hidden");
			$("#passWordDisplay").removeClass("hidden");
			$("#PACFilenameDisplay").removeClass("hidden");
		} else if (eap == "tls"){
			$("#identityDisplay").removeClass("hidden");
			$("#passWordDisplay").removeClass("hidden");
			$("#userCertDisplay").removeClass("hidden");
			$("#userCertPasswordDisplay").removeClass("hidden");
			$("#private-key-display").removeClass("hidden");
			$("#private-key-password-display").removeClass("hidden");
			$("#CACertDisplay").removeClass("hidden");
			$("#CACertPasswordDisplay").removeClass("hidden");
		} else if (eap == "ttls"){
			$("#identityDisplay").removeClass("hidden");
			$("#passWordDisplay").removeClass("hidden");
			$("#CACertDisplay").removeClass("hidden");
			$("#CACertPasswordDisplay").removeClass("hidden");
		} else {
			$("#identityDisplay").removeClass("hidden");
			$("#passWordDisplay").removeClass("hidden");
		}
	}
	switch (keymgmt){
		case "none":
			clearCredsDisplay();
			break;
		case "static":
			clearCredsDisplay();
			$("#wepIndexDisplay").removeClass("hidden");
			$("#wepTypeOnDisplay").removeClass("hidden");
			break;
		case "ieee8021x":
			clearCredsDisplay();
			if (authalg == "leap"){
				$("#leapUserNameDisplay").removeClass("hidden");
				$("#leapPassWordDisplay").removeClass("hidden");
			} else {
				displayProperEAPCreds();
			}
			break;
		case "wpa-psk":
			clearCredsDisplay();
			$("#pskDisplay").removeClass("hidden");
			break;
		case "wpa-eap":
			clearCredsDisplay();
			displayProperEAPCreds();
			break;
		default:
			break;
	}
}

function updateStatus(){
	id_string = "#"
	panel_heading_id_string = "panel_heading_";
	panel_button_id_string = "panel_button_";
	panel_collapse_id_string = "panel_collapse_";
	var getStatusJSON = $.getJSON( "networking_status", function( data ) {
		var old_interfaces = [];
		var old_panels = document.getElementsByClassName("panel-group");
		try{
			// Hide interface panels if they no larger available.
			for (var i = 0; i < old_panels.length; i++) {
				old_interfaces.push(old_panels[i].id);
				if (typeof data.status[old_panels[i].id] == 'undefined') {
					$(id_string.concat(old_panels[i].id)).addClass("hidden");
				}
			}

			for (interface in data.status){
				var interface_panel = document.getElementById(interface);
				// Add new panels if they dont exist
				if(!interface_panel){
					$('#root_interface').clone().attr('id', interface).appendTo('#panel_parent');
				}
				$("#updateProgressDisplay").addClass("hidden");
				$(id_string.concat(interface)).removeClass("hidden");
				panel_heading = document.getElementById(interface).childNodes[1].childNodes[1];
				panel_heading.id = panel_heading_id_string.concat(interface);

				panel_button = document.getElementById(panel_heading.id).childNodes[1].childNodes[1].childNodes[1];
				panel_button.id = panel_button_id_string.concat(interface);
				panel_button.href = id_string.concat(panel_collapse_id_string,interface);
				panel_button.innerText = interface;
				panel_collapse = document.getElementById(interface).childNodes[1].childNodes[3];
				panel_collapse.id = panel_collapse_id_string.concat(interface);
				panel_collapse_body = panel_collapse.childNodes[1];
				$(id_string.concat(panel_button.id)).attr("aria-controls", panel_collapse_id_string.concat(interface));
				// Device Type
				document.getElementById(interface).getElementsByClassName("devicetype")[0].innerText = DeviceTypetoString(data.status[interface].status.devicetype);
				// State
				document.getElementById(interface).getElementsByClassName("state")[0].innerText = CARDSTATEtoString(data.status[interface].status.state);
				// Active Connection
				if (data.status[interface].connection_active){
					$(document.getElementById(interface).getElementsByClassName("connection_active")[0]).removeClass("hidden");
					// ID
					document.getElementById(interface).getElementsByClassName("id")[0].childNodes[2].innerText = data.status[interface].connection_active.id;
					// UUID
					document.getElementById(interface).getElementsByClassName("uuid")[0].childNodes[2].innerText = data.status[interface].connection_active.uuid;
				} else {
					$(document.getElementById(interface).getElementsByClassName("connection_active")[0]).addClass("hidden");
				}
				// IPv4
				if (data.status[interface].ip4config){
					$(document.getElementById(interface).getElementsByClassName("ip4config")[0]).removeClass("hidden");
					// IPv4 Address
					document.getElementById(interface).getElementsByClassName("ipv4_address")[0].childNodes[2].innerText = data.status[interface].ip4config.address[0];
					// IPv4 Gateway
					document.getElementById(interface).getElementsByClassName("ipv4_gateway")[0].childNodes[2].innerText = data.status[interface].ip4config.gateway;
				} else {
					$(document.getElementById(interface).getElementsByClassName("ip4config")[0]).addClass("hidden");
				}
				// IPv6
				if (data.status[interface].ip6config){
					// Add entries and Display IPv6 addresses
					var total_addresses = Object.keys(data.status[interface].ip6config.address).length;
					var interface_ipv6 = interface.concat("_ipv6");
					$(document.getElementById(interface).getElementsByClassName("ip6config")[0]).attr('id', interface_ipv6)
						for (var i = 0; i < total_addresses; i++) {
							var interface_ipv6_address = interface.concat("_ipv6_").concat(i.toString());
							if(document.getElementById(interface_ipv6_address) == null){
								if (i == 0){
									$('#root_ipv6_address').clone().attr('id', interface_ipv6_address).insertAfter('#'.concat(interface_ipv6, ' #root_ipv6_address'));
								} else {
									$('#root_ipv6_address').clone().attr('id', interface_ipv6_address).insertAfter('#'.concat(interface_ipv6, ' #',interface_ipv6, '_', (i - 1).toString()));
								}
								$(document.getElementById(interface_ipv6_address)).removeClass("hidden");
							}
							$(document.getElementById(interface_ipv6_address))[0].childNodes[2].innerText = data.status[interface].ip6config.address[i];
						}
					// Remove unneeded entries
					var total_displayed = document.getElementById(interface).getElementsByClassName("ipv6_address").length;
					for (var i = (total_displayed - 1); i > total_addresses; i--) {
						consoleLog(i);
						$(document.getElementById(interface).getElementsByClassName("ipv6_address")[i]).remove();
					}

					$(document.getElementById(interface).getElementsByClassName("ip6config")[0]).removeClass("hidden");
					// IPv6 Gateway
					document.getElementById(interface).getElementsByClassName("ipv6_gateway")[0].childNodes[2].innerText = data.status[interface].ip6config.gateway;
				} else {
					$(document.getElementById(interface).getElementsByClassName("ip6config")[0]).addClass("hidden");
				}
				// Active Access Point
				if (data.status[interface].activeaccesspoint){
					$(document.getElementById(interface).getElementsByClassName("activeaccesspoint")[0]).removeClass("hidden");
					// SSID
					document.getElementById(interface).getElementsByClassName("ssid")[0].childNodes[2].innerText = data.status[interface].activeaccesspoint.ssid;
					// BSSID
					document.getElementById(interface).getElementsByClassName("bssid")[0].childNodes[2].innerText = data.status[interface].activeaccesspoint.bssid;
					// Frequency
					document.getElementById(interface).getElementsByClassName("frequency")[0].childNodes[2].innerText = data.status[interface].activeaccesspoint.frequency;
					// Signal Strength
					document.getElementById(interface).getElementsByClassName("strength")[0].childNodes[2].innerText = data.status[interface].activeaccesspoint.strength;
					// Progress Bar
					$(document.getElementById(interface).getElementsByClassName("progress_parent")[0]).removeClass("hidden");
					progress_bar = $(document.getElementById(interface).getElementsByClassName("progress-bar")[0]);
					progress_bar.removeClass("progress-bar-danger progress-bar-warning progress-bar-success hidden");
					if (data.status[interface].activeaccesspoint.strength == 0){ //Not connected
						progress_bar.addClass("progress-bar-danger");
						progress_bar.css('width',data.status[interface].activeaccesspoint.strength.toString().concat("%"));
					} else if (data.status[interface].activeaccesspoint.strength < 30){ //red
						progress_bar.addClass("progress-bar-danger");
						progress_bar.css('width',data.status[interface].activeaccesspoint.strength.toString().concat("%"));
					} else if (data.status[interface].activeaccesspoint.strength < 50){ //yellow
						progress_bar.addClass("progress-bar-warning");
						progress_bar.css('width',data.status[interface].activeaccesspoint.strength.toString().concat("%"));
					} else { //green
						progress_bar.addClass("progress-bar-success");
						progress_bar.css('width',data.status[interface].activeaccesspoint.strength.toString().concat("%"));
					}
					progress_bar.innerHTML = data.status[interface].activeaccesspoint.strength;
				} else {
					$(document.getElementById(interface).getElementsByClassName("activeaccesspoint")[0]).addClass("hidden");
				}
				// Wireless
				if (data.status[interface].wireless){
					$(document.getElementById(interface).getElementsByClassName("wireless")[0]).removeClass("hidden");
					// HW Address
					document.getElementById(interface).getElementsByClassName("wireless_hwaddress")[0].childNodes[2].innerText = data.status[interface].wireless.hwaddress;
					// Bit Rate
					document.getElementById(interface).getElementsByClassName("bitrate")[0].childNodes[2].innerText = data.status[interface].wireless.bitrate;
				} else {
					$(document.getElementById(interface).getElementsByClassName("wireless")[0]).addClass("hidden");
				}
				// Wired
				if (data.status[interface].wired){
					$(document.getElementById(interface).getElementsByClassName("wired")[0]).removeClass("hidden");
					// HW Address
					document.getElementById(interface).getElementsByClassName("wired_hwaddress")[0].childNodes[2].innerText = data.status[interface].wired.hwaddress;
					// Speed
					document.getElementById(interface).getElementsByClassName("speed")[0].childNodes[2].innerText = data.status[interface].wired.speed;
				} else {
					$(document.getElementById(interface).getElementsByClassName("wired")[0]).addClass("hidden");
				}
			}
			setIntervalUpdate(updateStatus);
		}
		catch {}
		return;
	})
	.fail(function(data) {
		consoleLog(data);
		consoleLog("Failed to get status, retrying.");
	});
}

function setIntervalUpdate(functionName){
	setTimeout(functionName, 3000)
}

function clickStatusPage(retry) {
	$("li").removeClass("active");
	$("#networking_main_menu>ul>li.active").removeClass("active");
	$("#networking_status").addClass("active");
	clearReturnData();
	$("#helpText").html("This page shows the current state of networking");
	$(".infoText").addClass("hidden");
	$.ajax({
		url: "plugins/networking/html/status.html",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function( data ) {
		$('#main_section').html(data);
		setIntervalUpdate(updateStatus);
	})
	.fail(function() {
		consoleLog("Error, couldn't get status.html.. retrying");
		if (retry < 5){
			retry++;
			$("#networking_status").removeClass("active");
			clickStatusPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function checkUUID(uuid) {
	var regexUUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
	return regexUUID.test(uuid);
}

function checkConnectionValues(){
	var result = true;
	pspDelay = document.getElementById("pspDelay");
	keymgmt = document.getElementById("key-mgmt");
	psk = document.getElementById("psk");
	ssid = document.getElementById("ssid");
	uuid = document.getElementById("uuid");

	if (!(parseInt(pspDelay.value) >= pspDelay.min && parseInt(pspDelay.value) <= pspDelay.max)){
		$("#pspDelayDisplay").addClass("has-error");
		result = false;
	} else {
		$("#pspDelayDisplay").removeClass("has-error");
	}
	if (keymgmt.value == "wpa-psk") {
		if (!(psk.value.length >= 8 && psk.value.length <= 64)){
			$("#pskDisplay").addClass("has-error");
			result = false;
		} else {
			$("#pskDisplay").removeClass("has-error");
		}
	}

	if (ssid.value == ''){
		("#SSIDDisplay").addClass("has-error");
		result = false;
	} else {
		$("#SSIDDisplay").removeClass("has-error");
	}

	if (uuid.value != ''){
		if (!checkUUID(uuid.value)) {
			$("#UUIDDisplay").addClass("has-error");
			result = false;
		} else {
			$("#UUIDDisplay").removeClass("has-error");
		}
	}

	return result;
}

function clearConnectionInts(){
	$("#pspDelayDisplay").removeClass("has-error");
}

function cleanup_output(value){
	if (value == null){
		return '';
	}
	return value;
}

function updateGetConnectionPage(uuid,retry){
	var data = {
			UUID: uuid,
		}
	$.ajax({
		url: "edit_connection",
		type: "POST",
		data: JSON.stringify(data),
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		var certs = {
			client_cert:"",
			private_key:"",
			ca_cert:"",
			pac_file:"",
		}
		document.getElementById("uuid").setAttribute("disabled","");
		document.getElementById("uuid").value = msg.connection.connection.uuid;
		document.getElementById("id").value = msg.connection.connection.id;
		document.getElementById("ssid").value = char_code_array_to_string(msg.connection['802-11-wireless'].ssid);
		document.getElementById("clientName").value = cleanup_output(msg.connection['802-11-wireless'].clientName);
		if (msg.connection['802-11-wireless'].txpower){
			if (msg.connection['802-11-wireless'].txpower == 0){
				document.getElementById("txPower").value = "Auto";
			} else {
				document.getElementById("txPower").value = msg.connection['802-11-wireless'].txpower;
			}
		}

		switch(msg.connection['802-11-wireless'].band) {
			case 'all':
				document.getElementById("band").selectedIndex = 0;
				break;
			case 'a':
				document.getElementById("band").selectedIndex = 1;
				break;
			case 'bg':
				document.getElementById("band").selectedIndex = 2;
				break;
			default:
				document.getElementById("band").selectedIndex = 0;
		}

		switch(msg.connection['802-11-wireless-security']['auth-alg']) {
			case 'open':
				document.getElementById("auth-alg").selectedIndex = 0;
				break;
			case 'shared':
				document.getElementById("auth-alg").selectedIndex = 1;
				break;
			case 'leap':
				document.getElementById("auth-alg").selectedIndex = 2;
				break;
			default:
				document.getElementById("auth-alg").selectedIndex = 0;
		}

		switch (msg.connection['802-11-wireless-security']['key-mgmt']){
				case "none":
					document.getElementById("key-mgmt").selectedIndex = 0;
					break;
				case "static":
					document.getElementById("key-mgmt").selectedIndex = 1;
					break;
				case "ieee8021x":
					document.getElementById("key-mgmt").selectedIndex = 2;
					break;
				case "wpa-psk":
					document.getElementById("key-mgmt").selectedIndex = 3;
					break;
				case "wpa-eap":
					document.getElementById("key-mgmt").selectedIndex = 4;
					break;
				default:
					break;
		}

		if (msg.connection['802-11-wireless-security'].eap){
			switch (msg.connection['802-11-wireless-security'].eap[0]){
					case "leap":
						document.getElementById("eap").selectedIndex = 0;
						break;
					case "md5":
						document.getElementById("eap").selectedIndex = 1;
						break;
					case "tls":
						document.getElementById("eap").selectedIndex = 2;
						break;
					case "peap":
						document.getElementById("eap").selectedIndex = 3;
						break;
					case "ttls":
						document.getElementById("eap").selectedIndex = 4;
						break;
					case "pwd":
						document.getElementById("eap").selectedIndex = 5;
						break;
					case "fast":
						document.getElementById("eap").selectedIndex = 6;
						break;
					default:
						break;
			}
		}

		switch(msg.connection['802-11-wireless'].powersave) {
			case 0:
				document.getElementById("powersave").selectedIndex = 0;
				break;
			case 1:
				document.getElementById("powersave").selectedIndex = 1;
				break;
			case 2:
				document.getElementById("powersave").selectedIndex = 2;
				break;
			case 3:
				document.getElementById("powersave").selectedIndex = 2;
				break;
			default:
				document.getElementById("powersave").selectedIndex = 0;
		}
		if (msg.connection['802-11-wireless-security']['key-mgmt'] == 'static'){
			document.getElementById("wep-tx-keyidx").selectedIndex =  msg.connection['802-11-wireless-security']['wep-tx-keyidx'];
			document.getElementById("wep-key0").value = cleanup_output(msg.connection['802-11-wireless-security']['wep-key0']);
			document.getElementById("wep-key1").value = cleanup_output(msg.connection['802-11-wireless-security']['wep-key1']);
			document.getElementById("wep-key2").value = cleanup_output(msg.connection['802-11-wireless-security']['wep-key2']);
			document.getElementById("wep-key3").value = cleanup_output(msg.connection['802-11-wireless-security']['wep-key3']);
		} else if (msg.connection['802-11-wireless-security']['key-mgmt'] == 'wpa-psk'){
			document.getElementById("psk").value =  cleanup_output(msg.connection['802-11-wireless-security'].psk);
		} else if (msg.connection['802-11-wireless-security']['key-mgmt'] == 'wpa-eap' || 'ieee8021x'){
			try {
				document.getElementById("identity").value =  cleanup_output(msg.connection['802-1x'].identity);
				document.getElementById("password-eap").value =  cleanup_output(msg.connection['802-1x'].password);
				document.getElementById("client-cert-password").value =  cleanup_output(msg.connection['802-1x']['client-cert-password']);
				document.getElementById("private-key-password").value =  cleanup_output(msg.connection['802-1x']['private-key-password']);
				document.getElementById("ca-cert-password").value =  cleanup_output(msg.connection['802-1x']['ca-cert-password']);

				certs.client_cert = strip_cert_file_text(msg.connection['802-1x']['client-cert']);
				certs.private_key = strip_cert_file_text(msg.connection['802-1x']['private-key']);
				certs.ca_cert = strip_cert_file_text(msg.connection['802-1x']['ca-cert']);
				certs.pac_file = strip_cert_file_text(msg.connection['802-1x']['pac-file']);
			}
			catch(err){
				consoleLog(err);
			}
			getCerts(certs,5);
		}
		onChangeSecurity();
	})
	.fail(function() {
		consoleLog("Failed to get connection data, retrying");
		if (retry < 5){
			retry++;
			updateGetConnectionPage(connectionName,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function selectedConnection(uuid,retry){
	if(!uuid){
		var uuid = document.getElementById("connectionSelect").value;
	}
	$.ajax({
		url: "plugins/networking/html/addConnection.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			$("#helpText").html("Adjust connection settings.");
			$(".infoText").addClass("hidden");
		},
		error: function (xhr, status) {
			consoleLog("Error, couldn't get addConnection.html");
		},
	})
	.done(function( msg ) {
		updateGetConnectionPage(uuid,0);
	})
	.fail(function() {
		consoleLog("Failed to get get Connection, retrying");
		if (retry < 5){
			retry++;
			selectedConnection(uuid,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function enableAutoConnectionSubmit(){
	$("#applyAutoConnection").removeClass("disabled");
}

function updateConnectionsPage(retry){
	$.ajax({
		url: "connections",
		type: "GET",
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		var x = document.getElementById("connectionSelect");
		x.size = String(msg.NumConfigs);
		var i = 0;
		for (var UUID in msg.connections) {
			var friendly_connection_name = msg.connections[UUID] + "(" + UUID + ")"
			var option = document.createElement("option");
			option.text = friendly_connection_name;
			option.value = UUID;
			x.add(option);
			if (UUID == msg.currentConfig){
				x.selectedIndex = i;
				option.id = "activeConnection";
				var helpText = document.getElementById("helpText").innerHTML;
				$("#helpText").html(helpText + " Connection " + friendly_connection_name + " is the active networking connection.");
			}
			i++;
		}
	})
	.fail(function() {
		consoleLog("Failed to get connections, retrying");
		if (retry < 5){
			retry++;
			updateConnectionsPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function activateConnection(retry){
	var current_connection = document.getElementById("activeConnection");
	var connection_to_activate = document.getElementById("connectionSelect");
	var data = {
			UUID: connection_to_activate.value,
	}
	consoleLog("Activating connection " + connection_to_activate.value);
	$.ajax({
		url: "activate_connection",
		type: "POST",
		data: JSON.stringify(data),
		contentType: "application/json",
		success: function (data) {
		},
		error: function (xhr, status) {
			consoleLog("Error, couldn't get activate_connection");
		},
	})
	.done(function( msg ) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		SDCERRtoString(msg.SDCERR);
		if (msg.SDCERR == defines.SDCERR.SDCERR_SUCCESS){
			try {
				current_connection.removeAttribute("id");
			}catch(err){
				consoleLog("No current connection: " + err);
			}
			connection_to_activate[connection_to_activate.selectedIndex].setAttribute("id", "activeConnection");
			$("#helpText").html("These are the current networking connections. Connection " + connection_to_activate[connection_to_activate.selectedIndex].text + " is the active connection.");
		}
	})
	.fail(function() {
		consoleLog("Failed to activate connection, retrying");
		if (retry < 5){
			retry++;
			activateConnection(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function showRenameConnection(){
	$("#newConnectionNameDisplay").removeClass("hidden");
}

function removeConnection(){
	var connectionSelect = document.getElementById("connectionSelect");
	var activeConnection = document.getElementById("activeConnection");
	var connection_to_remove = {
		UUID: connectionSelect.value
	}
	if (connectionSelect.value != activeConnection.value){
		$.ajax({
			url: "remove_connection",
			type: "POST",
			data: JSON.stringify(connection_to_remove),
			contentType: "application/json",
		})
		.done(function( msg ) {
			if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
				expiredSession();
				return;
			}
			SDCERRtoString(msg.SDCERR);
			if (document.getElementById("returnDataNav").innerHTML == "Success"){
				for(var i = 0; i < connectionSelect.options.length; i++) {
					if (connectionSelect.value == connectionSelect.options[i].value){
						connectionSelect.options.remove(i);
						connectionSelect.size = connectionSelect.size - 1;
					}
				}
				connectionSelect.selectedIndex = activeConnection.index;
			}
		});
	} else {
		CustomErrMsg("Can't delete active connection");
	}
};

function clickConnectionEditPage(retry) {
	$.ajax({
		url: "plugins/networking/html/connections.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$("li").removeClass("active");
			$("#networking_main_menu>ul>li.active").removeClass("active");
			$("#networking_edit").addClass("active");
			$('#main_section').html(data);
			clearReturnData();
			$("#helpText").html("These are the current networking connections.");
			$(".infoText").addClass("hidden");
			setTimeout(updateConnectionsPage(retry),1000);
		},
	})
	.fail(function() {
		consoleLog("Error, couldn't get connections.html.. retrying");
		if (retry < 5){
			retry++;
			clickConnectionEditPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function getAddConnectionList(retry){
	$.ajax({
		url: "connections",
		type: "GET",
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
	})
	.fail(function() {
		consoleLog("Failed to get number of connections, retrying");
		if (retry < 5){
			retry++;
			getAddConnectionList(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickAddConnectionPage(retry) {
	$.ajax({
		url: "plugins/networking/html/addConnection.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			var connection = {
				client_cert:"",
				private_key:"",
				ca_cert:"",
				pac_file:"",
			}
			getCerts(connection,0);
			$("li").removeClass("active");
			$("#networking_main_menu>ul>li.active").removeClass("active");
			$("#networking_Add").addClass("active");
			$("#helpText").html("Enter the name of the connection you would like to add.");
			$(".infoText").addClass("hidden");
		},
	})
	.done(function( msg ) {
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
	})
	.fail(function() {
		consoleLog("Error, couldn't get addConnection.html.. retrying");
		if (retry < 5){
			retry++;
			clickAddConnectionPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function updateAddConnection(){
	if ($('#advancedOptions').attr('aria-expanded') == "false"){
		document.getElementById("advancedOptions").innerHTML = "Hide advanced options";
	} else {
		document.getElementById("advancedOptions").innerHTML = "Show advanced options";
	}
}

function addConnection(){
	id = document.getElementById("id").value.trim();
	var id_array = [];
	for (var i = 0, len = id.length; i < len; i++) {
		id_array[i] = id.charCodeAt(i);
	}
	ssid = document.getElementById("ssid").value;
	var ssid_array = [];
	for (var i = 0, len = ssid.length; i < len; i++) {
		ssid_array[i] = ssid.charCodeAt(i);
	}
	var txpower = document.getElementById("tx-power").value;
	var txpower_int = parseInt(txpower);
	if (txpower.toLowerCase() == "auto" || txpower_int <= 0){
		txpower = 0;
		document.getElementById("tx-power").value = "Auto";
	}
	psk = document.getElementById("psk").value;
	var psk_array = [];
	for (var i = 0, len = psk.length; i < len; i++) {
		psk_array[i] = psk.charCodeAt(i);
	}
	if (id != ""){
		var new_connection = {
			uuid: document.getElementById("uuid").value,
			id: id_array,
			ssid: ssid_array,
			clientName: document.getElementById("clientName").value,
			txpower: txpower,
			authalg: document.getElementById("auth-alg").value,
			leapusername: document.getElementById("leap-username").value,
			leappassword: document.getElementById("leap-password").value,
			eap: document.getElementById("eap").value,
			//FIXME phase2auth should be a checkbox, not limited to one value
			phase2auth: document.getElementById("phase2-auth").value,
			keymgmt: document.getElementById("key-mgmt").value,
			band: document.getElementById("band").value,
			powersave: parseInt(document.getElementById("powersave").value),
			pspDelay: parseInt(document.getElementById("pspDelay").value),
			weptxkeyidx: parseInt(document.getElementById("wep-tx-keyidx").value),
			wepkey0: document.getElementById("wep-key0").value,
			wepkey1: document.getElementById("wep-key1").value,
			wepkey2: document.getElementById("wep-key2").value,
			wepkey3: document.getElementById("wep-key3").value,
			psk: psk_array,
			identity: document.getElementById("identity").value,
			password: document.getElementById("password-eap").value,
			clientcert: document.getElementById("client-cert").value,
			clientcertpassword: document.getElementById("client-cert-password").value,
			cacert: document.getElementById("ca-cert").value,
			cacertpassword: document.getElementById("ca-cert-password").value,
			privatekey: document.getElementById("private-key").value,
			privatekeypassword: document.getElementById("private-key-password").value,
			pacfile: document.getElementById("pac-file").value,
		}
		consoleLog(new_connection);
		if (!checkConnectionValues()){
			CustomErrMsg("Invalid Value");
			return;
		}
		$.ajax({
			url: "add_connection",
			type: "POST",
			data: JSON.stringify(new_connection),
			contentType: "application/json",
		})
		.done(function( msg ) {
			consoleLog(msg);
			consoleLog(msg.SDCERR);
			if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
				expiredSession();
				return;
			}
			SDCERRtoString(msg.SDCERR);
			if (msg.SDCERR == defines.SDCERR.SDCERR_SUCCESS){
				clearConnectionInts();
			}
		});
	} else {
		CustomErrMsg("Connection name can't be empty");
		consoleLog("Name is null");
	}
};

function regDomainToString(regDomain){
	switch(regDomain) {
		case defines.PLUGINS.networking.REG_DOMAIN.REG_FCC:
			return "FCC";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_ETSI:
			return "ETSI";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_TELEC:
			return "TELEC";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_WW:
			return "WW";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_KCC:
			return "KCC";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_CA:
			return "CA";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_FR:
			return "FR";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_GB:
			return "GB";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_AU:
			return "AU";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_NZ:
			return "NZ";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_CN:
			return "CN";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_BR:
			return "BR";
		case defines.PLUGINS.networking.REG_DOMAIN.REG_RU:
			return "RU";
		default:
			return "Unknown Regulatory Domain";
	}
}

function scanToConnection(){
	connectionName_Value = document.getElementById("connectionNameHidden").value;
	var connectionName_Array = [];
	for (var i = 0, len = connectionName_Value.length; i < len; i++) {
		connectionName_Array[i] = connectionName_Value.charCodeAt(i);
	}
	selectedConnection(connectionName_Array,0);
	$("li").removeClass("active");
	$("#networking_main_menu>ul>li.active").removeClass("active");
	$("#submenuEdit").addClass("active");

}

function addScanConnection(retry){
	id = document.getElementById("connectionName").value.trim();
	if (id == ""){
		$("#connectionNameDisplay").addClass("has-error");
		$("#connectionName").popover({content:'Please enter connection name',placement:'bottom'});
		$("#connectionName").popover('show')
		return;
	}

	var id_array = [];
	for (var i = 0, len = id.length; i < len; i++) {
		id_array[i] = id.charCodeAt(i);
	}
	ssid = document.getElementById("newSSID").value;
	var ssid_array = [];
	for (var i = 0, len = ssid.length; i < len; i++) {
		ssid_array[i] = ssid.charCodeAt(i);
	}
	var new_connection = {
		id: id_array,
		ssid: ssid_array,
		keymgmt: document.getElementById("security").getAttribute("keymgmt"),
		eap: 'peap',
		identity: 'foobar',
	}
	$.ajax({
		url: "add_connection",
		type: "POST",
		data: JSON.stringify(new_connection),
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		consoleLog(msg.SDCERR);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		SDCERRtoString(msg.SDCERR);
		if (document.getElementById("returnDataNav").innerHTML == "Success"){
			document.getElementById("goToConnection").textContent = "Edit Connection " + id;
			$("#goToConnectionDisplay").removeClass("hidden");
			document.getElementById("connectionNameHidden").value = id;
			document.getElementById("addTable").reset();
		}
	})
	.fail(function() {
		consoleLog("Error, couldn't new_connection.. retrying");
		if (retry < 5){
			retry++;
			getScan(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function allowDrop(ev){
	ev.preventDefault();
}

function drag(ev){
	var table = document.getElementById("scanTable");
	var index = $(ev.currentTarget).index() + 1;
	if (index > 0){
		ev.dataTransfer.setData("ssid", table.rows[index].cells[0].innerText);
		ev.dataTransfer.setData("security",table.rows[index].cells[4].innerHTML);
		ev.dataTransfer.setData("keymgmt",table.rows[index].getAttribute("keymgmt"));
	}
}

function drop(ev){
	ev.preventDefault();
	var table = document.getElementById("addTable");
	document.getElementById("newSSID").value = ev.dataTransfer.getData("ssid");
	document.getElementById("security").value = ev.dataTransfer.getData("security");
	document.getElementById("security").setAttribute("keymgmt",ev.dataTransfer.getData("keymgmt"));
	$("#connectionNameDisplay").removeClass("has-error");
	$("#addScanDisplay").removeClass("hidden");
}

function getScan(retry){
	$.ajax({
		url: "wifi_scan",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		if (msg.SDCERR == defines.SDCERR.SDCERR_NO_HARDWARE || msg.SDCERR == defines.SDCERR.SDCERR_FAIL){
			$("#updateProgressDisplay").addClass("hidden");
			$("#status-hardware").removeClass("hidden");
		} else {
			var table = document.getElementById("scanTable");
			for (var ap in msg["accesspoints"]){
				var row = table.insertRow(-1);
				row.setAttribute('draggable', true);
				row.setAttribute('ondragstart', 'drag(event)');
				row.setAttribute('keymgmt', msg["accesspoints"][ap].keymgmt);
				var cell0 = row.insertCell(0);
				var cell1 = row.insertCell(1);
				var cell2 = row.insertCell(2);
				var cell3 = row.insertCell(3);
				var cell4 = row.insertCell(4);
				if (msg["accesspoints"][ap].ssid != ""){
					cell0.innerHTML = msg["accesspoints"][ap].ssid;
				}
				cell1.innerHTML = msg["accesspoints"][ap].bssid;
				cell2.innerHTML = msg["accesspoints"][ap].freq;
				cell3.innerHTML = msg["accesspoints"][ap].strength;
				cell4.innerHTML = msg["accesspoints"][ap].security;
				row.onclick=function(){
					document.getElementById("newSSID").value = this.cells[0].innerText;
					document.getElementById("security").value = this.cells[4].innerHTML;
					document.getElementById("security").setAttribute("keymgmt",this.getAttribute("keymgmt"));
					$("#connectionNameDisplay").removeClass("has-error");
					$("#addScanDisplay").removeClass("hidden");
				};
			}
			$("#updateProgressDisplay").addClass("hidden");
			$("#scanTableDisplay").removeClass("hidden");
			$("#emptyNode").remove();
			$(function(){
				$("#scanTable").tablesorter( {sortList: [[0,0], [1,0]]} );
			});
		}
	})
	.fail(function() {
		consoleLog("Error, couldn't get networking scan.. retrying");
		if (retry < 5){
			retry++;
			getScan(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickScanPage(retry){
	$.ajax({
		url: "plugins/networking/html/scan.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
			$("#networking_main_menu>ul>li.active").removeClass("active");
			$("#wifi_scan").addClass("active");
			$("#helpText").html("Scan for wireless networks");
			$(".infoText").addClass("hidden");
		},
	})
	.done(function( data ) {
		getScan(0);
	})
	.fail(function() {
		consoleLog("Error, couldn't get scan.html.. retrying");
		if (retry < 5){
			retry++;
			clickScanPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function allowCertUpload(filepath){
	var fileName = filepath.replace(/^.*\\/, "")
	document.getElementById("submitCertButton").innerHTML = "Upload " + fileName;
	$("#submitCertButton").removeClass("disabled");
}

function char_code_array_to_string(code_array){
	var string_array = [];
	for(var i = 0; i < code_array.length; i++) {
		if (code_array[i] != 0){
			string_array.push(String.fromCharCode(code_array[i]));
		}
	}
	return string_array.join('');
}

function strip_cert_file_text(cert){
	if (cert != null){
		var cert_string = char_code_array_to_string(cert);
		return cert_string.trim().replace('file:///etc/ssl/','');
	}

	return "";
}

function generateCertList(connection,certs){
	var client_cert_id = document.getElementById("client-cert");
	var private_key_id = document.getElementById("private-key");
	var ca_cert_id = document.getElementById("ca-cert");
	var pac_file_id = document.getElementById("pac-file");
	var index = 1;

	function exists(id,option){
		var exists = false;
		$("#" + id + " option").each(function(){
			if (this.text === option) {
				exists = true;
				return false;
			}
		});
		if (exists == true){
			return true;
		}
		return false;
	}

	for (var key in certs) {
		var option_client_cert = document.createElement("option");
		var option_private_key = document.createElement("option");
		var option_ca_cert = document.createElement("option");
		var option_pac_file = document.createElement("option");
		option_client_cert.text = certs[key];
		option_private_key.text = certs[key];
		option_ca_cert.text = certs[key];
		option_pac_file.text = certs[key];
		// Add unique certs
		if (!exists("client_cert",certs[key])){
			client_cert_id.add(option_client_cert);
			if(option_client_cert.text === connection.client_cert) {
				client_cert_id.selectedIndex = index;
			}
		}
		if (!exists("private_key",certs[key])){
			private_key_id.add(option_private_key);
			if(option_private_key.text === connection.private_key) {
				private_key_id.selectedIndex = index;
			}
		}
		if (!exists("ca_cert",certs[key])){
			ca_cert_id.add(option_ca_cert);
			if(option_ca_cert.text === connection.ca_cert) {
				ca_cert_id.selectedIndex = index;
			}
		}
		if (!exists("pac_file",certs[key])){
			pac_file_id.add(option_pac_file);
			if(option_pac_file.text === connection.pac_file) {
				pac_file_id.selectedIndex = index;
			}
		}
		index++;
	}
}

function getCerts(connection,retry){
	$.ajax({
		url: "get_certificates",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		generateCertList(connection,msg.certs);
	})
	.fail(function() {
		consoleLog("Error, couldn't get certs.. retrying");
		if (retry < 5){
			retry++;
			getCerts(connection,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function getVersion(retry){
	$.ajax({
		url: "version",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		consoleLog(msg);
		document.getElementById("sdk").innerHTML = msg.sdk;
		document.getElementById("chipset").innerHTML = msg.chipset;
		document.getElementById("driver").innerHTML = msg.driver;
		document.getElementById("firmware").innerHTML = msg.firmware;
		document.getElementById("supplicant").innerHTML = msg.supplicant;
		document.getElementById("weblcm_python_webapp").innerHTML = msg.weblcm_python_webapp;
		document.getElementById("build").innerHTML = msg.build;
	})
	.fail(function() {
		consoleLog("Error, couldn't get version.. retrying");
		if (retry < 5){
			retry++;
			getVersion(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickVersionPage(retry){
	$.ajax({
		url: "plugins/networking/html/version.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
			$("#networking_main_menu>ul>li.active").removeClass("active");
			$("#networking_version").addClass("active");
			$("#helpText").html("System version information");
			$(".infoText").addClass("hidden");
		},
	})
	.done(function( data ) {
		getVersion(0);
	})
	.fail(function() {
		consoleLog("Error, couldn't get version.html.. retrying");
		if (retry < 5){
			retry++;
			clickGlobalsPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}
