from flask import Blueprint

scannerbp = Blueprint('scanner', __name__)

from . import views