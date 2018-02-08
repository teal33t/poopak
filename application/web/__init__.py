from flask import Flask, redirect, url_for
# from flask_login import LoginManagercurrent_user
import flask_login
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from rq import Queue
from web.captchar import SessionCaptcha
from web.models import User

from crawler import run as run_crawler
from worker import conn
from .config import redis_uri

import datetime
import uuid

app = Flask(__name__)

app.config['WTF_CSRF_ENABLED'] = True

app.config['REDIS_URL'] = redis_uri
app.config['QUEUES'] = 'default'

app.secret_key = "sacredtea"

app.config['SESSION_TYPE'] = 'filesystem'
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_LENGTH'] = 2


login_manager = flask_login.LoginManager()
login_manager.init_app(app)

login_manager.session_protection = "strong"
login_manager.login_view = 'auth.login'
login_manager.login_message=""


q = Queue(connection=conn)

csrf = CSRFProtect()
csrf.init_app(app)
captcha = SessionCaptcha(app)

client = MongoClient("mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "54nn4n"))


from werkzeug.security import generate_password_hash
from pymongo.errors import DuplicateKeyError

pass_hash = generate_password_hash("admin", method='pbkdf2:sha256')

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


from .dashboard import dashboardbp
app.register_blueprint(dashboardbp, url_prefix='/dashboard')


# @app.before_request
# def before_request():
#     # app.session.permanent = True
#     app.permanent_session_lifetime = datetime.timedelta(minutes=20)
#     # app.session.modified = True
#     # app.g.user = flask_login.current_user

@login_manager.user_loader
def load_user(id):
    u = client.crawler.users.find_one({"_id": id})
    if not u:
        return None
    return User(u['_id'])

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('auth.login'))

#
#
# @login_manager.user_loader
# def load_user(user_id):
#     return User.get(user_id)





# @app.route('/', methods=['GET', 'POST'])
# def index():
#     search_form = SearchForm(request.form)
#     alive_onions = client.crawler.documents.find({"status": 200}).count()
#     offline_checked_onions = client.crawler.documents.find({"status": 503}).count()
#     last_crawled = client.crawler.documents.find().sort("seen_time", DESCENDING).limit(1)
#     checked_onions = client.crawler.documents.count()
#     if search_form.validate_on_submit():
#         return redirect(url_for('.search', phrase=search_form.phrase.data.lower()))
#     return render_template('index.html', form=search_form,
#                            checked_onions=checked_onions,
#                            alive_onions=alive_onions,
#                            offline_onions=offline_checked_onions,
#                            last_crawled=last_crawled[0]['seen_time'])


# @app.route('/directory/<int:page_number>', methods=["GET"])
# def directory(page_number=1):
#     all_count = client.crawler.documents.count()
#     pagination = Pagination(page_number, n_per_page, all_count)
#     form = SearchForm()
#     all = client.crawler.documents.find({}).skip((page_number - 1) * n_per_page).limit(n_per_page)
#     return render_template('directory.html',
#                            results=all,
#                            search_form=form,
#                            all_count=all_count,
#                            pagination=pagination)



