// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function loggingAUTORUN(retry){
  return;
}

function submitlogSetting(retry){
  var data = {
    suppDebugLevel: $("#supp-debug-level").val(),
    driverDebugLevel: parseInt($("#driver-debug-level").val()),
  };

  $.ajax({
    url: "logSetting",
    type: "POST",
    data: JSON.stringify(data),
    contentType: "application/json",
  })
  .done(function( msg ) {
    SDCERRtoString(msg.SDCERR);
  })
  .fail(function() {
    consoleLog("Set log level failed");
  });
}

function queryLogData() {

  $("#bt-query-log").prop("disabled", true);
  $("#bt-query-log").val("Querying...");

  $.ajax({
    url: "logData?typ=" + $("#log-type").val() + "&priority=" + parseInt($("#log-level").val()) + "&days=" + parseInt($("#log-date-from").val()),
    type: "GET",
  })
  .done(function(msg){

    strLevel = ["Emerg", "Alert", "Critical", "Error", "Warning", "Notice", "Info", "Debug" ];

    table = $("#table-log-data").DataTable();
    table.clear().draw();

    data = msg.split(':#:');
    for(i=0; i<data.length-4; i+=4){
      table.row.add([ data[i], strLevel[data[i+1]], data[i+2], data[i+3] ]);
    }

    table.draw();

    $("#bt-query-log").prop("disabled", false);
    $("#bt-query-log").val("Query");
  })
  .fail(function() {
    $("#bt-query-log").prop("disabled", false);
    $("#bt-query-log").val("Query");
    consoleLog("Request log failed");
  });
}

function getlogSetting(retry){
  $.ajax({
    url: "logSetting",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(msg) {
    $("#supp-debug-level").val(msg.suppDebugLevel);
    $("#driver-debug-level").val(msg.driverDebugLevel);
  })
  .fail(function() {
    consoleLog("Get log level failed");
  });
}

function clickLoggingPage(retry){

  $.ajax({
    url: "plugins/logging/html/logging.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $("li").removeClass("active");
    $("#logging_main_menu").addClass("active");
    $("#logging_mini_menu").addClass("active");
    $("#main_section").html(data);
	  setLanguage("main_section");
    clearReturnData();
    $(".infoText").addClass("hidden");

    var table = $("#table-log-data").DataTable({
      "language": i18nData["dtLang"],
      ordering: false,
      responsive: true,
      bAutoWidth: false,
	  dom: '<l<t>ip>',
      "pagingType": "full",
      "pageLength": 25,
      columnDefs: [
        {
          targets: '_all',
          className: 'dt-left'
        }
      ]
    });

    $("#tab-log").bind("click", function() {
      $(this).show();
      if($("#set-log").length > 0){
        getlogSetting();
      }
    });
  })
  .fail(function() {
    consoleLog("Failed to get logging.html");
  });
}
