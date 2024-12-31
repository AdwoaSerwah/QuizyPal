#!/usr/bin/env python3
"""
Route module for the API
"""

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import getenv
from typing import Optional
from celery import Celery
from api.v1.views import app_views

# Load environment variables from a .env file
load_dotenv()

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['REDIS_URL'],
        backend=app.config['REDIS_URL']
    )
    celery.conf.update(app.config)
    return celery

# Initialize Flask app
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Configure the app with the database URL
app.config['SQLALCHEMY_DATABASE_URI'] = getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress the warning
app.config['SECRET_KEY'] = getenv('SECRET_KEY')
app.config['REDIS_URL'] = getenv("REDIS_URL")

# Initialize SQLAlchemy object
db = SQLAlchemy(app)

# Initialize Flask-Migrate with app and Base (Base contains the models' metadata)
migrate = Migrate(app, db)

# Create Celery app
celery = make_celery(app)

# Register the blueprint for API routes
app.register_blueprint(app_views)

# Enable CORS for the API, allowing all origins for `/api/v1/*` routes
CORS(app, resources={r"/api/v1/*": {"origins": "*"}})

# Error Handlers
@app.errorhandler(404)
def not_found(error) -> str:
    """
    Handles 404 Not Found errors.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and a 404 status code.
    """
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(401)
def unauthorized_error(error) -> str:
    """
    Handles 401 Unauthorized errors.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and a 401 status code.
    """
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden_error(error) -> str:
    """
    Handles 403 Forbidden errors.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and a 403 status code.
    """
    return jsonify({"error": "Forbidden"}), 403


# Utility function to provide application context for database testing
def create_app() -> Flask:
    """
    Create the Flask app with its application context for external testing.

    This is useful for cases where the app context is needed
    explicitly for tasks like database creation or testing.

    Returns:
        Flask: The created Flask application instance.
    """
    with app.app_context():
        db.create_all()  # Ensure all tables are created
    return app


if __name__ == "__main__":
    # Read host and port from environment variables,
    # default to "0.0.0.0" and "5000"
    host = getenv("API_HOST", "0.0.0.0")
    port = getenv("API_PORT", "5000")

    # Start the Flask application in debug mode
    app.run(host=host, port=port, debug=True)
