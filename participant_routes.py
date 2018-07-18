from flask import session, redirect, render_template, url_for
from cxt_app import app, db_models
import json


@app.route('/')
def index():
    return "Hello, world!"


@app.route('/p/login/<participant_url>/<pin>')
def participant_login(participant_url, pin):
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


@app.route('/p/<project_id>/login')
def test_participant_login(project_id):
    session['logged_in'] = True
    app.logger.debug('participant logged in')
    return 'Logged in'

@app.route('/p/logout')
def participant_logout():

    if 'logged_in' in session:
        del session['logged_in']
    app.logger.debug('pariticipant logged out')
    return 'Logged out'


@app.route('/p/<project_id>/moments')
def participant_moments(project_id):
    if 'logged_in' in session and session['logged_in']:
        return render_template('participant/participant_moments.html', logged_in=True, project_id=project_id, project_name='Demo Project')
    else:
        return redirect(url_for('participant_login',project_id=project_id))