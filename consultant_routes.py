from flask import session, abort, render_template, url_for, redirect, request, send_file
from datetime import datetime
from cxt_app import app, db_models
import json

def get_page_data():
    return {
        'support': app.config['SUPPORT_DETAILS']
    }

@app.route('/')
def index():

    consultant = get_active_consultant()

    if consultant == None:
        return redirect(url_for('consultant_login'))

    return render_template('dashboard/home.html',
                           consultant=consultant.to_dict(),
                           active_projects=consultant.get_active_project_details(),
                           page_data=get_page_data()
                        )


def remove_active_consultant():
    if 'active_consultant' in session:
        del session['active_consultant']

def get_active_consultant():
    if 'active_consultant' in session:
        return db_models.Consultant(session['active_consultant'])
    else:
        return None


## Project pages

@app.route('/projects/<proj_id>/')
def project_page(proj_id):

    c = get_active_consultant()
    if not c:
        return redirect(url_for('consultant_login'))

    try:
        p = db_models.Project(proj_id)
        # Get names of consultants for this project

        p_dict = p.to_dict()
        p_dict['consultants'] = [c.to_dict() for c in p.consultants]
        print(p_dict)
        return render_template('dashboard/project.html', project=p_dict, consultant=c.to_dict(), active_projects=c.get_active_project_details(), page_data=get_page_data())

    except db_models.ProjectNotFound:
        # TODO: 404 project not found page
        return render_template('dashboard/project.html', project=None, consultant=c.to_dict(), active_projects=c.get_active_project_details(), page_data=get_page_data())

@app.route('/projects/<proj_id>/moments/html')
def project_moments_feed(proj_id):

    c = get_active_consultant()
    if not c:
        return redirect(url_for('consultant_login'))

    return render_template('dashboard/moments_frame.html', project_id=proj_id)


@app.route('/projects/<proj_id>/download')
def project_download(proj_id):

    c = get_active_consultant()
    if not c:
        return redirect(url_for('consultant_login'))

    try:
        p = db_models.Project(proj_id)
        download_path = p.generate_download_bundle()
        return send_file(download_path, as_attachment=True)

    except db_models.ProjectNotFound:
        return redirect('/projects/{}/'.format(proj_id)), 404




## Login and logout

@app.route('/login/', methods=['GET', 'POST'])
def consultant_login():
    if request.method=="GET":
        return render_template('dashboard/login.html', page_data=get_page_data())
    elif request.method=="POST":
        try:
            c = db_models.Consultant.login(request.form['email'], request.form['password'])
            session['active_consultant'] = c.id
            return redirect(url_for('index'))
        except db_models.ConsultantLoginError:
            return render_template('dashboard/login.html', error="Sorry, but the email address and password that you entered do not appear to match. Please try agian.", page_data=get_page_data())
        except db_models.ConsultantNotFoundError:
            return render_template('dashboard/login.html', error="Sorry, but we did not recognise the email address that you entered. Please try agian.", page_data=get_page_data())

@app.route('/logout/')
def consultant_logout():

    remove_active_consultant()
    return redirect(url_for('index'))


""" TEST ROUTES """

@app.route('/test/new_consultant')
def test_new_consultant():
    return db_models.Consultant.add_new_to_db("joe@bloggs.net", "password", "JoeB", "Joe", "Bloggs", True, False).to_json()

@app.route('/test/delete_consultant/<id>')
def test_delete_consultant(id):

    if not 'active_consultant' in session:
        abort(401)

    try:
        active_consultant_id = json.loads(session['active_consultant'])['id']
        db_models.Consultant(id).delete_from_db(db_models.Consultant(active_consultant_id))
        return 'Consultant {} removed from DB.'.format(id)
    except db_models.ConsultantNotAdminError:
        abort(403)
    except db_models.DeleteAllAdminConsultantError:
        return 'Cannot remove only admin user!'


@app.route('/login/consultant/<email>/<password>')
def test_login_consultant(email, password):
    try:
        active_consultant = db_models.Consultant.login(email, password)
        session['active_consultant'] = active_consultant.to_json()
        return active_consultant.to_json()

    except:
        if 'active_consultant' in session:
            del session['active_consultant']
        return 'Login failure'

@app.route('/test/update_consultant/<id>')
def test_update_consultant(id):
    c = db_models.Consultant(id)
    c.first_name = "Updated first name"
    c.last_name = "Updated last name"
    active_consultant_id = json.loads(session['active_consultant'])['id']
    c.set_admin(True, db_models.Consultant(active_consultant_id))
    c.email = "updated - " + c.email
    c.active = True
    c.display_name = c.display_name + " - updated"
    return c.update_in_db().to_json()