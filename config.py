# config.py
from app import app

# Enable Flask's debugging features. Should be False in production
DEBUG = True

#secret key required to use CSRF
app.config['SECRET_KEY'] = '2fHGGFdePK'
