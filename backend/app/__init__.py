"""Application factory for the NetRadar backend service.

This module wires together Flask extensions, configuration, database
initialization, and API routes.
"""

from flask import Flask
from flask_cors import CORS

from app.daily_db import init_daily_db
from app.db import init_db


def create_app(config_class: str = "config.Config") -> Flask:
    """Create and configure a Flask application instance.

    Args:
        config_class: Dotted import path for the configuration object.

    Returns:
        A configured Flask application ready to run.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # The frontend is served from a separate origin in development.
    CORS(app)

    # Ensure required SQLite schema/indexes are available before requests.
    init_db(app.config["DATABASE_PATH"])
    init_daily_db(app.config["DAILY_DATABASE_PATH"])

    from app.routes import api

    app.register_blueprint(api.bp)
    return app
