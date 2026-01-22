from flask import Blueprint

master_bp = Blueprint('master', __name__)

@master_bp.route('/')
def index():
    return "Master Top"
