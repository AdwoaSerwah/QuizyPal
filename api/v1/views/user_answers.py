#!/usr/bin/env python3
""" Module of User Answers views
This module defines routes for managing user answers, including:
- Viewing user answers
- Viewing a user answer
- Creating new user answers
- Updating existing user answers
- Deleting user answers

Some routes are protected by JWT authentication, with the
option for role-based access control.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api.v1.services.auth_service import admin_required
from api.v1.services.user_answer_service import get_user_answer_by_id
from api.v1.services.user_answer_service import add_user_answer
from api.v1.services.user_answer_service import update_user_answer_by_id
from api.v1.utils.pagination_utils import get_paginated_data
from flask.typing import ResponseReturnValue
from models.user_answer import UserAnswer


@app_views.route('/user-answers', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_user_answers() -> ResponseReturnValue:
    """
    GET /api/v1/user-answers

    Get all user answers with pagination.
    This route retrieves user answers from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).

    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of user answers for the current page.
        - next_page: Next page number, if available.
        - prev_page: Previous page number, if available.
        - total_pages: Total number of pages.
    """
    # Get query parameters with defaults and validate
    try:
        # Convert query parameters to integers with defaults
        # Default page is 1
        page = int(request.args.get('page', 1))
        # Default page_size is 10
        page_size = int(request.args.get('page_size', 10))

        # Ensure both values are positive integers
        if page <= 0 or page_size <= 0:
            raise ValueError

    except (ValueError, TypeError):
        abort(400, description="page and page_size must be positive integers")

    # Use the helper function to get paginated user answers
    user_answer = get_paginated_data(storage, UserAnswer,
                                     page=page, page_size=page_size)

    # Change the "data" key to "user_answers"
    user_answer["user_answers"] = user_answer.pop("data")
    return jsonify(user_answer)


@app_views.route('/user-answers/<user_answer_id>',
                 methods=['GET'], strict_slashes=False)
@jwt_required()
def get_user_answer(user_answer_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/user-answers/:id

    Get a specific user answer by their user_answer_id.
    This route retrieves a single user answer based on the
    provided user_answer_id.

    Parameters:
        user_answer_id (str): The unique identifier for the user answer.

    Return:
        A JSON object representing the user answer if found.
        If the user answer is not found, returns a 404 error.
    """
    # Call the helper function to retrieve the user answer by its ID.
    user_answer = get_user_answer_by_id(user_answer_id, storage)

    # If the user answer is not found, abort with a 404 error
    if user_answer is None:
        abort(404, description="User Answer not found")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Check if the current user is an admin or
    # if they are trying to delete their own account
    if current_user_role != "admin" and user_answer.user_id != current_user_id:
        abort(403, description=(
            "You are not authorized to retrieve this user answer."
        ))

    # If the user answer is found, return it as a JSON object.
    return jsonify(user_answer.to_json())


@app_views.route('/user-answers/<user_answer_id>',
                 methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_user_answer(user_answer_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/user-answers/<user_answer_id>

    Delete a specific user answer by its ID. This route is restricted
    to admin users.

    Args:
        user_answer_id (str): The unique identifier of the user answer
        to be deleted.

    Returns:
        Response: A JSON response indicating whether the deletion
                  was successful. If the user answer does not exist,
                  returns a 404 error.
    """
    # Fetch the user answer from the database
    user_answer = get_user_answer_by_id(user_answer_id, storage)

    if user_answer is None:
        abort(404, description="User Answer not found")

    # Delete the user answer
    user_answer.delete()
    storage.save()

    return jsonify({"message": "User Answer successfully deleted."}), 200


@app_views.route('/user-answers', methods=['POST'], strict_slashes=False)
@jwt_required()
def add_user_answers():

    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")
    # Parse the request data
    data = request.get_json()

    # Delegate user answer creation to the helper function
    return add_user_answer(data, storage)


@app_views.route('/user-answers/<user_answer_id>',
                 methods=['PUT'], strict_slashes=False)
@jwt_required()
def update_user_answer(user_answer_id):
    """
    Update an existing user answer.

    Args:
        answer_id (str): ID of the UserAnswer to be updated.

    Returns:
        Response object: JSON response indicating success or error.
    """
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()
    # Delegate user answer update to the helper function
    return update_user_answer_by_id(data, storage, user_answer_id)
