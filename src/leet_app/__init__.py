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
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask.cli import with_appcontext
import click

# Define base class
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    Inherits from SQLAlchemy's DeclarativeBase.
    """
    pass

# Instantiate SQLAlchemy with Base
db = SQLAlchemy(model_class=Base)

# CLI command for loading data
@click.command("load-data")
@with_appcontext
def load_data_command():
    from leet_app.add_data import add_all_data
    add_all_data()

# Factory function
def create_app(test_config=None):
    """
    Creates and configures the Flask app instance.

    Args:
        test_config (dict, optional): A dictionary of configuration values for testing purposes. If None, the app uses default configuration.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Configuration
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, 'leet_heat_demand.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Load config
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialise database
    db.init_app(app)

    # Register models and blueprints within app context
    with app.app_context():
        from leet_app import models
        db.create_all()

        from leet_app.routes import bp
        app.register_blueprint(bp)

    # Register CLI command
    app.cli.add_command(load_data_command)

    # Register error handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    return app