// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function advancedAUTORUN(retry) {
  return;
}

function reboot(show) {

  if(show){
    var r = confirm(i18nData['Are you sure you want to reboot system?']);
    if (r == false)
      return;
  }

  $.ajax({
    url: "reboot",
    data: {},
    type: "PUT",
  })
  .done(function() {
    $("#helpText").html("System rebooting...");
    $("#bt-factory-reset").prop("disabled", true);
    $("#bt-reboot").prop("disabled", true);
    setTimeout(function(){ window.location.reload(true); }, 60000);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function factoryReset(){
  var r = confirm(i18nData['Are you sure you want to do factory reset?']);
  if (r == false)
    return;

  $.ajax({
    url: "factoryReset",
    type: "PUT",
    contentType: "application/json",
  })
  .done(function(msg) {
    SDCERRtoString(msg.SDCERR);
    reboot();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function doUpload(form, type) {

  var xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if(xhr.readyState === XMLHttpRequest.DONE) {
      var status = xhr.status;
      if (status === 0 || (200 <= status && status < 400)) {
        CustomMsg("Success", false);
      } else {
        CustomMsg("Failure", true);
      }
      $("#bt-import-"+type).prop("disabled", false);
    }
  }

  xhr.open('POST', "archiveFiles", true);
  xhr.send(form);
}

function importArchive(type){

  clearReturnData();

  var files = $("#input-file-"+type)[0].files;
  if( files.length == 0 )
  {
    CustomMsg("Please select the config archive first", true);
    return;
  }

  var passwd = $("#"+type+"-decrypt-passwd").val();
  if (passwd.length < 8 || passwd.length > 64){
    CustomMsg("8-64 characters are required", true);
    return;
  }

  var data = new FormData($("#form-import-"+type).get(0));

  $("#bt-import-"+type).prop("disabled", true);

  doUpload(data, type)
}

function doDelete(type) {
  $.ajax({
    url: "archiveFiles?typ="+type,
    type: "DELETE",
    dataType: "html",
  })
  .done(function(data){
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function doDownload(url, type) {
  var xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if(xhr.readyState == XMLHttpRequest.LOADING){
        CustomMsg("Downloading...", false);
    }
    else if(xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 0 || (200 <= xhr.status && xhr.status < 400)) {
        // IE10+ : (has Blob, but not a[download] or URL)
        if (navigator.msSaveBlob) {
          navigator.msSaveBlob(xhr.response, type+".zip");
        }
        else {
          var link = $("#archor-link-export-archive");
          link.attr("href", window.URL.createObjectURL(xhr.response));
          link.attr("download", type+".zip");
          link.get(0).click();
          window.URL.revokeObjectURL(this.href);
        }
      }
      else {
        CustomMsg("Failure", true);
      }

      CustomMsg("Downloaded", false);
      $("#bt-export-"+type).prop("disabled", false);

      doDelete(type);
    }
  }

  CustomMsg("Download start", false);
  $("#bt-export-"+type).prop("disabled", true);

  xhr.open('GET', url, true);
  xhr.responseType = 'blob';
  xhr.send();
}


function exportArchive(type) {
  var passwd = "";

  clearReturnData();

  if (type != "debug") {
    passwd = $("#"+type+"-encrypt-passwd").val();
    if (passwd.length < 8 || passwd.length > 64){
      CustomMsg("8-64 characters are required", true);
      return;
    }
  }

  var url = "archiveFiles?typ="+type+"&Password="+passwd;
  doDownload(url, type);
}

function clickAdvancedPage() {
  $.ajax({
    url: "plugins/advanced/html/advanced.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $(".active").removeClass("active");
    $("#advanced_main_menu").addClass("active");
    $("#advanced_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}
