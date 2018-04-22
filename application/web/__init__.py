from flask import Flask, redirect, url_for, send_from_directory
import flask_login
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from rq import Queue
from web.captchar import SessionCaptcha
from web.models import User

from crawler import run as run_crawler
from worker import conn
from .config import redis_uri, mongodb_uri, scr_upload_dir

# import datetime
# import uuid

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = True

app.config['REDIS_URL'] = redis_uri
app.config['QUEUES'] = 'default'

app.secret_key = "sacredtea"

app.config['SESSION_TYPE'] = 'filesystem'
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 4


login_manager = flask_login.LoginManager()
login_manager.init_app(app)

login_manager.session_protection = "strong"
login_manager.login_view = 'auth.login'
login_manager.login_message=""


q = Queue(name="high",connection=conn)

csrf = CSRFProtect()
csrf.init_app(app)
captcha = SessionCaptcha(app)


client = MongoClient(mongodb_uri)

from werkzeug.security import generate_password_hash
from pymongo.errors import DuplicateKeyError

pass_hash = generate_password_hash("123qweasdzxc", method='pbkdf2:sha256')
print (pass_hash)
# Insert the user in the DB
try:
    client.crawler.users.insert({"_id": "admin", "password": pass_hash})
    print("User created.")
except DuplicateKeyError:
    print("User already present in DB.")


from .filters import *
from .auth import authbp
app.register_blueprint(authbp, url_prefix='/auth')

from .search import searchbp
app.register_blueprint(searchbp)

from .scanner import scannerbp
app.register_blueprint(scannerbp, url_prefix='/scanner')

from .dashboard import dashboardbp
app.register_blueprint(dashboardbp, url_prefix='/dashboard')


#custom routes

@login_manager.user_loader
def load_user(id):
    u = client.crawler.users.find_one({"_id": id})
    if not u:
        return None
    return User(u['_id'])

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login'))


@app.route('/screenshots/<path:filename>')
def screenshots_path(filename):
    _filename = "%s.png" % filename
    return send_from_directory( scr_upload_dir , _filename)

from .errors import *
