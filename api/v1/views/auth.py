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
from flasgger.utils import swag_from
from config import redis_client
from api.v1.utils.email_utils import send_password_reset_email


@app_views.route('/login', methods=['POST'])
@swag_from('documentation/auth/login.yml')
def login() -> Dict[str, Any]:
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
      - 401 if user is not found or password is incorrect.
    """
    # Ensure request data is JSON
    if not request.get_json():
        return jsonify({'message': 'No data provided!'}), 400
    
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    # token_id = data.get('token_id')

    if not (username or email) or not password:
        return jsonify({'message': 'Email or username and password are required!'}), 400

    # Find the user by email or username
    if email:
        user = storage.get_by_value(User, "email", data.get('email'))
    else:
        user = storage.get_by_value(User, "username", data.get('username'))

    # If user not found or password does not match, return 401
    if not user:
        return jsonify({'message': 'User not found!'}), 401

    if not user.check_password(password):
        return jsonify({'message': 'Password is incorrect!'}), 401

    # Create access token and refresh tokens with custom claims
    access_token = create_access_token(
        identity=user.id,
        fresh=True,
        additional_claims={"role": user.role.value}
    )
    refresh_token = create_refresh_token(
        identity=user.id,
        )

    # Set token expiration (7 days from now)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Save the refresh token and its expiry to the database
    new_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,  # Save the actual token
        expires_at=expires_at
    )
    print(new_token.token)
    try:
        new_token.save()
        storage.save()
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred"}), 500

    # Calculate expiration time in seconds
    expires_in = (expires_at - datetime.now(timezone.utc)).total_seconds()

    # Cache the refresh token in Redis
    redis_client.set(
        f"refresh_token:{user.id}:{new_token.id}",
        ex=int(expires_in),
        value=refresh_token  # Store the actual refresh token
    )

    return jsonify({
        "message": "Logged in successfully",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_id": new_token.id
    }), 200


@app_views.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)
@swag_from('documentation/auth/refresh_token.yml')
def refresh_token() -> Dict[str, Any]:
    """
    POST /api/v1/refresh-token:
    Refreshes the access token and the refresh token, and rotates them.
    This ensures the refresh token is valid and is not blacklisted.
    If Redis is unavailable, the database is used as a fallback.

    Returns:
      - A JSON response containing new access and refresh tokens.
      - 400 if required data is missing.
      - 401 if the refresh token is invalid or expired.
    """
    # Ensure request data is JSON
    if not request.get_json():
        return jsonify({'message': 'No data provided!'}), 400
    
    current_user = get_jwt_identity()
    refresh_token_id = request.json.get("token_id", None)

    if not refresh_token_id:
        return jsonify({"error": "Refresh token ID is required"}), 400

    redis_key = f"refresh_token:{current_user}:{refresh_token_id}"
    old_refresh_jti = None  # Initialize the old_refresh_jti variable

    try:
        # Fetch refresh token from Redis
        stored_refresh_token = redis_client.get(redis_key)
        print(f"Stored refresh token: {stored_refresh_token}")
        if not stored_refresh_token:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        # stored_refresh_token = stored_refresh_token.decode("utf-8")

        # Check if token is blacklisted
        old_refresh_jti = get_jwt()["jti"]
        if redis_client.get(f"blacklist:{old_refresh_jti}"):
            return jsonify({"error": "Refresh token has been revoked"}), 401

    except Exception as redis_error:
        # app.logger.error(f"Redis error: {redis_error}")
        # Fallback to database
        print(f"Redis Error: str({redis_error})")
        db_refresh_token = storage.query(RefreshToken).filter_by(
            user_id=current_user, id=refresh_token_id
        ).first()
        print(f"db refresh token: {db_refresh_token}")

        if not db_refresh_token or db_refresh_token.is_expired():
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        # Reload token into Redis
        stored_refresh_token = db_refresh_token.token
        redis_client.setex(
            redis_key,
            int((db_refresh_token.expires_at - datetime.now(timezone.utc)).total_seconds()),
            db_refresh_token.token
        )

    # Retrieve user role
    user = storage.query(User).filter_by(id=current_user).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_role = user.role.value

    # Generate new tokens
    new_access_token = create_access_token(
        identity=current_user,
        fresh=True,
        additional_claims={"role": user_role}
    )
    new_refresh_token = create_refresh_token(identity=current_user)

    # Blacklist the old token
    redis_client.setex(
        f"blacklist:{old_refresh_jti}",
        int(timedelta(days=7).total_seconds()),
        "blacklisted"
    )

    # Store the new refresh token
    redis_client.setex(redis_key, int(timedelta(days=7).total_seconds()), new_refresh_token)

    # Update database with the new refresh token
    db_refresh_token = storage.query(RefreshToken).filter_by(
        user_id=current_user, id=refresh_token_id
    ).first()

    if db_refresh_token:
        db_refresh_token.token = new_refresh_token
        db_refresh_token.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        storage.save()
    else:
        db_refresh_token = RefreshToken(
            user_id=current_user,
            token=new_refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db_refresh_token.save()

    return jsonify({
        "token_id": db_refresh_token.id,
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }), 200


@app_views.route('/logout', methods=['POST'])
@jwt_required(refresh=True)
@swag_from('documentation/auth/logout.yml')
def logout() -> Dict[str, Any]:
    """
    POST /api/v1/logout:
    Logs the user out by invalidating the refresh token.
    The refresh token is blacklisted in Redis, and its status is marked as expired in the database.

    Returns:
      - A message confirming the successful logout.
      - 400 if the refresh token ID is missing.
      - 401 if the refresh token is invalid or expired.
    """
    current_user = get_jwt_identity()
    refresh_token_id = request.json.get("token_id", None)

    if not refresh_token_id:
        return jsonify({"error": "Refresh token ID is required"}), 400

    redis_key = f"refresh_token:{current_user}:{refresh_token_id}"

    try:
        # Step 1: Check Redis for blacklisted status
        old_refresh_jti = get_jwt()["jti"]
        blacklist_key = f"blacklist:{old_refresh_jti}"

        # Check if the token is already blacklisted
        if redis_client.get(blacklist_key):
            return jsonify({"error": "Token has been revoked"}), 401

        # Step 2: Fetch the refresh token from Redis
        stored_refresh_token = redis_client.get(redis_key)
        if not stored_refresh_token:
            return jsonify({"error": "Invalid or expired refresh token"}), 401

        # Step 3: Blacklist the token in Redis
        redis_client.setex(
            blacklist_key,
            int(timedelta(days=7).total_seconds()),  # Set blacklist duration to match token expiry
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app_views.route('/forgot-password', methods=['POST'], strict_slashes=False)
@swag_from('documentation/auth/forgot_password.yml')
def forgot_password():
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
        abort(400, description="Not a JSON")

    data = request.get_json()
    if not data or 'email' not in data:
        return abort(400, description='Missing email')
    email = data.get('email')

    # Look up the user by email
    user = storage.get_by_value(User, 'email', email)
    if user is None:
        abort(404, description="User not found")

    # Generate a reset token and save it
    user.generate_reset_token()
    print(user.reset_token)
    print(user.email)

    # Send the password reset email
    result = send_password_reset_email(user.email, user.reset_token)
    # Flash a message
    # flash('An email has been sent to your email address.')

    return jsonify({
        "message": result,
        "reset token": user.reset_token
        }), 200


@app_views.route('/reset-password/<token>', methods=['POST'], strict_slashes=False)
@swag_from('documentation/auth/reset_password.yml')
def reset_password(token):
    """
    POST /api/v1/reset-password/<token>:
    Handles the actual password reset using a token.

    Returns:
      - 200 if the password is successfully reset.
      - 400 if the token is invalid or expired.
      - 400 if the new password is not provided.
    """
    user = storage.get_by_value(User, "reset_token", token)

    # print(f"{datetime.now(timezone.utc)}: {type(datetime.now(timezone.utc))}")
    # print(f"{user.token_expiry}: {type(user.token_expiry)}")

    # Check if user and token are valid
    if not user:
        return jsonify({'error': 'Invalid or expired token'}), 400

    if user.token_expiry.tzinfo is None:
        user.token_expiry = user.token_expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > user.token_expiry:
        return jsonify({'error': 'Token expired'}), 400

    if not request.get_json():
        abort(400, description="Not a JSON")

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
