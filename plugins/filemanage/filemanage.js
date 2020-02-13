// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function filemanageAUTORUN(retry) {
  return;
}

function createFileList(type, data){

  var tbody = $("#table-"+ type + " > tbody");

  tbody.empty()

  for(i=0; i<data.length; i++){
	row = '<tr>';

	row += '<td>';
	row += i.toString();
	row += '</td>';

	row += '<td>';
	row += data[i];
	row += '</td>';

	//row += '<td>';
	//row += '<a class="btn btn-primary" role="button" href="download_file?typ='+type+"&fil=" + data[i] + '">';
	//row += "download</a>";
	//row += '</td>';

	row += '<td>';
	row += '<input type="button" id=' + data[i] + ' name=' + type + ' value="delete" class="btn btn-primary" role="button" onclick="delFile(this.id, this.name)">';
	row += '</td>';

	row += '</tr>';

	tbody.append(row)
  }
}

function getFileList(type){

  $.ajax({
    url: "files?typ="+type,
    type: "GET",
    contentType: "application/json",
  })
  .done(function(data) {
    createFileList(type, data);
  })
  .fail(function() {
    consoleLog("Failed to get files");
  });
}

function delFile(file, type){

  $.ajax({
    url: "files?typ="+type+"&fil="+file,
    contentType: "application/json",
    type: "DELETE",
  })
  .done(function(data) {
    getFileList(type);
  })
  .fail(function() {
    consoleLog("Failed to delete file");
  });
}

function uploadFile(form, file, type) {

  var xhr = new XMLHttpRequest();

  xhr.onload = function() {
    getFileList(type);
    $("#bt-import-"+type).prop("disabled", false);
  };

  xhr.onerror = function() {
    $("#bt-import-"+type).prop("disabled", false);
  };
  xhr.onabort = function() {
    $("#bt-import-"+type).prop("disabled", false);
  };

  var parts = file.name.split('.');
  if(parts[parts.length - 1] == "tgz")
    xhr.open('POST', "tarfiles", true);
  else
    xhr.open('POST', "files", true);
  xhr.send(form);
}

function importFile(type){

  var files = $("#input-file-"+type)[0].files;
  if( files.length == 0 )
    return;

  var data = new FormData($("#form-import-"+type)[0]);

  $("#bt-import-"+type).prop("disabled", true);

  uploadFile(data, files[0], type)
}

function clickFileManagePage(retry)
{
  $.ajax({
    url: "plugins/filemanage/html/file_manage.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $("li").removeClass("active");
    $("#filemanage_main_menu").addClass("active");
    $('#main_section').html(data);
    clearReturnData();
    $("#helpText").html("Manage profiles, certificates, etc.");
    $(".infoText").addClass("hidden");
	getFileList("cert");
	getFileList("profile");
  })
  .fail(function() {
    if (retry < 5){
      retry++;
      clickFileManagePage(retry);
    } else {
      consoleLog("Retry max attempt reached");
    }
  });
}
