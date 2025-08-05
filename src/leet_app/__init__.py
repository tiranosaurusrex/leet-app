"""
This module initialises the Flask application, configures the app settings,
sets up the database, and registers the app’s blueprint and error handlers.

It handles:
- Application creation
- Database configuration and initialization
- Blueprint registration for modular route handling
- 404 error handling

Uses Flask-SQLAlchemy for database integration.
"""

import os
from flask import Flask, render_template
from src.leet_app.extensions import db
from flask.cli import with_appcontext
import click

# CLI command to load CSV data on demand
@click.command("load-data")
@with_appcontext
def load_data_command():
    from src.leet_app.add_data import add_all_data
    add_all_data()


def create_app(test_config=None):
    """Factory: create & configure the Flask app."""
    app = Flask(__name__, instance_relative_config=True)

    # core config
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "leet_heat_demand.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile("config.py", silent=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize extensions
    db.init_app(app)
    app.cli.add_command(load_data_command)

    # all setup in application context
    with app.app_context():
        # 1) create DB tables
        from src.leet_app import models
        db.create_all()

        # 2) load initial CSV data (safe if tables already populated)
        from src.leet_app.add_data import add_all_data
        add_all_data()

        # 3) register your routes blueprint
        from src.leet_app.routes import bp
        app.register_blueprint(bp)

        # 4) 404 handler
        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("404.html"), 404

    return app
