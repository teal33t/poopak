from flask import Blueprint

searchbp = Blueprint("search", __name__)

from . import views
