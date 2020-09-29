// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function advancedAUTORUN(retry) {

  $(document).on("click", "#advanced_mini_menu, #advanced_main_menu", function(){
    clickAdvancedPage();
  });

  $(document).on("click", "#bt-import-config", function(){
    fileUpload($("#form-import-config"), $("#input-file-config"), $("#bt-import-config"), $("#config-encrypt-password").val());
  });

  $(document).on("click", "#bt-export-config", function(){
    fileDownload('config', $("#bt-export-config"), $("#config-decrypt-password").val());
  });

  $(document).on("click", "#bt-export-log", function(){
    fileDownload('log', $("#bt-export-log"), $("#log-encrypt-password").val());
  });

  $(document).on("click", "#bt-export-debug", function(){
    fileDownload('debug', $("#bt-export-debug"));
  });

  $(document).on("click", "#bt-reboot", function(){
    reboot(true);
  });

  $(document).on("click", "#bt-factory-reset", function(){
    factoryReset();
  });

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
