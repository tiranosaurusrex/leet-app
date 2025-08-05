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
import click
from flask import Flask, render_template
from flask.cli import with_appcontext

from src.leet_app.extensions import db


# -----------------------------------------------------------------------------
# CLI command to load CSV data on demand
# -----------------------------------------------------------------------------
@click.command("load-data")
@with_appcontext
def load_data_command():
    """Manual trigger to ingest CSV into the database."""
    from src.leet_app.add_data import add_all_data
    add_all_data()


# -----------------------------------------------------------------------------
# Application factory
# -----------------------------------------------------------------------------
def create_app(test_config=None):
    """Factory: create & configure the Flask app."""
    app = Flask(__name__, instance_relative_config=True)

    # Core configuration
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(
            app.instance_path, "leet_heat_demand.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Override with test config or instance config file
    if test_config:
        app.config.from_mapping(test_config)
    else:
        app.config.from_pyfile("config.py", silent=True)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    app.cli.add_command(load_data_command)

    # All setup within application context
    with app.app_context():
        # 1) Create all tables
        from src.leet_app import models  # noqa: F401
        db.create_all()

        # 2) Seed database from CSV (safe: skips if already populated)
        from src.leet_app.add_data import add_all_data  # noqa: F401
        add_all_data()

        # 3) Register blueprint for routes
        from src.leet_app.routes import bp  # noqa: F401
        app.register_blueprint(bp)

        # 4) 404 error handler
        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("404.html"), 404

    return app