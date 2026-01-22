from flask import Flask, redirect, url_for
from .extensions import db, migrate
from .models import *
from .delay import delay_bp
from .master import master_bp

def create_app():
    app = Flask(__name__)

    # Configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./delay_info.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    app.register_blueprint(delay_bp, url_prefix='/delay')
    app.register_blueprint(master_bp, url_prefix='/master')

    # Root redirect
    @app.route('/')
    def index():
        return redirect(url_for('delay.list_event'))

    return app
