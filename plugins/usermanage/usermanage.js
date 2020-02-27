// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function usermanageAUTORUN(retry) {
  return;
}

function addPasswdInputOnkeyup(prefix){

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
  $("#"+id).addClass("hidden");
}

function addPasswdInputOnfocus(id, prefix){
  addPasswdInputOnkeyup(prefix);
  $("#"+id).removeClass("hidden");
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
    return "8-84 characters are required";
  }
}

function updatePassword()
{
  current_password = $("#current-password").val();

  new_password = $("#upm-password").val();
  err = validatePassword(new_password);
  if(err){
	CustomErrMsg(err);
	return;
  }

  confirm_password = $("#confirm-password").val();
  if (new_password !== confirm_password){
	CustomErrMsg("Your password and confirmation password don't match");
	return;
  }

  var creds = {
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
      login("root", new_password);
	}
  })
  .fail(function() {
    consoleLog("Failed to update password");
  });
}


function create_user_list(data) {

  var tbody = $("#table-user > tbody");

  tbody.empty()

  for(i=0; i<data.length; i++)
  {
	row = '<tr>';

	row += '<td>';
	row += i.toString();
	row += '</td>';

	row += '<td>';
	row += data[i];
	row += '</td>';

	row += '<td>';
	row += '<input type="button" id=' + data[i] + ' name=' + data[i] + ' value="delete" class="btn btn-primary" role="button" onclick="delUser()">';
	row += '</td>';

	row += '</tr>';

	tbody.append(row)
  }
}

function get_user_list()
{
  clearReturnData();

  $.ajax({
    url: "users",
    type: "GET",
    contentType: "application/json",
  })
  .done(function(data) {
    create_user_list(data);
  })
  .fail(function() {
    consoleLog("Failed to get user list");
  });
}

function addUser()
{
  var creds = {
    username: $("#ipm-username").val(),
    password: $("#ipm-password").val(),
  }

  err = validatePassword(creds.password);
  if(err){
	CustomErrMsg(err);
	return;
  }

  err = validateUsername(creds.username);
  if(err){
	CustomErrMsg(err);
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
      CustomErrMsg("Add user failed");
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

function delUser()
{
  $.ajax({
    url: "users?username="+event.srcElement.id,
    contentType: "application/json",
    type: "DELETE",
  })
  .done(function(data) {
    if(data['SDCERR'] == 1){
      CustomErrMsg("Delete user failed");
    }
    else{
      get_user_list();
    }
  })
  .fail(function() {
    consoleLog("Failed to delete user");
  });
}

function clickAddOrDelUser()
{
  $.ajax({
    url: "plugins/usermanage/html/add_del_user.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $("li").removeClass("active");
    $("#add_del_user_main_menu").addClass("active");
    $("#add_del_user_mini_menu").addClass("active");
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("Add/delete users");
    $(".infoText").addClass("hidden");
    get_user_list();
  })
  .fail(function() {
    consoleLog("Failed to get add_del_user.html");
  });
}

function clickUpdatePassword(message)
{
  $.ajax({
    url: "plugins/usermanage/html/update_password.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done( function(data) {
    $("li").removeClass("active");
    $("#update_password_main_menu").addClass("active");
    $("#update_password_mini_menu").addClass("active");
    $('#main_section').html(data);
    clearReturnData();
    $("#helpText").html(message);
    $(".infoText").addClass("hidden");
  })
  .fail(function() {
    consoleLog("Failed to get update_password.html");
  });
}
