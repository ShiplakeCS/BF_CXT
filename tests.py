from cxt_app import app
from cxt_app.db_models import Project, Participant, Client, Consultant, Moment
from datetime import  datetime
import shutil, os, random

def new_project_with_participants():

    bf_code = input("Enter a BF code for this project: ")

    test_project = Project.add_new_to_db(bf_code, 4, "Test Project", 1, True, datetime.utcnow())

    test_project.assign_consultant_to_project(Consultant(3))

    test_project.add_multiple_participants(8)

    # Generate 3 moments per participant

    for p in test_project.participants:

        for i in range(3):

            shutil.copy(os.path.join(app.root_path, "static", "images", 'moment_media_placeholder.png'), os.path.join(app.config['UPLOAD_FOLDER']))

            moment_rating = random.randint(1,5)

            p.add_moment(moment_rating, "Test moment {}".format(i), None, None, ['moment_media_placeholder.png'])


        for m in p.moments:
            m.add_comment("Hello!", test_project.consultants[0])
            m.add_comment("Hi there!")

    print("Added test project {}".format(test_project.id))



