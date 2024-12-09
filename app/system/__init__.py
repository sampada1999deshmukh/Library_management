from flask import Blueprint

bp = Blueprint("Library", __name__)

from . import routes, service