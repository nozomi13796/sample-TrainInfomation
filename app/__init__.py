import os
from flask import Flask, redirect, url_for
from .extensions import db, migrate
from .models import *
from .delay import delay_bp
from .master import master_bp

def create_app():
    app = Flask(__name__)

    # Configurations
    if os.environ.get("RENDER"):
        db_path = "/temp/delay_info.db"
    else:
        db_path = "delay_info.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
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

    # Seed CLI command
    @app.cli.command("seed")
    def seed_command():
        from seed.seed import run_seed
        with app.app_context():
            db.drop_all()
            db.create_all()
            run_seed()

    return app
