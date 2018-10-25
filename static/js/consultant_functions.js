// On document ready

$(function () {

    update_copyright_date_in_footer();
    // Attach change password submit button function
    $('#change_password_form').find('input[type=submit]').click(process_change_password);
    // Add list of participants for this project to sessionStorage
})

function update_copyright_date_in_footer() {

    var d = new Date();
    $('#copyright_year').text(d.getFullYear());

}

function process_change_password(e) {
    e.preventDefault();

    var form_data = $('#change_password_form').serialize();

    if ($('[name=confirm_pass]').val() != $('[name=new_pass]').val()) {
        $('#change_password_form').prepend('<div id="confirm_password_error" class="alert alert-danger mx-4">Your new password and confirmed password do not match. Please try again.</div>');
        $('#confirm_pass').val('');
        $('#new_pass').val('');
        $('#confirm_pass').click(function () {
            $('#confirm_password_error').remove();
        })
        $('#new_pass').click(function () {
            $('#confirm_password_error').remove();
        })
    }

    else {

        $.ajax({
            url: '/api/consultants/' + $('[name=c_id]').val() + '/change_password',
            data: $('#change_password_form').serialize(),
            type: 'POST',
            success: function (response) {

                // reset change password form and hide modal
                $('#change_password_form').find('input[type=password]').val('');
                $('#cancel_change_password_button').trigger('click');

            },
            error: function (error) {

                $('#change_password_form').prepend('<div id="change_password_error" class="alert alert-danger mx-4">' + error.responseText + '</div>');
                $('#change_password_form').find('input').click(function () {
                    $('#change_password_error').remove();
                })
            }
        });
    }

}

function update_project_status_activity(iso_date) {

    var d = new Date(iso_date + "Z");

    $('#project_last_activity_ts').text(d.toLocaleDateString() + " " +
        String(d.getHours()).padStart(2, "0") + ":" +
        String(d.getMinutes()).padStart(2, "0"));
}

function set_project_activation(proj_id, active) {

    if (active == "false") {
        if (confirm("Are you sure you wish to archive this project? All participants will be set to inactive and will have to be re-activated in future if you choose to re-activate this project.")) {
            $.ajax({
                url: '/api/projects/' + proj_id + '/activate',
                data: {'active': active},
                type: 'POST',
                success: function (response) {

                    // reset change password form and hide modal
                    console.log(response.responseText);
                    location.reload();

                },
                error: function (error) {

                    console.log(error.responseText);
                }
            });
        }
    }
    else {
        $.ajax({
            url: '/api/projects/' + proj_id + '/activate',
            data: {'active': active},
            type: 'POST',
            success: function (response) {

                // reset change password form and hide modal
                console.log(response.responseText);
                location.reload();

            },
            error: function (error) {

                console.log(error.responseText);
            }
        });

    }


}

function refresh_participants() {

    // Get list of participants for this project
    $.get({
            url: '/api/projects/' + $("#project_id").val() + '/participants/',
            success: function (participants) {

                for (i = 0; i < participants.length; i++) {
                    var p = participants[i];
                    $('#participant_info_card').find('.card-body').append(render_participant_details(p));
                    if (i < participants.length - 1) {
                        $('#participant_info_card').find('.card-body').append('<hr>');
                    }
                }
            },
            dataType: 'json'
        }
    );
}

function render_participant_details(p) {

    // Start participant div
    var html = '<div id="participant_' + p.id + '_details">';
    // Header
    html += '<div id="participant_' + p.id + '_header" class="mb-2">';
    html += '<h6 style="margin-bottom: 0px;"><a href="javascript:load_and_show_participant_modal(' + p.project_id + ',' + p.id + ')" class="text-body">' + p.display_name + '</a>';
    html += '<div id="participant_' + p.id + '_header_info" class="d-inline-block"><span class="badge badge-pill badge-info ml-2 align-top">' + p.moments_count + '</span>';

    if (p.active) {

        html += '<a id="participant_' + p.id + '_active_badge" class="badge badge-success ml-2 align-top" href="javascript:set_participant_active_state(' + p.id + ', \'false\');">Active</a>';
    }
    else {
        html += '<a id="participant_' + p.id + '_active_badge" class="badge badge-secondary ml-2 align-top" href="javascript:set_participant_active_state(' + p.id + ', \'true\');">Inactive</a>';
    }
    html += '</div></h6><span class="small text-muted" id="participant_' + p.id + '_description">' + p.description + '</span></div>';

    // Info

    var activity = new Date(p.last_activity_ts + "Z");

    html += '<div class="row small">';
    html += '<div class="col">Internal ID: ' + p.id + '</div>';
    html += '<div class="col">Last activity: ' + activity.toLocaleDateString() + ' ' + String(activity.getHours()).padStart(2, "0") + ':' + String(activity.getMinutes()).padStart(2, "0") + '</div>';

    html += '</div></div>';

    return html;
}

function set_participant_active_state(p_id, state) {

    console.log('running set_participant_active_state');

    $.ajax({
        url: '/api/participants/' + p_id,
        method: 'put',
        data: {active: state},
        success: function (result, status, xhr) {

            console.log(result);

            if (JSON.parse(result).active) {
                $('#participant_' + p_id + '_active_badge').replaceWith('<a id="participant_' + p_id + '_active_badge" class="badge badge-success ml-2 align-top" href="javascript:set_participant_active_state(' + p_id + ', \'false\');">Active</a>');
                // Update modal badge (shouldn't matter if not showing)
                $('#view_edit_participant_modal').find('#participant_' + p_id + '_active_badge').replaceWith('<a id="participant_' + p_id + '_active_badge" class="badge badge-success ml-2" href="javascript:set_participant_active_state(' + p_id + ', \'false\');">Active</a>');
            }
            else {
                $('#participant_' + p_id + '_active_badge').replaceWith('<a id="participant_' + p_id + '_active_badge" class="badge badge-secondary ml-2 align-top" href="javascript:set_participant_active_state(' + p_id + ', \'true\');">Inactive</a>');
                // Update modal badge
                $('#view_edit_participant_modal').find('#participant_' + p_id + '_active_badge').replaceWith('<a id="participant_' + p_id + '_active_badge" class="badge badge-secondary ml-2" href="javascript:set_participant_active_state(' + p_id + ', \'true\');">Inactive</a>');
            }
        }
    });
}

function scroll_to_item(moment_id = null, comment_id = null) {

    if (comment_id) {

        // expand comments area within moment
        $('#moments_frame').contents().find('#moment_' + moment_id + '_comments').addClass('show');
        $('#moments_frame').contents().find('#moment_' + moment_id + '_comment_' + comment_id)[0].scrollIntoView({behavior: 'smooth'});

    }
    else {
        $('#moments_frame').contents().find('#moment_' + moment_id)[0].scrollIntoView({behavior: 'smooth'});
    }

}

function load_and_show_participant_modal(proj_id, p_id, mode = 'view') {

    var port = "";

    if (window.location.port != 80 && window.location.port != 443 && window.location.port != "") {
        port = ":" + window.location.port;
    }

    var https_url_base = window.location.protocol + "//" + window.location.hostname + port;

    var ending;

    if (mode == 'view') {
        ending = p_id;
    }
    else if (mode == 'edit') {
        ending = p_id + '/edit';
    }

    else if (mode == 'add') {
        ending = 'add';
    }

    var modal_url = https_url_base + '/projects/' + proj_id + '/participants/' + ending;
    console.log(modal_url);

    /*$('#participant_modal_placeholder').load(modal_url, null, function () {
        $('#view_edit_participant_modal').modal('show');
    });
    */
    $('#participant_modal_placeholder').load('https://cxt.bunnyfoot.com/projects/10/participants/68/', null, function () {
        $('#view_edit_participant_modal').modal('show');
    });

}

function delete_participant_from_project(project_id, participant_id) {

    $.ajax({
        url: 'https://cxt.bunnyfoot.com/api/projects/' + project_id + '/participants/' + participant_id,
        method: 'delete',
        success: function (data, status, xhr) {
            // Show dialogue, close window
            deleted_p = JSON.parse(data);
            alert(deleted_p.display_name + " successfully deleted.");
            $('#view_edit_participant_modal').modal('hide');
            window.location.reload();
        },
        error: function (xhr, status, error) {
            // show error message in modal
            var err_msg = xhr.responseText;
            $('#view_edit_participant_modal').find('.modal-body').append('<div class="alert alert-warning alert-dismissible mt-4"><button type="button" class="close" data-dismiss="alert">&times;</button>' + err_msg + '</div>');
        }
    });
}

function show_client_modal(client_id = null, mode) {

    var ending;

    if (mode == 'add') {
        ending = 'add';
    }
    else if (mode == 'edit') {
        ending = client_id + '/edit'
    }
    else if (mode == 'view') {
        ending = client_id + '/view'
    }
    $('#client_modal_placeholder').load('https://cxt.bunnyfoot.com/clients/' + ending, null, function () {
        $('#client_modal').modal('show');
    });


}

function show_consultant_modal(consultant_id = null, mode) {

    var ending;

    if (mode == 'add') {
        ending = 'add';
    }
    else if (mode == 'edit') {
        ending = consultant_id + '/edit'
    }
    else if (mode == 'view') {
        ending = consultant_id + '/view'
    }
    $('#consultant_modal_placeholder').load('https://cxt.bunnyfoot.com/consultants/' + ending, null, function () {
        $('#consultant_modal').modal('show');
    });

}

function show_project_modal(project_id = null, mode) {

    var ending;

    console.log('show project modal triggered');

    if (mode == 'add') {
        ending = 'add';
    }
    else if (mode == 'edit') {
        ending = project_id + '/edit';
    }

    $('#project_modal_placeholder').load('https://cxt.bunnyfoot.com/projects/' + ending, null, function () {
        $('#project_modal').modal('show');
    });
}
