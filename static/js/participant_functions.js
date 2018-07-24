function start_moments_and_comments_feed_ajax(p_id){

    var callback_interval_sec = 10;

    sessionStorage.moments_displayed = "";
    sessionStorage.comments_displayed = "";
    sessionStorage.highest_moment_id = 0;
    sessionStorage.highest_comment_id = 0;

    load_participant_moments(p_id);


    window.setInterval(get_new_moments, callback_interval_sec * 1000, p_id);
    window.setInterval(get_moment_comments, callback_interval_sec * 1000, p_id);

}

function render_moment_html(m) {

    var moment_html = '<div class="moment_card card mb-4" id="moment_' + m.id + '">';

    ////// MOMENT CARD HEADER

    var modified_date = new Date(m.modified_ts);

    moment_html += '<div class="card-header small"> ' +
        '<span class="float-left">' + modified_date.toLocaleDateString() + ' ' + modified_date.getHours() + ':' + modified_date.getMinutes() + '</span>' +
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
            moment_html += '<a href="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/original" aria-label="original thumbnail"><img class="card-img-bottom mb-2" src="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/large" alt="Moment image" style="width:100%"></a>';

        }
        //if video...
        else if (m.media[media_num].media_type == 'video') {
            moment_html += '<video width="100%" controls><source src="/api/participants/' + m.parent_participant_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/original" type="video/mp4"></video>';
        }


    }

    if (m.gps.lat != null) {
        moment_html += '<a href="https://www.google.com/maps/search/?api=1&query=' + m.gps.lat + ',' + m.gps.long + '" class="small text-muted">&#x1F4CD; Location captured</a>';
    }
    moment_html += '</div>';

    ////// MOMENT CARD FOOTER
    // generate moment card footer as placeholder for comments

    moment_html += '<div class="card-footer">' +
        '<span id = "moment_' + m.id + '_new_comment_indicator" class="text-info d-none">&#9679;</span>'+
        '<button id="moment_' + m.id + '_show_comments_button" data-toggle="collapse" data-target="#moment_' + m.id + '_comments">' +
        'Comments (<span id="moment_'+ m.id +'_comments_count_label">0</span>)</button>' +
        '<div id="moment_' + m.id + '_comments" class="collapse">' +
        '<button id="moment_' + m.id+ '_add_comment_button" class="btn btn-info btn-sm btn-block text-light" onclick="">Add comment</button>' +
        '</div></div>';

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
                    // add jquery to animate display of new moments
                    sessionStorage.moments_displayed += moments.moments[i].id + ',';
                    var new_moment_card = $('#moments div:first-child');
                    new_moment_card.hide();

                    // add new item indicator (green dot) to moment card header
                    new_moment_card.find(".card-header span.float-left").prepend("<span id = 'new_moment_indicator' class='text-success mr-2'>&#9679;</span>");
                    new_moment_card.slideDown("fast");
                    new_moment_card.hover(function () {
                        $(this).find("#new_moment_indicator").remove();
                    });
                    setTimeout(function () {
                        new_moment_card.find("#new_moment_indicator").remove();
                    }, 60 * 1000);
                }

                if (new_moments.count > 0) {
                    sessionStorage.highest_moment_id = new_moments.highest_moment_id;
                }

            }
        }


        xhr.open('GET', '/api/participants/' + p_id + '/moments/?min=' + (parseInt(sessionStorage.highest_moment_id) + 1) + '&limit=' + limit + "&order=asc", true);

        xhr.send(null);
    }

}

function render_comment_html(c) {

    var comment_ts = new Date(c.ts);

    if (c.consultant_author){
        var display_name = c.display_name;
    }
    else {
        display_name = "You";
    }

    var comment_html = '<div class="card mb-2" id="moment_' + c.parent_moment+ '_comment_' + c.id + '">';
    comment_html += '<div class="card-body"><div class="card-title small">';
    comment_html += '<span class="font-weight-bold">' + display_name + '</span><br/>' + comment_ts.toLocaleDateString() + ' ' + comment_ts.getHours() + ':' + comment_ts.getMinutes();
    comment_html += '</div>';
    comment_html += '<p class="card-text">'+c.text+'</p>\n';
        comment_html += '</div>';
    comment_html += '</div>';

    return comment_html;
}

function append_comment_to_moment(c, first_run=false) {

    var target_button_name = '#moment_' + c.parent_moment + '_add_comment_button';
    // find moment div for comment's parent moment and append to div before button
    $(render_comment_html(c)).insertBefore(target_button_name);

    // increment moment's comment count
    var target_count_label = '#moment_' + c.parent_moment + '_comments_count_label';
    $(target_count_label).text(parseInt($(target_count_label).text()) + 1);

    // show moment's new comment indicator
    if (!first_run){
        var target_indicator_label = '#moment_' + c.parent_moment + '_new_comment_indicator';
        $(target_indicator_label).removeClass('d-none');
        $('#moment_'+c.parent_moment).find('.card-footer').click(function (){
            $(target_indicator_label).addClass('d-none');
        });
    }
}


function get_moment_comments(p_id, first_run=false) {

    if (!sessionStorage.highest_comment_id) {
        sessionStorage.highest_comment_id = 0;
    }
    else if (sessionStorage.highest_comment_id=='null'){
        sessionStorage.highest_comment_id = 0;
    }

    if (first_run){
        sessionStorage.highest_comment_id = 0;
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
                append_comment_to_moment(current_comment, first_run);
                sessionStorage.comments_displayed += current_comment.id + ',';
            }

            // update highest_comment_id for next call
            if (participant_comments.count > 0){
                sessionStorage.highest_comment_id = participant_comments.highest_comment_id;
                if (!first_run){
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


function load_moments_old(p_id) {
    // To get new moments for participant moment page
    var xhr = new XMLHttpRequest();
    xhr.onload = function () {
        if (xhr.status === 200) {
            responseObject = JSON.parse(xhr.responseText);

            var content = "";
            for (var i = 0; i < responseObject.length; i++) {
                content += "<div class='moment' id='moment_" + responseObject[i].id + "'>" +
                    "<span class='moment_timestamp'>" + responseObject[i].timestamp + " </span>";

                // Show rating stars (out of 5, filled as appropriate
                var filled_stars = 0;
                for (var r = 0; r < responseObject[i].rating; r++) {
                    content += "<span class='moment_rating_indicator'>&#x2605;</span>";
                    filled_stars += 1;
                }
                for (var r = 0; r < (5 - filled_stars); r++) {
                    content += "<span class='moment_rating_indicator'>&#x2606;</span>";
                }
                content += "<br />";

                // Show moment text
                content += "<p>" + responseObject[i].text + "</p>";

                // Show moment media if added.
                // TODO: Current only shows image, need to determine type and show either image or video as appropriate.
                if (responseObject[i].media != '') {
                    content += "<img  class='moment_media' src='" + responseObject[i].media + "'/>";

                }
                else {
                    content += "<p>No media uploaded for this moment</p>";
                }

                // Add placeholder for comments
                content += "<div id='moment_" + responseObject[i].id + "_comments' class='moment_comments'>" +
                    "<br /><button type='button'>Add comment</button></div>";

                content += "</div>";
            }
            document.getElementById('moments').innerHTML = content;
        }
    };
    xhr.open('GET', '/api/participants/' + p_id + '/moments/since/0', true);

    xhr.send(null);
}


function append_comment(comment_data, moment_id) {

    // Appends a comment to a given moment's div, based on the moment_id value passed

    var comment_date = new Date(comment_data.timestamp);

    var comment_html =
        "<div class='comment'>" +
        "<div class='comment_metadata'>" +
        "<p class='comment_author'>" + comment_data.author + "</p>" +
        "<p class='comment_time'>" + comment_date.toLocaleTimeString() + "</p>" +
        "<p class='comment_date'>" + comment_date.toLocaleDateString() + "</p>" +
        "</div>" +
        "<div class='comment_text'>" +
        "<span class='comment_text'>" + comment_data.text + "</span>" +
        "</div>" +
        "</div>";

    var moment_div = document.getElementById("moment_" + moment_id);
    var existing_content = moment_div.innerHTML;

    // remove final </div> from innerHTML

    existing_content = existing_content.slice(0, existing_content.lastIndexOf("</div>"));

    moment_div.innerHTML = existing_content + comment_html + "</div>";


}

function load_comment_counts() {

    var xhr_count = new XMLHttpRequest();

    xhr_count.onload = function () {

        if (xhr_count.status === 200) {

            var comment_counts = JSON.parse(xhr_count.responseText);

            for (i = 0; i < comment_counts.length; i++) {
                var comments_div = document.getElementById("moment_" + comment_counts[i].moment_id + "_comments");
                var existing_html = comments_div.innerHTML;

                comments_div.innerHTML = "<h3 class='moment_comment_count'>Comments (" +
                    comment_counts[i].count + ")</h3>" + existing_html;
            }
        }
    }

    xhr_count.open('GET', '/api/get/comments/count/1');
    xhr_count.send(null);
}

function load_comments() {

    // Loads new comments for a given participant and appends them to the appropriate Moment div by calling
    // append_comment()

    var xhr = new XMLHttpRequest();

    xhr.onload = function () {

        if (xhr.status === 200) {

            var comments = JSON.parse(xhr.responseText);

            for (var i = 0; i < comments.length; i++) {
                append_comment(comments[i], comments[i].moment_id);
            }

        }
    };
    xhr.open('GET', '/api/get/comments/1', true);
    xhr.send(null);
}