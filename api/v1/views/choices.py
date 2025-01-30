#!/usr/bin/env python3
"""
Choice API Endpoints

This module defines the Flask routes for managing quiz choices
in the QuizyPal API.

It includes endpoints for:
- Retrieving choices with pagination
- Getting a specific choice by ID
- Deleting a choice with validation
- Creating multiple choices
- Updating an existing choice

All routes require authentication and admin privileges.

Routes:
- GET /choices
- GET /choices/<choice_id>
- DELETE /choices/<choice_id>
- POST /choices
- PUT /choices/<choice_id>

Dependencies:
- Flask
- Flask-JWT-Extended for authentication
- Models and services for handling database operations
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models import storage
from flask_jwt_extended import jwt_required
from api.v1.services.auth_service import admin_required
from api.v1.utils.pagination_utils import get_paginated_data
from models.choice import Choice
from api.v1.services.question_service import get_question_by_id
from flask.typing import ResponseReturnValue
from api.v1.services.choice_service import (
    get_choice_by_id, add_choices,
    update_choice_by_id, validate_correct_answers
)


@app_views.route('/choices', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_choices() -> ResponseReturnValue:
    """
    GET /api/v1/choices

    Get all choices with pagination.
    This route retrieves choices from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).

    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of choices for the current page.
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

    # Use the helper function to get paginated choices
    result = get_paginated_data(storage, Choice,
                                page=page, page_size=page_size)

    # Change the "data" key to "choices"
    result["choices"] = result.pop("data")
    return jsonify(result)


@app_views.route('/choices/<choice_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_choice(choice_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/choices/:id

    Get a specific choice by their choice_id.
    This route retrieves a single choice based on the provided choice_id.

    Parameters:
        choice_id (str): The unique identifier for the choice.

    Return:
        A JSON object representing the choice if found.
        If the choice is not found, returns a 404 error.
    """
    # Call the helper function to retrieve the choice by its ID.
    choice = get_choice_by_id(choice_id, storage)

    # If the choice is not found, abort with a 404 error".
    if choice is None:
        abort(404, description="Choice not found")

    # If the choice is found, return it as a JSON object.
    return jsonify(choice.to_json())


@app_views.route('/choices/<choice_id>',
                 methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_choice(choice_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/choices/:id

    Delete a specific choice by their choice_id.
    This route deletes a choice after verifying the
    identity of the choice making the request.

    Parameters:
        choice_id (str): The unique identifier of the choice
        to be deleted.

    Return:
        A JSON response indicating whether the deletion was successful.
        If the choice does not exist or the current choice is unauthorized,
        it returns an error.
    """
    choice = get_choice_by_id(choice_id, storage)

    if choice is None:
        abort(404, description="Choice not found")

    if choice.choice_text == "no_answer":
        abort(400, description="'no_answer choice cannot be deleted")
    # Retrieve the related question and existing choices
    question_id = choice.question_id
    question = get_question_by_id(question_id, storage)
    if not question:
        abort(404, description="Question not found")

    # Get the list of existing choices
    existing_choices = storage.get_by_value(Choice, 'question_id', question_id)
    # Remove the 'no_answer' choice from the existing_choices
    if existing_choices:
        if not isinstance(existing_choices, list):
            existing_choices = [existing_choices]

    existing_choices = [
        ch for ch in existing_choices
        if ch.choice_text != "no_answer" and ch.id != choice.id
    ]

    if len(existing_choices) < 2:
        abort(404, description=(
            "There must be at least two valid choices for a question"
        ))

    allow_multiple_answers = question.allow_multiple_answers
    # Validate if the deletion would cause any issues with the correct answers
    validate_correct_answers(existing_choices,
                             False,
                             allow_multiple_answers,
                             question.question_text)

    # Proceed with deletion if no validation issues
    choice.delete()
    storage.save()

    return jsonify({"message": "Choice successfully deleted."}), 200


@app_views.route('/choices', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_choices() -> ResponseReturnValue:
    """
    POST /api/v1/choices/

    Create a new choice.
    This route allows admins to create a new choice by accepting
    the necessary information in a JSON payload. The input is validated,
    and duplicate choices or invalid data are rejected.

    Return:
        A JSON response with the created choice object or error messages
        for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()
    choices = data.get('choices')

    if not (choices and isinstance(choices, list)):
        abort(400, description=(
            "'choices' key is required and must be a non-empty list."
        ))

    for choice in choices:
        if not isinstance(choice, dict):
            abort(400, description="Each choice must be a dictionary.")
    # Delegate choice creation to the helper function
    return add_choices(data, storage)


@app_views.route('/choices/<choice_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_choice(choice_id: str = None) -> ResponseReturnValue:
    """
    PUT /api/v1/choices/<choice_id>

    Update an existing choice.

    This route allows admins to update an existing choice by providing updated
    information in a JSON payload. Validations ensure updates are consistent
    with the business rules.

    URL Params:
        - choice_id (str): The ID of the choice to update.

    Returns:
        A JSON response with the updated choice object or error messages
        for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate choice creation to the helper function
    return update_choice_by_id(data, storage, choice_id)
