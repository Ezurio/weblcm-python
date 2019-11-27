// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function swupdateAUTORUN(retry) {
	return;
}


var fw_start;
var fw_reader;
var fw_xhr;
var fw_step = 1024*128;

function upload_one_chunk() {
    var file = document.querySelector('input[type=file]').files[0];
	var blob = file.slice(fw_start, fw_start + fw_step);
	fw_reader.onload = function(e){
		var data = fw_reader.result;
		fw_xhr.open('POST', "/update_firmware", true);
		fw_xhr.setRequestHeader("Content-Type", "application/octet-stream");
		fw_xhr.send(data);
	}

    fw_reader.readAsArrayBuffer(blob);
}

function update_start() {

	$.ajax({
		url: "/update_firmware_start",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function() {

		$("#helpText").html("Start to update firmware.");

		document.getElementById("total_progress_bar_text").innerHTML = "0/0";
		document.getElementById("total_progress_bar").value = 0;
		document.getElementById("cur_progress_bar_text").innerHTML = "Image";
		document.getElementById("cur_progress_bar").value = 0;
		document.getElementById("fw_update_status").innerHTML = "Update Status: ";

		if(intervalId)
			clearInterval(intervalId);
		intervalId = setInterval(update_progress, 1000);
	})
	.fail(function() {
		//consoleLog("Failed to start firmware upload!");
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
		$("#helpText").html("Firmware update finished.");
	})
	.fail(function() {
		//console.log("Failed to end firmware update!");
	});
}

function updateFirmware() {

	update_start();

	fw_start = 0;

	fw_reader = new FileReader();
	fw_xhr = new XMLHttpRequest();

	fw_xhr.upload.onprogress = function(event) {
		//console.log(`Uploaded ${event.loaded} of ${event.total} bytes`);
	};

	fw_xhr.upload.onerror = function() {
		console.log(`Error during the upload: ${fw_xhr.status}`);
	};

	fw_xhr.upload.onabort = function() {
		console.log(`Abort during the upload: ${fw_xhr.status}`);
	};

	fw_xhr.onloadend = function() {
		if (fw_xhr.status == 200) {
			var file = document.querySelector('input[type=file]').files[0];
			fw_start += fw_step;
			if(fw_start < file.size)
				upload_one_chunk();
			else
				update_end();
		} else {
			console.log("error " + this.status);
		}
	};

	upload_one_chunk();
}

function update_progress() {
	$.ajax({
		url: "/get_progress_state",
		contentType: "application/json",
		data: {},
		type: "GET",
	})
	.done(function(data) {
		if(data.SDCERR == 1) {
			//console.log("Update progress not started yet...")
		}
		else{
			document.getElementById("total_progress_bar_text").innerHTML = data.cur_step + "/" + data.nsteps;
			document.getElementById("total_progress_bar").value = data.cur_step * 100/data.nsteps;
			document.getElementById("cur_progress_bar_text").innerHTML = data.cur_image;
			document.getElementById("cur_progress_bar").value = data.cur_percent;
			document.getElementById("fw_update_status").innerHTML = "Update Status: " + data.state;
		}
	})
	.fail(function(data) {
		if(intervalId > 0){
			clearInterval(intervalId);
			intervalId = 0;
		}
		console.log("Failed to get progress state.");
	});
}

function updateBootenv(){

	var bootEnv = {
		bootside: document.getElementById("boot_env_bootside_select").value,
	}

	$.ajax({
		url: "/update_bootenv",
		contentType: "application/json",
		data: JSON.stringify(bootEnv),
		type: "POST",
	})
	.done(function(data) {
		document.getElementById("boot_env_bootside_select").value = data.bootside;
	})
	.fail(function(data) {
		console.log("Failed to update bootenv");
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
		if (intervalId){
			clearInterval(intervalId);
			intervalId = 0;
		}
		$('#main_section').html(data);
		clearReturnData();
		$("#networking_main_menu>ul>li.active").removeClass("active");
		$("#main_menu>li.active").removeClass("active");
		updateBootenv();
		$(".infoText").addClass("hidden");
		$("#helpText").html("Firmware Update");
	})
	.fail(function(){
		console.log("Error, couldn't get swupdate.html.. retrying");
		if (retry < 5){
			retry++;
			clickSWUpdatePage(retry);
		} else {
			console.log("Retry max attempt reached");
		}
	});
}
