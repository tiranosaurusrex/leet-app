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
from flask import Flask, render_template
from src.leet_app.extensions import db
from sqlalchemy.orm import DeclarativeBase
from flask.cli import with_appcontext
import click

# Define base class (used by SQLAlchemy in extensions.py)
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Inherits from SQLAlchemy's DeclarativeBase.
    """
    pass


# CLI command for loading data manually
@click.command("load-data")
@with_appcontext
def load_data_command():
    from src.leet_app.add_data import add_all_data
    add_all_data()


def create_app(test_config=None):
    """
    Creates and configures the Flask app instance.

    Args:
        test_config (dict, optional): Configuration values for testing.
    Returns:
        Flask: The configured Flask application.
    """
    print("✅ DEBUG: create_app() called", flush=True)
    app = Flask(__name__, instance_relative_config=True)

    # Core configuration
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "leet_heat_demand.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Override with instance config or test config
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # All DB setup, data loading, and blueprint registration must live inside this context
    with app.app_context():
        # Register models and create tables
        from src.leet_app import models
        db.create_all()

        # Load seed data only once
        if app.config.get("INITIAL_DATA_LOADED") != "true":
            from src.leet_app.add_data import add_all_data
            try:
                print("🧪 DEBUG: Starting initial data load", flush=True)
                add_all_data()
            except Exception as e:
                print(f"❌ ERROR in initial data load: {e}", flush=True)

        # Register application routes
        from src.leet_app.routes import bp
        app.register_blueprint(bp)

    # Make the load-data command available
    app.cli.add_command(load_data_command)

    # 404 error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app