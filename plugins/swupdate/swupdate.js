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
    fw_xhr.open('PUT', "firmware", true);
    fw_xhr.setRequestHeader("Content-Type", "application/octet-stream");
    fw_xhr.send(data);
  }

  fw_reader.readAsArrayBuffer(blob);
}

function updateFirmware() {

  if( $("#fw-name")[0].files.length == 0 )
    return;

  $("#bt-firmware-update").prop("disabled", true);
  $("#fw-update-status").text(i18nData['Checking...']);

  $.ajax({
    url: "firmware",
    type: "POST",
    dataType: "json",
  })
  .done(function(msg) {

    if(msg.SDCERR){
      if (msg.message in i18nData)
        $("#fw-update-status").text(i18nData[msg.message]);
      else
        $("#fw-update-status").text(msg.message);
      $("#bt-firmware-update").prop("disabled", false);
      return;
    }

    fw_start = 0;
    fw_total_bytes = $("#fw-name")[0].files[0].size;

    r = Math.round(fw_start * 100/fw_total_bytes);
    $(".progress-bar").attr("aria-valuenow", r);
    $(".progress-bar").attr("style", "width: "+ r + "%");
    $(".progress-bar").text(r + "%");
    $("#fw-update-status").text(i18nData['Updating...']);

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
      update_end(i18nData['Update failed!']);
    };

    fw_xhr.upload.onabort = function() {
      update_end(i18nData['Update aborted!']);
    };

    fw_xhr.onloadend = function() {
      if (fw_xhr.status == 200) {
        if(fw_start < fw_total_bytes)
          upload_one_chunk();
        else
          update_end(i18nData['Update finished. Please reboot device!']);
      }
      else {
        update_end(i18nData['Update failed!']);
      }
    };

    upload_one_chunk();
  })
  .fail(function(xhr){
    $("#bt-firmware-update").prop("disabled", false);
  });
}

function update_end(msg) {

  $.ajax({
    url: "firmware",
    type: "DELETE",
  })
  .done(function() {
    $("#fw-update-status").text(msg);
    $("#bt-firmware-update").prop("disabled", false);
  })
  .fail(function() {
  });
}

function clickSWUpdatePage() {
  $.ajax({
    url: "plugins/swupdate/html/swupdate.html",
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $("li").removeClass("active");
    $("#swupdate_main_menu").addClass("active");
    $("#swupdate_mini_menu").addClass("active");
    $('#main_section').html(data);
    setLanguage("main_section");
    clearReturnData();
    $(".infoText").addClass("hidden");
  })
  .fail(function(){
    console.log("Error, couldn't get swupdate.html");
  });
}
