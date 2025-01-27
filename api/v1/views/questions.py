from api.v1.views import app_views
from flask import abort, jsonify, request
from models.question import Question
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flasgger.utils import swag_from
from api.v1.services.auth_service import admin_required
from api.v1.utils.string_utils import format_text_to_title
from api.v1.utils.pagination_utils import get_paginated_data
from models.topic import Topic
from models.result import Result
from models.question import Question
from api.v1.services.question_service import get_question_by_id, add_question, update_question_by_id, get_choices_for_question
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Any
from flask.typing import ResponseReturnValue


@app_views.route('/questions', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_questions() -> ResponseReturnValue:
    """
    GET /api/v1/questions

    Get all questions with pagination.
    This route retrieves questions from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).
    
    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of questions for the current page.
        - next_page: Next page number, if available.
        - prev_page: Previous page number, if available.
        - total_pages: Total number of pages.
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

    # Use the helper function to get paginated questions
    result = get_paginated_data(storage, Question, page=page, page_size=page_size)

    # Change the "data" key to "questions"
    result["questions"] = result.pop("data")
    return jsonify(result)


@app_views.route('/questions/<question_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_question(question_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/questions/:id

    Get a specific question by their question_id.
    This route retrieves a single question based on the provided question_id.
    
    Parameters:
        question_id (str): The unique identifier for the question.
        
    Return:
        A JSON object representing the question if found.
        If the question is not found, returns a 404 error.
    """
    # Call the helper function `get_question_by_id` to retrieve the question by its ID.
    question = get_question_by_id(question_id, storage)

    # If the question is not found, abort with a 404 error and message "question not found".
    if question is None:
        abort(404, description="Question not found")

    # If the question is found, return it as a JSON object.
    return jsonify(question.to_json())


@app_views.route('/questions/<question_id>/choices', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_question_choices(question_id: str = None) -> ResponseReturnValue:
    """
    Get all choices for a specific question, ensuring the user has an in-progress quiz
    and the question belongs to the associated quiz.

    Args:
        question_id: The ID of the question whose choices are to be retrieved.

    Returns:
        A JSON response containing a list of choices or an error message.
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Fetch the question by ID
    question = storage.get(Question, question_id)
    if not question:
        abort(404, description="Question not found")

    # Check if the user has an in-progress result for the quiz the question belongs to
    result = storage.filter_by(Result, quiz_id=question.quiz_id, user_id=user_id, status="in-progress")
    if not result and current_user_role != "admin":
        abort(403, description="You do not have an in-progress quiz for the associated quiz.")

    # Fetch all choices for the question
    choice_list = get_choices_for_question(question_id, storage)

    return jsonify(choice_list), 200


@app_views.route('/questions/<question_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_question(question_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/questions/:id

    Delete a specific question by their question_id.
    This route deletes a question after verifying the identity of the question making the request.
    
    Parameters:
        question_id (str): The unique identifier of the question to be deleted.
        
    Return:
        A JSON response indicating whether the deletion was successful.
        If the question does not exist or the current question is unauthorized, it returns an error.
    """
    question = get_question_by_id(question_id, storage)

    if question is None:
        abort(404, description="Question not found")

    # Delete the question
    question.delete()
    storage.save()

    return jsonify({"message": "Question successfully deleted."}), 200


@app_views.route('/questions', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_question() -> ResponseReturnValue:
    """
    POST /api/v1/questions/

    Create a new question.
    This route allows admins to create a new question by accepting the necessary information 
    in a JSON payload. The input is validated, and duplicate questions or invalid data are rejected.

    Return:
        A JSON response with the created question object or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate question creation to the helper function
    return add_question(data, storage)


@app_views.route('/questions/<question_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_question(question_id: str = None) -> ResponseReturnValue:
    """
    PUT /api/v1/questions/<question_id>

    Update an existing question.

    This route allows admins to update an existing question by providing updated 
    information in a JSON payload. Validations ensure updates are consistent with 
    the business rules.

    URL Params:
        - question_id (str): The ID of the question to update.

    Returns:
        A JSON response with the updated question object or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate question creation to the helper function
    return update_question_by_id(data, storage, question_id)
