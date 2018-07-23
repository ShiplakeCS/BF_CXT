function load_participant_moments(p_id, since_moment_id) {

    var xhr = new XMLHttpRequest();

    xhr.onload = function () {

        // If the response to the request is OK
        if (xhr.status === 200) {
            // Get collection of moments
            moments = JSON.parse(xhr.responseText);

            // for each moment, render a moment card

            for (var i = 0; i < moments.length; i++) {

                moment_html = "";

                // get current moment
                m = moments[i];

                moment_html = '<div class="card mb-4" id="moment_x">';

                // generate moment card header

                modified_date = new Date(m.modified_ts);

                moment_html += '<div class="card-header small"> ' +
                    '<span class="float-left">' + modified_date.toLocaleDateString() + ' ' + modified_date.getHours() + ':' + modified_date.getMinutes() + '</span>' +
                    '<span class="float-right text-muted" style="font-family:sans-serif">';

                for (var r = 0; r < m.rating; r++) {
                    moment_html += '&#x2605;';
                }

                for (var r = 0; r < (5 - m.rating); r++) {
                    moment_html += '&#x2606;';
                }

                moment_html += '</span>' +
                    '</div>';

                // generate moment card body

                moment_html += '<div class="card-body">' +
                    '<p class="card-text">' + m.text + '</p>';

                //TODO: Replace with dynamically loaded moment media for each one found in m.media
                for (var media_num = 0; media_num < m.media.length; media_num++) {

                    // if image...

                    if (m.media[media_num].media_type == 'image') {
                        moment_html += '<a href="/api/participants/' + p_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/original" aria-label="original thumbnail"><img class="card-img-bottom mb-2" src="/api/participants/' + p_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/large" alt="Moment image" style="width:100%"></a>';

                    }
                    //if video...
                    else if (m.media[media_num].media_type == 'video') {
                        moment_html += '<video width="100%" controls><source src="/api/participants/' + p_id + '/moments/' + m.id + '/media/' + m.media[media_num].id + '/original" type="video/mp4"></video>';
                    }


                }

                if (m.gps.lat != null) {
                    moment_html += '<a href="https://www.google.com/maps/search/?api=1&query=' + m.gps.lat + ',' + m.gps.long + '" class="small text-muted">&#x1F4CD; Location captured</a>';
                }
                moment_html += '</div>';

                // generate moment card footer as placeholder for comments

                moment_html += '<div class="card-footer">' +
                    '<button data-toggle="collapse" data-target="#moment_' + m.id + '_comments">' +
                    'Comments (count)</button>' +
                    '<div id="moment_' + m.id + '_comments" class="collapse">' +
                    '</div>' +
                    '</div>';

                moment_html += '</div>';
                // append moment to moments div
                $('#moments').append(moment_html);

            }


        }

    }

    xhr.open('GET', '/api/participants/' + p_id + '/moments/since/' + since_moment_id, true);

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