from flask import Blueprint

# from web.app import client

authbp = Blueprint("auth", __name__)


from . import views
