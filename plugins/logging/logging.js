// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function loggingAUTORUN(retry){
	return;
}

function submitLogging(retry){
	var LoggingData = {
		suppDebugLevel: document.getElementById("suppDebugLevel").value,
		driverDebugLevel: parseInt(document.getElementById("driverDebugLevel").value),
	}
	console.log(LoggingData)
	$.ajax({
		url: "set_logging",
		type: "POST",
		data: JSON.stringify(LoggingData),
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
		consoleLog("Failed to send logging data, retrying");
		if (retry < 5){
			retry++;
			submitLogging(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function requestLog(retry){
	$.ajax({
		url: "request_log",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		consoleLog(msg)
		if ( ! $("#generate_log").hasClass("disabled")){
			systemd_age = document.getElementById("systemd_age")
			if (systemd_age){
				systemd_age.innerText = msg.systemd_age;
			}
			if (parseInt(msg.systemd_age) > 0){
				$("#dl_logging_button").removeClass("disabled");
			} else {
				$("#dl_logging_button").addClass("disabled");
			}
		}

		var table = document.getElementById("logTable");
		// Check if we have moved off logging page
		if (table){
			for (var entry in msg["log"]){
				var row = table.insertRow(-1);
				var cell0 = row.insertCell(0);
				var cell1 = row.insertCell(1);
				var cell2 = row.insertCell(2);
				cell0.innerHTML = msg["log"][entry][0];
				cell1.innerHTML = msg["log"][entry][1];
				cell2.innerHTML = msg["log"][entry][2];
			}
			$("#updateProgressDisplay").addClass("hidden");
			$("#refresh_logging_button").removeClass("hidden");
			$("#logTableDisplay").removeClass("hidden");
			$("#emptyNode").remove();
			requestLog(retry)
		}
	})
	.fail(function() {
		consoleLog("Error, couldn't get log.. retrying");
		if (retry < 5){
			retry++;
			requestLog(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function generateLog(log,retry){
	$("#generate_log").addClass("disabled");
	$("#dl_logging_button").addClass("disabled");
	document.getElementById("systemd_age").innerText = "--";
	$.ajax({
		url: "generate_log",
		type: "POST",
		data: JSON.stringify(log),
		contentType: "application/json",
	})
	.done(function(msg) {
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		consoleLog(msg)
		if (msg.SDCERR == defines.SDCERR.SDCERR_SUCCESS){
			$("#generate_log").removeClass("disabled");
		}
	})
	.fail(function() {
		consoleLog("Error, couldn't generate log.. retrying");
		if (retry < 5){
			retry++;
			generateLog(log,retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function getLogging(retry){
	$.ajax({
		url: "get_logging",
		type: "GET",
		contentType: "application/json",
	})
	.done(function(msg) {
		consoleLog(msg);
		if (msg.SESSION == defines.SDCERR.SDCERR_FAIL){
			expiredSession();
			return;
		}
		document.getElementById("suppDebugLevel").value = msg.suppDebugLevel;
		document.getElementById("driverDebugLevel").value = msg.driverDebugLevel;
		requestLog(0);
	})
	.fail(function() {
		consoleLog("Error, couldn't get logging.. retrying");
		if (retry < 5){
			retry++;
			getLogging(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}

function clickLoggingPage(retry){
	$.ajax({
		url: "plugins/logging/html/logging.html",
		data: {},
		type: "GET",
		dataType: "html",
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			$("#networking_main_menu>ul>li.active").removeClass("active");
			$("#main_menu>li.active").removeClass("active");
			$("#logging_main_menu").addClass("active");
			$("#helpText").html("Logging options");
			$(".infoText").addClass("hidden");
		},
	})
	.done(function( data ) {
		$('input[type=file]').bootstrapFileInput();
		$('.file-inputs').bootstrapFileInput();
		getLogging(0);
	})
	.fail(function() {
		consoleLog("Error, couldn't get logging.html.. retrying");
		if (retry < 5){
			retry++;
			clickLoggingPage(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}
