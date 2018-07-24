from flask import session, redirect, render_template, url_for, request, abort
from cxt_app import app, db_models
import json


@app.route('/')
def index():
    return "Hello, world!"

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
        return render_template('participant/not_auth.html', hide_nav_links=True)

    else:
        # redirect to moments feed
        return redirect(url_for('participant_moments'))

# Login and authentication

@app.route('/p/<participant_url_key>/login', methods=['GET', 'POST'])
def participant_login(participant_url_key):

    remove_active_particiant()

    participant_url_key = participant_url_key.replace("-", "%2D")

    basic_project_info = db_models.Participant.get_basic_info_from_login_url(participant_url_key)

    if basic_project_info != None:

        if request.method == 'GET':
        # Check that participant URL is valid and not expired

            return render_template('participant/participant_login.html', hide_nav_links=True,
                                   participant_url_key=participant_url_key,
                                   researcher_details={'name': basic_project_info['consultant_name'],
                                                       'email': basic_project_info['consultant_email']})


        elif request.method == "POST":

            # Attempt to login participant

            try:
                p = db_models.Participant.login(participant_url_key, request.form['pin'])
                session['active_participant_id'] = p.id

                return redirect(url_for('participant_home'))

            except db_models.ParticipantLoginFailed:
                return render_template('participant/participant_login.html', hide_nav_links=True, participant_url_key=participant_url_key, pin_error=True, researcher_details={'name':basic_project_info['consultant_name'], 'email':basic_project_info['consultant_email']})

            except db_models.ParticipantNotActive:
                return render_template('participant/error.html', hide_nav_links=True, error_messages=["We're really sorry but your PIN seems to have expired.", "If you believe that this is a mistake and that you should still be able to take part in your research then please contact your researcher by replying to the email that contained your link to this project."], support_details=app.config['SUPPORT_DETAILS'], participant_url_key=participant_url_key), 403

            except Exception as e:
                return render_template('participant/participant_login.html', hide_nav_links=True)


    else:
        return render_template('participant/error.html', hide_nav_links=True, error_messages=[
            "We could not find any research projects that match the URL you have entered.",
            "If you believe that you should be able to access this project then please check that you haven't been sent a more recent login URL via email."],
                               support_details=app.config['SUPPORT_DETAILS'],
                               participant_url_key=participant_url_key), 404


@app.route('/p/logout')
def participant_logout():

    remove_active_particiant()
    return render_template('participant/logout.html', hide_nav_links=True)


# Moments feed


@app.route('/p/moments')
def participant_moments():

    participant = get_active_participant()

    if participant == None:
        return render_template('participant/not_auth.html', hide_nav_links=True)

    project = db_models.Project(participant.project_id)

    return render_template('participant/moments.html', participant_id=participant.id, researcher_details={'name':project.consultants[0].display_name, 'email':project.consultants[0].email}, support_details={'contact_email':app.config['SUPPORT_DETAILS']['contact_email'], 'contact_name':app.config['SUPPORT_DETAILS']['contact_email']}, onload='load_participant_moments({})'.format(participant.id))



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