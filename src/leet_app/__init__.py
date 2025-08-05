"""
This module initialises the Flask application, configures the app settings,
sets up the database, and registers the app's blueprint and error handlers.

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

from .extensions import db

@click.command("load-data")
@with_appcontext
def load_data_command():
    """Populate the database from CSV."""
    from .add_data import add_all_data
    add_all_data()


def create_app(test_config=None):
    """
    Creates and configures the Flask app instance.

    Args:
        test_config (dict, optional): A dictionary of configuration values for testing.
    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- Basic configuration ---
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI=(
            "sqlite:///" + os.path.join(app.instance_path, "leet_heat_demand.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Override with testing config or instance config.py
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize the DB extension
    db.init_app(app)

    # Make our custom CLI command available
    app.cli.add_command(load_data_command)

    # Create tables, register blueprint, error handlers—all inside app context
    with app.app_context():
        import src.leet_app.models  # so that SQLAlchemy sees all models
        db.create_all()

        # Register your routes blueprint
        from .routes import bp
        app.register_blueprint(bp)

        # 404 page
        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("404.html"), 404

    return app
