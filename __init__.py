from flask import Flask
from config import Config

"""from flask_sqlalchemy import SQLAlchemy  # SQL Alchemy addition
from flask_migrate import Migrate  # SQL Alchemy/Migrate addition
"""
app = Flask(__name__)
app.config.from_object(Config)
# Add SQL Alchemy instances
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)

# Add endpoints
from cxt_app import db_models, participant_routes, consultant_routes, api_routes
