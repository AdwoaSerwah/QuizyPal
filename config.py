from dotenv import load_dotenv
import redis
from celery import Celery
from flask_mail import Mail
from datetime import timedelta
import os
"""
This module configures the Flask application with environment variables and
sets up key services such as Redis, Celery, and Flask-Mail.

- Loads environment variables using dotenv.
- Configures Flask settings, including database and JWT authentication.
- Sets up Redis for caching and task queue management.
- Initializes Flask-Mail for email handling.
- Provides a factory function to create a Celery instance.

Classes:
    - Config: Centralized configuration class for application settings.

Functions:
    - make_celery(app): Creates and returns a Celery instance
      configured with Flask settings.

Globals:
    - redis_client: Redis client instance for interacting with the cache.
    - mail: Flask-Mail instance for handling email communication.
"""
# Load environment variables from .env
load_dotenv()


class Config:
    """Centralized app configuration."""
    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSONIFY_PRETTYPRINT_REGULAR = True

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # Flask-Mail settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    MAIL_USE_SSL = True
    # app.config['MAIL_USE_TLS'] = True


# Redis client
redis_client = redis.StrictRedis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)

# Mail instance
mail = Mail()


# Celery factory
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=Config.REDIS_URL,
        backend=Config.REDIS_URL
    )
    celery.conf.update(app.config)
    return celery
