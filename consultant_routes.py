from flask import session, abort
from datetime import datetime
from cxt_app import app, db_models
import json


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