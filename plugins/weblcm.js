var defines;
var i18nData;
var currUserPermission;
var currUser;

function consoleLog(message) {
  console.log(message);
}

function httpErrorResponseHandler(xhr, textStatus, errorThrown) {
  switch (xhr.status) {
    //HTTP 401 Unauthorized Error
    case 401:
      logout();
      break;
    default:
      consoleLog("HTTP Error: " + xhr.status);
      break;
  }
}

function loadjscssfile(key, filetype) {
  let jsPath = "plugins/" + key + "/" + key + "." + filetype;
  if (filetype == "js") {

    let fileref = document.createElement('script');

    fileref.setAttribute("type", "text/javascript");
    fileref.setAttribute("src", jsPath);
    fileref.onload = function () {
      window[key + "AUTORUN"](0);
    }

    document.getElementsByTagName("head")[0].appendChild(fileref);
  }
}

function weblcm_init() {
  let i, lang;
  let plugins = ["networking", "logging", "swupdate", "usermanage", "advanced", "datetime"];

  for (i = 0; i < plugins.length; i++) {
    loadjscssfile(plugins[i], "js");
  }

  lang = window.navigator.userLanguage || window.navigator.language;
  if (lang == "zh" || lang == "zh-CN") {
    $("#language").val("zh-CN");
  }
  else {
    $("#language").val("en");
  }
  $("#language").change()
}

function clearReturnData() {
  if ($("#alert-msg-main-subdiv").length)
    $("#alert-msg-main-subdiv").remove();
  if ($("#alert-msg-mini-subdiv").length)
    $("#alert-msg-mini-subdiv").remove();
}

function setReturnData(alerttype, message) {
  $("#alert-msg-main").append('<div id="alert-msg-main-subdiv" class="alert ' + alerttype + '"><a class="close" data-dismiss="alert">×</a><span>' + message + '</span></div>')
  $("#alert-msg-mini").append('<div id="alert-msg-mini-subdiv" class="alert ' + alerttype + '"><a class="close" data-dismiss="alert">×</a><span>' + message + '</span></div>')
}

function CustomMsg(message, err) {

  clearReturnData()

  if (err) {
    setReturnData("alert-danger", i18nData[message] ? i18nData[message] : message);
  }
  else {
    setReturnData("alert-success", i18nData[message] ? i18nData[message] : message);
  }
}

function SDCERRtoString(SDCERR) {

  clearReturnData()

  switch (parseInt(SDCERR)) {
    case defines.SDCERR.SDCERR_SUCCESS:
      setReturnData("alert-success", i18nData['Success'] ? i18nData['Success'] : "Success");
      break;
    case defines.SDCERR.SDCERR_FAIL:
      setReturnData("alert-danger", i18nData['Failure'] ? i18nData['Failure'] : "Failure");
      break;
    default:
      setReturnData("alert-danger", i18nData['Unknown Data'] ? i18nData['Unknown Data'] : "Unknown Data");
      break;
  }
}

function enterKeyPress(e) {

  //'Enter' key
  if (e.keyCode === 13) {
    e.preventDefault();
    $("#bt-login").trigger("click");
  }
}

function login(user, passwd) {
  var creds = {
    username: user,
    password: passwd,
  }

  // Clear any old return code message
  clearReturnData()

  $.ajax({
    url: "login",
    data: JSON.stringify(creds),
    type: "POST",
    contentType: "application/json",
  })
  .done(function (data) {
    if (data.SDCERR == defines.SDCERR.SDCERR_SUCCESS) {
      $("#form-login").addClass("d-none");
      $("#form-logout").removeClass("d-none");

      clearReturnData();

      currUser = creds.username;
      currUserPermission = data.PERMISSION;

      if (data.REDIRECT == 1) {
        $("#networking_main_menu").addClass("d-none");
        $("#networking_mini_menu").addClass("d-none");
        clickUpdatePassword();
      }
      else {
        const MENU_ID_TYPE_OFFSET = 10; //"_main_menu"
        $(".locked").each(function () {
          let id = $(this).attr('id');
          if (-1 !== currUserPermission.indexOf(id.slice(0, id.length - MENU_ID_TYPE_OFFSET))) {
            $(this).removeClass("d-none");
          }
        });
        $("#networking_main_menu").removeClass("d-none");
        $("#networking_mini_menu").removeClass("d-none");
        $("#usermanage_main_menu").removeClass("d-none");
        $("#usermanage_mini_menu").removeClass("d-none");
        clickStatusPage();

      }
    } else {
      switch (data.SDCERR) {
        case defines.SDCERR.SDCERR_USER_LOGGED:
          CustomMsg("User is already logged in", true);
          break;
        case defines.SDCERR.SDCERR_USER_BLOCKED:
          CustomMsg("User is temporarily blocked", true);
          break;
        case defines.SDCERR.SDCERR_FAIL:
        default:
          CustomMsg("Credentials are invalid", true);
          break;
      }
    }
    $("#username").val("");
    $("#password").val("");
  })
  .fail(function (data) {
    consoleLog("Error, couldn't get login.. retrying");
  });
}

function logout() {
  $.ajax({
    url: "login",
    data: {},
    type: "DELETE",
    contentType: "application/json",
  })
  .always(function (data) {
    $("#form-logout").addClass("d-none");
    $("#form-login").removeClass("d-none");
    $(".locked").addClass("d-none");
    location.reload();
    clickStatusPage();
  });
}

function setLanguage(id) {
  $("#" + id + " .i18n").each(function () {
    value = $(this).attr('name');
    if (this.tagName.toLowerCase() === 'input') {
      if ($(this).attr("placeholder")) {
        $(this).attr("placeholder", i18nData[value]);
      }
      if ($(this).attr("value")) {
        $(this).attr("value", i18nData[value]);
      }
    } else if (this.tagName.toLowerCase() === 'option') {
      if ($(this).text()) {
        $(this).text(i18nData[value]);
        }
    } else {
      $(this).html(i18nData[value]);
    }
  });
}

function onChangeLanguageType() {
  lang = $("#language").val();
  $.ajax({
    url: 'assets/i18n/' + lang + '.json',
    dataType: 'json',
    success: function (data) {
      i18nData = data;
      setLanguage("main_menu");
      setLanguage("navbar_menu");
      setLanguage("main_section");
      setLanguage("help_section");
    }
  });
}

// Add event listeners once the DOM has fully loaded
$(document).ready( function (){

  $(document).on("click", "#bt-login", function() {
    login($("#username").val(), $("#password").val());
  });

  $(document).on("click", "#bt-logout", logout);

  $(document).on("keypress", "#password", enterKeyPress);

  $(document).on("change", "#language", onChangeLanguageType);

  $.ajax({
    url: "definitions",
    type: "GET",
    cache: false,
    contentType: "application/json",
  })
  .done(function (data) {
    defines = data;
    weblcm_init();
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
});
