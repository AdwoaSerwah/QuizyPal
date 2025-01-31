#!/usr/bin/env python3
""" Module of Results views
This module defines routes for managing results, including:
- Viewing results
- Viewing a result
- Creating new results
- Updating existing results
- Deleting results
- Retrieving result feedback

Some routes are protected by JWT authentication, with the
option for role-based access control.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api.v1.services.auth_service import admin_required
from api.v1.services.result_service import get_result_by_id, add_result
from api.v1.services.result_service import update_result_by_id
from api.v1.services.result_service import calculate_feedback
from api.v1.utils.pagination_utils import get_paginated_data
from api.v1.services.quiz_service import get_quiz_by_id
from datetime import datetime, timezone
from flask.typing import ResponseReturnValue
from models.question import Question
from models.result import Result
from models.user_answer import UserAnswer
from models.choice import Choice


@app_views.route('/results', methods=['GET'], strict_slashes=False)
@jwt_required()
@admin_required
def get_results() -> ResponseReturnValue:
    """
    GET /api/v1/results

    Get all results with pagination.
    This route retrieves results from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).

    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of results for the current page.
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

    # Use the helper function to get paginated results
    result = get_paginated_data(storage, Result,
                                page=page, page_size=page_size)

    # Change the "data" key to "results"
    result["results"] = result.pop("data")
    return jsonify(result)


@app_views.route('/results/<result_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_result(result_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/results/:id

    Get a specific result by their result_id.
    This route retrieves a single result based on the provided result_id.

    Parameters:
        result_id (str): The unique identifier for the result.

    Return:
        A JSON object representing the result if found.
        If the result is not found, returns a 404 error.
    """
    # Call the helper function to retrieve the result by its ID.
    result = get_result_by_id(result_id, storage)

    # If the result is not found, abort with a 404 error.
    if result is None:
        abort(404, description="Result not found")

    # Get the current user's identity from the JWT token
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Check if the current user is an admin or
    # if they are trying to delete their own account
    if current_user_role != "admin" and result.user_id != current_user_id:
        abort(403,
              description="You are not authorized to retrieve this result.")

    # If the result is found, return it as a JSON object.
    return jsonify(result.to_json())


@app_views.route('/results/<result_id>',
                 methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_result(result_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/results/<result_id>

    Delete a specific result by its ID. This route is restricted to admins.

    Args:
        result_id (str): The unique identifier of the result to be deleted.

    Returns:
        Response: A JSON response indicating if the deletion was successful.
                  If the result does not exist, returns a 404 error.
    """
    # Fetch the result from the database
    result = get_result_by_id(result_id, storage)

    if result is None:
        abort(404, description="Result not found")

    # Delete the result
    result.delete()
    storage.save()

    return jsonify({"message": "Result successfully deleted."}), 200


@app_views.route('/results', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required  # Only admins should be able to create results directly
def create_result() -> ResponseReturnValue:
    """
    POST /api/v1/results

    Create a new result (quiz attempt) for a user.
    This route is used by admins to manually create results for users.

    Return:
        A JSON response containing the created result's data.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")
    # Parse the request data
    data = request.get_json()

    # Delegate result creation to the helper function
    return add_result(data, storage)


@app_views.route('/results/<result_id>',
                 methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_result(result_id: str = None) -> ResponseReturnValue:
    """
    PUT /api/v1/results/:id
    Update a specific result by its result_id.

    Parameters:
        result_id (str): The unique identifier of the result to be updated.

    Return:
        A JSON response indicating whether the update was successful.
        If the result does not exist or the current result is unauthorized,
        it returns an error.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate result creation to the helper function
    return update_result_by_id(data, storage, result_id)


@app_views.route('/results/<result_id>/feedback',
                 methods=['GET'], strict_slashes=False)
@jwt_required()
def get_result_feedback(result_id: str) -> ResponseReturnValue:
    """
    GET /api/v1/results/:result_id/feedback/
    Retrieve feedback for a completed quiz based on the user's
    answers and overall performance.

    Parameters:
        result_id (str): The unique identifier of the result (quiz attempt).

    Return:
        A JSON response containing the quiz feedback.
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Fetch the result object
    result = get_result_by_id(result_id, storage)
    if not result:
        abort(404, description="Result not found")

    # Check if the user ID from the JWT matches the user ID
    # associated with the result
    if result.user_id != user_id and current_user_role != "admin":
        abort(403, description="You are not authorized to view this feedback.")

    # Check if the quiz status is completed or timed-out
    if result.status.value not in ["completed", "timed-out"]:
        abort(400, description="Quiz has not been completed or timed out yet.")

    # Fetch the associated quiz from the result object
    quiz = result.quiz
    quiz = get_quiz_by_id(quiz.id, storage)
    if not quiz:
        abort(404, description="Quiz not found")

    # Fetch all questions for the quiz
    all_questions = storage.filter_by(Question, quiz_id=quiz.id)

    # Fetch all user answers for this result
    user_answers = storage.filter_by(UserAnswer, result_id=result_id)
    user_answers_map = {}
    for answer in user_answers:
        user_answers_map[answer.question_id] = answer.choice_id

    # Initialize variables
    total_score = 0
    max_score = len(all_questions)
    unanswered_questions = []
    answers_details = []
    correct_answers = 0
    incorrect_answers = 0

    # Check each question and calculate score
    for question in all_questions:
        correct_choices = [
            choice.id
            for choice in question.choices
            if choice.is_correct
        ]

        # Initialize user_selected_choice_ids outside the block
        user_selected_choice_ids = []

        if question.allow_multiple_answers:
            # Determine the number of correct choices and
            # the total number of choices
            correct_answers_count = len(correct_choices)
            total_choices_count = len(question.choices) - 1

            # Points per correct answer and points per incorrect answer
            points_per_correct_answer = 1 / correct_answers_count
            # 1 divided by total choices for penalty
            penalty_per_incorrect_choice = 1 / total_choices_count

            # User's selected choices
            user_selected_choices = storage.filter_by(UserAnswer,
                                                      result_id=result_id,
                                                      question_id=question.id)

            user_selected_choice_ids = [
                answer.choice_id
                for answer in user_selected_choices
            ]

            # Calculate correct selections
            correct_selections = sum(
                1
                for choice_id in user_selected_choice_ids
                if choice_id in correct_choices
            )

            # Calculate the number of incorrect selections
            incorrect_selections = sum(
                1
                for choice_id in user_selected_choice_ids
                if choice_id not in correct_choices
            )

            # Penalize by subtracting the number of incorrect choices
            points_awarded = (
                (correct_selections * points_per_correct_answer)
                - (incorrect_selections * penalty_per_incorrect_choice)
            )

            # Ensure points are not negative
            points_awarded = max(points_awarded, 0)

            total_score += points_awarded

            # Determine if all correct answers were selected
            is_correct = set(user_selected_choice_ids) == set(correct_choices)
            if is_correct:
                correct_answers += 1
            else:
                incorrect_answers += 1
        else:  # Single-answer question
            user_choice_id = user_answers_map.get(question.id)
            if user_choice_id:
                # Assign the single selected choice
                user_selected_choice_ids = [user_choice_id]
            else:
                user_selected_choice_ids = []  # No answer selected

            if user_choice_id and user_choice_id in correct_choices:
                points_awarded = 1
                total_score += 1
                correct_answers += 1
                is_correct = True
            elif user_choice_id is None:
                points_awarded = 0
                unanswered_questions.append(question.id)
                is_correct = False
            else:
                incorrect_answers += 1
                points_awarded = 0
                is_correct = False

        # Append detailed answer information
        answers_details.append({
            "question_order_number": question.order_number,
            "question_text": question.question_text,
            "user_choice": (
                "no_answer"
                if not user_selected_choice_ids
                else ", ".join(
                    [
                        storage.get(Choice, choice_id).choice_text
                        for choice_id in user_selected_choice_ids
                    ]
                )  # Join multiple selected choices with commas
            ),
            "correct_choice": ", ".join(
                [
                    storage.get(Choice, c_id).choice_text
                    for c_id in correct_choices
                ]
            ),
            "points_awarded": round(points_awarded, 2),
        })

    # Calculate the percentage score
    total_score = round(total_score, 2)
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0

    # Generate feedback based on percentage
    feedback = calculate_feedback(percentage)

    completion_time_minutes = round(result.time_taken / 60)

    # Compare the calculated score with the current result.score
    # If the calculated score is different, update it
    if result.score != total_score:
        result.score = total_score
        result.updated_at = datetime.now(timezone.utc)
        storage.save()

    # Final response
    return jsonify({
        "quiz_title": quiz.title,
        "feedback": feedback,
        "date": result.created_at.strftime("%d-%m-%y"),
        "completion_time": f"{completion_time_minutes} minutes",
        "time_limit": f"{quiz.time_limit} minutes",
        "status": result.status.value,
        "correct_answers": correct_answers,
        "incorrect_answers": incorrect_answers,
        "no_answers": len(unanswered_questions),
        "total_questions": max_score,
        "user_score": total_score,
        "total_score": max_score,
        "percentage": f"{percentage}%",
        "answers": answers_details
    }), 200
