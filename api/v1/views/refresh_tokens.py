#!/usr/bin/env python3
"""
Handles refresh token management in the QuizyPal API,
including retrieval, rotation, revocation, and deletion.
Implements JWT authentication, role-based access control,
and secure token storage in Redis and the database.

Endpoints:
- GET /refresh-tokens (Admin): List refresh tokens.
- GET /refresh-tokens/<id>: Retrieve a token (Admin/Owner).
- POST /refresh-tokens: Rotate and refresh tokens.
- DELETE /refresh-tokens/<id> (Admin): Delete a token.
- PUT /refresh-tokens/<id> (Admin): Revoke a token.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask_jwt_extended import create_access_token, create_refresh_token
from api.v1.services.auth_service import admin_required
from api.v1.utils.pagination_utils import get_paginated_data
from models.refresh_token import RefreshToken
from api.v1.services.refresh_token_service import get_refresh_token_by_id
from flask.typing import ResponseReturnValue
from config import redis_client, Config
from datetime import datetime, timezone
from models.user import User


@app_views.route('/refresh-tokens', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_refresh_tokens() -> ResponseReturnValue:
    """
    GET /api/v1/refresh-tokens

    Get all refresh tokens with pagination.
    This route retrieves refresh tokens from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).

    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of refresh tokens for the current page.
        - next_page: Next page number, if available.
        - prev_page: Previous page number, if available.
        - total_pages: Total number of pages.
    """
    # Get query parameters with defaults and validate
    try:
        # Convert query parameters to integers with defaults
        page = int(request.args.get('page', 1))  # Default page is 1
        # Default page_size is 10
        page_size = int(request.args.get('page_size', 10))

        # Ensure both values are positive integers
        if page <= 0 or page_size <= 0:
            raise ValueError

    except (ValueError, TypeError):
        abort(400, description="page and page_size must be positive integers")

    # Use the helper function to get paginated refresh tokens
    result = get_paginated_data(storage, RefreshToken,
                                page=page, page_size=page_size)

    # Change the "data" key to "refresh tokens"
    result["refresh_tokens"] = result.pop("data")
    return jsonify(result)


@app_views.route('/refresh-tokens/<refresh_token_id>',
                 methods=['GET'], strict_slashes=False)
@jwt_required()
def get_refresh_token(refresh_token_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/refresh-tokens/:id

    Get a specific refresh token by its refresh_token_id.
    This route retrieves a single refresh token based on the
    provided refresh_token_id.

    Parameters:
        refresh_token_id (str): The unique identifier for the refresh token.

    Return:
        A JSON object representing the refresh token if found.
        If the refresh token is not found, returns a 404 error.
    """
    # Call the helper function to retrieve the refresh token by its ID.
    refresh_token = get_refresh_token_by_id(refresh_token_id, storage)

    # If the refresh token is not found, abort with a 404 error.
    if refresh_token is None:
        abort(404, description="Refresh Token not found")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    user_role = get_jwt()["role"]

    # Check if the current user is an admin or if they are trying to
    # retrieve their own refresh token
    if user_role != "admin" and refresh_token.user_id != current_user_id:
        abort(403, description=(
                "You are not authorized to retrieve this "
                "refresh token."
            )
        )

    # If the refresh token is found, return it as a JSON object.
    return jsonify(refresh_token.to_json())


@app_views.route('/refresh-tokens/<refresh_token_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_refresh_token(refresh_token_id: str) -> ResponseReturnValue:
    """
    DELETE /api/v1/refresh-tokens/:id
    Deletes the specified refresh token, invalidates it in Redis,
    and removes it from the database.

    Returns:
      - A message confirming the successful deletion.
      - 400 if the refresh token ID is missing or invalid.
      - 404 if the refresh token is not found.
    """
    # Ensure that the refresh token ID is provided
    if not refresh_token_id:
        abort(400, description="Refresh token ID is required")

    if not isinstance(refresh_token_id, str):
        abort(400, description="Refresh token ID must be a string")

    # Now, find the refresh token in the database and remove it
    db_refresh_token = storage.query(RefreshToken).filter_by(
        id=refresh_token_id
    ).first()

    if not db_refresh_token:
        abort(404, description="Refresh token not found")

    redis_key = f"refresh_token:{db_refresh_token.user_id}:{refresh_token_id}"

    # Fetch refresh token from Redis
    stored_refresh_token = redis_client.get(redis_key)
    if stored_refresh_token:
        redis_client.delete(redis_key)  # Delete from Redis

    # Remove from the database
    storage.delete(db_refresh_token)  # Delete from the database
    storage.save()

    return jsonify({"message": "Refresh token deleted successfully"}), 200


@app_views.route('/refresh-tokens', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token() -> ResponseReturnValue:
    """
    POST /api/v1/refresh-tokens:
    Refreshes the access token and the refresh token, and rotates them.
    This ensures the refresh token is valid and is not blacklisted.
    The refresh token can only be used for refreshing once then revoked
    If Redis is unavailable, the database is used as a fallback.

    Returns:
      - A JSON response containing new access and refresh tokens.
      - 400 if required data is missing.
      - 401 if the refresh token is invalid or expired.
    """
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
    # Extract token after "Bearer"
    request_refresh_token = request_refresh_token.split("Bearer ")[-1]

    redis_key = f"refresh_token:{current_user}:{refresh_token_id}"

    # Check if the token is blacklisted first for quicker response
    old_refresh_jti = get_jwt()["jti"]
    if redis_client.get(f"blacklist:{old_refresh_jti}"):
        abort(401, description="Refresh token has been revoked")

    # Try to get the token from Redis
    stored_refresh_token = redis_client.get(redis_key)

    # If the token is found in Redis, compare it with the request token
    if stored_refresh_token:
        print(f"stored_refresh_token: {stored_refresh_token}")
        print(f"request_refresh_token: {request_refresh_token}")
        if stored_refresh_token != request_refresh_token:
            abort(401, description=(
                "The refresh token does not match the "
                "token_id provided"
            ))
    else:
        # Fallback to the database if the token is not in Redis
        db_refresh_token = storage.query(RefreshToken).filter_by(
            user_id=current_user, id=refresh_token_id,
            token=request_refresh_token
        ).first()

        if not db_refresh_token:
            # Separate error for non-existent token
            abort(404, description="Refresh token not found")

        if db_refresh_token.is_expired or db_refresh_token.has_expired():
            abort(401,
                  description="Invalid, revoked, or expired refresh token")

    # Retrieve user role
    user = storage.query(User).filter_by(id=current_user).first()
    if not user:
        abort(404, description="User not found")

    user_role = user.role.value

    # Generate new tokens
    new_access_token = create_access_token(
        identity=current_user,
        fresh=True,
        additional_claims={"role": user_role}
    )
    new_refresh_token = create_refresh_token(identity=current_user)

    # Access expiration values from Config
    refresh_token_exp = Config.JWT_REFRESH_TOKEN_EXPIRES

    # Blacklist the old token
    redis_client.setex(
        f"blacklist:{old_refresh_jti}",
        int(refresh_token_exp.total_seconds()),
        "blacklisted"
    )

    # Store the new refresh token in Redis
    redis_client.setex(redis_key,
                       int(refresh_token_exp.total_seconds()),
                       new_refresh_token)

    # Update database with the new refresh token
    db_refresh_token = storage.query(RefreshToken).filter_by(
        user_id=current_user, id=refresh_token_id
    ).first()

    if db_refresh_token:
        db_refresh_token.token = new_refresh_token
        expires_at_time = datetime.now(timezone.utc) + refresh_token_exp
        db_refresh_token.expires_at = expires_at_time

        expires_now = datetime.now(timezone.utc)
        db_refresh_token.is_expired = expires_now > db_refresh_token.expires_at

        storage.save()
    else:
        # Calculate expiration in advance
        expires_at = datetime.now(timezone.utc) + refresh_token_exp
        db_refresh_token = RefreshToken(
            user_id=current_user,
            token=new_refresh_token,
            expires_at=expires_at,
            # Same logic as the if block
            is_expired=datetime.now(timezone.utc) > expires_at
        )
        db_refresh_token.save()

    return jsonify({
        "token_id": db_refresh_token.id,
        "access_token": new_access_token,
        "refresh_token": new_refresh_token
    }), 201


@app_views.route('/refresh-tokens/<refresh_token_id>', methods=['PUT'])
@jwt_required(refresh=True)
# @admin_required
def update_refresh_token(refresh_token_id: str) -> ResponseReturnValue:
    """
    PUT /api/v1/refresh-tokens/:id
    Updates the status of the specified refresh token
    (reverses revocation/expiration).

    Returns:
      - A JSON response indicating the refresh token was successfully updated.
      - 400 if the provided data is missing or invalid.
      - 404 if the refresh token is not found.
    """
    # Ensure request data is JSON and contains valid parameters
    current_user = get_jwt_identity()
    print(current_user)

    user = storage.get(User, current_user)

    if not user or user.role.value != "admin":
        abort(403, description="Authenticated admin access required")

    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()
    updated = False

    if 'is_revoked' not in data:
        abort(400, description=(
                "The 'is_revoked' field is required in the request body "
                "to update the refresh token status."
            )
        )

    # Extract the revocation status change from the request
    is_revoked = data.get("is_revoked")
    if not isinstance(is_revoked, bool):
        abort(400, description="is_revoked must be a boolean")

    # Fetch the refresh token from the database
    db_refresh_token = storage.query(RefreshToken).filter_by(
        user_id=current_user, id=refresh_token_id
    ).first()

    if not db_refresh_token:
        abort(404, description="Refresh token not found")

    # Extract the JTI from the refresh token stored in the database
    old_refresh_jti = get_jwt()["jti"]

    print(f"db_refresh_token.is_expired: {db_refresh_token.is_expired}")
    print(f"is_revoked: {is_revoked}")
    if is_revoked != db_refresh_token.is_expired:
        db_refresh_token.is_expired = is_revoked

        # Access expiration values from Config
        refresh_token_exp = Config.JWT_REFRESH_TOKEN_EXPIRES
        blacklist_key = f"blacklist:{old_refresh_jti}"

        # If revoking, add the JTI to the Redis blacklist
        if is_revoked:
            redis_client.setex(
                blacklist_key,
                int(refresh_token_exp.total_seconds()),
                "blacklisted"
            )
        else:
            # If un-revoking, remove the JTI from the Redis blacklist
            redis_client.delete(blacklist_key)

        updated = True

    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the refresh token status"
    else:
        message = "Refresh token status updated successfully"

        # Save the updated refresh token to the database
        db_refresh_token.updated_at = datetime.now(timezone.utc)
        storage.save()

    return jsonify({
        "message": message,
        "refresh_token": db_refresh_token.to_json(),
    }), 200
