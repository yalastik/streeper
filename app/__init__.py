# app/__init__.py
import os
import stripe
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer
from flask_login import LoginManager

# Initialize the app
app = Flask(__name__)
Bootstrap(app)

db_path = os.path.join(os.path.dirname(__file__), 'users.db')
channels_path = os.path.join(os.path.dirname(__file__), 'channels.db')
posts_path = os.path.join(os.path.dirname(__file__), 'posts.db')
withdrawals_path = os.path.join(os.path.dirname(__file__), 'withdrawals.db')

db_uri = 'sqlite:///{}'.format(db_path)

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_BINDS'] = {'channels': 'sqlite:///{}'.format(channels_path),
                                  'posts': 'sqlite:///{}'.format(posts_path),
                                  'withdrawals': 'sqlite:///{}'.format(withdrawals_path)}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config.from_pyfile('config.cfg')


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#Mail_settings
mail = Mail(app)
s = URLSafeTimedSerializer('giax5RHYLB')

# stripe keys
pub_key = 'pk_test_rW2nCw0ukmmWD7KWQwIzWOlW'
secret_key = 'sk_test_mqlBWdwuEV2Dm69ymxOIDwtg'
stripe.api_key = secret_key

# Load the views
from app import views

# Load the config file
app.config.from_object('config')