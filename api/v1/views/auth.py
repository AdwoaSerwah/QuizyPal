#!/usr/bin/env python3
"""
This module handles authentication-related routes for users. It includes:

- Login: Authenticates users and provides access and refresh tokens.
- Refresh Token: Refreshes the access token using a valid refresh token.
- Logout: Logs the user out by invalidating the refresh token.
- Forgot Password: Sends a password reset link to the user.
- Reset Password: Resets the user's password after they follow the reset link.
"""
from flask import jsonify, request, abort
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta, timezone
from models import storage
from models.user import User
from models.refresh_token import RefreshToken
from typing import Dict, Any
from api.v1.views import app_views
from config import redis_client, Config
from api.v1.utils.email_utils import send_password_reset_email
from flask.typing import ResponseReturnValue


@app_views.route('/login', methods=['POST'])
def login() -> ResponseReturnValue:
    """
    Authenticates a user by verifying their credentials (username/email and password),
    generates an access token and refresh token, and saves the refresh token to both the 
    database and Redis cache.

    Request JSON data:
      - 'username': The user's username (optional if 'email' is provided).
      - 'email': The user's email (optional if 'username' is provided).
      - 'password': The user's password.

    Return:
      - A JSON response containing a success message, access token, and refresh token.
      - 400 if required fields are missing.
      - 403 if user is not found or password is incorrect.
      - 500 for internal server errors.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")
    
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not (username or email) or not password:
        abort(400, description="Email or username and password are required!")

    # Find the user by email or username
    if email:
        user = storage.get_by_value(User, "email", email)
    else:
        user = storage.get_by_value(User, "username", username)

    # If user not found or password does not match, return 403
    if not user or not user.check_password(str(password)):
        abort(403, description="Invalid credentials!")

    # Create access token and refresh tokens with custom claims
    access_token = create_access_token(
        identity=user.id,
        fresh=True,
        additional_claims={"role": user.role.value}
    )
    refresh_token = create_refresh_token(identity=user.id)

    # Access expiration values from Config
    refresh_token_exp = Config.JWT_REFRESH_TOKEN_EXPIRES

    # Set token expiration (7 days from now)
    expires_at = datetime.now(timezone.utc) + refresh_token_exp

    # Save the refresh token and its expiry to the database
    new_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )

    try:
        new_token.save()
        storage.save()
    except Exception:
        abort(500, description="An unexpected error occurred while saving token")

    # Cache the refresh token in Redis
    redis_key = f"refresh_token:{user.id}:{new_token.id}"
    redis_client.set(
        redis_key,
        value=refresh_token,
        ex=int((expires_at - datetime.now(timezone.utc)).total_seconds())
    )

    return jsonify({
        "message": "Logged in successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_id": new_token.id
    }), 200

@app_views.route('/logout', methods=['POST'])
@jwt_required(refresh=True)
def logout() -> ResponseReturnValue:
    """
    POST /api/v1/logout:
    Logs the user out by invalidating the refresh token.
    The refresh token is blacklisted in Redis, and its status is marked as expired in the database.

    Returns:
      - A message confirming the successful logout.
      - 400 if the refresh token ID is missing.
      - 401 if the refresh token is invalid or expired.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")
    
    current_user = get_jwt_identity()
    refresh_token_id = request.json.get("token_id", None)

    if not refresh_token_id:
        abort(400, description="Refresh token ID is required")

    if not isinstance(refresh_token_id, str):
        abort(400, description="Refresh token ID must be a string")

    # Retrieve the refresh token from the Authorization header
    request_refresh_token = request.headers.get('Authorization')
    request_refresh_token = request_refresh_token.split("Bearer ")[-1]  # Extract token after "Bearer"

    # Access expiration values from Config
    refresh_token_exp = Config.JWT_REFRESH_TOKEN_EXPIRES

    redis_key = f"refresh_token:{current_user}:{refresh_token_id}"

    # Step 1: Check Redis for blacklisted status
    old_refresh_jti = get_jwt()["jti"]
    blacklist_key = f"blacklist:{old_refresh_jti}"

    # Check if the token is already blacklisted
    if redis_client.get(blacklist_key):
        abort(401, description="Token has been revoked")

    # Step 2: Fetch the refresh token from Redis
    stored_refresh_token = redis_client.get(redis_key)
    
    # If the token is found in Redis, compare it with the request token
    if stored_refresh_token:
        if stored_refresh_token != request_refresh_token:
            abort(401, description="The refresh token does not match the token_id provided")
    else:
        # Fallback to the database if the token is not in Redis
        db_refresh_token = storage.query(RefreshToken).filter_by(
            user_id=current_user, id=refresh_token_id, token=request_refresh_token
        ).first()

        if not db_refresh_token or db_refresh_token.is_expired:
            abort(401, description="Invalid, revoked, or expired refresh token, or token does not match the provided token ID")
    
    # Step 3: Blacklist the token in Redis
    redis_client.setex(
        blacklist_key,
        int(refresh_token_exp.total_seconds()),  # Set blacklist duration to match token expiry
        "blacklisted"
    )

    # Mark the refresh token as expired in the database
    db_refresh_token = storage.query(RefreshToken).filter_by(
        user_id=current_user, id=refresh_token_id
    ).first()

    if db_refresh_token:
        db_refresh_token.is_expired = True  # Mark as expired instead of deleting
        storage.save()

    return jsonify({"message": "Logged out successfully"}), 200


@app_views.route('/forgot-password', methods=['POST'], strict_slashes=False)
def forgot_password() -> ResponseReturnValue:
    """
    POST /api/v1/forgot-password:
    Handles the forgot password request.
    It generates a reset token and sends a password reset link to the user's email.

    Returns:
      - A success message with the reset token if the email is found.
      - 400 if the request data is not in JSON format or is missing the email.
      - 404 if the user is not found.
    """
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()
    if not data or 'email' not in data:
        abort(400, description='Missing email')
    email = data.get('email')

    if not email:
        abort(400, description='Email must not be empty or null')

    # Look up the user by email
    user = storage.get_by_value(User, 'email', email)
    if user is None:
        abort(404, description="User not found")

    # Generate a reset token and save it
    user.generate_reset_token()
    print(user.reset_token)
    print(user.email)

    message = send_password_reset_email(user.email, user.reset_token)
    # Return the success response immediately
    message = 'An email has been sent to your email address containing the reset token.'

    return jsonify({
        "message": message,
        "reset token": user.reset_token
        }), 200


@app_views.route('/reset-password/<token>', methods=['POST'], strict_slashes=False)
def reset_password(token: str = None) -> ResponseReturnValue:
    """
    POST /api/v1/reset-password/<token>:
    Handles the actual password reset using a token.

    Returns:
      - 200 if the password is successfully reset.
      - 400 if missing or invalid data.
    """
    if not token:
        abort(404, description="Token ID is required")
    user = storage.get_by_value(User, "reset_token", token)

    # Check if user and token are valid
    if not user:
        abort(400, description="Invalid or expired reset token")

    if user.token_expiry.tzinfo is None:
        user.token_expiry = user.token_expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > user.token_expiry:
        abort(400, description="Token has expired")

    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    # Proceed to reset the password
    data = request.get_json()
    print(f"data: {data}")
    if 'new_password' not in data:
        return jsonify({
            "error": "New password required in the json data",
            "format": {"new_password": "your_new_password"}
        }), 400

    user.set_password(data.get('new_password'))
    print(f"Password: {user.password}")
    user.reset_token = None
    user.token_expiry = None
    user.save()

    return jsonify({'message': 'Password reset successful.'}), 200
