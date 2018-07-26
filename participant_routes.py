from flask import session, redirect, render_template, url_for, request, abort, send_from_directory
from werkzeug.utils import secure_filename
from cxt_app import app, db_models
import json, os


@app.route('/')
def index():
    return "Hello, world!"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def remove_active_particiant():
    if 'active_participant_id' in session:
        del session['active_participant_id']

def get_active_participant():
    if 'active_participant_id' in session:
        return db_models.Participant(session['active_participant_id'])
    else:
        return None




# General routes

@app.route('/p/')
def participant_home():
    p = get_active_participant()

    if p == None:
        page_data = {}
        return render_template('participant/not_auth.html', hide_nav_links=True, page_data=page_data)

    else:
        # redirect to moments feed
        return redirect(url_for('participant_moments'))

# Login and authentication

@app.route('/p/<participant_url_key>/login', methods=['GET', 'POST'])
def participant_login(participant_url_key):

    remove_active_particiant()

    page_data = {'support_details': app.config['SUPPORT_DETAILS']}

    participant_url_key = participant_url_key.replace("-", "%2D")

    basic_project_info = db_models.Participant.get_basic_info_from_login_url(participant_url_key)

    if basic_project_info != None:

        page_data['researcher_details'] = {
            'name': basic_project_info['consultant_name'],
            'email': basic_project_info['consultant_email']}

        if request.method == 'GET':
        # Check that participant URL is valid and not expired

            return render_template('participant/participant_login.html', hide_nav_links=True,
                                   participant_url_key=participant_url_key,
                                   page_data=page_data)


        elif request.method == "POST":

            # Attempt to login participant

            try:
                p = db_models.Participant.login(participant_url_key, request.form['pin'])
                session['active_participant_id'] = p.id

                return redirect(url_for('participant_home'))

            except db_models.ParticipantLoginFailed:

                return render_template('participant/participant_login.html', hide_nav_links=True, participant_url_key=participant_url_key, pin_error=True, page_data=page_data)

            except db_models.ParticipantNotActive:
                return render_template('participant/error.html', hide_nav_links=True, error_messages=["We're really sorry but your PIN seems to have expired.", "If you believe that this is a mistake and that you should still be able to take part in your research then please contact your researcher by replying to the email that contained your link to this project."], page_data=page_data, participant_url_key=participant_url_key), 403

            except Exception as e:
                return render_template('participant/participant_login.html', hide_nav_links=True, page_data=page_data)


    else:
        return render_template('participant/error.html', hide_nav_links=True, error_messages=[
            "We could not find any research projects that match the URL you have entered.",
            "If you believe that you should be able to access this project then please check that you haven't been sent a more recent login URL via email."],page_data=page_data, participant_url_key=participant_url_key), 404


@app.route('/p/logout')
def participant_logout():

    remove_active_particiant()
    page_data = {
        'support_details': app.config['SUPPORT_DETAILS']
    }
    return render_template('participant/logout.html', hide_nav_links=True, page_data=page_data)


# Moments feed


@app.route('/p/moments')
def participant_moments():

    participant = get_active_participant()

    if participant == None:
        return render_template('participant/not_auth.html', hide_nav_links=True)

    project = db_models.Project(participant.project_id)

    page_data = {
        'participant_id': participant.id,
        'researcher_details': {'name':project.consultants[0].display_name, 'email':project.consultants[0].email},
        'support_details': app.config['SUPPORT_DETAILS'],
        'onload':'start_moments_and_comments_feed_ajax({})'.format(participant.id)
    }

    return render_template('participant/moments.html', page_data=page_data)

@app.route('/p/capture', methods=['GET', 'POST'])
def participant_moment_capture():

    participant = get_active_participant()

    if participant == None:
        return render_template('participant/not_auth.html', hide_nav_links=True)

    if request.method == 'GET':

        project = db_models.Project(participant.project_id)

        page_data = {
            'participant_id': participant.id,
            'researcher_details': {'name':project.consultants[0].display_name, 'email':project.consultants[0].email},
            'support_details': app.config['SUPPORT_DETAILS'],
            'onload':None
        }

        return render_template('participant/capture_moment.html', page_data=page_data)

    elif request.method == 'POST':

        media = []

        if request.form['media_path'] != "":
            media = [request.form['media_path']]

        location_status = None

        try:
            gps_long = float(request.form['gps_long'])
            gps_lat = float(request.form['gps_lat'])

        except ValueError:
            gps_long = None
            gps_lat = None
            location_status = request.form['gps_long']

        new_moment = participant.add_moment(int(request.form['rating']), request.form['text_comment'], gps_long, gps_lat, media, location_status)

        #return new_moment.to_json()   # Useful if posting data via AJAX and need to wait for response data before moving on
        return redirect(url_for('participant_moments'))

@app.route('/p/capture/media', methods=['POST'])
def participant_moment_capture_media():

    # receive the uploaded file and save in temporary file folder
    participant = get_active_participant()

    if participant == None:
        abort(401)

    # Make path within temporary folder to save uploaded file
    temp_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], str(participant.id))
    os.makedirs(temp_folder_path, exist_ok=True)

    try:
        f = request.files['file']

        if f:
            if f.filename[-3:].upper() in ['PNG', 'JPG', 'MOV', 'MP4', 'M4V'] or f.filename[-4:].upper() in ['JPEG']:
                filename = secure_filename(f.filename)
                f.save(os.path.join(temp_folder_path, filename))
                return json.dumps({'file_path': str(os.path.join(str(participant.id), filename))})
            else:
                return json.dumps({'error':'Uploaded files must end in .png, .jpg, .jpeg, .mov, .mp4 or .m4v', 'error_code':'501', 'filename': f.filename})

        # uploaded_files = request.files.getlist("file[]")
        # temp_file_path_list = []
        #
        # for file in uploaded_files:
        #     if file.filename[-3:].upper() in ['PNG', 'JPG', 'MOV', 'MP4', 'M4V'] or file.filename[-4:].upper() in ['JPEG']:
        #         filename = secure_filename(file.filename)
        #         file.save(os.path.join(temp_folder_path, filename))
        #         temp_file_path_list.append({'file':str(os.path.join(str(participant.id), filename))})
        #     else:
        #         temp_file_path_list.append({'error':'Uploaded files must end in .png, .jpg, .jpeg, .mov, .mp4 or .m4v', 'error_code':'501', 'filename': file.filename})
        # return json.dumps({'files':temp_file_path_list})

    except NameError:
        return json.dumps(
            {'error': 'No files uploaded', 'error_code': '502'}), 401


"""
Removed code:

@app.route('/p/login/<participant_url>/<pin>')
def participant_login2(participant_url, pin):
    # TODO: call static method for participant to authenticate and get their object

    # Clear any active participant session
    if 'active_participant_id' in session:
        del session['active_participant_id']

    participant_url = participant_url.replace("-", "%2D")

    try:
        p = db_models.Participant.login(participant_url, pin)
        session['active_participant_id'] = p.id
        return p.to_json()

    except db_models.ParticipantLoginFailed:
        return json.dumps({'error_code': '102', 'error_text': 'Participant login failed. Check that URL and PIN are both current.'}, indent=4), 401

    except db_models.ParticipantNotActive:
        return json.dumps({'error_code': '103', 'error_text': 'Participant not active, login not permitted.'}, indent=4), 403


@app.route('/p/<project_id>/moments')
def participant_moments(project_id):
    if 'logged_in' in session and session['logged_in']:
        return render_template('participant/participant_moments.html', logged_in=True, project_id=project_id, project_name='Demo Project')
    else:
        return redirect(url_for('participant_login',project_id=project_id))
    


"""