from flask import Blueprint

dashboardbp = Blueprint('dashboard', __name__)

from . import views