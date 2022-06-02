from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB.get('connection_string')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
