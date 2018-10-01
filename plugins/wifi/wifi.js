// Copyright (c) 2017, Laird
// Contact: ews-support@lairdtech.com

function wifiAUTORUN(retry){
	clickStatusPage(0);
}

function updateInfoText(option,retry){
	$.ajax({
		url: "plugins/wifi/html/info.html",
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
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		if (retry < 5){
			retry++;
			$("#wifi_status").removeClass("active");
			clickStatusPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function CARDSTATEtoString(CARDSTATE){
	switch(CARDSTATE) {
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_UNKNOWN:
			return "Unknown";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_UNMANAGED:
			return "Unmanaged";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_UNAVAILABLE:
			return "Unavailable";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_DISCONNECTED:
			return "Disconnected";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_PREPARE:
			return "Preparing";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_NEED_AUTH:
			return "Need Auth";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_IP_CONFIG:
			return "Connecting";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_IP_CHECK:
			return "IP Check";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_SECONDARIES:
			return "Secondaries";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_ACTIVATED:
			return "Activated";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_DEACTIVATING:
			return "Deactivating";
		case defines.PLUGINS.wifi.NMDeviceState.NM_DEVICE_STATE_FAILED:
			return "Failed";
		default:
			return "Unknown State";
	}
}

function onChangePowersave(){
	var powerSave = parseInt(document.getElementById("powerSave").value);
	switch (powerSave){
		case defines.PLUGINS.wifi.POWERSAVE.POWERSAVE_OFF:
		case defines.PLUGINS.wifi.POWERSAVE.POWERSAVE_MAX:
			$("#pspDelayDisplay").addClass("hidden");
			break;
		case defines.PLUGINS.wifi.POWERSAVE.POWERSAVE_FAST:
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
	var getStatusJSON = $.getJSON( "wifi_status", function( data ) {
		consoleLog(data)
		if (data.SESSION == defines.SDCERR.SDCERR_FAIL){
			$("#loggout").addClass("hidden");
			$("#loggin").removeClass("hidden");
			$(".locked").addClass("hidden");
		}
		$("#updateProgressDisplay").addClass("hidden");
		if (data.SDCERR == defines.SDCERR.SDCERR_NO_HARDWARE || data.SDCERR == defines.SDCERR.SDCERR_FAIL){
			$("#status-success").addClass("hidden");
			$("#status-hardware").removeClass("hidden");
		} else {
			$("#status-success").removeClass("hidden");
			$("#status-hardware").addClass("hidden");
			var strength = data.strength.toString().concat("%");
			var SSID_Array = [];

			if (data.ssid != null){
				for(var i = 0; i < data.ssid.length; i++) {
					SSID_Array.push(String.fromCharCode(data.ssid[i]));
				}
				$('#ssid').html(SSID_Array.join(''));
			}

			$('#cardState').html(CARDSTATEtoString(data.cardState));
			$('#configName').html(data.configName);
			$('#channel').html(data.channel);
			$('#strength').html(strength);
			$('#clientName').html(data.clientName);
			$('#client_MAC').html(data.client_MAC);
			$('#client_IP').html(data.client_IP);
			$('#APName').html(data.APName);
			$('#AP_MAC').html(data.AP_MAC);
			$('#AP_IP').html(data.AP_IP);

			var IPv6 = document.getElementById("IPv6");
			while (IPv6.hasChildNodes()) {
				IPv6.removeChild(IPv6.lastChild);
			}
			if (data.IPv6.length > 0){
				for (var i = 0; i < data.IPv6.length; i++) {
					var divAddress = document.createElement("div");
					divAddress.className = "col-xs-6 col-sm-6 placeholder text-left";
					var divStrong = document.createElement("strong");
					var strongText = document.createTextNode("IPv6: ");
					var divSpan = document.createElement("span");
					var spanText = document.createTextNode(data.IPv6[i].address);
					divAddress.appendChild(divStrong);
					divStrong.appendChild(strongText);
					divAddress.appendChild(divSpan);
					divSpan.appendChild(spanText);
					IPv6.appendChild(divAddress);
				}
			}

			$('#bitRate').html(data.bitRate);
			$('#txPower').html(data.txPower);
			$('#beaconPeriod').html(data.beaconPeriod);
			$('#DTIM').html(data.DTIM);

			$("#progressbar").removeClass("progress-bar-danger progress-bar-warning progress-bar-success");
			if (data.strength == 0){ //Not connected
				$("#progressbar").addClass("progress-bar-danger");
				$("#progressbar").css('width',strength);
			} else if (data.strength < 30){ //red
				$("#progressbar").addClass("progress-bar-danger");
				$("#progressbar").css('width',strength);
			} else if (data.strength < 50){ //yellow
				$("#progressbar").addClass("progress-bar-warning");
				$("#progressbar").css('width',strength);
			} else { //green
				$("#progressbar").addClass("progress-bar-success");
				$("#progressbar").css('width',strength);
			}
			document.getElementById("progressbar").innerHTML = strength;
		}
	})
	.fail(function(data) {
		consoleLog(data);
		consoleLog("Failed to get status.php, retrying.");
		setIntervalUpdate(updateStatus);
	});
}

function setIntervalUpdate(functionName){
	if (!intervalId){
		intervalId = setInterval(functionName, 1000);
	} else {
		consoleLog("Interval already set");
	}
}

function clickStatusPage(retry) {
	if (intervalId){
		consoleLog("Status already active");
	} else {
		$("li").removeClass("active");
		$("#wifi_status").addClass("active");
		clearReturnData();
		$("#helpText").html("This page shows the current state of WiFi");
		$(".infoText").addClass("hidden");
		$.ajax({
			url: "plugins/wifi/html/status.html",
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
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			if (retry < 5){
				retry++;
				$("#wifi_status").removeClass("active");
				clickStatusPage(retry);
			} else {
				consoleLog("Retry max attempt reached");
			}
		});
	}
}

function checkProfileValues(){
	var result = true;
	pspDelay = document.getElementById("pspDelay");
	keymgmt = document.getElementById("key-mgmt");
	psk = document.getElementById("psk");

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

	return result;
}

function clearProfileInts(){
	$("#pspDelayDisplay").removeClass("has-error");
}

function submitProfile(retry){
	profileName_Value = document.getElementById("profileName").value;
	var profileName_Array = [];
	for (var i = 0, len = profileName_Value.length; i < len; i++) {
		profileName_Array[i] = profileName_Value.charCodeAt(i);
	}
	SSID_Value = document.getElementById("SSID").value;
	var CharCode_Array = [];
	for (var i = 0, len = SSID_Value.length; i < len; i++) {
		CharCode_Array[i] = SSID_Value.charCodeAt(i);
	}
	var txPower_value = document.getElementById("txPower").value;
	var txPower = parseInt(txPower_value);
	if (txPower_value.toLowerCase() == "auto" || txPower <= 0){
		txPower = 0;
		document.getElementById("txPower").value = "Auto";
	} else if (txPower > defines.PLUGINS.wifi.MAX_TX_POWER.MAX_MW) {
		if (defines.PLUGINS.wifi.MAX_TX_POWER.MAX_MW != 0){
			CustomErrMsg("TX Power is out of range");
			return;
		}
	}
	PSK_Value = document.getElementById("psk").value;
	var PSK_Array = [];
	for (var i = 0, len = PSK_Value.length; i < len; i++) {
		PSK_Array[i] = PSK_Value.charCodeAt(i);
	}
	var profileData = {
		profileName: profileName_Array,
		SSID: CharCode_Array,
		clientName: document.getElementById("clientName").value,
		txPower: txPower,
		authType: parseInt(document.getElementById("authType").value),
		eapType: parseInt(document.getElementById("eapType").value),
		wepType: parseInt(document.getElementById("wepType").value),
		radioMode: parseInt(document.getElementById("radioMode").value),
		powerSave: parseInt(document.getElementById("powerSave").value),
		pspDelay: parseInt(document.getElementById("pspDelay").value),
		wepIndex: parseInt(document.getElementById("wepIndex").value),
		index1: document.getElementById("index1").value,
		index2: document.getElementById("index2").value,
		index3: document.getElementById("index3").value,
		index4: document.getElementById("index4").value,
		psk: PSK_Array,
		userName: document.getElementById("userName").value,
		passWord: document.getElementById("passWord").value,
		userCert: document.getElementById("userCert").value,
		userCertPassword: document.getElementById("userCertPassword").value,
		CACert: document.getElementById("CACert").value,
		PACFilename: document.getElementById("PACFilename").value,
		PACPassword: document.getElementById("PACPassword").value,
	}
	consoleLog(profileData);
	if (!checkProfileValues()){
		CustomErrMsg("Invalid Value");
		return;
	}
	$.ajax({
		url: "plugins/wifi/php/setProfile.php",
		type: "POST",
		data: JSON.stringify(profileData),
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		SDCERRtoString(msg.SDCERR);
		$("#submitButton").addClass("disabled");
		if (msg.SDCERR == defines.SDCERR.SDCERR_SUCCESS){
			clearProfileInts();
		}
	})
	.fail(function() {
		consoleLog("Failed to get profile data, retrying");
		if (retry < 5){
			retry++;
			submitProfile(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function SelectedIndex(sel, val) {
	for(var i = 0, j = sel.options.length; i < j; ++i) {
		if(sel.options[i].value == val) {
		sel.selectedIndex = i;
		break;
		}
	}
}

function updateGetProfilePage(profileName,retry){
	var data = {
			profileName: profileName,
		}
	$.ajax({
		url: "plugins/wifi/php/getProfile.php",
		type: "POST",
		data: JSON.stringify(data),
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		document.getElementById("profileName").value = msg.configName;
		var profileName_Array = [];
		if (msg.configName != null){
			for(var i = 0; i < msg.configName.length; i++) {
				profileName_Array.push(String.fromCharCode(msg.configName[i]));
			}
			document.getElementById("profileName").value = profileName_Array.join('');
		}
		document.getElementById("SSID").value = msg.SSID;
		var SSID_Array = [];
		if (msg.SSID != null){
			for(var i = 0; i < msg.SSID.length; i++) {
				SSID_Array.push(String.fromCharCode(msg.SSID[i]));
			}
			document.getElementById("SSID").value = SSID_Array.join('');
		}
		document.getElementById("clientName").value = msg.clientName;
		if (msg.txPower == 0){
			document.getElementById("txPower").value = "Auto";
		} else {
			document.getElementById("txPower").value = msg.txPower;
		}
		document.getElementById("authType").selectedIndex =  msg.authType;
		//If index does not start at 0 and run contiguously we must check against options value
		SelectedIndex(document.getElementById("wepType"),msg.wepType);
		SelectedIndex(document.getElementById("eapType"),msg.eapType);
		SelectedIndex(document.getElementById("radioMode"),msg.radioMode);
		document.getElementById("powerSave").selectedIndex =  msg.powerSave;
		if (msg.powerSave == defines.PLUGINS.wifi.POWERSAVE.POWERSAVE_FAST){
			$("#pspDelayDisplay").removeClass("hidden");
			document.getElementById("pspDelay").value = msg.pspDelay;
		}
		if (msg.wepType == defines.PLUGINS.wifi.WEPTYPE.WEP_ON){
			$("#wepIndexDisplay").removeClass("hidden");
			document.getElementById("wepIndex").selectedIndex =  msg.wepIndex - 1;
			$("#wepTypeOnDisplay").removeClass("hidden");
			document.getElementById("index1").value =  msg.WEPKey1;
			document.getElementById("index2").value =  msg.WEPKey2;
			document.getElementById("index3").value =  msg.WEPKey3;
			document.getElementById("index4").value =  msg.WEPKey4;
		} else if (msg.wepType == defines.PLUGINS.wifi.WEPTYPE.WPA_PSK || msg.wepType == defines.PLUGINS.wifi.WEPTYPE.WPA2_PSK || msg.wepType == defines.PLUGINS.wifi.WEPTYPE.WPA_PSK_AES || msg.wepType == defines.PLUGINS.wifi.WEPTYPE.WPA2_PSK_TKIP){
			$("#pskDisplay").removeClass("hidden");
			document.getElementById("psk").value =  msg.PSK;
		} else if (msg.eapType >= defines.PLUGINS.wifi.EAPTYPE.EAP_LEAP){
			if (msg.eapType > defines.PLUGINS.wifi.EAPTYPE.EAP_LEAP){
				$("#certDisplay").removeClass("hidden");
			}
			$("#eapTypeDisplay").removeClass("hidden");
			$("#userNameDisplay").removeClass("hidden");
			document.getElementById("userName").value =  msg.userName;
			if (!(msg.eapType == defines.PLUGINS.wifi.EAPTYPE.EAP_EAPTLS || msg.eapType == defines.PLUGINS.wifi.EAPTYPE.EAP_PEAPTLS)){
				$("#passWordDisplay").removeClass("hidden");
				document.getElementById("passWord").value =  msg.passWord;
			} else {
				$("#userCertDisplay").removeClass("hidden");
				document.getElementById("userCert").value =  msg.userCert;
				$("#userCertPasswordDisplay").removeClass("hidden");
				document.getElementById("userCertPassword").value =  msg.userCertPassword;
			}
			if (msg.eapType > defines.PLUGINS.wifi.EAPTYPE.EAP_EAPFAST && msg.eapType < defines.PLUGINS.wifi.EAPTYPE.EAP_WAPI_CERT){
				$("#CACertDisplay").removeClass("hidden");
				document.getElementById("CACert").value =  msg.CACert;
			}
			if (msg.eapType == defines.PLUGINS.wifi.EAPTYPE.EAP_EAPFAST){
				$("#PACFilenameDisplay").removeClass("hidden");
				document.getElementById("PACFilename").value =  msg.PACFileName;
				$("#PACPasswordDisplay").removeClass("hidden");
				document.getElementById("PACPassword").value =  msg.PACPassword;
			}
			getCerts(msg,0);
		}
	})
	.fail(function() {
		consoleLog("Failed to get profile data, retrying");
		if (retry < 5){
			retry++;
			updateGetProfilePage(profileName,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function selectedProfile(selectedProfile,retry){
	if(!selectedProfile){
		var selectedProfile_value = document.getElementById("profileSelect").value;
		var selectedProfile_Array = [];
		for (var i = 0, len = selectedProfile_value.length; i < len; i++) {
			selectedProfile_Array[i] = selectedProfile_value.charCodeAt(i);
		}
		var selectedProfile = selectedProfile_Array;
	}
	$.ajax({
		url: "plugins/wifi/html/getProfile.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$('#main_section').html(data);
			clearReturnData();
			$("#helpText").html("Adjust profile settings.");
			$(".infoText").addClass("hidden");
		},
		error: function (xhr, status) {
			consoleLog("Error, couldn't get getProfile.html");
		},
	})
	.done(function( msg ) {
		updateGetProfilePage(selectedProfile,0);
	})
	.fail(function() {
		consoleLog("Failed to get get Profile, retrying");
		if (retry < 5){
			retry++;
			selectedProfile(selectedProfile,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function enableAutoProfileSubmit(){
	$("#applyAutoProfile").removeClass("disabled");
}

function updateSelectProfilePage(retry){
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
		var x = document.getElementById("profileSelect");
		x.size = String(msg.NumConfigs);
		var i = 0;
		for (var UUID in msg.profiles) {
			var friendly_connection_name = msg.profiles[UUID] + "(" + UUID + ")"
			var option = document.createElement("option");
			option.text = friendly_connection_name;
			option.value = UUID;
			x.add(option);
			if (UUID == msg.currentConfig){
				x.selectedIndex = i;
				option.id = "activeProfile";
				var helpText = document.getElementById("helpText").innerHTML;
				$("#helpText").html(helpText + " Profile " + friendly_connection_name + " is the active WiFi profile.");
			}
			i++;
		}
	})
	.fail(function() {
		consoleLog("Failed to get profiles, retrying");
		if (retry < 5){
			retry++;
			updateSelectProfilePage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function activateProfile(retry){
	var current_connection = document.getElementById("activeProfile");
	var connection_to_activate = document.getElementById("profileSelect");
	var data = {
			UUID: connection_to_activate.value,
	}
	consoleLog("Activating profile " + connection_to_activate.value);
	$.ajax({
		url: "activate_connection",
		type: "POST",
		data: JSON.stringify(data),
		contentType: "application/json",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
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
			current_connection.removeAttribute("id");
			connection_to_activate[connection_to_activate.selectedIndex].setAttribute("id", "activeProfile");
			$("#helpText").html("These are the current WiFi profiles. Profile " + connection_to_activate[connection_to_activate.selectedIndex].text + " is the active profile.");
		}
	})
	.fail(function() {
		consoleLog("Failed to activate profile, retrying");
		if (retry < 5){
			retry++;
			activateProfile(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function renameProfile(retry){
	var profileSelect = document.getElementById("profileSelect");
	var selectedProfile = profileSelect.options[profileSelect.selectedIndex].text;
	var selectedProfile_Array = [];
	for (var i = 0, len = selectedProfile.length; i < len; i++) {
		selectedProfile_Array[i] = selectedProfile.charCodeAt(i);
	}
	var	newProfileName_Value = document.getElementById("newProfileName").value.trim();
	var newProfileName_Array = [];
	for (var i = 0, len = newProfileName_Value.length; i < len; i++) {
		newProfileName_Array[i] = newProfileName_Value.charCodeAt(i);
	}
	var profileName = {
			currentName: selectedProfile_Array,
			newName: newProfileName_Array,
	}
	$.ajax({
		url: "plugins/wifi/php/renameProfile.php",
		type: "POST",
		data: JSON.stringify(profileName),
		contentType: "application/json",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
		},
		error: function (xhr, status) {
			consoleLog("Error, couldn't get renameProfile.php");
		},
	})
	.done(function( msg ) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		SDCERRtoString(msg.SDCERR);
		if (document.getElementById("returnDataNav").innerHTML == "Success"){
			var currentActiveProfile = document.getElementById("activeProfile").value;
			for(var i = 0; i < profileSelect.options.length; i++) {
				if (selectedProfile == profileSelect.options[i].text){
					profileSelect.options[i].text = newProfileName_Value;
					if (currentActiveProfile == selectedProfile){
						$("#helpText").html("These are the current WiFi profiles. Profile " + newProfileName_Value + " is the active profile.");
					}
				}
			}
			$("#newProfileNameDisplay").addClass("hidden");
		}
	})
	.fail(function() {
		consoleLog("Failed to rename profile, retrying");
		if (retry < 5){
			retry++;
			renameProfile(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function showRenameProfile(){
	$("#newProfileNameDisplay").removeClass("hidden");
}

function removeProfile(){
	var profileSelect = document.getElementById("profileSelect");
	var activeProfile = document.getElementById("activeProfile");
	var connection_to_remove = {
		UUID: profileSelect.value
	}
	if (profileSelect.value != activeProfile.value){
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
				for(var i = 0; i < profileSelect.options.length; i++) {
					if (profileSelect.value == profileSelect.options[i].value){
						profileSelect.options.remove(i);
						profileSelect.size = profileSelect.size - 1;
					}
				}
				profileSelect.selectedIndex = activeProfile.index;
			}
		});
	} else {
		CustomErrMsg("Can't delete active profile");
	}
};

function submitAutoProfile(retry){
	var rows,index,profile,value;
	var autoProfileList = [];
	var autoProfileValues = [];
	rows = document.getElementById("autoProfileTable").rows;
	for (index = 1; index < rows.length; index++){
		profile = rows[index].cells[0].innerHTML;
		var profileSelect_Array = [];
		for (var i = 0, len = profile.length; i < len; i++) {
			profileSelect_Array[i] = profile.charCodeAt(i);
		}
		value = rows[index].cells[1].children[0].checked;
		autoProfileList[index] = profileSelect_Array;
		autoProfileValues[index] = value;
	}
	var autoProfile = {
		profileList: autoProfileList,
		profileValues: autoProfileValues,
	}
	consoleLog(autoProfile);
	$.ajax({
		url: "plugins/wifi/php/setAutoProfileList.php",
		type: "POST",
		data: JSON.stringify(autoProfile),
		contentType: "application/json",
	})
	.done(function( msg ) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		SDCERRtoString(msg.SDCERR);
		$("#applyAutoProfile").addClass("disabled");
	});
}

function clickProfileEditPage(retry) {
	$.ajax({
		url: "plugins/wifi/html/selectProfile.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$("li").removeClass("active");
			$("#wifi_edit").addClass("active");
			$('#main_section').html(data);
			clearReturnData();
			$("#helpText").html("These are the current WiFi profiles.");
			$(".infoText").addClass("hidden");
			setTimeout(updateSelectProfilePage(retry),1000);
		},
	})
	.fail(function() {
		consoleLog("Error, couldn't get selectProfile.html.. retrying");
		if (retry < 5){
			retry++;
			clickProfileEditPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function getAddProfileList(retry){
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
		consoleLog("Failed to get number of profiles, retrying");
		if (retry < 5){
			retry++;
			getAddProfileList(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickAddProfilePage(retry) {
	$.ajax({
		url: "plugins/wifi/html/addProfile.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$('#main_section').html(data);
			clearReturnData();
			var profile = {
				client_cert:"",
				private_key:"",
				ca_cert:"",
				pac_file:"",
			}
			getCerts(profile,0);
			$("li").removeClass("active");
			$("#wifi_Add").addClass("active");
			$("#helpText").html("Enter the name of the profile you would like to add.");
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
		consoleLog("Error, couldn't get addProfile.html.. retrying");
		if (retry < 5){
			retry++;
			clickAddProfilePage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function updateAddProfile(){
	if ($('#advancedOptions').attr('aria-expanded') == "false"){
		document.getElementById("advancedOptions").innerHTML = "Hide advanced options";
	} else {
		document.getElementById("advancedOptions").innerHTML = "Show advanced options";
	}
}

function addProfile(){
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
		if (!checkProfileValues()){
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
				clearProfileInts();
			}
		});
	} else {
		CustomErrMsg("Profile name can't be empty");
		consoleLog("Name is null");
	}
};

function regDomainToString(regDomain){
	switch(regDomain) {
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_FCC:
			return "FCC";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_ETSI:
			return "ETSI";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_TELEC:
			return "TELEC";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_WW:
			return "WW";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_KCC:
			return "KCC";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_CA:
			return "CA";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_FR:
			return "FR";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_GB:
			return "GB";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_AU:
			return "AU";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_NZ:
			return "NZ";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_CN:
			return "CN";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_BR:
			return "BR";
		case defines.PLUGINS.wifi.REG_DOMAIN.REG_RU:
			return "RU";
		default:
			return "Unknown Regulatory Domain";
	}
}

function scanToProfile(){
	profileName_Value = document.getElementById("profileNameHidden").value;
	var profileName_Array = [];
	for (var i = 0, len = profileName_Value.length; i < len; i++) {
		profileName_Array[i] = profileName_Value.charCodeAt(i);
	}
	selectedProfile(profileName_Array,0);
	$("li").removeClass("active");
	$("#submenuEdit").addClass("active");

}

function addScanProfile(retry){
	id = document.getElementById("profileName").value.trim();
	if (id == ""){
		$("#profileNameDisplay").addClass("has-error");
		$("#profileName").popover({content:'Please enter profile name',placement:'bottom'});
		$("#profileName").popover('show')
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
			document.getElementById("goToProfile").textContent = "Edit Profile " + id;
			$("#goToProfileDisplay").removeClass("hidden");
			document.getElementById("profileNameHidden").value = id;
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
	$("#profileNameDisplay").removeClass("has-error");
	$("#addScanDisplay").removeClass("hidden");
}

function getScan(retry){
	$.ajax({
		url: "wifi_scan",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		if (msg.SDCERR == defines.SDCERR.SDCERR_NO_HARDWARE){
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
					$("#profileNameDisplay").removeClass("has-error");
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
		consoleLog("Error, couldn't get WiFi scan.. retrying");
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
		url: "plugins/wifi/html/scan.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
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

function uploadCert(retry){
	var file_data = $('#fileToUpload').prop('files')[0];
	if (file_data != null){
		var form_data = new FormData();
		form_data.append('file', file_data);
		$.ajax({
			url: 'plugins/wifi/php/upload.php', // point to server-side PHP script
			cache: false,
			contentType: false,
			processData: false,
			data: form_data,
			type: 'POST',
		})
		.done(function( data ) {
			consoleLog(data);
			SDCERRtoString(data.SDCERR);
			if (data.SDCERR ==  defines.SDCERR.SDCERR_SUCCESS){
				clearReturnData();
				$("#submitCertButton").addClass("disabled");
				$("#certFail").addClass("hidden");
				$("#certSuccess").removeClass("hidden");
				var profile = {
					userCert:"",
					CACert:"",
					PACFileName:"",
				}
				var certs = {
					0:file_data.name,
				};
				generateCertList(profile,certs);
			} else {
				SDCERRtoString(data.SDCERR);
				$("#certSuccess").addClass("hidden");
				$("#certFail").removeClass("hidden");
			}
		})
	}
}

function generateCertList(profile,certs){
	var client_cert_id = document.getElementById("client-cert");
	var private_key_id = document.getElementById("private-key");
	var ca_cert_id = document.getElementById("ca-cert");
	var pac_file_id = document.getElementById("pac-file");
	var client_cert_index = client_cert_id.length;
	var private_key_index = private_key_id.length;
	var ca_cert_index = ca_cert_id.length;
	var pac_file_index = pac_file_id.length;

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
			if(option_client_cert.text === profile.client_cert) {
				client_cert_id.selectedIndex = userCert_index;
			}
			client_cert_index++;
		}
		if (!exists("private_key",certs[key])){
			private_key_id.add(option_private_key);
			if(option_private_key.text === profile.private_key) {
				private_key_id.selectedIndex = private_key_index;
			}
			client_cert_index++;
		}
		if (!exists("ca_cert",certs[key])){
			ca_cert_id.add(option_ca_cert);
			if(option_ca_cert.text === profile.ca_cert) {
				ca_cert_id.selectedIndex = ca_cert_index;
			}
			ca_cert_index++;
		}
		if (!exists("pac_file",certs[key])){
			pac_file_id.add(option_pac_file);
			if(option_pac_file.text === profile.pac_file) {
				pac_file_id.selectedIndex = pac_file_index;
			}
			pac_file_index++;
		}
	}
}

function getCerts(profile,retry){
	$.ajax({
		url: "get_certificates",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		consoleLog(msg);
		generateCertList(profile,msg.certs);
	})
	.fail(function() {
		consoleLog("Error, couldn't get getCerts.php.. retrying");
		if (retry < 5){
			retry++;
			getCerts(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function generateLog(retry){
	$.ajax({
		url: "plugins/wifi/php/generateLog.php",
		type: "POST",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		setIntervalUpdate(checkLog);
	})
	.fail(function() {
		consoleLog("Error, couldn't get generateLog.php.. retrying");
		if (retry < 5){
			retry++;
			generateLog(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function removeLog(retry){
	$.ajax({
		url: "plugins/wifi/php/removeLog.php",
		type: "POST",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		document.getElementById("generateLog").textContent = "Generate";
		$("#generateLog").removeClass("disabled");
		$("#downloadLog").addClass("disabled");
	})
	.fail(function() {
		consoleLog("Error, couldn't get removeLog.php.. retrying");
		if (retry < 5){
			retry++;
			removeLog(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function checkLog(){
	var getStatusJSON = $.getJSON( "plugins/wifi/php/checkLog.php", function( data ) {
		if (data.state == "finished"){
			document.getElementById("generateLog").textContent = "Finished";
			$("#generateLog").addClass("disabled");
			$("#downloadLog").removeClass("disabled");
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
		} else if (data.state == "stopped"){
			$("#generateLog").removeClass("disabled");
			$("#downloadLog").addClass("disabled");
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
		} else if (data.state == "running"){
			document.getElementById("generateLog").textContent = "Generating";
			$("#generateLog").addClass("disabled");
			$("#downloadLog").addClass("disabled");
		}
	})
	.fail(function(data) {
		consoleLog("Error, couldn't get checkLog.php.. retrying");
		setIntervalUpdate(checkLog);
	});
}

function submitAdvanced(retry){
	var AdvancedData = {
		suppDebugLevel: parseInt(document.getElementById("suppDebugLevel").value),
		driverDebugLevel: parseInt(document.getElementById("driverDebugLevel").value),
	}
	$.ajax({
		url: "plugins/wifi/php/setAdvanced.php",
		type: "POST",
		data: JSON.stringify(AdvancedData),
		contentType: "application/json",
	})
	.done(function( msg ) {
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		SDCERRtoString(msg.SDCERR);
		$("#submitButton").addClass("disabled");
	})
	.fail(function() {
		consoleLog("Failed to send advanced data, retrying");
		if (retry < 5){
			retry++;
			submitAdvanced(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function getAdvanced(retry){
	$.ajax({
		url: "plugins/wifi/php/getAdvanced.php",
		type: "POST",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		document.getElementById("suppDebugLevel").value = msg.suppDebugLevel;
		document.getElementById("driverDebugLevel").value = msg.driverDebugLevel;
		setIntervalUpdate(checkLog);
	})
	.fail(function() {
		consoleLog("Error, couldn't get getAdvanced.php.. retrying");
		if (retry < 5){
			retry++;
			getAdvanced(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickAdvancedPage(retry){
	$.ajax({
		url: "plugins/wifi/html/advanced.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
			$("#wifi_advanced").addClass("active");
			$("#helpText").html("Advanced configuration options");
			$(".infoText").addClass("hidden");
		},
	})
	.done(function( data ) {
		$('input[type=file]').bootstrapFileInput();
		$('.file-inputs').bootstrapFileInput();
		getAdvanced(0);
	})
	.fail(function() {
		consoleLog("Error, couldn't get advanced.html.. retrying");
		if (retry < 5){
			retry++;
			clickAdvancedPage(retry);
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
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		consoleLog(msg);
		document.getElementById("sdk").innerHTML = msg.sdk;
		document.getElementById("chipset").innerHTML = msg.chipset;
		document.getElementById("driver").innerHTML = msg.driver;
		document.getElementById("firmware").innerHTML = msg.firmware;
		document.getElementById("supplicant").innerHTML = msg.supplicant;
		document.getElementById("lrd_nm_webapp").innerHTML = msg.lrd_nm_webapp;
		document.getElementById("build").innerHTML = msg.build;
	})
	.fail(function() {
		consoleLog("Error, couldn't get version.php.. retrying");
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
		url: "plugins/wifi/html/version.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			if (intervalId){
				clearInterval(intervalId);
				intervalId = 0;
			}
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
			$("#wifi_version").addClass("active");
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
