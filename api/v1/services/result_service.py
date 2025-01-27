#!/usr/bin/env python3
"""
Result Service Module

This module provides helper functions for managing results, such as adding a new result 
with input validation, formatting, and database interaction.

Functions:
    - add_result: Validates input data, ensures result uniqueness, and saves results to the database.

Dependencies:
    - models.result.Result: The Result model.
    - flask: For JSON responses and error handling.
    - api.v1.utils.string_utils: For text formatting utilities.
"""
from flask import jsonify, abort
from api.v1.utils.string_utils import format_text_to_title
from models.quiz import Quiz
from api.v1.services.topic_service import get_topic_by_id
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from models.user import User
from models.result import Result, QuizSessionStatus
from api.v1.services.quiz_service import get_quiz_by_id
from decimal import Decimal


def get_all_results(storage) -> List[Dict]:
    """
    Helper function to get all Results.

    Args:
        storage (object): Storage instance to handle database operations.
    
    Returns:
        List of dicts: A list of all Results in JSON serializable format.
    """
    all_results = [result.to_json() for result in storage.all(Result).values()]
    return all_results


def get_result_by_id(result_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a result by its ID.

    Args:
        result_id (str): The unique identifier for the result.
        storage (object): Storage instance to handle database operations.
    
    Returns:
        dict: A dictionary representing the result if found.
        None: If the result is not found.
    """
    if not result_id:
        abort(400, description="Result ID is required")

    if not isinstance(result_id, str):
        abort(400, description="Result ID must be a string")
    result = storage.get(Result, result_id)

    return result


def get_quiz_results_for_user(user_id: str, quiz_id: Optional[str], storage: Any) -> List[Dict]:
    """
    Fetch all results for a specific user, or specific quiz results if quiz_id is provided.

    Args:
        user_id: The ID of the user whose results are to be retrieved.
        quiz_id: (Optional) The ID of the quiz whose results are to be retrieved.
        storage: The storage handler for querying data.

    Returns:
        A list of results for the user, as JSON-serializable dictionaries.
    """
    if quiz_id:
        # Fetch results filtered by user_id and quiz_id
        results = storage.filter_by(Result, user_id=user_id, quiz_id=quiz_id)
    else:
        # Fetch all results for the user
        results = storage.filter_by(Result, user_id=user_id)
    
    # Sort results by creation date
    results.sort(key=lambda q: q.created_at, reverse=True)

    return [result.to_json() for result in results]


def add_result(data: Dict[str, Any], storage: Any) -> tuple:
    """
    Helper function to add a result.

    Args:
        data (dict): The data for the new result.
        storage (object): Storage instance to handle database operations.

    Returns:
        Response object: JSON response indicating success or error.
    """
    if 'user_id' not in data or 'quiz_id' not in data:
        abort(400, description="User ID and Quiz ID are required")

    user_id = data.get("user_id")
    quiz_id = data.get("quiz_id")
    score = data.get("score", 0.00)
    time_taken = data.get("time_taken", 0)
    status = data.get("status", "in-progress")
    submitted_at = data.get("submitted_at", datetime.now(timezone.utc))
    start_time = data.get("start_time", datetime.now(timezone.utc))
    end_time = data.get("end_time", datetime.now(timezone.utc))

    if not user_id or not quiz_id:
        abort(400, description="User ID and Quiz ID are required")

    if not isinstance(user_id, str):
        abort(400, description="User ID must be a string")

    # Check if the userexist in the database
    user = storage.get(User, user_id)

    if user is None:
        abort(404, description="User not found")

    quiz = get_quiz_by_id(quiz_id, storage)
    if quiz is None:
        abort(404, description="Quiz not found")

    validate_score(score)
    validate_time_taken(time_taken)
    status = validate_status(status)
    for field in [submitted_at, start_time, end_time]:
        print(f"type: {(type(field))}")
        validate_datetime(field)

    # Create a new Result object
    new_result = Result(
        user_id=user_id,
        quiz_id=quiz_id,
        score=score,
        time_taken=time_taken,
        status=status,
        submitted_at=submitted_at,
        start_time=start_time,
        end_time=end_time
    )

    # Save the result to the database
    storage.new(new_result)
    storage.save()

    # Return the created result
    return jsonify(new_result.to_json()), 201

def update_result_by_id(data: Dict[str, Any], storage: Any, result_id: str) -> tuple:
    # Fetch the result by result_id
    result = get_result_by_id(result_id, storage)
    if result is None:
        abort(404, description="Result not found")

    if 'quiz_id' in data:
        quiz_id = data.get('quiz_id')
        quiz = get_quiz_by_id(quiz_id, storage)
        if quiz is None:
            abort(404, description="Quiz not found")

    if 'user_id' in data:
        user_id = data.get('user_id')
        if not isinstance(user_id, str):
            abort(400, description="User ID must be a string")
        # Check if the userexist in the database
        user = storage.get(User, user_id)
        if user is None:
            abort(404, description="User not found")

    if 'score' in data:
        score = data.get('score')
        validate_score(score)


    if 'time_taken' in data:
        time_taken = data.get('time_taken')
        validate_time_taken(time_taken)

    if 'status' in data:
        status = data.get('status')
        data['status'] = validate_status(status)
    
    if 'submitted_at' in data:
        submitted_at = data.get('submitted_at')
        validate_datetime(submitted_at)

    if 'start_time' in data:
        start_time = data.get('start_time')
        validate_datetime(start_time)

    if 'end_time' in data:
        end_time = data.get('end_time')
        validate_datetime(end_time)

    updated = False
    fields = ['quiz_id', 'user_id', 'score', 'time_taken', 'status', 'submitted_at', 'start_time', 'end_time']

    for key, value in data.items():
        if key in fields:
            if value == getattr(result, key):
                continue
            setattr(result, key, value)
            updated = True
    
    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the result"
    else:
        message = "Result updated successfully"

        # Save updated result to the database
        result.updated_at = datetime.now(timezone.utc)
        result.save()

    return jsonify({
        "message": message,
        "result": result.to_json()
    }), 200


def validate_score(score: Optional[Decimal]) -> None:
    # Validate score (Decimal type, between 0 and 100)
    if not isinstance(score, float):
        abort(400, description="Score must be a float.")
    if score < 0.00 or score > 100.00:
        abort(400, description="Score must be between 0.00 and 100.00.")


def validate_time_taken(time_taken: Optional[int]) -> None:
    # Validate time_taken (int type, >= 0)
    if not isinstance(time_taken, int):
        abort(400, description=f"Time taken must be an integer.")
    if time_taken < 0:
        abort(400, description="Time taken must be greater than or equal to 0.")


def validate_status(status: str) -> None:
    # Validate status (must be a valid QuizSessionStatus)
    try:
        status_enum = QuizSessionStatus.from_str(status)
        return status_enum
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


def validate_datetime(field: Optional[datetime]) -> None:
    if not isinstance(field, datetime):
        abort(400, description=f"{field} must be a datetime object.")
            
    if field > datetime.now(timezone.utc):
        abort(400, description=f"{field} cannot be in the future.")


def calculate_feedback(percentage: float) -> str:
    """
    Generate feedback based on the quiz percentage score.
    """
    if percentage >= 90:
        return "Excellent! You're a star!"
    elif percentage >= 80:
        return "Great job! Keep it up!"
    elif percentage >= 70:
        return "Good effort! You're improving!"
    elif percentage >= 50:
        return "Satisfactory. Aim higher next time!"
    else:
        return "Needs improvement. Keep practicing!"
