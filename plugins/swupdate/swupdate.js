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
  $(".progress-bar").attr("aria-valuenow", 0);
  $(".progress-bar").attr("style", "width: 0%");
  $(".progress-bar").text("0%");
  $("#fw-update-status").text(i18nData['Checking...']);

  $.ajax({
    url: "firmware",
    type: "POST",
    dataType: "json",
  })
  .done(function(msg) {

    if(msg.SDCERR){
      update_end(i18nData[msg.message] ? i18nData[msg.message] : msg.message);
      return;
    }

    fw_start = 0;
    fw_total_bytes = $("#fw-name")[0].files[0].size;

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
          update_end_check();
      }
      else {
        update_end(i18nData['Update failed!']);
      }
    };

    upload_one_chunk();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    update_end(i18nData['Update failed!']);
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function update_end_check(){
  $.ajax({
    url: "firmware",
    type: "GET",
    cache: false,
    dataType: "json",
  })
  .done(function(msg) {
    update_end(msg.SDCERR ? i18nData['Update failed!'] : i18nData['Update finished. Please reboot device!']);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
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
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function clickSWUpdatePage() {
  $.ajax({
    url: "plugins/swupdate/html/swupdate.html",
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $(".active").removeClass("active");
    $("#swupdate_main_menu").addClass("active");
    $("#swupdate_mini_menu").addClass("active");
    $('#main_section').html(data);
    setLanguage("main_section");
    clearReturnData();

    //In case swupdate was cancelled by clicking a menu item, backend needs to be updated.
    update_end(i18nData['Update Status']);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}
