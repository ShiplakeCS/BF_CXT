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

@app.route('/consultants/')
def consultants_table_page():

    c = get_active_consultant()

    if not c:
        return redirect(url_for('consultant_login'))
    if not c.admin:
        abort(401)

    all_consultants = db_models.Consultant.get_all_consultants_dicts()

    return render_template('dashboard/consultants_table.html', consultants=all_consultants, consultant=c.to_dict(), page_data=get_page_data(), active_projects=c.get_active_project_details())


@app.route('/clients/')
def clients_table_page():

    c = get_active_consultant()

    if not c:
        return redirect(url_for('consultant_login'))

    all_clients = db_models.Client.get_all_clients_dicts()

    return render_template('dashboard/clients_table.html', clients=all_clients, consultant=c.to_dict(), page_data=get_page_data(), active_projects=c.get_active_project_details())


@app.route('/projects/')
def projects_table_page():

    c = get_active_consultant()
    if not c:
        return redirect(url_for('consultant_login'))

    all_projects = db_models.Project.get_all_projects_dicts()

    for p in all_projects:
        cs = []
        for consultant in p['consultants']:
            cs.append(db_models.Consultant(consultant).to_dict())
        p['consultants'] = cs
        p['num_participants'] = len(p['participants'])

    return render_template('dashboard/projects_table.html', projects=all_projects, active_projects=c.get_active_project_details(), consultant=c.to_dict(), page_data=get_page_data())

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
        return render_template('dashboard/project.html', project=p_dict, consultant=c.to_dict(),
                               active_projects=c.get_active_project_details(), page_data=get_page_data())

    except db_models.ProjectNotFound:
        # TODO: 404 project not found page
        return render_template('dashboard/project.html', project=None, consultant=c.to_dict(),
                               active_projects=c.get_active_project_details(), page_data=get_page_data())


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
        return send_file(download_path, as_attachment=True, mimetype='application/zip')

    except db_models.ProjectNotFound:
        return redirect('/projects/{}/'.format(proj_id)), 404



## Modal forms

@app.route('/projects/<proj_id>/participants/<participant_id>/')
def project_participant_view(proj_id, participant_id):

    c = get_active_consultant()
    if not c:
        abort(401)

    # if not (c.admin or int(proj_id) in c.project_ids):
    #     abort(401)

    try:
        p = db_models.Participant(participant_id)

        return render_template('dashboard/modals/view_edit_participant_form.html', participant=p.to_dict(), read_only=True)

    except db_models.ParticipantNotFoundError:
        abort(404)

@app.route('/projects/<proj_id>/participants/<participant_id>/edit')
def project_participant_edit(proj_id, participant_id):
    c = get_active_consultant()
    if not c:
        abort(401)

    if not (c.admin or int(proj_id) in c.project_ids):
        abort(401)

    try:
        p = db_models.Participant(participant_id)
        print(p.to_dict())

        return render_template('dashboard/modals/view_edit_participant_form.html', participant=p.to_dict())

    except db_models.ParticipantNotFoundError:
        abort(404)

@app.route('/projects/<proj_id>/participants/add')
def project_participant_add(proj_id):

    c = get_active_consultant()
    if not c:
        abort(401)

    if not (c.admin or int(proj_id) in c.project_ids):
        abort(401)

    return render_template('dashboard/modals/view_edit_participant_form.html', proj_id = proj_id)


@app.route('/projects/<proj_id>/participants/<participant_id>/edit/new/<i>')
def project_participant_pin(proj_id, participant_id, i):

    c = get_active_consultant()
    if not c:
        abort(401)

    if not (c.admin or int(proj_id) in c.project_ids):
        abort(401)

    try:
        p = db_models.Participant(participant_id)
        if i.lower()=='pin':
            p.generate_new_pin()
        elif i.lower() == 'url':
            p.generate_login_url(c)
        else:
            abort(400)

        p.update_in_db()

        return p.to_json()

    except db_models.ParticipantNotFoundError:
        abort(404)

@app.route('/projects/<proj_id>/participants/<participant_id>/download')
def projects_participants_download(proj_id, participant_id):

    c = get_active_consultant()
    if not c:
        abort(401)

    if not (c.admin or int(proj_id) in c.project_ids):
        abort(401)

    try:
        p = db_models.Participant(participant_id)

        download_file = p.generate_download_bundle(ignore_moment_flag=True, participant_zip=True)

        return send_file(download_file, as_attachment=True, mimetype='application/zip')

    except db_models.ParticipantNotFoundError:
        abort(404)

@app.route('/clients/add', methods=["GET"])
def client_modal_add():

    c = get_active_consultant()
    if not c or not c.admin:
        abort(401)

    return render_template('/dashboard/modals/add_view_edit_client.html', consultant = c.to_dict())

@app.route('/clients/<client_id>/edit', methods=["GET"])
def client_modal_edit(client_id):

    c = get_active_consultant()
    if not c or not c.admin:
        abort(401)

    try:

        client = db_models.Client(client_id)

        return render_template('/dashboard/modals/add_view_edit_client.html', client = client.to_dict(), consultant = c.to_dict())

    except db_models.ClientNotFoundError:
        abort(404)

@app.route('/clients/<client_id>/view', methods=['GET'])
def client_modal_view(client_id):

    c = get_active_consultant()
    if not c:
        abort(401)

    try:

        client = db_models.Client(client_id)

        return render_template('/dashboard/modals/add_view_edit_client.html', client = client.to_dict(), read_only=True, consultant = c.to_dict())

    except db_models.ClientNotFoundError:
        abort(404)

@app.route('/consultants/<consultant_id>/edit', methods=['GET'])
def consultant_modal_edit(consultant_id):

    c = get_active_consultant()
    if not c or not c.admin:
        abort(401)

    try:
        consultant_edit = db_models.Consultant(consultant_id)

        return render_template('dashboard/modals/add_view_edit_consultant.html', consultant=consultant_edit.to_dict(), active_consultant=c)

    except db_models.ConsultantNotFoundError:
        abort(404)

@app.route('/consultants/<consultant_id>/view', methods=['GET'])
def consultant_modal_view(consultant_id):

    c = get_active_consultant()
    if not c:
        abort(401)

    try:
        consultant_edit = db_models.Consultant(consultant_id)

        return render_template('dashboard/modals/add_view_edit_consultant.html', consultant=consultant_edit.to_dict(), active_consultant=c, read_only=True)

    except db_models.ConsultantNotFoundError:
        abort(404)


@app.route('/consultants/add', methods=['GET'])
def consultants_modal_add():

    c = get_active_consultant()
    if not c or not c.admin:
        abort(401)

    return render_template('dashboard/modals/add_view_edit_consultant.html', active_consultant=c)


@app.route('/projects/add', methods=['GET'])
def project_modal_add():

    c = get_active_consultant()
    if not c: #or not c.admin:
        abort(401)

    return render_template('dashboard/modals/add_edit_project.html', active_consultant=c.to_dict())

@app.route('/projects/<project_id>/edit', methods=['GET'])
def project_modal_edit(project_id):

    c = get_active_consultant()
    if not c or not c.admin:
        abort(401)

    try:
        project = db_models.Project(project_id)

        return render_template('dashboard/modals/add_edit_project.html', active_consultant=c.to_dict(), project=project.to_dict())

    except db_models.ProjectNotFound:
        abort(404)

## Login and logout

@app.route('/login/', methods=['GET', 'POST'])
def consultant_login():
    if request.method == "GET":
        return render_template('dashboard/login.html', page_data=get_page_data())
    elif request.method == "POST":
        try:
            c = db_models.Consultant.login(request.form['email'], request.form['password'])
            session['active_consultant'] = c.id
            return redirect(url_for('index'))
        except db_models.ConsultantLoginError as e:
            return render_template('dashboard/login.html',
                                   error=str(e),
                                   page_data=get_page_data())
        except db_models.ConsultantNotFoundError:
            return render_template('dashboard/login.html',
                                   error="Sorry, but we did not recognise the email address that you entered. Please try agian.",
                                   page_data=get_page_data())


@app.route('/logout/')
def consultant_logout():
    remove_active_consultant()
    return redirect(url_for('index'))


""" TEST ROUTES """


@app.route('/test/new_consultant')
def test_new_consultant():
    return db_models.Consultant.add_new_to_db("joe@bloggs.net", "password", "JoeB", "Joe", "Bloggs", True,
                                              False).to_json()


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
