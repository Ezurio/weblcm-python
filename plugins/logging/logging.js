// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function loggingAUTORUN(retry){
  return;
}

function submitLogging(retry){
  var LoggingData = {
    suppDebugLevel: $("#supp-debug-level").val(),
    driverDebugLevel: parseInt($("#driver-debug-level").val()),
  }
  $.ajax({
    url: "set_logging_level",
    type: "POST",
    data: JSON.stringify(LoggingData),
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

  strLevel = ["Emerg", "Alert", "Critical", "Error", "Warning", "Notice", "Info", "Debug" ];

  $("#bt-query-log").prop("disabled", true);
  $("#bt-query-log").val("Querying...");

  filter = {
    type: $("#log-type").val(),
    priority: parseInt($("#log-level").val()),
	from: parseInt($("#log-date-from").val()),
  };

  $.ajax({
    url: "request_log",
    type: "POST",
	data: JSON.stringify(filter),
    contentType: "application/json",
  })
  .done(function(data) {

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
    consoleLog("Request log failed");
  });
}

function getLoggingLevel(retry){
  $.ajax({
    url: "get_logging_level",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(msg) {
    $("#supp-debug-level").val(msg.suppDebugLevel);
    $("#driver-debug-level").val(msg.driverDebugLevel);
  })
  .fail(function() {
    consoleLog("Get logging failed");
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
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("Logging options");
    $(".infoText").addClass("hidden");

    var table = $("#table-log-data").DataTable({
      ordering: false,
      responsive: true,
      bAutoWidth: false,
      dom: "l<'pull-right'B>tip",
      buttons: [
        {
          extend: "csvHtml5",
          filename: "log",
          text: "Download",
          className: "btn btn-primary",
          exportOptions: {
            modifier: {
              search: "none"
            }
          }
        },
      ]
    });

    $("#tab-log").bind("click", function() {
      $(this).show();
      if($("#set-log").length > 0){
        getLoggingLevel();
      }
    });
  })
  .fail(function() {
    if (retry < 5){
      retry++;
      clickLoggingPage(retry);
    } else {
      consoleLog("Retry max attempt reached");
    }
  });
}
