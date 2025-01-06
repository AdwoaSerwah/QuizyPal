#!/usr/bin/env python3
"""
Route module for the API
"""

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from config import Config, mail, make_celery
from api.v1.views import app_views
from models import storage
from os import getenv, environ
from flask_mail import Message

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize JWTManager
jwt = JWTManager(app)

# Initialize SQLAlchemy and Flask-Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Mail
mail.init_app(app)


"""
with app.app_context():
    msg = Message('Test Email',
                  sender='takeabite56@gmail.com',
                  recipients=['adwoaserwahkyeibaffour@gmail.com',
                              'lindseylinwood56@gmail.com'])
    msg.body = 'This is a test email.'
    try:
        mail.send(msg)
        print("Test email sent.")
    except Exception as e:
        print(f"Error sending test email: {e}")
"""

# Create Celery app
celery = make_celery(app)

# Register the blueprint for API routes
app.register_blueprint(app_views)

# Enable CORS for the API
CORS(app, resources={r"/api/v1/*": {"origins": "*"}})


# Utility function to provide application context for database testing
def create_app() -> Flask:
    """
    Create the Flask app with its application context for external testing.

    This is useful for cases where the app context is needed
    explicitly for tasks like database creation or testing.

    Returns:
        Flask: The created Flask application instance.
    """
    from models.engine.db_storage import DBStorage

    # Set the environment to 'test' to use the test database
    environ["FLASK_ENV"] = "test"

    # Create a new instance of DBStorage for testing
    storage = DBStorage()

    with app.app_context():
        storage.reload()  # Ensure storage is fully initialized
    return app


@app.teardown_appcontext
def close_db(error):
    """ Close Storage """
    storage.close()


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
    message = getattr(error, "description", "Not found")
    return jsonify({'error': message}), 404


@app.errorhandler(401)
def unauthorized_error(error) -> str:
    """
    Handles 401 Unauthorized errors.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and a 401 status code.
    """
    message = getattr(error, "description", "Unauthorized")
    return jsonify({"error": message}), 401


@app.errorhandler(403)
def forbidden_error(error) -> str:
    """
    Handles 403 Forbidden errors.

    Args:
        error: The error object.

    Returns:
        A JSON response with the error message and a 403 status code.
    """
    message = getattr(error, "description", "Forbidden")
    return jsonify({"error": message}), 403

# Swagger setup
app.config['SWAGGER'] = {'title': 'QuizyPal Restful API', 'uiversion': 1}
Swagger(app)

if __name__ == "__main__":
    host = getenv("API_HOST", "0.0.0.0")
    port = getenv("API_PORT", "5000")
    app.run(host=host, port=port, threaded=True, debug=True)
