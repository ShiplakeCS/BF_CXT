function start_moments_and_comments_feed_ajax(p_id) {

    var callback_interval_sec = 10;

    sessionStorage.moments_displayed = "";
    sessionStorage.comments_displayed = "";
    sessionStorage.highest_moment_id = 0;
    sessionStorage.highest_comment_id = 0;
    sessionStorage.p_id = p_id;
    load_participant_moments(p_id);


    window.setInterval(get_new_moments, callback_interval_sec * 1000, p_id);
    window.setInterval(get_moment_comments, callback_interval_sec * 1000, p_id);

}

function render_moment_html(m) {

    var moment_html = '<div class="moment_card card mb-4" id="moment_' + m.id + '">';

    ////// MOMENT CARD HEADER

    var modified_date = new Date(m.modified_ts + "Z");

    moment_html += '<div class="card-header small"> ' +
        '<span class="float-left">' + modified_date.toLocaleDateString() + ' ' + String(modified_date.getHours()).padStart(2, "0") + ':' + String(modified_date.getMinutes()).padStart(2, "0") + '</span>' +
        '<span class="float-right text-muted" style="font-family:sans-serif">';

    // Generate ratings stars: Filled in stars
    for (var r = 0; r < m.rating; r++) {
        moment_html += '&#x2605;';
    }
    // Generate ratings stars: empty in stars
    for (var r = 0; r < (5 - m.rating); r++) {
        moment_html += '&#x2606;';
    }

    moment_html += '</span>' +
        '</div>';

    ////// MOMENT CARD BODY
    moment_html += '<div class="card-body">' +
        '<p class="card-text">' + m.text + '</p>';

    //TODO: Replace with dynamically loaded moment media for each one found in m.media
    for (var media_num = 0; media_num < m.media.length; media_num++) {

        // if image...

        if (m.media[media_num].media_type == 'image') {
            moment_html += '<a href="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/original" aria-label="original thumbnail"><img class="card-img-bottom mb-2 img-thumbnail" src="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/large" alt="Moment image" style="width:100%"></a>';

        }
        //if video...
        else if (m.media[media_num].media_type == 'video') {
            moment_html += '<video width="100%" controls <!--preload="none"-->><source src="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/video/video.mp4" type="video/mp4"></video>';
        }


    }

    if (m.gps.lat != null) {
        moment_html += '<a href="https://www.google.com/maps/search/?api=1&query=' + m.gps.lat + ',' + m.gps.long + '" class="small text-muted">&#x1F4CD; Location captured</a>';
    }
    moment_html += '</div>';

    ////// MOMENT CARD FOOTER
    // generate moment card footer as placeholder for comments

    moment_html += '<div class="card-footer small">' +
        '<span id = "moment_' + m.id + '_new_comment_indicator" class="text-info d-none">&#9679;</span>' +
        '<button id="moment_' + m.id + '_show_comments_button" data-toggle="collapse" data-target="#moment_' + m.id + '_comments" class="btn btn-secondary btn-sm">' +
        'Comments <span id="moment_' + m.id + '_comments_count_label" class="badge badge-light">0</span></button>' +
        '<div id="moment_' + m.id + '_comments" class="mt-2 collapse">' +
        '<div id="moment_' + m.id + '_comments_form">' +
        '<div>\n' +
        '<label for="new_comment">Add comment:</label>\n' +
        '<textarea id="moment_' + m.id + '_new_comment" class="form-control mb-2" rows="2" name="comment_text"></textarea><button id="moment_' + m.id + '_save_comment_button" class="btn btn-info btn-sm btn-block text-light" onclick=process_new_comment(' + m.id + ',' + m.parent_participant_id + ')>Save comment</button>\n' +
        '</div>' +
        '</div></div></div>';

    moment_html += '</div>';

    return moment_html;

}

function load_participant_moments(p_id, min_id = null, max_id = null, limit = 20, order = 'desc') {

    // Run when the moments feed page first loads. Subsequent calls for new moments are via get_new_moments()

    var xhr = new XMLHttpRequest();

    xhr.onload = function () {

        // If the response to the request is OK
        if (xhr.status === 200) {
            // Get collection of moments
            var moments = JSON.parse(xhr.responseText);

            // for each moment, render a moment card

            for (var i = 0; i < moments.count; i++) {

                // append moment to moments div
                $('#moments').append(render_moment_html(moments.moments[i]));

                // add moment to list of displayed moments
                sessionStorage.moments_displayed += moments.moments[i].id + ',';

            }

            // apply comments to moments
            get_moment_comments(p_id, true);

            // add 'load more' link
            if (moments.moment_count_below_min >= 20) {
                $('#moments').append("<div>\n" +
                    "\t<a id='load_more_moments' href=\"#\" class=\"text-center d-block\">Load next 20 moments</a>\n" +
                    "</div>");
            }
            else if (moments.moment_count_below_min > 1) {
                $('#moments').append("<div>\n" +
                    "\t<a id='load_more_moments' href=\"#\" class=\"text-center d-block\">Load next " + moments.moment_count_below_min + " moments</a>\n" +
                    "</div>");
            }
            else if (moments.moment_count_below_min == 1) {
                $('#moments').append("<div>\n" +
                    "\t<a id='load_more_moments' href=\"#\" class=\"text-center d-block\">Load last moment</a>\n" +
                    "</div>");
            }
            $('a#load_more_moments').on('click', function (e) {
                e.preventDefault();
                $(this).remove();
                load_participant_moments(p_id, min_id = 0, max_id = (moments.lowest_moment_id - 1));

            });

            // Update the highest moment id value in session storage for later use by get_new_moments()
            sessionStorage.highest_moment_id = moments.highest_moment_id;
        }

    }

    xhr.open('GET', '/api/participants/' + p_id + '/moments/?min=' + min_id + '&max=' + max_id + '&limit=' + limit, true);

    xhr.send(null);
}

function get_new_moments(p_id, limit = 20) {

    if (sessionStorage.highest_moment_id) {

        var xhr = new XMLHttpRequest();

        xhr.onload = function () {

            // If the response to the request is OK
            if (xhr.status === 200) {
                // Get collection of moments
                new_moments = JSON.parse(xhr.responseText);

                // for each moment, render a moment card

                for (var i = 0; i < new_moments.count; i++) {

                    // append moment to moments div
                    $('#moments').prepend(render_moment_html(new_moments.moments[i]));
                    // add moment id to list of displayed moments
                    sessionStorage.moments_displayed += new_moments.moments[i].id + ',';

                    // update highest_moment_id in sessionStorage
                    if (new_moments.moments[i].id > parseInt(sessionStorage.highest_moment_id)) {
                        sessionStorage.highest_moment_id = new_moments.moments[i].id;
                    }

                    // add jquery to animate display of new moments
                    var new_moment_card = $('#moments div:first-child');
                    new_moment_card.hide();

                    // add new item indicator (green dot) to moment card header
                    new_moment_card.find(".card-header span.float-left").prepend("<span id = 'new_moment_indicator' class='text-info mr-2'>&#9679;</span>");
                    new_moment_card.slideDown("fast");
                    new_moment_card.hover(function () {
                        $(this).find("#new_moment_indicator").remove();
                    });
                    setTimeout(function () {
                        new_moment_card.find("#new_moment_indicator").remove();
                    }, 60 * 1000);
                }

                // if (new_moments.count > 0) {
                //     sessionStorage.highest_moment_id = new_moments.highest_moment_id;
                // }

            }
        }


        xhr.open('GET', '/api/participants/' + p_id + '/moments/?min=' + (parseInt(sessionStorage.highest_moment_id) + 1) + '&limit=' + limit + "&order=asc", true);

        xhr.send(null);
    }

}

function render_comment_html(c) {

    var comment_ts = new Date(c.ts + "Z");

    if (c.consultant_author) {
        var display_name = c.display_name;
    }
    else {
        display_name = "You";
    }

    var comment_html = '<div class="card mb-2" id="moment_' + c.parent_moment + '_comment_' + c.id + '">';
    comment_html += '<div class="card-body"><div class="card-title">';
    comment_html += '<span class="font-weight-bold">' + display_name + '</span><br/>' + comment_ts.toLocaleDateString() + ' ' + String(comment_ts.getHours()).padStart(2, "0") + ':' + String(comment_ts.getMinutes()).padStart(2, "0");
    comment_html += '</div>';
    comment_html += '<p class="card-text">' + c.text + '</p>\n';
    comment_html += '</div>';
    comment_html += '</div>';

    return comment_html;
}

function append_comment_to_moment(c, hide_notification = false, animate = false) {

    var target_comment_form = '#moment_' + c.parent_moment + '_comments_form';
    // find moment div for comment's parent moment and append to div before button
    $(render_comment_html(c)).insertBefore(target_comment_form);

    // increment moment's comment count
    var target_count_label = '#moment_' + c.parent_moment + '_comments_count_label';
    $(target_count_label).text(parseInt($(target_count_label).text()) + 1);

    // show moment's new comment indicator
    if (!hide_notification) {

        var target_comments_button = '#moment_' + c.parent_moment + '_show_comments_button';
        $(target_comments_button).removeClass('btn-secondary');
        $(target_comments_button).addClass('btn-info');

        $('#moment_' + c.parent_moment).find('.card-footer').click(function () {
            $(target_comments_button).removeClass('btn-info');
            $(target_comments_button).addClass('btn-secondary');
        });

        // var target_indicator_label = '#moment_' + c.parent_moment + '_new_comment_indicator';
        // $(target_indicator_label).removeClass('d-none');
        // $('#moment_'+c.parent_moment).find('.card-footer').click(function (){
        //     $(target_indicator_label).addClass('d-none');
        // });
    }

    if (animate) {
        $('#moment_' + c.parent_moment + '_comment_' + c.id).addClass('d-none');
        $('#moment_' + c.parent_moment + '_comment_' + c.id).slideUp('fast');
        $('#moment_' + c.parent_moment + '_comment_' + c.id).removeClass('d-none');
        $('#moment_' + c.parent_moment + '_comment_' + c.id).slideDown('fast');
    }

}

function get_moment_comments(p_id, first_run = false, hide_notification = false) {

    if (!sessionStorage.highest_comment_id) {
        sessionStorage.highest_comment_id = 0;
    }
    else if (sessionStorage.highest_comment_id == 'null') {
        sessionStorage.highest_comment_id = 0;
    }

    if (first_run) {
        sessionStorage.highest_comment_id = 0;
        hide_notification = true;
    }

    var xhr = new XMLHttpRequest();

    xhr.onload = function () {

        // If the response to the request is OK
        if (xhr.status === 200) {

            var participant_comments = JSON.parse(xhr.responseText);

            // For each comment...
            for (i = 0; i < participant_comments.count; i++) {
                // render comment as HTML
                current_comment = participant_comments.comments[i];
                // append to appropriate moment div
                append_comment_to_moment(current_comment, hide_notification);
                sessionStorage.comments_displayed += current_comment.id + ',';
            }

            // update highest_comment_id for next call
            if (participant_comments.count > 0) {
                sessionStorage.highest_comment_id = participant_comments.highest_comment_id;
                if (!hide_notification) {
                    // Show alert that new comments found
                    var alert_html = '<div class="alert alert-info alert-dismissible"><button type="button" class="close" data-dismiss="alert">&times;</button>You have new comments.</div>';

                    $('#moments').before(alert_html);
                }

            }
        }
    }
    // Make ajax call to get comments
    xhr.open('GET', '/api/participants/' + p_id + '/moments/comments/?moment_ids=' + sessionStorage.moments_displayed + '&exclude_comment_ids=' + sessionStorage.comments_displayed, true);


    xhr.send(null);

}

function process_new_comment(moment_id, participant_id) {

    // clear any existing warning messages
    $('textarea#moment_' + moment_id + '_new_comment').parent().find('p.text-danger').remove();

    // get comment text
    comment_text = $('textarea#moment_' + moment_id + '_new_comment').val();

    if (comment_text.length > 0) {
        // post comment to DB in background
        $.post('/api/participants/' + participant_id + '/moments/' + moment_id + '/comments/', {text: comment_text}, function (data) {
            // clear text area
            $('textarea#moment_' + moment_id + '_new_comment').val('');
            // get new comments for moment but hide 'new comments' notification
            get_moment_comments(participant_id, false, true);

        }).fail(function (data) {

            // get moment comment form and show warning text.

            $('textarea#moment_' + moment_id + '_new_comment').parent().find('label').after('<p class="text-danger">Your comment could not be added at this time. Please check that you have an internet connection and try again.</p>');

            console.log('There was a problem processing the comment: ' + data);
        });
    }


}

function get_location_for_moment_capture() {

    console.log('get_location triggered');
    $('#location').find('button').remove();
    $('#location').append("<div><span class='text-muted align-middle'>Getting location...</span><img src='/static/images/getting_location_animation.gif' class='ml-2' height='18px width='18px'></div>");

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(location_success, location_fail);
    } else {
        $('#location').find('button').remove();
        $('#location').append('<span class="text-warning">Your browser doesn\'t appear to support location services.</span>');
    }

    function location_success(position) {
        $('#gps_lat').val(position.coords.latitude);
        $('#gps_long').val(position.coords.longitude);
        sessionStorage.gps_long = position.coords.longitude;
        sessionStorage.gps_lat = position.coords.latitude;
        $('#location').find('div').remove();
        $('#location').append("<div><span class='text-success align-middle'>Location captured</span> <a href='#' class='btn-sm btn-light ml-2'>remove</a></div>");
        $('#location').find('a').click(function (e) {
            e.preventDefault();
            revoke_location_from_moment_capture();
        })

    }

    function location_fail(position) {
        $('#gps_lat').val('AttemptedButFailed');
        $('#gps_long').val('AttemptedButFailed');
    }
}

function revoke_location_from_moment_capture() {
    $('#gps_lat').val('Revoked');
    $('#gps_long').val('Revoked');
    $('#location').html('<p>Would you like to record your present location?</p><button class="btn btn-secondary btn-sm">Get location</button>');
}

function upload_files_attempt() {

    // Helpful resources:
    // https://stackoverflow.com/questions/18334717/how-to-upload-a-file-using-an-ajax-call-in-flask
    // https://stackoverflow.com/questions/166221/how-can-i-upload-files-asynchronously - progress bar explanation
    // https://www.w3schools.com/bootstrap4/bootstrap_progressbars.asp

    $(':file').on('change', function () {
        var file = this.files[0];
        if (file.size > 1024 * 10 * 1024) {
            alert('Warning, your upload size is greater than 10MB. This could take a long time unless you have a strong 4G or WiFi connection.')
        }
        $('#file_upload_button').trigger('click');

        // Also see .name, .type
    });

    $('#file_upload_button').on('click', function () {

        // Hide the upload form and show the progress bar
        $('#file_upload_form').addClass('d-none');
        $('#progress_bar').removeClass(('d-none'));
        // Disable the save moment button
        $('#save_moment_button').removeClass('btn-success');
        $('#save_moment_button').addClass('btn-light');
        $('#save_moment_button').addClass('text-muted');
        $('#save_moment_button').attr('disabled', 'disabled');

        // Do the upload
        $.ajax({
            url: '/p/capture/media',
            type: 'POST',
            data: new FormData($('#file_upload_form')[0]),
            cache: false,
            contentType: false,
            processData: false,
            timeout: 60000,
            success: function (result) {
                // To be called if all has gone well
                console.log(result);
                $('#progress_bar').addClass(('d-none'));
                var filepath = JSON.parse(result).file_path;
                $('#media_path').val(filepath);
                $('#media').append("<div id='uploaded_files'><span class='text-success align-middle'>&#128247; " +
                    filepath +
                    " uploaded.</span> <a href='#' id='remove_media_link' class='btn-sm btn-light ml-2'>remove</a></div>");
                $('#remove_media_link').click(function (e) {
                    e.preventDefault();
                    remove_uploaded_file(e);
                })

            },
            error: function (xhr, status, error) {
                // Tell the user that an error occured and show the upload form again so that they can attempt another upload
                $('#progress_bar').addClass(('d-none'));
                $('#media').prepend('<div><span class="text-warning align-middle">There was a problem uploading your file. Please check that you have a good internet connection and try again or save this moment without uploading your file.</span></div>');
                $('#file_upload_form').removeClass('d-none');
            },
            complete: function (xhr, status) {
                $('#save_moment_button').addClass('btn-success');
                $('#save_moment_button').removeClass('btn-light');
                $('#save_moment_button').removeClass('text-muted');
                $('#save_moment_button').removeAttr('disabled');
            },

            // Use a custom XMLHttpRequest object to make AJAX call with attached uploading progress listener
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable) {
                            $('.progress-bar').attr({style: 'width:' + (e.loaded / e.total) * 100 + '%'})
                        }
                    }, false);
                }
                return myXhr;
            }
        });
    });
}

function remove_uploaded_file(e) {

    if ($('#file_upload_input').val() != '') {
        // trigger ajax call to remove the file from the temp folder - need to write API route for this

        $.ajax({
            type: 'DELETE',
            url: '/api/participants/' + sessionStorage.p_id + '/moments/media/files/' + $('#media_path').val(),
            timeout: 60000,
            error: function (xhr, status, error) {
                if (e){
                    e.stopPropagation();
                    e.preventDefault();
                }
                console.log('unable to erase file.')
            },
            success: function () {
                $('#uploaded_files').remove();
                $('#file_upload_input').val('');
                $('#file_upload_form').removeClass('d-none');
                $('.progress-bar').attr({style: 'width:0%'});
                $('#media_path').val('');
            }
        });

    }

}