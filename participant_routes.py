from flask import session, redirect, render_template, url_for
from cxt_app import app


@app.route('/')
def index():
    return "Hello, world!"


@app.route('/p/<project_id>/login')
def participant_login(project_id):
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