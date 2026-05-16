from flask import Blueprint

lichess_bp = Blueprint("lichess", __name__)

from app.lichess import routes  # noqa: E402,F401
