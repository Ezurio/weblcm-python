var g_defines;
var g_i18nData;
var g_curr_user_permission;
var g_curr_user;
var g_sess_timeout_id = -1;

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

function loadjsfile(key) {
  let jsPath = "plugins/" + key + "/" + key + ".js";

  let fileref = document.createElement('script');
  fileref.setAttribute("type", "text/javascript");
  fileref.setAttribute("src", jsPath);
  fileref.onload = function () {
    window[key + "AUTORUN"](0);
  }

  document.getElementsByTagName("head")[0].appendChild(fileref);
}

function loadmenu(menu, id){

  return $.ajax({
    url: "plugins/" + menu,
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function( data ) {
    $("#"+id).html(data);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
}

function weblcm_init(plugins) {
  let i, lang;
  let requests = [];

  for (i = 0; i < plugins.length; i++) {
    requests.push(loadjsfile(plugins[i]));
  }

  requests.push(loadmenu("main_menu.html", "main_menu"));
  requests.push(loadmenu("mini_menu.html", "mini_menu"));

  $.when.apply($, requests)
  .done( function() {
    if (login() == false){
      $("#form-login").removeClass("d-none");
    }
  });
  //"Lang" can be effective even session is closed.
  lang = window.localStorage.getItem("Lang") || window.navigator.userLanguage || window.navigator.language;
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

function customMsg(message, err) {

  clearReturnData()

  if (err) {
    setReturnData("alert-danger", g_i18nData[message] ? g_i18nData[message] : message);
  }
  else {
    setReturnData("alert-success", g_i18nData[message] ? g_i18nData[message] : message);
  }
}

function SDCERRtoString(SDCERR) {

  clearReturnData()

  switch (parseInt(SDCERR)) {
    case g_defines.SDCERR.SDCERR_SUCCESS:
      setReturnData("alert-success", g_i18nData['Success'] ? g_i18nData['Success'] : "Success");
      break;
    case g_defines.SDCERR.SDCERR_FAIL:
      setReturnData("alert-danger", g_i18nData['Failure'] ? g_i18nData['Failure'] : "Failure");
      break;
    default:
      setReturnData("alert-danger", g_i18nData['Unknown Data'] ? g_i18nData['Unknown Data'] : "Unknown Data");
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


function session_timeout(){
  logout();
  setTimeout(function() { alert("Session expired"); }, 0);
}

function login(user, passwd) {

  let ret = false;
  let creds = {
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
    if (data.SDCERR == g_defines.SDCERR.SDCERR_SUCCESS) {
      $("#form-login").addClass("d-none");
      $("#form-logout").removeClass("d-none");

      clearReturnData();

      g_curr_user = creds.username;
      g_curr_user_permission = data.PERMISSION;

      if (data.REDIRECT == 1) {
        $("#status_main_menu").addClass("d-none");
        $("#status_mini_menu").addClass("d-none");
        $("#help_main_menu").addClass("d-none");
        $("#help_mini_menu").addClass("d-none");
        clickUpdatePassword();
      }
      else {
        const MENU_ID_TYPE_OFFSET = 10; //"_main_menu"
        $(".locked").each(function () {
          let id = $(this).attr('id');
          if (g_curr_user_permission) {
            if (-1 !== g_curr_user_permission.indexOf(id.slice(0, id.length - MENU_ID_TYPE_OFFSET))) {
              $(this).removeClass("d-none");
            }
          }
        });
        $("#networking_main_menu").removeClass("d-none");
        $("#networking_mini_menu").removeClass("d-none");
        $("#system_main_menu").removeClass("d-none");
        $("#system_mini_menu").removeClass("d-none");
        clickStatusPage();
      }

      if(g_sess_timeout_id != -1){
        clearTimeout(g_sess_timeout_id);
      }
      g_sess_timeout_id = setTimeout(session_timeout, g_defines.SETTINGS.session_timeout * 60 * 1000);

      ret = true;

    } else if(user && passwd){
      switch (data.SDCERR) {
        case g_defines.SDCERR.SDCERR_USER_LOGGED:
          customMsg("User is already logged in", true);
          break;
        case g_defines.SDCERR.SDCERR_USER_BLOCKED:
          customMsg("User is temporarily blocked", true);
          break;
        case g_defines.SDCERR.SDCERR_SESSION_CHECK_FAILED:
          customMsg("User is not allowed for the session");
          break;
        case g_defines.SDCERR.SDCERR_FAIL:
        default:
          customMsg("Credentials are invalid", true);
          break;
      }
    }

    $("#username").val("");
    $("#password").val("");
  })
  .fail(function (data) {
    consoleLog("Error, couldn't get login.. retrying");
  });

  return ret;
}

function logout() {
  $.ajax({
    url: "login",
    type: "DELETE",
  })
  .always(function () {

    $("#form-logout").addClass("d-none");
    $("#form-login").removeClass("d-none");
    $(".locked").addClass("d-none");

    location.reload();
  });
}

function setLanguage(id) {
  $("#" + id + " .i18n").each(function () {
    value = $(this).attr('name');
    if (this.tagName.toLowerCase() === 'input') {
      if ($(this).attr("placeholder")) {
        $(this).attr("placeholder", g_i18nData[$(this).attr("placeholder")]);
      }
      if ($(this).attr("value")) {
        $(this).attr("value", g_i18nData[value]);
      }
    } else if (this.tagName.toLowerCase() === 'option') {
      if ($(this).text()) {
        $(this).text(g_i18nData[value]);
        }
    } else {
      $(this).html(g_i18nData[value]);
    }
  });
}

function onChangeLanguageType() {
  lang = $("#language").val();
  $.ajax({
    url: 'assets/i18n/' + lang + '.json',
    dataType: 'json',
    success: function (data) {
      g_i18nData = data;
      setLanguage("main_menu");
      setLanguage("navbar_menu");
      setLanguage("main_section");
      setLanguage("help_section");
    }
  });
  window.localStorage.setItem('Lang', lang);
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
    g_defines = data;
    weblcm_init(data['PLUGINS']);
  })
  .fail(function( xhr, textStatus, errorThrown) {
    httpErrorResponseHandler(xhr, textStatus, errorThrown)
  });
});
