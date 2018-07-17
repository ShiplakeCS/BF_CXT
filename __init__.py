from flask import Flask

app = Flask(__name__)
app.secret_key = 'abc'

from cxt_app import participant_routes, api_routes
