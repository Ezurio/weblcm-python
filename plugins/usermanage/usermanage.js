// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function usermanageAUTORUN(retry) {
  return;
}

function addPasswdInputOnkeyup(prefix) {

  var psw = $("#"+prefix+"-password");

  // Validate lowercase letters
  var letter = $("#"+prefix+"-lower");
  if(psw.val().match(/[a-z]/g)) {
    letter.removeClass("text-danger");
    letter.addClass("text-success");
  } else {
    letter.removeClass("text-success");
    letter.addClass("text-danger");
  }

  // Validate uppercase letters
  var capital = $("#"+prefix+"-upper");
  if(psw.val().match(/[A-Z]/g)) {
    capital.removeClass("text-danger");
    capital.addClass("text-success");
  } else {
    capital.removeClass("text-success");
    capital.addClass("text-danger");
  }

  // Validate numbers
  var number = $("#"+prefix+"-number");
  if(psw.val().match(/[0-9]/g)) {
    number.removeClass("text-danger");
    number.addClass("text-success");
  } else {
    number.removeClass("text-success");
    number.addClass("text-danger");
  }

  // Validate special letters
  var special = $("#"+prefix+"-special");
  if(psw.val().match(/[@$!%*?&]/g)) {
    special.removeClass("text-danger");
    special.addClass("text-success");
  } else {
    special.removeClass("text-success");
    special.addClass("text-danger");
  }

  // Validate length
  var length = $("#"+prefix+"-length");
  if(psw.val().length >= 8 && psw.val().length <= 64) {
    length.removeClass("text-danger");
    length.addClass("text-success");
  } else {
    length.removeClass("text-success");
    length.addClass("text-danger");
  }
}

function addPasswdInputOnblur(id){
  $("#"+id).addClass("d-none");
}

function addPasswdInputOnfocus(id, prefix){
  addPasswdInputOnkeyup(prefix);
  $("#"+id).removeClass("d-none");
}

function validateUsername(username){
  if (username.length < 4 || username.length > 64)
    return "4-64 characters required for username";

  inval = username.match(/\W/g);
  if(inval != null)
    return "Only number, lowercase, uppercase and underscore is allowed for username"

  return;
}

function validatePassword(psw) {
  if(psw.match(/[a-z]/g) == null) {
    return "Minimally one lowercase charcter required";
  }

  if(psw.match(/[A-Z]/g) == null) {
    return "Minimally one uppercase charcter required";
  }

  if(psw.match(/[0-9]/g) == null) {
    return "Minimally one number is required";
  }

  if(psw.match(/[@$!%*?&]/g) == null) {
    return "Minimally one special charcter is required";
  }

  if(psw.length < 8 || psw.length > 64) {
    return "8-64 characters are required";
  }
}

function updatePassword() {
  current_password = $("#current-password").val();

  new_password = $("#upm-password").val();
  err = validatePassword(new_password);
  if(err){
	CustomMsg(err, true);
	return;
  }

  confirm_password = $("#confirm-password").val();
  if (new_password !== confirm_password){
	CustomMsg("Password and confirmation password do not match", true);
	return;
  }

  var creds = {
    username: currUser,
    current_password: current_password,
    new_password: new_password,
  }

  $.ajax({
    url: "users",
    contentType: "application/json",
    data: JSON.stringify(creds),
    type: "PUT",
  })
  .done(function(data) {
    SDCERRtoString(data.SDCERR);

    if (data.REDIRECT == 1){
      login(currUser, new_password);
	}
  })
  .fail(function() {
    consoleLog("Failed to update password");
  });
}


function createUserList(users) {

  var tbody = $("#table-user > tbody");

  tbody.empty()

  for (var name in users) {
    row = '<tr permission="'+ users[name] + '">';

    row += '<td class="text-center">';
    row += name;
    row += '</td>';

    row += '<td class="text-center">';
    row += '<input type="button" class="btn btn-primary" role="button" id="bt-load-permission-' + name + '" value="' + i18nData['load perm'] + '" onclick="loadPermission()">';
    row += '</td>';

    row += '<td class="text-center">';
    row += '<input type="button" class="btn btn-primary" role="button" id="bt-update-permission-' + name + '" value="' + i18nData['update perm'] + '" onclick="updatePermission()">';
    row += '</td>';

    row += '<td class="text-center">';
    row += '<input type="button" class="btn btn-primary" role="button" id="bt-del-user-' + name + '" value="' + i18nData['delete user'] + '" onclick="delUser()">';
    row += '</td>';

    row += '</tr>';

    tbody.append(row);
  }

  $("#table-user tbody").on("click", "tr td:first-child", function(e){
    row = $(this).closest('tr');
    row.addClass('bg-info').siblings().removeClass('bg-info');
  });
}

function get_user_list() {
  clearReturnData();

  $.ajax({
    url: "users",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(data) {
    createUserList(data);
    clearPerm();
  })
  .fail(function() {
    consoleLog("Failed to get user list");
  });
}

function clearPerm() {

  $("[id^=user-permission-]:checked").not(":disabled").each(function() {
    $(this).prop('checked', false);
  });

}

function setPerm(perm){

  clearPerm();

  let arr = perm.split(" ");
  arr.forEach(function (item, index) {
    $("#user-permission-"+item).prop('checked', true);
  });
}


function getPerm() {
  var perm = "";

  $("[id^=user-permission-]").each(function() {
    if ($(this).is(":checked")){
      perm = $(this).attr("name").concat(" ", perm);
    }
  });

  return perm;
}

function addUser() {
  var perm = getPerm();

  var creds = {
    username: $("#ipm-username").val(),
    password: $("#ipm-password").val(),
    permission: perm,
  }

  err = validatePassword(creds.password);
  if(err){
	CustomMsg(err, true);
	return;
  }

  err = validateUsername(creds.username);
  if(err){
	CustomMsg(err, true);
	return;
  }

  $.ajax({
    url: "users",
    contentType: "application/json",
    data: JSON.stringify(creds),
    type: "POST",
  })
  .done(function(data) {
    if(data['SDCERR'] == 1){
      CustomMsg("Add user failed", true);
    }
    else{
	  $("#ipm-username").val("");
	  $("#ipm-password").val("");
      get_user_list();
	}
  })
  .fail(function() {
    consoleLog("Failed to add user");
  });
}

function loadPermission(){
  var id = event.srcElement.id;
  var row = $("#"+id).closest('tr');
  var perm = row.attr("permission");
  setPerm(perm);
  row.addClass('bg-info').siblings().removeClass('bg-info');
}

function updatePermission(){
  var id = event.srcElement.id;
  var row = $("#"+id).closest('tr');

  if(!row.hasClass("bg-info"))
  {
    CustomMsg("Please select user first by clicking user name", true);
    return;
  }

  var perm = getPerm();
  var creds = {
    username: id.slice(21),
    permission: perm,
  };

  $.ajax({
    url: "users",
    contentType: "application/json",
    data: JSON.stringify(creds),
    type: "PUT",
  })
  .done(function(data) {
    SDCERRtoString(data.SDCERR);
    if(data['SDCERR'] == 0){
      row.attr("permission", perm);
      setPerm(perm);
    }
  })
  .fail(function() {
    consoleLog("Failed to update user permission");
  });
}

function delUser(){
  var id = event.srcElement.id;
  var row = $("#"+id).closest('tr');

  if(!row.hasClass("bg-info"))
  {
    CustomMsg("Please select user first by clicking user name", true);
    return;
  }

  $.ajax({
    url: "users?username=" + id.slice(12),
    contentType: "application/json",
    type: "DELETE",
  })
  .done(function(data) {
    if(data['SDCERR'] == 1){
      CustomMsg("Delete user failed", true);
    }
    else{
      get_user_list();
    }
  })
  .fail(function() {
    consoleLog("Failed to delete user");
  });
}

function createPermissionsTable(){

  var types = defines.PLUGINS.usermanage.UserPermssionTypes;
  var attrs = defines.PLUGINS.usermanage.UserPermssionAttrs;
  var j = 0;


  var tbody = $("#table-user-permission > tbody");
  tbody.empty()

  for (let i = 0; i < types.length; i++){

    if(attrs[i][0].length == 0)
      continue;

    if (j == 0){
      row = '<tr>';
    }
    ++j;

    row += '<td class="text-left">';
    row += '<label>';
    row += '<input type="checkbox" id="user-permission-' + types[i] + '" name="' + types[i] + '" ' + attrs[i][1] + " " + attrs[i][2] + '>';
    row +=  (i18nData[attrs[i][0]] ? i18nData[attrs[i][0]] : attrs[i][0]) + '</label>'
    row += '</td>';

    if (j == 4){
      row += '</tr>';
      tbody.append(row);
      j = 0;
    }
  }

  if (j % 4){
    row += '</tr>';
    tbody.append(row);
  }
}

function clickAddOrDelUser(){
  $.ajax({
    url: "plugins/usermanage/html/add_del_user.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $(".active").removeClass("active");
    $("#add_del_user_main_menu").addClass("active");
    $("#add_del_user_mini_menu").addClass("active");
    $("#main_section").html(data);
    setLanguage("main_section");
    clearReturnData();
    createPermissionsTable();
    get_user_list();
  })
  .fail(function() {
    consoleLog("Failed to get add_del_user.html");
  });
}

function clickUpdatePassword(){
  $.ajax({
    url: "plugins/usermanage/html/update_password.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done( function(data) {
    $(".active").removeClass("active");
    $("#update_password_main_menu").addClass("active");
    $("#update_password_mini_menu").addClass("active");
    $('#main_section').html(data);
    setLanguage("main_section");
    clearReturnData();
  })
  .fail(function() {
    consoleLog("Failed to get update_password.html");
  });
}
