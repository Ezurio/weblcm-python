// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function swupdateAUTORUN(retry) {
	return;
}

var fw_start;
var fw_reader;
var fw_xhr;
var fw_total_bytes = 0;
var fw_step = 1024*128;

function upload_one_chunk() {
    var file = document.querySelector('input[type=file]').files[0];
	var blob = file.slice(fw_start, fw_start + fw_step);

	fw_reader.onload = function(e) {
		var data = fw_reader.result;
		fw_xhr.open('POST', "/update_firmware", true);
		fw_xhr.setRequestHeader("Content-Type", "application/octet-stream");
		fw_xhr.send(data);
	}

    fw_reader.readAsArrayBuffer(blob);
}

function updateFirmware() {

	if( document.querySelector('input[type=file]').files.length == 0 )
		return;

	$.ajax({
		url: "/update_firmware_start",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function() {
		try {

			fw_start = 0;
			fw_total_bytes = document.querySelector('input[type=file]').files[0].size;

			r = Math.round(fw_start * 100/fw_total_bytes);
			document.getElementsByClassName('progress-bar').item(0).setAttribute('aria-valuenow', r);
			document.getElementsByClassName('progress-bar').item(0).style.width = r + "%";
			document.getElementsByClassName('progress-bar').item(0).innerHTML = r + "%";
			document.getElementById("fw_update_status").innerHTML = "Updating...";

			fw_reader = new FileReader();
			fw_xhr = new XMLHttpRequest();

			fw_xhr.upload.onprogress = function(event) {
				fw_start +=  event.loaded;
				r = Math.round(fw_start * 100/fw_total_bytes);
				document.getElementsByClassName('progress-bar').item(0).setAttribute('aria-valuenow', r);
				document.getElementsByClassName('progress-bar').item(0).style.width = r + "%";
				document.getElementsByClassName('progress-bar').item(0).innerHTML = r + "%";
			};

			fw_xhr.upload.onerror = function() {
				document.getElementById("fw_update_status").innerHTML = "Update failed! Please reboot the device.";
			};

			fw_xhr.upload.onabort = function() {
				document.getElementById("fw_update_status").innerHTML = "Update aborted! Please reboot the device.";
			};

			fw_xhr.onloadend = function() {
				if (fw_xhr.status == 200) {
					if(fw_start < fw_total_bytes)
						upload_one_chunk();
					else
						update_end();
				}
				else {
					document.getElementById("fw_update_status").innerHTML = "Server error! Please reboot the device.";
				}
			};

			upload_one_chunk();
		}
		catch (error){
			console.log(error);
		}
	})
	.fail(function() {
	});
}

function update_end() {
	$.ajax({
		url: "/update_firmware_end",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function() {
		document.getElementById("fw_update_status").innerHTML = "Update finished. Waiting for device reboot...";
	})
	.fail(function() {
	});
}

function clickSWUpdatePage(retry) {
	$.ajax({
		url: "plugins/swupdate/html/swupdate.html",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function(data){
		$('#main_section').html(data);
		clearReturnData();
		$("#networking_main_menu>ul>li.active").removeClass("active");
		$("#main_menu>li.active").removeClass("active");
		$(".infoText").addClass("hidden");
		$("#helpText").html("Firmware Update");
	})
	.fail(function(){
		if (retry < 5){
			retry++;
			clickSWUpdatePage(retry);
		} else {
			console.log("Error, couldn't get swupdate.html");
		}
	});
}
