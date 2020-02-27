// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function advancedAUTORUN(retry) {
  return;
}

function reboot(show) {

  if(show){
    var r = confirm("Are you sure you want to reboot system?");
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
    setTimeout(function(){ location.reload(true); }, 5000);
  })
  .fail(function() {
    consoleLog("Reboot failed");
  });
}

function factoryReset(){
  var r = confirm("Are you sure you want to do factory reset?");
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
  .fail(function() {
    consoleLog("Factory reset failed");
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
    $("li").removeClass("active");
    $("#advanced_main_menu").addClass("active");
    $("#advanced_mini_menu").addClass("active");
    $('#main_section').html(data);
    clearReturnData();
    $(".infoText").addClass("hidden");
    $("#helpText").html("Advanced control");
  })
  .fail(function(){
    console.log("Error, couldn't get advanced.html");
  });
}
