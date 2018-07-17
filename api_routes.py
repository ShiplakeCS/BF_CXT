from flask import session, abort
from datetime import datetime
from cxt_app import app

import json

@app.route('/api/get/moments/<participant_id>')
def get_moments(participant_id):

    if 'logged_in' in session and session['logged_in']:

        moments =[
            {
                "id":1,
                "timestamp": "Mon Jul 16 09:43:11 2018",
                "rating":3,
                "text":"A perfectly normal experience of buying a train ticket.",
                "media": "/static/images/moment_media_placeholder.png"
            },
            {
                "id":2,
                "timestamp": datetime.ctime(datetime.utcnow()),
                "rating": 5,
                "text": "Amazing customer service!",
                "media": ""

            },
            {
                "id":3,
                "timestamp": "Mon Jul 16 10:30:20 2018",
                "rating": 1,
                "text": "Horrible burger!",
                "media": "/static/images/moment_media_placeholder.png"
            }
        ]

        return json.dumps(moments, sort_keys=True, indent=4)

    else:
        print((str(session)))
        print("Attempt to access moments when not logged in!")

        abort(401)


@app.route('/api/get/comments/<participant_id>')
def get_comments(participant_id):

    if 'logged_in' in session and session['logged_in']:

        comments = [

            {
                "id": 1,
                "moment_id": 1,
                "timestamp": "Mon Jul 16 09:43:11 2018",
                "text": "Why do you say that?",
                "author": "Bob"
            },

            {
                "id": 2,
                "moment_id": 1,
                "timestamp": "Mon Jul 16 09:43:11 2018",
                "text": "It just was!.",
                "author": "Jane"
            },

            {
                "id": 3,
                "moment_id": 2,
                "timestamp": "Mon Jul 16 09:43:11 2018",
                "text": "This is a comment on moment 2",
                "author": "Bob"
            },
            {
                "id": 4,
                "moment_id": 1,
                "timestamp": "Mon Jul 16 09:43:11 2018",
                "text": "Ok, then :)",
                "author": "Bob"

            }
        ]

        return json.dumps(comments, sort_keys=True, indent=4)

    else:
        print((str(session)))
        print("Attempt to access comments when not logged in!")

        abort(401)




@app.route('/api/get/comments/count/<participant_id>')
def get_comments_count(participant_id):



    counts = [
        {
            "moment_id": 1,
            "count": 3
        },
        {
            "moment_id": 2,
            "count": 1

        },
        {
            "moment_id": 3,
            "count": 0
        }
    ]

    return json.dumps(counts)
