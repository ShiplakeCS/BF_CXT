import sqlite3, json, uuid, dateutil.parser, random
from flask import g
from cxt_app import app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class DB:
    """
    Provides static methods to access the database
    """

    @staticmethod
    def connect_db():
        # See http://flask.pocoo.org/docs/0.12/tutorial/setup/#tutorial-setup
        db = sqlite3.connect(app.config['DB_PATH'])
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def get_db():
        # if not hasattr(g, 'db'):
        #     g.db = DB.connect_db()
        # return g.db
        return DB.connect_db()

    @staticmethod
    @app.teardown_appcontext
    def close_db(error):
        if hasattr(g, 'db'):
            g.db.close()


class ConsultantNotFoundError(Exception):
    pass


class ConsultantLoginError(Exception):
    pass


class ConsultantUpdateError(Exception):
    pass


class ConsultantNotAdminError(Exception):
    pass


class DeleteAllAdminConsultantError(Exception):
    pass

class DeleteSelfAdminConsultantError(Exception):
    pass

class Consultant:

    def __init__(self, id=None, email=None, display_name=None, first_name=None, last_name=None, active=None,
                 admin=None):

        # If an id value is provided then attempt to load from the database

        if id:
            # Returns a Constulant instance with values populate from the Consultant table in the DB
            try:
                id = int(id)
            except:
                raise ValueError("Consultant ID must be an integer")

            db = DB.get_db()
            # db = DB.connect_db()

            consultant = db.execute(
                "SELECT email, display_name, first_name, last_name, active, admin FROM Consultant WHERE id=?",
                [str(id)]).fetchone()
            if not consultant:
                raise ConsultantNotFoundError("No consultant found with ID {}".format(id))

            self.__id = id
            self.__email = consultant['email']
            self.__display_name = consultant['display_name']
            self.__first_name = consultant['first_name']
            self.__last_name = consultant['last_name']
            self.__active = consultant['active'] == 1
            self.__admin = consultant['admin'] == 1


        else:
            # If no id value then return a new object with values passed to constructor

            self.__id = None
            self.__email = email
            self.__display_name = display_name
            self.__first_name = first_name
            self.__last_name = last_name
            self.__active = active
            self.__admin = admin

    @property
    def id(self):
        return self.__id

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, value):
        if len(value) > 5:
            self.__email = value
        else:
            raise ValueError("Email address invalid")

    @property
    def display_name(self):
        return self.__display_name

    @display_name.setter
    def display_name(self, value):
        if len(value) < 3:
            raise ValueError("Display name must contain at least 3 characters.")
        self.__display_name = value

    @property
    def first_name(self):
        return self.__first_name

    @first_name.setter
    def first_name(self, value):
        if len(value) < 1:
            raise ValueError("First name must contain at least 1 character.")
        self.__first_name = value

    @property
    def last_name(self):
        return self.__last_name

    @last_name.setter
    def last_name(self, value):
        if len(value) < 1:
            raise ValueError("Last name must contain at least 1 character.")
        self.__last_name = value

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value: bool):
        self.__active = value

    @property
    def admin(self):
        return self.__admin

    @property
    def project_ids(self):
        return Consultant.get_project_ids(self.id)

    def set_admin(self, value, authorised_consultant):
        if not authorised_consultant.admin:
            raise ValueError("Consultant id {} (display name: {}) is not authorised to set admin proprerty of "
                             "other consultants.".format(authorised_consultant.id, authorised_consultant.display_name))
        self.__admin = value

    def update_in_db(self):
        # Add code to update current consultant object's values within the DB
        db = DB.get_db()
        try:
            db.execute(
                "UPDATE Consultant SET email=?, display_name=?, first_name=?, last_name=?, active=?, admin=? WHERE id=?",
                [self.email, self.display_name, self.first_name, self.last_name, str(int(self.active)),
                 str(int(self.admin)),
                 str(self.id)])
            db.commit()
            return Consultant(self.id)
        except sqlite3.IntegrityError:
            raise ConsultantUpdateError("IntegrityError raised, most likely due to unique data vilotion. "
                                        "Check that email address already in use.")

    def delete_from_db(self, admin_consultant):

        # Check that an admin consultant has requested this action
        if not admin_consultant.admin:
            raise ConsultantNotAdminError

        if admin_consultant.id == self.id:
            raise DeleteSelfAdminConsultantError("Admin consultants cannot erase themselves from the database.")

        # If self consultant to be removed is admin, check that at least one admin will remain.

        db = DB.get_db()

        if self.admin:

            row = db.execute("select count(id) as 'admin_count' from Consultant where admin=1").fetchone()

            if row['admin_count'] < 2:
                raise DeleteAllAdminConsultantError("Cannot delete consultant {} as doing so would leave no admin "
                                                    "consultants!".format(self.id))

        # Proceed to remove consultant from database

        db.execute("DELETE FROM Consultant WHERE id=?", [str(self.id)])
        db.commit()

    def to_dict(self):
        return {
            'id': self.__id,
            'email': self.__email,
            'display_name': self.__display_name,
            'first_name': self.__first_name,
            'last_name': self.__last_name,
            'active': self.__active,
            'admin': self.__admin,
            'projects': self.project_ids
            # TODO: Determine whether this should be included in representation of consultant
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    @staticmethod
    def add_new_to_db(email, password, display_name, first_name, last_name, active, admin):

        # TODO: Add email address validation

        if len(email) < 5:
            raise ValueError("Email address not valid")
        elif len(display_name) == 0:
            raise ValueError("Display name not provided")
        elif len(first_name) == 0:
            raise ValueError("First name not provided")
        elif len(last_name) == 0:
            raise ValueError("Last name not provided")
        elif active not in [0, 1]:
            raise ValueError("Active user flag invalid")
        elif admin not in [0, 1]:
            raise ValueError("Admin user flag invalid")

        password_hash = generate_password_hash(password)

        if admin == True:
            admin = 1
        elif admin == False:
            admin = 0

        if active == True:
            active = 1
        elif active == False:
            active = 0

        db = DB.get_db()
        # db = DB.connect_db()
        cur = db.execute("INSERT INTO Consultant VALUES(?, ?,?,?,?,?,?,?)",
                         [None, email, password_hash, display_name, first_name, last_name, active, admin])
        db.commit()
        new_id = cur.lastrowid

        return Consultant(new_id)

    @staticmethod
    def login(email, password):
        db = DB.get_db()
        row = db.execute("SELECT id, password_hash FROM Consultant WHERE email=?", [email]).fetchone()
        if not row:
            raise ConsultantNotFoundError("No consultant found with email address: {}".format(email))

        if not check_password_hash(row['password_hash'], password):
            raise ConsultantLoginError("Email and password do not match")

        return Consultant(row['id'])

    @staticmethod
    def get_project_ids(consultant_id):
        #TODO: Move this feature to Project object as it involves Project table.
        project_ids = []
        db = DB.get_db()
        rows = db.execute("SELECT project FROM ProjectConsultant WHERE consultant=?", [consultant_id]).fetchall()
        for r in rows:
            project_ids.append(r['project'])
        return project_ids

    @staticmethod
    def get_all_consultants_json():
        consultant_list = []
        db = DB.get_db()
        consultant_ids = db.execute("SELECT id FROM Consultant ORDER BY id ASC").fetchall()
        for row in consultant_ids:
            consultant_list.append(Consultant(row['id']).to_dict())

        return json.dumps(consultant_list, indent=4)

class ClientNotFoundError(Exception):
    pass


class ClientUpdateError(Exception):
    pass


class Client:

    def __init__(self, id):

        try:
            id = int(id)
        except ValueError:
            raise ClientNotFoundError("Client ID must be an integer value!")

        db = DB.get_db()
        client_details = db.execute(
            "SELECT description, contact_name, contact_email, contact_phone FROM Client WHERE id=?",
            [str(id)]).fetchone()

        if client_details:
            self.__id = id
            self.__description = client_details['description']
            self.__contact_name = client_details['contact_name']
            self.__contact_email = client_details['contact_email']
            self.__contact_phone = client_details['contact_phone']

        else:
            raise ClientNotFoundError("No client found with ID {}".format(id))

    @property
    def id(self):
        return self.__id

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, value):

        if len(value) < 1:
            raise ValueError("Client description must be at least 1 character")

        self.__description = value

    @property
    def contact_name(self):
        return self.__contact_name

    @contact_name.setter
    def contact_name(self, value):
        if len(value) < 1:
            raise ValueError("Client name must be at least 1 character")
        self.__contact_name = value

    @property
    def contact_email(self):
        return self.__contact_email

    @contact_email.setter
    def contact_email(self, value):
        # TODO: Add proper email validation
        if len(value) < 5:
            raise ValueError("Invalid email provided for client")
        self.__contact_email = value

    @property
    def contact_phone(self):
        return self.__contact_phone

    @contact_phone.setter
    def contact_phone(self, value):
        if len(value) < 8:
            # TODO: Add proper phone validation
            raise ValueError("Contact phone must be at least 8 characters")
        self.__contact_phone = value

    @property
    def project_ids(self):
        return Client.get_project_ids(self.__id)

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def update_in_db(self):

        db = DB.get_db()
        try:
            db.execute("UPDATE Client SET description=?, contact_name=?, contact_email=?, contact_phone=? WHERE id=?",
                       [self.description, self.contact_name, self.contact_email, self.contact_phone, str(self.id)])
            db.commit()
            return Client(self.id)
        except sqlite3.IntegrityError:
            raise ClientUpdateError("sqlite3.IntegrityError raised. Most likely due to duplicate client name.")

    def delete_from_db(self, admin_consultant):

        if not admin_consultant.admin:
            raise ConsultantNotAdminError

        db = DB.get_db()
        db.execute("DELETE FROM Client WHERE id=?", str(self.id))
        db.commit()
        return 'Client {}({}) removed from database'.format(self.description, self.id)

    @staticmethod
    def add_new_to_DB(description, c_name, c_email, c_phone):

        if len(description) < 1:
            raise ValueError("Client description must be at least 1 character.")

        db = DB.get_db()
        cur = db.execute("INSERT INTO Client VALUES (?, ?, ?, ?, ?)", [None, description, c_name, c_email, c_phone])
        db.commit()
        new_id = cur.lastrowid

        return Client(new_id)

    @staticmethod
    def get_project_ids(client_id):
        project_ids = []
        db = DB.connect_db()
        projects = db.execute("SELECT id FROM Project WHERE client=?", [str(client_id)]).fetchall()
        for p in projects:
            project_ids.append(p['id'])
        return project_ids

    @staticmethod
    def get_all_clients_json():

        client_list = []

        db = DB.get_db()

        client_ids = db.execute("SELECT id FROM Client ORDER BY description ASC").fetchall()

        for row in client_ids:
            client_list.append(Client(int(row['id'])).to_dict())

        return json.dumps(client_list, indent=4)


class ParticipantNotFoundError(Exception):
    pass

class ParticipantLoginFailed(Exception):
    pass

class ParticipantNotActive(Exception):
    pass

class ProjectNotFound(Exception):
    pass

class Participant:

    def __init__(self, id):
        try:
            self.__id = int(id)
        except ValueError:
            raise ParticipantNotFoundError("Participant ID must be an integer.")

        db = DB.get_db()
        row = db.execute("SELECT project, within_project_num, display_name, active, last_activity_ts, description, login_url, pin FROM Participant WHERE id=?", [str(self.id)]).fetchone()

        if row:
            self.__project_id = int(row['project'])
            self.__within_project_number = int(row['within_project_num'])
            self.__display_name = row['display_name']
            self.__active = row['active'] == 1
            self.__last_activity_ts = dateutil.parser.parse(row['last_activity_ts'])
            self.__description = row['description']
            self.__login_URL = row['login_url']
            self.__pin = row['pin']

        else:
            raise ParticipantNotFoundError("No participant found with ID {}".format(id))

    @property
    def id(self):
        return self.__id

    @property
    def project_id(self):
        return self.__project_id

    @property
    def within_project_number(self):
        return self.__within_project_number

    @within_project_number.setter
    def within_project_number(self, value):
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Within project number an  integer and unique within project {}".format(self.__project_id))

        if value < 1:
            raise ValueError("Within project number must be a positive integer.")

        db = DB.get_db()
        participant_numbers = []
        rows = db.execute("SELECT within_project_num FROM Participant WHERE project=?", str(self.__project_id))
        for r in rows:
            participant_numbers.append(int(r['within_project_num']))

        if value in participant_numbers:
            raise ValueError("A participant is already assigned within-project number {} for project {}".format(value, self.__project_id))

        self.__within_project_number = value

    @property
    def display_name(self):
        return self.__display_name

    @display_name.setter
    def display_name(self, value):
        if len(value) < 1:
            raise ValueError("Participant display name must be at least 1 character.")
        self.__display_name = value

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, value:bool):
        self.__active = value

    @property
    def last_activity_ts(self):
        return self.__last_activity_ts

    @last_activity_ts.setter
    def last_activity_ts(self, value):
        self.__last_activity_ts = value

    @property
    def description(self):
        return self.__description

    @description.setter
    def description(self, value):
        self.__description = value

    @property
    def login_url(self):
        return self.__login_URL

    @property
    def pin(self):
        return self.__pin

    @pin.setter
    def pin(self, value:str):

        if not value.isnumeric():
            raise ValueError("PIN must contain numbers only")

        elif len(value) < 4:
            raise ValueError("PIN must contain at least four numbers")

        self.__pin = value

    def update_last_activity_ts(self):
        self.__last_activity_ts = datetime.utcnow()
        db = DB.get_db()
        db.execute("UPDATE Participant SET last_activity_ts=? WHERE id=?", (datetime.isoformat(self.last_activity_ts), self.id))
        db.commit()
        return 'Timestamp updated'

    def generate_login_url(self, admin_consultant):

        if not admin_consultant.admin:
            raise ConsultantNotAdminError

        self.__login_URL = Participant.get_random_login_url()

    @staticmethod
    def get_random_login_url():
        new_url = str(uuid.uuid4()).replace('-', '%2D')
        # Check if the URL is unique in the participant table
        db = DB.get_db()
        row = db.execute("SELECT id FROM Participant WHERE login_url=?",[new_url]).fetchone()
        if row:
            # url already exists, get another
            new_url = Participant.get_random_login_url()
        return new_url

    def generate_new_pin(self):
        self.pin = Participant.get_random_pin()

    @staticmethod
    def get_random_pin():
        new_pin = str(random.randint(0,9999)).zfill(4)
        return new_pin

    def update_in_db(self):

        db = DB.get_db()
        db.execute("UPDATE Participant SET within_project_num=?, display_name=?, active=?, last_activity_ts=?, description=?, login_url=?, pin=? WHERE id=?",
                   [self.within_project_number, self.display_name, str(int(self.active)), datetime.isoformat(self.last_activity_ts),
                    self.description, self.login_url, self.pin, self.id])
        db.commit()
        return Participant(self.id)

    def delete_from_db(self):
        pass

    @staticmethod
    def add_new_to_db(project_id, display_name, active, last_activity_ts, description):
    #  within-project-num is auto generated using
    #  select within_project_num from Participant where project = 1 order by within_project_num desc
    # PIN and Login URL are also randomly generated

        db = DB.get_db()

        # Get within project number
        row = db.execute("SELECT within_project_num FROM Participant WHERE project=? ORDER BY within_project_num DESC",
                         (str(project_id))).fetchone()

        if row:
            next_within_project_num = int(row['within_project_num']) + 1
        else:
            next_within_project_num = 1

        login_url = Participant.get_random_login_url()
        pin = Participant.get_random_pin()

        cur = db.execute("INSERT INTO Participant VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         [None, str(project_id), str(next_within_project_num), display_name, str(int(active)),
                          last_activity_ts, description, login_url, pin])
        db.commit()
        new_id = int(cur.lastrowid)
        return Participant(new_id)

    @staticmethod
    def bulk_add_to_db(participants_list, as_json=False):
        # TODO: Work through a list of participant details (provided as a list of dicts or in json format) and add each to the database using add_new_to_db()

        added_participants = []

        if as_json:
            # code to get json into dictionary form first
            participants_list = json.loads(participants_list)

        for p in participants_list:

            added_participants.append(Participant.add_new_to_db(p['project_id'], p['display_name'], p['active'],
                                                                p['last_activity_ts'], p['description']))

        return added_participants

    @staticmethod
    def login(url, pin):

        # Find participant ID for participant with matching url and pin, else raise login exception
        db = DB.get_db()

        result = db.execute("SELECT id, active FROM Participant WHERE login_url=? and pin=?", [url, pin]).fetchone()

        if not result:
            raise ParticipantLoginFailed("Participant login URL/PIN mismatch. Check PIN is correct and that URL is still active. Your research consultant can issue you with a new login URL and PIN if necessary.")

        if result['active'] != 1:
            raise ParticipantNotActive

        return Participant(result['id'])

    @staticmethod
    def get_participant_ids_for_project(project_id):

        participant_ids = []

        db = DB.get_db()
        rows = db.execute("SELECT id FROM Participant where project=? order by project asc", [project_id]).fetchall()

        if not rows:
            raise ProjectNotFound("No project could be found with ID {}".format(project_id))

        for r in rows:
            participant_ids.append(int(r['id']))

        return participant_ids

    @staticmethod
    def get_participants_for_project(project_id):

        ps = []

        pids = Participant.get_participant_ids_for_project(project_id)

        for id in pids:
            ps.append(Participant(id))

        return ps

    def to_dict(self):
        # TODO: return representation of self as a dict
        return {
            "id": self.id,
            "project_id": self.project_id,
            "within_project_number": self.within_project_number,
            "display_name": self.display_name,
            "active": self.active,
            "last_activity_is": datetime.isoformat(self.last_activity_ts),
            "description": self.description,
            "login_url": self.login_url,
            "pin": self.pin
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)


class ProjectTypeNotExistError(Exception):
    pass

class ProjectBFCodeError(Exception):
    pass

class ProjectActivationError(Exception):
    pass

class Project:

    def __init__(self, id):

        try:
            self.__id = int(id)
        except ValueError:
            raise ProjectNotFound("Project ID must be an integer.")

        db = DB.get_db()

        project_details = db.execute("SELECT Project.bf_code, Project.client, Project.title, Project.project_type, Project.active, Project.start_ts, Project.last_activity_ts FROM Project WHERE Project.id=?", [self.__id]).fetchone()

        if not project_details:
            raise ProjectNotFound("No project found with ID {}".format(id))

        self.__bf_code = project_details['bf_code']
        self.__client_id = project_details['client']
        self.__title = project_details['title']
        self.__project_type_id = project_details['project_type']
        self.__active = 1 == project_details['active']
        self.__start_ts = dateutil.parser.parse(project_details['start_ts'])
        self.__last_activity_ts = dateutil.parser.parse(project_details['last_activity_ts'])
        self.__consultants = []
        self.__participants = []
        self.__tags = []


    @property
    def id(self):
        return self.__id

    @property
    def bf_code(self):
        return self.__bf_code

    @property
    def client_id(self):
        return self.__client_id

    @client_id.setter
    def client_id(self, value:int):
        # Check client exists by attempting to create a Client instance
        c = Client(value)
        self.__client_id = c.id
        self.update_last_activity_ts()

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, value):

        if len(value) < 1:
            raise ValueError("Project title must be at least 1 character.")

        self.__title = value
        self.update_last_activity_ts()

    @property
    def project_type_id(self):
        return self.__project_type_id

    @project_type_id.setter
    def project_type_id(self, value):

        # Check value is an acceptable project type from project type table

        row = DB.get_db().execute("SELECT description FROM ProjectType WHERE id=?",[str(value)]).fetchone()

        if not row:
            raise ProjectTypeNotExistError("No project type found with ID {}".format(value))

        self.__project_type_id = int(value)
        self.update_last_activity_ts()

    @property
    def project_type_description(self):

        row = DB.get_db().execute("SELECT description FROM ProjectType WHERE id=?", [str(self.__project_type_id)]).fetchone()

        return row['description']

    @property
    def active(self):
        return self.__active

    @property
    def start_ts(self):
        return self.__start_ts

    @start_ts.setter
    def start_ts(self, value):

        if type(value) == datetime:
            self.__start_ts = value

        else:
            self.__start_ts = dateutil.parser.parse(value)

    @property
    def last_activity_ts(self):
        return self.__last_activity_ts

    @last_activity_ts.setter
    def last_activity_ts(self, value):

        if type(value) == datetime:
            self.__last_activity_ts = value

        else:
            self.__last_activity_ts = dateutil.parser.parse(value)

    @property
    def consultants(self):

        if len(self.__consultants) == 0:
            self.refresh_assigned_consultants()

        return self.__consultants

    @property
    def client(self):
        return Client(self.__client_id)

    @property
    def participants(self):

        if len(self.__participants) == 0:

            self.__participants = self.refresh_assigned_participants()

        return self.__participants

    @property
    def tags(self):
        if len(self.__tags) == 0:
            self.__tags = self.refresh_project_tags()
        return self.__tags

    def refresh_assigned_consultants(self):

        self.__consultants = []

        consultant_ids = DB.get_db().execute(
            "SELECT consultant FROM ProjectConsultant WHERE project=? ORDER BY consultant ASC", [self.__id])

        for row in consultant_ids:
            self.__consultants.append(Consultant(int(row['consultant'])))

        return self.__consultants

    def refresh_assigned_participants(self):

        self.__participants = Participant.get_participants_for_project(self.id)
        self.update_last_activity_ts()

        return self.__participants

    def refresh_project_tags(self):

        self.__tags = []

        tag_rows = DB.get_db().execute("SELECT text FROM Tag WHERE project=? ORDER BY text ASC", [self.id]).fetchall()

        for row in tag_rows:
            self.__tags.append(row['text'])

        return self.__tags

    def update_last_activity_ts(self):
        self.last_activity_ts = datetime.utcnow()

    def update_bf_code(self, bf:str, admin_constulant:Consultant):

        bf = bf.upper()

        if bf[:2] != "BF":
            raise ProjectBFCodeError("BF code not in correct format, must start with BF.")

        if not admin_constulant.admin:
            raise ConsultantNotAdminError("Only admin users have permission to update a project's BF code once created.")

        # Check bf code not already in use
        bf_check = DB.get_db().execute("SELECT id FROM Project WHERE bf_code=?", [bf]).fetchone()

        if bf_check:
            raise ProjectBFCodeError("Cannot update project's internal BF code to {} as it is already in use.".format(bf))

        self.__bf_code = bf
        self.update_last_activity_ts()

    def add_tag(self, tag):

        if len(tag)<1:
            raise ValueError("Tags must be at least 1 character in length.")

        # Check if tag already exists for project - don't add if it is already present

        tag_check = DB.get_db().execute("SELECT id FROM Tag WHERE project=? AND text=?", [self.id, tag]).fetchone()

        if not tag_check:

            db = DB.get_db()
            db.execute("INSERT INTO Tag VALUES (?,?,?)", [None, self.id, tag])
            db.commit()

        return self.refresh_project_tags()

    def assign_consultant_to_project(self, c:Consultant):

        # If the consultant has already been assigned then just don't do anything
        for consultant in self.__consultants:
            if consultant.id == c.id:
                return

        db = DB.get_db()
        db.execute("INSERT INTO ProjectConsultant VALUES (?,?)", [self.id, c.id])
        db.commit()
        self.refresh_assigned_consultants()
        self.update_last_activity_ts()
        return self.consultants

    def remove_consultant_from_project(self, c:Consultant, admin_consultant:Consultant):

        if not admin_consultant.admin:
            raise ConsultantNotAdminError("Only admin consultants can remove consultants from projects!")

        db = DB.get_db()
        db.execute("DELETE FROM ProjectConsultant WHERE project=? AND consultant=?", [self.id, c.id])
        db.commit()
        self.refresh_assigned_consultants()
        self.update_last_activity_ts()
        return self.consultants

    def activate(self, requesting_consultant:Consultant):

        # Only assigned consultants or admin can activate a project

        consultant_match = False

        for consultant in self.consultants:
            if consultant.id == requesting_consultant.id:
                consultant_match = True
                break

        if consultant_match or requesting_consultant.admin:
            self.__active = True

        else:
            raise ProjectActivationError("Only administrators and assigned consultants can activate a project.")

    def deactivate(self, requesting_consultant: Consultant):

        # Only assigned consultants or admin can activate a project

        consultant_match = False

        for consultant in self.consultants:
            if consultant.id == requesting_consultant.id:
                consultant_match = True
                break

        if consultant_match or requesting_consultant.admin:
            self.__active = False

        else:
            raise ProjectActivationError("Only administrators and assigned consultants can deactivate a project.")

    def update_in_db(self):
        pass

    def delete_from_db(self, admin_consultant:Consultant):
        pass

    @staticmethod
    def add_new_to_db(bf_code, client_id, title, project_type_id, active, start_ts):
        pass

    def to_dict(self):
        pass

    def to_json(self):
        pass

@app.teardown_appcontext
def close_db(error):
    DB.close_db(error)
