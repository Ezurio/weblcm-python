// Copyright (c) 2020, Ezurio
// Contact: support@ezurio.com

function helpAUTORUN(retry){

  $(document).on("click", "#help_version_mini_menu, #help_version_main_menu", function(){
    clickHelpVersionPage();
  });
}

function clickHelpVersionPage(){

  function getVersion(){
    $.ajax({
      url: "version",
      type: "GET",
      cache: false,
    })
    .done(function(msg) {
      $("#version-driver").text(msg['driver']);
      $("#version-kernel-vermagic").text(msg['kernel_vermagic']);
      $("#version-supplicant").text(msg['supplicant']);
      $("#version-build").text(msg['build']);
      $("#version-nm").text(msg['nm_version']);
      $("#version-weblcm").text(msg['weblcm_python_webapp']);
      $("#version-radio-stack").text(msg['radio_stack']);
      $("#version-bluez").text(msg['bluez']);
      $("#version-u-boot").text(msg['u-boot']);
    })
    .fail(function( xhr, textStatus, errorThrown) {
      httpErrorResponseHandler(xhr, textStatus, errorThrown)
    });
  }

  $.ajax({
    url: "plugins/help/html/version.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $(".active").removeClass("active");
    $("#help_version_main_menu").addClass("active");
    $("#help_version_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
    getVersion(0);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}
