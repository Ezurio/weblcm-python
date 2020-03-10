// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function loggingAUTORUN(retry){
  return;
}

function submitLogLevel(retry){
  var data = {
    suppDebugLevel: $("#supp-debug-level").val(),
    driverDebugLevel: parseInt($("#driver-debug-level").val()),
  };

  $.ajax({
    url: "logLevel",
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
    url: "logData",
    type: "GET",
    data: {
      typ: $("#log-type").val(),
      priority: parseInt($("#log-level").val()),
      days: parseInt($("#log-date-from").val()),
    },
    contentType: "application/json",
  })
  .done(function(data){

    strLevel = ["Emerg", "Alert", "Critical", "Error", "Warning", "Notice", "Info", "Debug" ];

    table = $("#table-log-data").DataTable();
    table.clear().draw();

    for(i=0; i<data.length; i++){
      table.row.add([ data[i]['time'], strLevel[data[i]['priority']], data[i]['identifier'], data[i]['message'] ]);
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

function getLogLevel(retry){
  $.ajax({
    url: "logLevel",
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
    clearReturnData();
    $("#helpText").html("Logging options");
    $(".infoText").addClass("hidden");

    var table = $("#table-log-data").DataTable({
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
        getLogLevel();
      }
    });
  })
  .fail(function() {
    consoleLog("Failed to get logging.html");
  });
}
