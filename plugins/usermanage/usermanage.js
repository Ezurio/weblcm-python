// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function usermanageAUTORUN(retry) {
  return;
}

function updatePassword()
{
  current_password = $("#current-password").val();
  new_password = $("#new-password").val();
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
    CustomErrMsg(data['SDCERR'] == 1 ? "Password update failed" : "Password updated");
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
    username: $("#add-username").val(),
    password: $("#add-password").val(),
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
	  $("#add-username").val("");
	  $("#add-password").val("");
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

function clickAddOrDelUser(retry)
{
  $.ajax({
    url: "plugins/usermanage/html/add_del_user.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done(function(data){
    $("#main_section").html(data);
    clearReturnData();
    $("#helpText").html("Add/delete users");
    $(".infoText").addClass("hidden");
    get_user_list();
  })
  .fail(function() {
    if (retry < 5){
      retry++;
      clickAddOrDelUser(retry);
    } else {
      consoleLog("Retry max attempt reached");
    }
  });
}

function clickUpdatePassword(retry)
{
  $.ajax({
    url: "plugins/usermanage/html/update_password.html",
    data: {},
    type: "GET",
    dataType: "html",
  })
  .done( function(data) {
    $('#main_section').html(data);
    clearReturnData();
    $("#helpText").html("Update login user password.");
    $(".infoText").addClass("hidden");
  })
  .fail(function() {
    if (retry < 5){
      retry++;
      clickUpdatePassword(retry);
    } else {
      consoleLog("Retry max attempt reached");
    }
  });
}
