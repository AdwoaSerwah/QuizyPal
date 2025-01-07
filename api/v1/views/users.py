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
from config import redis_client
from datetime import timedelta
from flasgger.utils import swag_from
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from email_validator import validate_email, EmailNotValidError


@app_views.route('/users', methods=['GET'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/user/get_users.yml')
def get_users() -> str:
    """
    GET /api/v1/users

    Get all users.
    This route retrieves all user records from the storage and
    returns them as a JSON list.
    
    Return:
        A JSON array containing all User objects.
        If no users are found, it returns an empty list.
    """
    all_users = [user.to_json() for user in storage.all(User).values()]
    return jsonify(all_users)


@app_views.route('/users/<user_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/user/get_user.yml', methods=['GET'])
def get_user(user_id: str = None) -> str:
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
        abort(404, description="User ID is required")

    user = storage.get(User, user_id)
    if user is None:
        abort(404, description="User not found")

    return jsonify(user.to_json())


@app_views.route('/users/<user_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/user/delete_user.yml', methods=['DELETE'])
def delete_user(user_id: str = None) -> str:
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
        abort(404, description="User ID is required")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Check if the current user is an admin or if they are trying to delete their own account
    if current_user_role != "admin" and user_id != current_user_id:
        abort(403, description="You are not authorized to delete this user.")

    user = storage.get(User, user_id)
    if user is None:
        abort(404, description="User not found")

    # Blacklist the user's refresh tokens if they exist
    refresh_tokens = storage.query(RefreshToken).filter_by(user_id=user_id).all()
    for token in refresh_tokens:
        redis_client.setex(
            f"blacklist:{token.token}",
            int(timedelta(days=7).total_seconds()),  # Blacklist duration (adjust as needed)
            "blacklisted"
        )
        # Remove from the database
        storage.delete(token)

    # Delete the user
    user.delete()
    storage.save()

    return jsonify({"message": "User successfully deleted."}), 200


@app_views.route('/users', methods=['POST'], strict_slashes=False)
@swag_from('documentation/user/create_user.yml', methods=['POST'])
def create_user() -> str:
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
        return jsonify({'message': 'No data provided!'}), 400

    data = request.get_json()

    # Define the required fields
    required_fields = ['first_name', 'last_name', 'username', 'email', 'password']

    # Check for missing required fields
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing {field}'}), 400

    # Validate fields (attempt to convert to string and max length of 128)
    for field in required_fields:
        value = data.get(field)
        try:
            # Attempt to convert to string
            value = str(value)
        except (ValueError, TypeError):
            return jsonify(
                {'message': f'{field} must be a string.'}), 400

        # Check for max length of 128 characters
        if len(value) > 128:
            return jsonify(
                {'message': f'{field} cannot be longer than 128 characters.'}
                ), 400

        # Update the field with the converted string value
        data[field] = value

    # Validate email format
    email = data.get('email')
    try:
        validate_email(email)  # Validate email format
    except EmailNotValidError as e:
        return jsonify({'message': f'Invalid email format: {e}'}), 400

    # Check for existing username
    username = data.get('username')
    if storage.get_by_value(User, "username", username):
        return jsonify({'message': 'Username already exists!'}), 400

    # Check for existing email
    if storage.get_by_value(User, "email", email):
        return jsonify({'message': 'Email already registered!'}), 400

    # Validate the role
    role = data.get('role', 'user')  # Default to 'User' if not provided

    # Check if the current user is authenticated and has an 'admin' role
    # Assuming that the current user's identity is available via JWT (get_jwt_identity)
    current_user_role = None
    if role == "admin":
        # Ensure user is logged in and is an admin
        if 'Authorization' not in request.headers:
            return jsonify({'message': 'Only admins can assign the role of "Admin".'}), 403
        
        try:
            verify_jwt_in_request()  # Verify JWT
            current_user_role = get_jwt()['role']  # Get current user identity
            if current_user_role != 'admin':
                return jsonify({'message': 'Only admins can assign the role of "Admin".'}), 403
        except Exception as e:
            return jsonify({'message': f'Invalid or missing token: {str(e)}'}), 401

    try:
        role_enum = Role.from_str(data.get('role', 'user'))  # Default to 'user' if no role provided
    except ValueError as e:
        return jsonify({'message': str(e)}), 400

    # Create new user instance using kwargs
    data['role'] = role  # Set the role in data before passing it to the User constructor
    instance = User(**data)

    try:
        instance.save()
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

    return jsonify({
        "message": "User created successfully",
        "user": instance.to_json()
    }), 201


@app_views.route('/users/<user_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/user/update_user.yml', methods=['PUT'])
def update_user(user_id: str = None) -> str:
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
    if not request.get_json():
        return jsonify({'message': 'No data provided!'}), 400

    data = request.get_json()

    # Retrieve the user by ID
    user = storage.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    # Get the current authenticated user's details
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()['role']

    # If the user is not an admin, they can only update their own information
    if current_user_role != 'admin' and current_user_id != user_id:
        return jsonify({'message': 'You are not authorized to update this user.'}), 403

    # Helper function for field validation
    def validate_field(field_name, field_value, max_length=128):
        if len(field_value) > max_length:
            return f"{field_name} cannot be longer than {max_length} characters."
        return None

    # Update user fields if provided in the request
    updatable_fields = ['first_name', 'last_name', 'username', 'email', 'password']
    for field in updatable_fields:
        value = data.get(field)
        if value is not None:
            value = str(value)
            error_message = validate_field(field, value)
            if error_message:
                return jsonify({'message': error_message}), 400

            if field == 'email':
                try:
                    validate_email(value)
                except EmailNotValidError as e:
                    return jsonify({'message': f'Invalid email format: {e}'}), 400

                # Ensure no other user has this email
                if value != user.email and storage.get_by_value(User, 'email', value):
                    return jsonify({'message': 'Email already registered!'}), 400

            if field == 'username':
                # Ensure no other user has this username
                if value != user.username and storage.get_by_value(User, 'username', value):
                    return jsonify({'message': 'Username already exists!'}), 400

            # Update the user field
            setattr(user, field, value)

    # Handle role updates (Admins only)
    if current_user_role == 'admin' and 'role' in data:
        try:
            role = Role.from_str(data['role'])
            user.role = role
        except ValueError:
            return jsonify({'message': 'Invalid role provided!'}), 400

    # Save the updated user
    try:
        user.save()
    except Exception as e:
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500

    return jsonify({
        'message': 'User updated successfully!',
        'user': user.to_json()}), 200
