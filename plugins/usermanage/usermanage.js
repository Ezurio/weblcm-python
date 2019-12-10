// Copyright (c) 2019, Laird
// Contact: support@lairdconnect.com

function usermanageAUTORUN(retry) {
	return;
}

function updatePassword()
{
	current_password = document.getElementById("current_password").value;
	new_password = document.getElementById("new_password").value;
	confirm_password = document.getElementById("confirm_password").value;

	if (new_password !== confirm_password)
	{
		alert("Your password and confirmation password don't match");
		return;
	}

	var creds = {
		current_password: current_password,
		new_password: new_password,
	}

	$.ajax({
		url: "/update_user",
		contentType: "application/json",
		data: JSON.stringify(creds),
		type: "POST",
	})
	.done(function(data) {
		if(data['SDCERR'] == 1)
			alert('update password failed');
	})
	.fail(function() {
		alert("Failed to update password");
	});
}


function create_user_list(data) {
  var res = data.trim().split(" ");

  var elem = document.getElementById('user_list_table');
  if (elem)
  {
      elem.parentNode.removeChild(elem);
  }

  var list = document.createElement("table");
  list.style.width = '100%';
  list.setAttribute("id", "user_list_table");
  list.setAttribute("class", "table table-striped");

  var tbdy = document.createElement('tbody');

  for(i=0; i<res.length; i++)
  {
    var user = document.createElement("tr");

    var c1 = document.createElement("td");
    var seq = document.createTextNode(i);
    c1.style.width = "20%"
    c1.appendChild(seq);
    user.appendChild(c1);

    var c2 = document.createElement("td");
    var name = document.createTextNode(res[i]);
    c2.style.width = "50%"
    c2.appendChild(name);
    user.appendChild(c2);

    var c3 = document.createElement("td");
    if(i > 0)
    {
        var bt = document.createElement('input');
        bt.type = "button";
        bt.name = res[i];
        bt.id = res[i];
        bt.value = "delete";
        bt.className = "btn btn-primary";
        bt.onclick = function(){delUser();};
        c3.appendChild(bt);
    }
    c3.style.width = "30%"
    user.appendChild(c3);

    tbdy.appendChild(user);
  }

  list.appendChild(tbdy);
  document.body.appendChild(list);

  var user_list_div=document.querySelector("#user_list_div");
  user_list_div.append(list);
}

function get_user_list()
{
	$.ajax({
		url: "/get_user_list",
		data: {},
		type: "GET",
		dataType: "html",
	})
	.done(function(data) {
		create_user_list(data);
	})
	.fail(function() {
		alert("Failed to get user list");
	});
}

function addUser()
{
	var creds = {
		username: document.getElementById('add_username').value,
		password: document.getElementById('add_password').value,
	}
	$.ajax({
		url: "/add_user",
		contentType: "application/json",
		data: JSON.stringify(creds),
		type: "POST",
	})
	.done(function(data) {
		if(data['SDCERR'] == 1)
			alert('Add user failed');
		else
			get_user_list();
	})
	.fail(function() {
		alert("Failed to add new user");
	});
}

function delUser()
{
	user = event.srcElement.id;

	var creds = {
		username: user,
	}
	$.ajax({
		url: "/delete_user",
		contentType: "application/json",
		data: JSON.stringify(creds),
		type: "POST",
	})
	.done(function(data) {
		if(data['SDCERR'] == 1)
			alert('Del user failed');
		else
			get_user_list();
	})
	.fail(function() {
		alert("Failed to delete user");
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
		$('#main_section').html(data);
		clearReturnData();
		$("li").removeClass("active");
		$("#usermanage_main_menu>ul>li.active").removeClass("active");
		$("#add_del_user").addClass("active");
		$("#helpText").html("Add/delete users");
		$(".infoText").addClass("hidden");

		get_user_list();
	})
	.fail(function() {
		consoleLog("Error, couldn't get add_del_user.html.. retrying");
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
		success: function (data) {
			$('#main_section').html(data);
			clearReturnData();
			$("li").removeClass("active");
			$("#usermanage_main_menu>ul>li.active").removeClass("active");
			$("#update_password").addClass("active");
			$("#helpText").html("Update login user password.");
			$(".infoText").addClass("hidden");
		},
	})
	.fail(function() {
		consoleLog("Error, couldn't get update_password.html.. retrying");
		if (retry < 5){
			retry++;
			clickUpdatePassword(retry);
		} else {
			consoleLog("Retry max attempt reached");
		}
	});
}
