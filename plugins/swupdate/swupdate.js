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
  var file = $("#fw-name")[0].files[0];
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

  if( $("#fw-name")[0].files.length == 0 )
    return;

  $.ajax({
    url: "/update_firmware_start",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function() {

    fw_start = 0;
    fw_total_bytes = $("#fw-name")[0].files[0].size;

    r = Math.round(fw_start * 100/fw_total_bytes);
    $(".progress-bar").attr("aria-valuenow", r);
    $(".progress-bar").attr("style", "width: "+ r + "%");
    $(".progress-bar").text(r + "%");
    $("#fw-update-status").text("Updating...");

    fw_reader = new FileReader();
    fw_xhr = new XMLHttpRequest();

    fw_xhr.upload.onprogress = function(event) {
      fw_start +=  event.loaded;
      r = Math.round(fw_start * 100/fw_total_bytes);
      $(".progress-bar").attr("aria-valuenow", r);
      $(".progress-bar").attr("style", "width: "+ r + "%");
      $(".progress-bar").text(r + "%");
    };

    fw_xhr.upload.onerror = function() {
      $("#bt-firmware-update").prop("disabled", false);
      $("#fw-update-status").text("Update failed! Please reboot the device.");
    };

    fw_xhr.upload.onabort = function() {
      $("#bt-firmware-update").prop("disabled", false);
      $("#fw-update-status").text("Update aborted! Please reboot the device.");
    };

    fw_xhr.onloadend = function() {
      if (fw_xhr.status == 200) {
        if(fw_start < fw_total_bytes)
          upload_one_chunk();
        else
          update_end();
      }
      else {
        $("#bt-firmware-update").prop("disabled", false);
        $("#fw-update-status").text("Update failed! Please reboot the device.");
      }
    };

    upload_one_chunk();
    $("#bt-firmware-update").prop("disabled", true);
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
    $("#fw-update-status").text("Update finished. Please reboot device!");
    $("#bt-firmware-update").prop("disabled", false);
  })
  .fail(function() {
  });
}

function clickSWUpdatePage() {
  $.ajax({
    url: "plugins/swupdate/html/swupdate.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $("li").removeClass("active");
    $("#swupdate_main_menu").addClass("active");
    $("#swupdate_mini_menu").addClass("active");
    $('#main_section').html(data);
    clearReturnData();
    $(".infoText").addClass("hidden");
    $("#helpText").html("Firmware Update");
  })
  .fail(function(){
    console.log("Error, couldn't get swupdate.html");
  });
}
