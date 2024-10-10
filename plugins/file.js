/*
 * SPDX-License-Identifier: LicenseRef-Ezurio-Clause
 * Copyright (C) 2024 Ezurio LLC.
 */

function doFileUpload(form, $bt) {

  var xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if(xhr.readyState === XMLHttpRequest.DONE) {
      var status = xhr.status;
      if (status === 0 || (200 <= status && status < 400)) {
        customMsg("Success", false);
      } else {
        customMsg("Failure", true);
      }
      $bt.prop("disabled", false);
    }
  }

  xhr.open('POST', "file", true);
  xhr.send(form);
}

function fileUpload($form, $file, $bt) {

  var files = $file[0].files;
  if( files.length == 0 ) {
    customMsg("Please select the config archive first", true);
    return;
  }

  var data = new FormData($form.get(0));

  $bt.prop("disabled", true);

  doFileUpload(data, $bt)
}

function fileDelete(type, filename) {
  $.ajax({
    type: "DELETE",
    url: "file?type=" + type + "&file=" + filename,
  })
  .done(function(data) {
    if(data['SDCERR'] == 1){
      customMsg("Delete File Failed", true);
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function doFileDownload(url, type, $bt) {

  let xhr = new XMLHttpRequest();

  xhr.onreadystatechange = function() {
    if(xhr.readyState == XMLHttpRequest.LOADING){
        customMsg("Downloading...", false);
    }
    else if(xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 0 || (200 <= xhr.status && xhr.status < 400)) {
        // IE10+ : (has Blob, but not a[download] or URL)
        if (navigator.msSaveBlob) {
          navigator.msSaveBlob(xhr.response, type + ".zip");
        }
        else {
          var link = $("#archor-link-export-archive");
          link.attr("href", window.URL.createObjectURL(xhr.response));
          link.attr("download", type + ".zip");
          link.get(0).click();
          window.URL.revokeObjectURL(this.href);
        }
        customMsg("Downloaded", false);
      }
      else {
        customMsg("Failure", true);
      }

      $bt.prop("disabled", false);
    }
  }

  customMsg("Download start", false);
  $bt.prop("disabled", true);

  xhr.open('GET', url, true);
  xhr.responseType = 'blob';
  xhr.send();
}

function fileDownload(type, $bt, passwd) {

  let url = "file?type=" + type;

  if (passwd){
    url += "&password=" + passwd;
  }

  doFileDownload(url, type, $bt);
}

function getFileList(type, callback) {

  $.ajax({
    url: "files?type=" + type,
    type: "GET",
    cache: false,
  })
  .done(function(data) {
    if(callback && data['files']){
      callback(data['files']);
    }
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}
