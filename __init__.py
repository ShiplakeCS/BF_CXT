from flask import Flask
from config import Config
import os, json

"""from flask_sqlalchemy import SQLAlchemy  # SQL Alchemy addition
from flask_migrate import Migrate  # SQL Alchemy/Migrate addition
"""
app = Flask(__name__)
app.config.from_object(Config)
# Add SQL Alchemy instances
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)

app.config['MOMENT_MEDIA_FOLDER'] = os.path.join(app.root_path, "project_data")
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "upload_temp")
app.config['TEMP_FOLDER'] = os.path.join(app.root_path, "temp")
app.config['DOWNLOAD_BUNDLES_FOLDER'] = os.path.join(app.root_path, "project_data", "download_bundles")
app.config['SUPPORT_DETAILS'] = {"contact_name": "Bunnyfoot Support", "contact_email": "support@bunnyfoot.com"}
app.config['GOOGLE_MAPS_API_KEY'] = 'AIzaSyCQop7Ow0qProMtA53UjodYntMf7yaZozs'

# Add endpoints
from cxt_app import db_models, participant_routes, consultant_routes, api_routes
