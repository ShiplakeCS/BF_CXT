function load_moments() {
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
    xhr.open('GET', '/api/get/moments/1', true);
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