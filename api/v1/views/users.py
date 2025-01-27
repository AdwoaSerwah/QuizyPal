#!/usr/bin/env python3
""" Module of Users views
This module defines routes for managing users, including:
- Viewing users
- Viewing a user
- Creating new users
- Updating existing users
- Deleting users

Some routes are protected by JWT authentication, with the
option for role-based access control.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models.user import User, Role
from models.refresh_token import RefreshToken
from config import redis_client, Config
from datetime import timedelta, datetime, timezone
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from email_validator import validate_email, EmailNotValidError
from api.v1.utils.pagination_utils import get_paginated_data
from flask.typing import ResponseReturnValue
from api.v1.services.auth_service import admin_required
from api.v1.services.result_service import get_quiz_results_for_user
from api.v1.services.user_answer_service import get_result_answers_for_user
from api.v1.utils.string_utils import format_text_to_title
from api.v1.services.quiz_service import get_quiz_by_id


@app_views.route('/users', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_users() -> ResponseReturnValue:
    """
    GET /api/v1/users

    Get all users.
    This route retrieves all user records from the storage and
    returns them as a JSON list.
    
    Return:
        A JSON array containing all User objects.
        If no users are found, it returns an empty list.
    """
    # Get query parameters with defaults and validate
    try:
        # Convert query parameters to integers with defaults
        page = int(request.args.get('page', 1))  # Default page is 1
        page_size = int(request.args.get('page_size', 10))  # Default page_size is 10

        # Ensure both values are positive integers
        if page <= 0 or page_size <= 0:
            raise ValueError

    except (ValueError, TypeError):
        abort(400, description="page and page_size must be positive integers")

    # Use the helper function to get paginated quizzes
    result = get_paginated_data(storage, User, page=page, page_size=page_size)

    # Change the "data" key to "quizzes"
    result["users"] = result.pop("data")
    return jsonify(result)


@app_views.route('/users/<user_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_user(user_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/users/:id

    Get a specific user by their user_id.
    This route retrieves a single user based on the provided user_id.
    
    Parameters:
        user_id (str): The unique identifier for the user.
        
    Return:
        A JSON object representing the user if found.
        If the user is not found, returns a 404 error.
    """
    if user_id is None:
        abort(400, description="User ID is required")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Check if the current user is an admin or if they are trying to delete their own account
    if current_user_role != "admin" and user_id != current_user_id:
        abort(403, description="You are not authorized to retrieve this user.")

    user = storage.get(User, user_id)
    if user is None:
        abort(404, description="User not found")

    return jsonify(user.to_json())

 
@app_views.route('/users/<user_id>/results', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_user_quiz_results(user_id: str) -> ResponseReturnValue:
    """
    Get all results for a specific user or specific quiz results if quiz_id is provided.

    Args:
        user_id: The ID of the user whose results are to be retrieved.

    Returns:
        A JSON response containing a list of results.
    """
    quiz_id = request.args.get('quiz_id')
    if not user_id:
        abort(400, description="User ID is required")

    user = storage.get(User, user_id)
    if not user:
        abort(404, description="User not found")

    # Get the current user's identity and role from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt().get("role")

    # Authorization: Admins or the user themselves can access results
    if current_user_role != "admin" and user_id != current_user_id:
        abort(403, description="Access denied: You can only view your own results.")

    # Fetch and return results
    result_list = get_quiz_results_for_user(user_id, quiz_id, storage)
    return jsonify(result_list), 200


@app_views.route('/users/<user_id>/user-answers', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_user_result_user_answers(user_id: str) -> ResponseReturnValue:
    """
    Get all user answers for a specific user or specific result user answers if result_id is provided.

    Args:
        user_id: The ID of the user whose user answers are to be retrieved.

    Returns:
        A JSON response containing a list of user answers.
    """
    result_id = request.args.get('result_id')
    quiz_id = request.args.get('quiz_id')
    if not user_id:
        abort(400, description="User ID is required")

    user = storage.get(User, user_id)
    if not user:
        abort(404, description="User not found")

    # Get the current user's identity and role from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt().get("role")

    # Authorization: Admins or the user themselves can access user answers
    if current_user_role != "admin" and user_id != current_user_id:
        abort(403, description="Access denied: You can only view your own user answers.")

    # Fetch and return user answers
    user_answer_list = get_result_answers_for_user(user_id, result_id, quiz_id, storage)
    return jsonify(user_answer_list), 200



@app_views.route('/users/<user_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
def delete_user(user_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/users/:id

    Delete a specific user by their user_id.
    This route deletes a user after verifying the identity of the user making the request.
    
    Parameters:
        user_id (str): The unique identifier of the user to be deleted.
        
    Return:
        A JSON response indicating whether the deletion was successful.
        If the user does not exist or the current user is unauthorized, it returns an error.
    """
    if user_id is None:
        abort(400, description="User ID is required")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Check if the current user is an admin or if they are trying to delete their own account
    if current_user_role != "admin" and user_id != current_user_id:
        abort(403, description="You are not authorized to delete this user.")

    user = storage.get(User, user_id)
    if user is None:
        abort(404, description="User not found")

    # Access expiration values from Config
    refresh_token_exp = Config.JWT_REFRESH_TOKEN_EXPIRES

    # Blacklist the user's refresh tokens in Redis
    print(user.refresh_tokens)
    for token in user.refresh_tokens:  # Automatically fetched due to the relationship
        redis_client.setex(
            f"blacklist:{token.token}",
            int(refresh_token_exp.total_seconds()),  # Blacklist duration
            "blacklisted"
        )
    # Delete the user
    user.delete()
    storage.save()

    return jsonify({"message": "User successfully deleted."}), 200


@app_views.route('/users', methods=['POST'], strict_slashes=False)
def create_user() -> ResponseReturnValue:
    """ 
    POST /api/v1/users/

    Create a new user.
    This route allows the creation of a new user by accepting the necessary information 
    in a JSON payload. The input is validated, and duplicate users or invalid data are rejected.

    JSON body:
        - email: The user's email address (must be unique and valid).
        - password: The user's password.
        - first_name: The user's first name.
        - last_name: The user's last name.
        - username: The user's username (must be unique).
        - role: (optional) Role of the user (default is 'user').

    Return:
        A JSON response with the created user object, or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Define the required fields
    required_fields = ['first_name', 'last_name', 'username', 'email', 'password']

    # Check for missing required fields
    for field in required_fields:
        if field not in data:
            abort(400, description=f"Missing {field}")
        value = data.get(field)
        if not value:
            abort(400, description=f"{field} must not be null or empty")
        if not isinstance(value, str):
            abort(400, description=f"{field} must be a string.")
        if len(value) > 128:
            abort(400, description=f"{field} cannot be longer than 128 characters.")
        if field == 'first_name' or field == 'last_name':
            # Update the field with the converted string value
            formatted_text = format_text_to_title(value)
            data[field] = formatted_text

    # Validate email format
    email = data.get('email')
    try:
        validate_email(email)  # Validate email format
    except EmailNotValidError as e:
        return jsonify({'error': f'Invalid email format: {e}'}), 400

    # Check for existing username
    username = data.get('username')
    if storage.get_by_value(User, "username", username):
        abort(400, description="Username already exists!")

    # Check for existing email
    if storage.get_by_value(User, "email", email):
        abort(400, description="Email already registered!")

    # Validate the role
    role = data.get('role', 'user')  # Default to 'User' if not provided

    # Check if the current user is authenticated and has an 'admin' role
    # Assuming that the current user's identity is available via JWT (get_jwt_identity)
    current_user_role = None
    if role == "admin":
        # Ensure user is logged in and is an admin
        if 'Authorization' not in request.headers:
            abort(403, description="Admin role can only be assigned by an authenticated admin.")
        
        try:
            verify_jwt_in_request()  # Verify JWT
            current_user_role = get_jwt()['role']  # Get current user identity
            if current_user_role != 'admin':
                return jsonify({'error': 'Only admins can assign the role of "admin".'}), 403
        except Exception as e:
            return jsonify({'error': f'Invalid or missing token: {str(e)}'}), 401

    try:
        role_enum = Role.from_str(data.get('role', 'user'))  # Default to 'user' if no role provided
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Create new user instance using kwargs
    data['role'] = role_enum  # Set the role in data before passing it to the User constructor
    instance = User(**data)

    try:
        instance.save()
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

    return jsonify({
        "message": "User created successfully",
        "user": instance.to_json()
    }), 201


@app_views.route('/users/<user_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_user(user_id: str = None) -> ResponseReturnValue:
    """ 
    PUT /api/v1/users/:id

    Update user information.
    This route allows an authenticated user or admin to update a user's details 
    (such as first name, last name, username, email, and password). 
    Role updates are restricted to admin users only.

    Parameters:
        user_id (str): The unique identifier for the user.
    
    JSON body:
        - first_name (optional)
        - last_name (optional)
        - username (optional)
        - email (optional)
        - password (optional)
        - role (optional)

    Return:
        A JSON response with the updated user object, or error messages for invalid input.
    """
    # Ensure request data is JSON
    if user_id is None:
        abort(404, description="User ID is required")
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Retrieve the user by ID
    user = storage.get(User, user_id)
    if not user:
        abort(404, description="User not found!")

    # Get the current authenticated user's details
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()['role']

    # If the user is not an admin, they can only update their own information
    if current_user_role != 'admin' and current_user_id != user_id:
        abort(403, description="You are not authorized to update this user.")

    # Track if any updates are made
    updated = False

    # Update user fields if provided in the request
    updatable_fields = ['first_name', 'last_name', 'username', 'email', 'password']
    for field in updatable_fields:
        if field in data and field != 'role':
            value = data.get(field)
            if not value:
                abort(400, description=f"{field} must not be null or empty")
            if not isinstance(value, str):
                abort(400, description=f"{field} must be a string.")
            if len(value) > 128:
                abort(400, description=f"{field} cannot be longer than 128 characters.")
            if field == 'first_name' or field == 'last_name':
                # Update the field with the converted string value
                value = format_text_to_title(value)
            current_value = getattr(user, field)
            if field == 'password':
                print(user.check_password(value))
                if user.check_password(value):
                    continue

            # Skip if the value is the same
            if value == current_value:
                continue

            if field == 'email':
                try:
                    validate_email(value)
                except EmailNotValidError as e:
                    return jsonify({'error': f'Invalid email format: {e}'}), 400

                # Ensure no other user has this email
                if storage.get_by_value(User, 'email', value):
                    abort(400, description="Email already registered!")

            if field == 'username':
                # Ensure no other user has this username
                if storage.get_by_value(User, 'username', value):
                    abort(400, description="Username already exists!")

            # Update the user field
            setattr(user, field, value)
            updated = True

    # Handle role updates (Admins only)
    if 'role' in data:
        if data.get('role') == "admin" and current_user_role != 'admin':
            abort(403, description="Only admins can assign the role of 'admin'.")
        
        try:
            role = Role.from_str(data['role'])
            if user.role != role:
                user.role = role
                updated = True
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
    # If no updates were made, return a specific message
    if not updated:
        message = 'No changes were made to the user.'
    else:
        message = 'User updated successfully!'
        # Save the updated user
        try:
            user.updated_at = datetime.now(timezone.utc)
            user.save()
        except Exception as e:
            return jsonify({'error': f'An error occurred: {str(e)}'}), 500

    return jsonify({
        'message': message,
        'user': user.to_json()
    }), 200
