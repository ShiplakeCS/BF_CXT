from flask import session, abort, request, send_file, redirect, url_for, send_from_directory
from cxt_app import app, db_models, tests
import json, os, shutil, datetime
from werkzeug.utils import secure_filename


# Read for more details on builing an API, particularly its routes: https://www.restapitutorial.com/index.html
# Read for more details on authentication and authorisation when accessing an API: https://blog.restcase.com/restful-api-authentication-basics/

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/config')
def show_config():
    return json.dumps(
        {"upload_folder": app.config['UPLOAD_FOLDER'], "moment_media_folder": app.config['MOMENT_MEDIA_FOLDER']},
        indent=4)


# TODO: These routes do not yet represent a true, stateless RESTful API. They require that a user has set up a session and has logged in/authenticated to that session. This works for web-app, but wouldn't for a native app requesting info via an API.

def auth_consultant():
    # TODO: Replace logic for authroising a consultant to provide a true authenticated API

    return 'active_consultant' in session and session['active_consultant'] is not None


def get_active_consultant():
    if 'active_consultant' in session:
        return db_models.Consultant(session['active_consultant'])
    else:
        return None


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
        return json.dumps({"error_code": "301", "error_text": "No consultant found with ID {}".format(id)}), 404


@app.route('/api/consultants/', methods=['GET', 'POST'])
def api_consultants():

    if not auth_consultant():
        abort(401)

    if request.method == "GET":
        return db_models.Consultant.get_all_consultants_json()

    elif request.method == "POST":
        try:
            consultant = db_models.Consultant.add_new_to_db(request.values['email'], request.values['reset_password'], request.values['display_name'], request.values['first_name'], request.values['last_name'], request.values['active']=='true', request.values['admin']=='true')
            return consultant.to_json()

        except Exception as e:
            return str(e), 400


@app.route('/api/consultants/<consultant_id>', methods=['GET', 'PUT', 'DELETE'])
def api_consulant_actions(consultant_id):

    if not auth_consultant():
        abort(401)

    try:
        consultant = db_models.Consultant(consultant_id)

        if request.method == "GET":
            return consultant.to_json()

        elif request.method == "PUT":

            c = get_active_consultant()
            if not c.admin:
                abort(401)

            consultant.email = request.values['email']
            consultant.display_name = request.values['display_name']
            consultant.first_name = request.values['first_name']
            consultant.last_name = request.values['last_name']
            print(request.values['active'])
            consultant.active = request.values['active'] == 'true'
            consultant.set_admin(request.values['admin'] == 'true', c)

            print(request.values['reset_password'])

            if request.values['reset_password'] != "":
                consultant.change_password("", request.values['reset_password'], c)

            consultant.update_in_db()

            return consultant.to_json()

        elif request.method == "DELETE":

            c = get_active_consultant()
            if not c.admin:
                abort(401)

            consultant.delete_from_db(c)

            return consultant.to_json()

    except db_models.ConsultantNotFoundError:
        abort(404)

    except db_models.ConsultantUpdateError as e:
        return str(e), 400

    except Exception as e:
        return str(e), 400

@app.route('/api/consultants/<c_id>/change_password', methods=['POST'])
def change_consultant_password(c_id):
    c = get_active_consultant()

    if not c or not c.admin or c.id != int(c_id):
        abort(401)
    try:
        c.change_password(request.form['old_pass'], request.form['new_pass'])
        return 'password updated for consultant {}'.format(c_id)
    except:
        return 'Incorrect original password provided', 401


## Participant routes

@app.route('/api/participants/<int:id>', methods=['GET', 'PUT'])
def get_participant(id):
    # Only authorise is a consultant is logged in or a participant has logged in and the currently logged-in
    # participant is the same as the participant's info being requested.

    if request.method == "GET":
        if auth_consultant() or auth_participant(id):

            try:
                return db_models.Participant(id).to_json()
            except db_models.ParticipantNotFoundError:
                return json.dumps({"error_code": "101", "error_text": "No participant found with ID {}".format(id)})

        else:
            abort(401)

    elif request.method == "PUT":
        # Update participant based on values sent with request
        if auth_consultant():
            try:
                p = db_models.Participant(id)

                if 'active' in request.values:
                    p.active = True if request.values['active'] == 'true' else False

                p.update_in_db()

                return p.to_json()

            except db_models.ParticipantNotFoundError:
                abort(404)
        else:
            abort(401)


@app.route('/api/participants/<p_id>/moments/since/<m_id>')
def get_participant_moments_since_id(p_id, m_id):
    if auth_consultant() or auth_participant(p_id):
        return db_models.Moment.get_moments_for_participant_json(int(p_id), int(m_id))

    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/')
def get_participants_moments(p_id):
    min_id = None
    max_id = None
    limit = None
    order = None

    if request.args.get('min'):
        min_id = request.args.get('min')
    if request.args.get('max'):
        max_id = request.args.get('max')
    if request.args.get('order'):
        order = request.args.get('order')
    if request.args.get('limit'):
        limit = request.args.get('limit')

    if auth_consultant() or auth_participant(p_id):
        return db_models.Moment.get_moments_for_participant_json(int(p_id), min_id, max_id, limit, order)

    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/<moment_id>/', methods=['DELETE'])
def delete_participant_moment(p_id, moment_id):
    if auth_consultant() or auth_participant(p_id):

        try:
            moment_to_delete = db_models.Moment(moment_id)
            if moment_to_delete.parent_participant_id != int(p_id):
                abort(401)  # Not the correct participant therefore cannot delete
            moment_to_delete.delete_from_db()
            return moment_to_delete.to_json()

        except db_models.MomentNotFoundError:
            abort(400)
    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/comments/')
def get_participants_comments(p_id):
    if auth_consultant() or auth_participant(p_id):

        comments_since_id = request.args.get('since')

        if comments_since_id:
            return db_models.MomentComment.get_comments_for_participant_json(p_id, comments_since_id)

        moment_ids = request.args.get('moment_ids')
        exclude_comment_ids = request.args.get('exclude_comment_ids')

        if moment_ids:
            moment_ids = moment_ids.replace("%2C", ",")
            moment_ids = moment_ids.split(',')
            try:
                moment_ids.remove("")
            except ValueError:
                pass

        if exclude_comment_ids:
            exclude_comment_ids = exclude_comment_ids.replace("%2C", ",")
            exclude_comment_ids = exclude_comment_ids.split(',')
            try:
                exclude_comment_ids.remove("")
            except ValueError:
                pass

        if moment_ids or exclude_comment_ids:
            return db_models.MomentComment.get_comments_for_moment_ids_json(moment_ids, exclude_comment_ids)

        else:
            abort(404)
    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/<moment_id>/media/<media_id>/video/<path:filename>')
def get_participant_moment_media_video(p_id, moment_id, media_id, filename):
    if auth_consultant() or auth_participant(p_id):

        media = db_models.MomentMedia(media_id)

        if media.parent_moment_id != int(moment_id):
            abort(404)

        if media.media_type != 'video':
            abort(400)

        return send_from_directory(media.media_file_path, media.original_filename)

    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/<moment_id>/media/<media_id>/<size>/')
def get_participant_moment_media(p_id, moment_id, media_id, size):
    if auth_consultant() or auth_participant(p_id):

        media = db_models.MomentMedia(media_id)

        if media.parent_moment_id != int(moment_id):
            abort(404)

        if media.media_type == 'video':
            return send_file(media.path_original, attachment_filename='video.mp4')

        if size == 'original':
            return send_file(media.path_original, attachment_filename=media.original_filename)
        elif size == 'small':
            return send_file(media.path_small_thumb, attachment_filename=media.original_filename)
        elif size == 'large':
            return send_file(media.path_large_thumb, attachment_filename=media.original_filename)


    else:
        abort(401)


## Moment media

@app.route('/api/participants/<p_id>/moments/media/temp/<filename>', methods=['GET', 'DELETE'])
def delete_temp_media_file(p_id, filename):
    if auth_consultant() or auth_participant(p_id):
        filename = secure_filename(filename)

        if request.method.upper() == "DELETE":
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], "{}_thumb.jpg".format(filename))):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], "{}_thumb.jpg".format(filename)))
                return json.dumps({'deleted_filepath': filename})
            except:
                abort(400)
        elif request.method.upper() == "GET":
            try:
                return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except:
                abort(404)
    else:
        abort(401)


@app.route('/api/participants/<p_id>/moments/<moment_id>/comments/', methods=['post'])
def add_participant_moment_comment(p_id, moment_id):
    if auth_participant(p_id):

        comment_text = request.values['text']
        if len(comment_text) > 0:
            new_comment_id = db_models.Moment(moment_id).add_comment(comment_text)
            return json.dumps({'new_comment_id': new_comment_id})
        else:
            abort(400)
    else:
        abort(401)


## Project routes

@app.route('/api/projects/', methods=['GET', 'POST'])
def api_projects():

    if not auth_consultant():
        abort(401)

    if request.method == "GET":

        return db_models.Project.get_all_projects_json()

    elif request.method == "POST":

        # Add a project to DB
        start_date = []
        for s in request.values['start_ts'].split('-'):
            start_date.append(int(s))

        start_date_object = datetime.datetime(start_date[0], start_date[1], start_date[2])

        try:

            p = db_models.Project.add_new_to_db(request.values['code'], int(request.values['client']), request.values['title'], 1, request.values['active']=='true', start_date_object)

            c_list = request.values['consultants'].split("consultants=")
            c_ids = []
            for c in c_list:
                if c != '':
                    c = c.rstrip('&')
                    c_ids.append(int(c))

            for id in c_ids:
                c = db_models.Consultant(id)

                p.assign_consultant_to_project(c)

            p.add_multiple_participants(int(request.values['participants']))

            return p.to_json()

        except db_models.ProjectBFCodeError as e:
            return str(e), 400

        except db_models.ConsultantNotFoundError as e:
            return str(e), 400

        except Exception as e:

            return str(e), 400



@app.route('/api/projects/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
def get_project(project_id):
    if not auth_consultant():
        abort(401)

    try:
        p = db_models.Project(project_id)

        if request.method == "GET":
            return p.to_json()

        elif request.method == "PUT":

            # Update project's data
            start_date = []
            for s in request.values['start_ts'].split('-'):
                start_date.append(int(s))

            start_date_object = datetime.datetime(start_date[0], start_date[1], start_date[2])

            if request.values['code'] != p.bf_code:
                p.update_bf_code(request.values['code'], get_active_consultant())
            p.title = request.values['title']

            if request.values['active'] == 'true':
                p.activate(get_active_consultant())
            elif request.values['active'] == 'false':
                p.deactivate(get_active_consultant())

            p.client_id = int(request.values['client'])
            p.start_ts = start_date_object

            # If the consultant assignments have been provided, then need to check for any consultant IDs not already assigned and add them, also check if there are assigned consultants to remove. Might be best to simply remove all consultants and reassign.

            c_ids = []
            for id in request.values['consultants'].split("consultants="):
                if id != '':
                    id = id.rstrip('&')
                    c_ids.append(int(id))

            if len(c_ids) > 0:

                for c in p.consultants:
                    p.remove_consultant_from_project(c, get_active_consultant())

                for id in c_ids:
                    p.assign_consultant_to_project(db_models.Consultant(id))

            p.update_last_activity_ts()
            p.update_in_db()

            return p.to_json()

        if request.method == "DELETE":
            p.delete_from_db(get_active_consultant())
            return p.to_json()

    except db_models.ProjectBFCodeError as e:
        return str(e), 400

    except db_models.ConsultantNotAdminError as e:
        return str(e), 401

    except db_models.ProjectNotFound as e:
        return str(e), 404

    except db_models.DeleteActiveProjectError as e:
        return str(e), 400

    except Exception as e:
        return str(e), 400


@app.route('/api/projects/<int:project_id>/client', methods=['GET'])
def get_project_client(project_id):
    if not auth_consultant():
        abort(401)

    try:
        return db_models.Project(project_id).client.to_json()

    except db_models.ProjectNotFound:
        return json.dumps({"error_code": 201, "error_text": "No project found with ID {}".format(project_id)}), 404


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
        return json.dumps({"error_code": 201, "error_text": "No project found with ID {}".format(project_id)}), 404


@app.route('/api/projects/<project_id>/activate', methods=['POST'])
def set_project_active_state(project_id):
    if not auth_consultant():
        abort(401)

    p = db_models.Project(project_id)

    try:
        if request.values['active'].lower() == 'true':
            p.activate(get_active_consultant())
        elif request.values['active'].lower() == 'false':
            p.deactivate(get_active_consultant())

        p.update_in_db()

        return str(p.active)

    except db_models.ProjectActivationError:
        return 'Consultant not authorised to set the active state of this project', 401
    except ValueError:
        abort(400)


@app.route('/api/projects/<project_id>/participants/', methods=['GET', 'POST'])
def get_project_participants(project_id):
    if not auth_consultant():
        abort(401)

    try:
        if request.method == 'GET':
            project_participants = db_models.Participant.get_participants_for_project(project_id)

            participants_dicts = []

            for p in project_participants:
                participants_dicts.append(p.to_dict())

            return json.dumps(participants_dicts, indent=4)

        elif request.method == "POST":

            project = db_models.Project(project_id)
            consultant = get_active_consultant()

            if not project.consultant_is_assigned(consultant) and not consultant.admin:
                return 'Only consultants assigned to this project can add participants.', 401

            new_participant = project.add_new_participant(request.values['display_name'], True,
                                                          request.values['description'])

            return new_participant.to_json()

    except db_models.ProjectNotFound:

        return json.dumps({"error_code": "201", "error_text": "No project found with ID {}".format(project_id)}), 404


@app.route('/api/projects/<project_id>/participants/<participant_id>', methods=["PUT", "GET", "DELETE"])
def api_projects_participant(project_id, participant_id):
    if not auth_consultant():
        abort(401)

    c = get_active_consultant()

    try:

        if request.method == "PUT":

            if not db_models.Project(project_id).consultant_is_assigned(c):
                return 'Only consultants assigned to this project can update its participants.', 401

            p = db_models.Participant(participant_id)
            if p.project_id != int(project_id):
                abort(401)
            p.display_name = request.values['display_name']
            p.description = request.values['description']
            p.update_in_db()
            return p.to_json()

        elif request.method == "GET":

            return db_models.Participant(participant_id).to_json()

        elif request.method == "DELETE":

            p = db_models.Participant(participant_id)
            p.delete_from_db(c)
            return p.to_json()

    except db_models.DeleteActiveParticipantError:
        return 'You cannot delete an active participant. Please deactivate this participant before deleting.', 400

    except db_models.ConsultantNotAssignedToProjectError:
        return 'Only those consultants that are assigned to a project can delete its participants.', 401

    except db_models.ParticipantNotFoundError:
        abort(404)

    except Exception as e:
        return str(e), 400


@app.route('/api/projects/<proj_id>/moments', methods=['GET'])
def get_project_moments(proj_id):
    if not auth_consultant():
        abort(401)

    if 'since_moment_id' in request.values:
        since_moment_id = request.values['since_moment_id']
    else:
        since_moment_id = 0

    if 'order' in request.values:
        order = request.values['order']
    else:
        order = "asc"

    # Get moments for a project, since the specified moment id
    moments = db_models.Moment.get_moments_for_project(proj_id, since_moment_id)

    moment_dicts = []

    for m in moments['moments']:
        m_dict = m.to_dict()
        m_dict['participant_display_name'] = db_models.Participant(m.parent_participant_id).display_name
        moment_dicts.append(m_dict)

    return json.dumps(moment_dicts, indent=4)


@app.route('/api/projects/<proj_id>/moments/<moment_id>/comments/', methods=['post'])
def add_project_moment_comment(proj_id, moment_id):
    if not auth_consultant():
        abort(401)

    consultant = get_active_consultant()

    try:
        comment_id = db_models.Moment(moment_id).add_comment(request.values['comment_text'], consultant)
        return str(comment_id)

    except db_models.ConsultantNotAssignedToProjectError:
        return 'Only assigned consultants can comment on project moments', 401


@app.route('/api/projects/<proj_id>/moments/<moment_id>/comments/<comment_id>', methods=['DELETE'])
def api_project_moment_comment(proj_id, moment_id, comment_id):
    if not auth_consultant():
        abort(401)

    if request.method == "DELETE":
        try:
            if not db_models.Project(proj_id).consultant_is_assigned(get_active_consultant()):
                abort(401)

            c = db_models.MomentComment(comment_id)

            if c.parent_moment_id != int(moment_id) or db_models.Moment(moment_id).parent_participant.project_id != int(
                    proj_id):
                abort(400)

            c.delete_from_db()

            return "MomentComment ID {} deleted".format(c.id), 200

        except db_models.MomentCommentNotFoundError:
            abort(404)
        except db_models.ProjectNotFound:
            abort(404)
        except db_models.MomentNotFoundError:
            abort(404)
        except:
            abort(400)


@app.route('/api/projects/<proj_id>/moments/<moment_id>', methods=['DELETE'])
def api_projects_moments(proj_id, moment_id):
    if not auth_consultant():
        abort(401)

    if request.method == "DELETE":

        try:
            if not db_models.Project(proj_id).consultant_is_assigned(get_active_consultant()):
                abort(401)

            m = db_models.Moment(moment_id)

            if not m.parent_participant.project_id == int(proj_id):
                abort(400)

            return m.delete_from_db().to_json()

        except db_models.MomentNotFoundError:
            abort(404)

        except db_models.ProjectNotFound:
            abort(404)

        except:
            abort(400)


@app.route('/api/projects/<proj_id>/moments/comments/', methods=['get'])
def get_project_moment_comments(proj_id):
    if not auth_consultant():
        abort(401)

    if 'since_comment_id' in request.values:
        since_comment_id = request.values['since_comment_id']
    else:
        since_comment_id = 0

    if 'order' in request.values:
        order = request.values['order']
    else:
        order = "asc"

    comments = db_models.MomentComment.get_comments_for_project(proj_id, since_comment_id, order)

    return json.dumps([c.to_dict() for c in comments['comments']], indent=4)


@app.route('/api/projects/<proj_id>/moments/<moment_id>/mark_download', methods=['post'])
def set_project_moment_active_state(proj_id, moment_id):
    if not auth_consultant():
        abort(401)

    try:
        m = db_models.Moment(moment_id)
        m.mark_for_download = 1 if request.values['mark_download'] == 'true' else 0
        m.update_in_db()
        return m.to_json()

    except db_models.MomentNotFoundError:
        abort(404)


## Client routes

@app.route('/api/clients/', methods=['GET', 'POST'])
def api_clients():
    if not auth_consultant():
        abort(401)

    if request.method == "GET":

        return db_models.Client.get_all_clients_json()

    elif request.method == "POST":

        c = get_active_consultant()

        if not c.admin:
            return 'Only administrator users can add clients', 401

        try:
            new_client = db_models.Client.add_new_to_db(request.values['description'], request.values['contact_name'],
                                                        request.values['contact_email'],
                                                        request.values['contact_phone'])

            return new_client.to_json()

        except ValueError as e:
            return str(e), 400


@app.route('/api/clients/<int:client_id>', methods=['GET'])
def get_client(client_id):
    if not auth_consultant():
        abort(401)

    try:
        return db_models.Client(client_id).to_json()

    except db_models.ClientNotFoundError:
        return json.dumps({"error_code": 401, "error_text": "No client found with ID {}".format(client_id)},
                          indent=4), 404


@app.route('/api/clients/<client_id>', methods=['PUT'])
def api_clients_update(client_id):

    if not auth_consultant():
        abort(401)

    c = get_active_consultant()

    if not c.admin:
        return 'Only administrator users can modify clients', 401

    try:
        client = db_models.Client(client_id)
        client.description = request.values['description']
        client.contact_name = request.values['contact_name']
        client.contact_email = request.values['contact_email']
        client.contact_phone = request.values['contact_phone']

        client.update_in_db()

        return client.to_json()

    except ValueError as e:
        return str(e), 400


@app.route('/api/clients/<client_id>', methods=['DELETE'])
def api_clients_delete(client_id):
    if not auth_consultant():
        abort(401)

    c = get_active_consultant()

    if not c.admin:
        return 'Only administrator users can delete clients', 401

    try:
        client = db_models.Client(client_id)
        deleted_client = client.delete_from_db(c)
        return deleted_client.to_json()

    except db_models.ClientNotFoundError:
        abort(404)

    except db_models.ClientDeleteError as e:
        return str(e), 400


@app.route('/tests/participants/<p_id>/add_moment')
def test_participant_add_moment(p_id):
    tests.add_moment_to_participant(p_id)
    m = db_models.Participant(p_id).moments[0]
    return json.dumps(m.to_dict(), indent=4)


@app.route('/tests/projects/<proj_id>/add_moments')
def test_projects_add_moments(proj_id):
    tests.add_moment_to_project(proj_id)

    moments = []

    for p in db_models.Project(proj_id).participants:
        participant_moments = db_models.Moment.get_moments_for_participant(p.id)['moments']

        moments.append([m.to_dict() for m in participant_moments])

    return json.dumps(moments, indent=4)
