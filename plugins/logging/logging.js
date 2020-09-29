// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function loggingAUTORUN(retry){

  $(document).on("click", "#logging_mini_menu, #logging_main_menu", function(){
    clickLoggingPage();
  });

  $(document).on("click", "#bt-query-log", function(){
    queryLogData();
  });

  $(document).on("click", "#bt-submit-loglevel", function(){
    submitlogSetting();
  });
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
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function queryLogData() {

  $("#bt-query-log").prop("disabled", true);
  $("#bt-query-log").val("Querying...");

  $.ajax({
    url: "logData?type=" + $("#log-type").val() + "&priority=" + parseInt($("#log-level").val()) + "&days=" + parseInt($("#log-date-from").val()),
    type: "GET",
    cache: false,
  })
  .done(function(msg){

    strLevel = ["Emerg", "Alert", "Critical", "Error", "Warning", "Notice", "Info", "Debug" ];

    table = $("#table-log-data").DataTable();
    table.clear().draw();

    data = msg.split(':#:');
    for(i=0; i<=data.length-4; i+=4){
      table.row.add([ data[i], strLevel[data[i+1]], data[i+2], data[i+3] ]);
    }

    table.draw();

    $("#bt-query-log").prop("disabled", false);
    $("#bt-query-log").val("Query");
  })
  .fail(function( xhr, textStatus, errorThrown) {
    $("#bt-query-log").prop("disabled", false);
    $("#bt-query-log").val("Query");
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function getlogSetting(retry){
  $.ajax({
    url: "logSetting",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function(msg) {
    $("#supp-debug-level").val(msg.suppDebugLevel);
    $("#driver-debug-level").val(msg.driverDebugLevel);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
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
    $(".active").removeClass("active");
    $("#logging_main_menu").addClass("active");
    $("#logging_mini_menu").addClass("active");
    $("#main_section").html(data);
	  setLanguage("main_section");
    clearReturnData();

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
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}
