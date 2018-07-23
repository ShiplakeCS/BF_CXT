from flask import session, abort, request, send_file, send_from_directory
from datetime import datetime
from cxt_app import app, db_models
import json

# Read for more details on builing an API, particularly its routes: https://www.restapitutorial.com/index.html
# Read for more details on authentication and authorisation when accessing an API: https://blog.restcase.com/restful-api-authentication-basics/

@app.route('/config')
def show_config():
    return json.dumps({"upload_folder":app.config['UPLOAD_FOLDER'], "moment_media_folder": app.config['MOMENT_MEDIA_FOLDER']}, indent=4)



# TODO: These routes do not yet represent a true, stateless RESTful API. They require that a user has set up a session and has logged in/authenticated to that session. This works for web-app, but wouldn't for a native app requesting info via an API.

def auth_consultant():

    # TODO: Replace logic for authroising a consultant to provide a true authenticated API

    return 'active_consultant' in session and session['active_consultant']is not None


def auth_participant(id):

    id = int(id)
    return 'active_participant_id' in session and int(session['active_participant_id']) == id



## Consultant routes

@app.route('/api/consultants/<int:id>', methods=['GET'])
def get_consultant(id):

    if not auth_consultant():
        abort(401)

    try:
        c = db_models.Consultant(id)
        return c.to_json()

    except db_models.ConsultantNotFoundError:
        return json.dumps({"error_code":"301", "error_text":"No consultant found with ID {}".format(id)}), 404

@app.route('/api/consultants/', methods=['GET'])
def get_consultants():

    if not auth_consultant():
        abort(401)

    # TODO: Add get all consultants static method to consultant object
    return db_models.Consultant.get_all_consultants_json()



## Participant routes

@app.route('/api/participants/<int:id>', methods=['GET'])
def get_participant(id):

    # Only authorise is a consultant is logged in or a participant has logged in and the currently logged-in
    # participant is the same as the participant's info being requested.

    if auth_consultant() or auth_participant(id):

        try:
            return db_models.Participant(id).to_json()
        except db_models.ParticipantNotFoundError:
            return json.dumps({"error_code":"101", "error_text":"No participant found with ID {}".format(id)})

    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/since/<m_id>')
def get_participant_moments_since_id(p_id, m_id):

    if auth_consultant() or auth_participant(p_id):
        return db_models.Moment.get_moments_for_participant_json(int(p_id), int(m_id))

    else:
        abort(401)

@app.route('/api/participants/<p_id>/moments/<moment_id>/media/<media_id>/<size>')
def get_participant_moment_media(p_id, moment_id, media_id, size):
    if auth_consultant() or auth_participant(p_id):

        media = db_models.MomentMedia(media_id)

        if media.parent_moment_id != int(moment_id):
            abort(404)
        if size == 'original':
            return send_file(media.path_original, attachment_filename=media.original_filename)
        elif size == 'small':
            return send_file(media.path_small_thumb, attachment_filename=media.original_filename)
        elif size == 'large':
            return send_file(media.path_large_thumb, attachment_filename=media.original_filename)


    else:
        abort(401)


## Project routes

@app.route('/api/projects/', methods=['GET'])
def get_projects():

    if not auth_consultant():
        abort(401)

    return db_models.Project.get_all_projects_json()

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):

    if not auth_consultant():
        abort(401)

    try:
        return db_models.Project(project_id).to_json()

    except db_models.ProjectNotFound:
        return json.dumps({"error_code":201, "error_text": "No project found with ID {}".format(project_id)}), 404


@app.route('/api/projects/<int:project_id>/client', methods=['GET'])
def get_project_client(project_id):

    if not auth_consultant():
        abort(401)

    try:
        return db_models.Project(project_id).client.to_json()

    except db_models.ProjectNotFound:
        return json.dumps({"error_code":201, "error_text": "No project found with ID {}".format(project_id)}), 404


@app.route('/api/projects/<int:project_id>/consultants', methods=['GET'])
def get_project_consultants(project_id):

    if not auth_consultant():
        abort(401)

    consultant_dicts = []

    try:
        for c in db_models.Project(project_id).consultants:
            consultant_dicts.append(c.to_dict())

        return json.dumps(consultant_dicts, indent=4)

    except db_models.ProjectNotFound:
        return json.dumps({"error_code":201, "error_text": "No project found with ID {}".format(project_id)}), 404

@app.route('/api/projects/<project_id>/participants', methods=['GET'])
def get_project_participants(project_id):

    if not auth_consultant():
        abort(401)


    try:
        project_participants = db_models.Participant.get_participants_for_project(project_id)

        participants_dicts = []

        for p in project_participants:

            participants_dicts.append(p.to_dict())

        return json.dumps(participants_dicts, indent=4)

    except db_models.ProjectNotFound:

        return json.dumps({"error_code":"201", "error_text":"No project found with ID {}".format(project_id)}), 404


## Client routes

@app.route('/api/clients/', methods=['GET'])
def get_all_clients():

    if not auth_consultant():
        abort(401)

    return db_models.Client.get_all_clients_json()

@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):

    if not auth_consultant():
        abort(401)

    try:
        return db_models.Client(client_id).to_json()

    except db_models.ClientNotFoundError:
        return json.dumps({"error_code": 401, "error_text": "No client found with ID {}".format(client_id)}, indent=4), 404


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
