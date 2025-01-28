#!/usr/bin/env python3
"""
User Answer Service Module

This module provides helper functions for managing user answers, such as adding a new user answer 
with input validation, formatting, and database interaction.

Functions:
    - add_user_answer: Validates input data, ensures user answer uniqueness, and saves user answers to the database.

Dependencies:
    - models.user_answer.UserAnswer: The UserAnswer model.
    - flask: For JSON responses and error handling.
    - api.v1.utils.string_utils: For text formatting utilities.
"""
from flask import jsonify, abort
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from models.user_answer import UserAnswer
from models.user import User
from api.v1.services.result_service import get_result_by_id
from api.v1.services.question_service import get_question_by_id
from api.v1.services.quiz_service import get_quiz_by_id
from api.v1.services.choice_service import get_choice_by_id
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt


def get_all_user_answers(storage) -> List[Dict]:
    """
    Helper function to get all User Answers.

    Args:
        storage (object): Storage instance to handle database operations.
    
    Returns:
        List of dicts: A list of all User Answers in JSON serializable format.
    """
    all_user_answers = [user_answer.to_json() for user_answer in storage.all(UserAnswer).values()]
    return all_user_answers


def get_user_answer_by_id(user_answer_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a user answer by its ID.

    Args:
        user_answer_id (str): The unique identifier for the user answer.
        storage (object): Storage instance to handle database operations.
    
    Returns:
        dict: A dictionary representing the user answer if found.
        None: If the user answer is not found.
    """
    if not user_answer_id:
        abort(400, description="User Answer ID is required")

    if not isinstance(user_answer_id, str):
        abort(400, description="User Answer ID must be a string")
    user_answer = storage.get(UserAnswer, user_answer_id)

    return user_answer


def get_result_answers_for_user(user_id: str, result_id: Optional[str], quiz_id: Optional[str], storage: Any) -> List[Dict]:
    """
    Fetch all user answers for a specific user, or specific result/user answers if result_id or quiz_id is provided.

    Args:
        user_id: The ID of the user whose user answers are to be retrieved.
        result_id: (Optional) The ID of the result (specific attempt) whose user answers are to be retrieved.
        quiz_id: (Optional) The ID of the quiz whose user answers are to be retrieved. If provided along with result_id,
                it will have no effect since result_id uniquely identifies the result.
        storage: The storage handler for querying data.

    Returns:
        A list of user answers for the user, as JSON-serializable dictionaries.

    Notes:
        - You may provide either parameter or neither, but providing both is redundant.
        - Providing both quiz_id and result_id is effectively the same as providing just result_id.
    """
    if result_id:
        result = get_result_by_id(result_id, storage)
        if not result:
            abort(404, description="Result not found")
        # Fetch user answers filtered by user_id and result_id
        user_answers = storage.filter_by(UserAnswer, user_id=user_id, result_id=result_id)
    elif quiz_id:
        quiz = get_quiz_by_id(quiz_id, storage)
        if not quiz:
            abort(404, description="Quiz not found")
        # Fetch all user answers for the user filtered by quiz_id (all results for that quiz)
        user_answers = storage.filter_by(UserAnswer, user_id=user_id, quiz_id=quiz_id)
    else:
        # Fetch all user answers for the user
        user_answers = storage.filter_by(UserAnswer, user_id=user_id)
    
    # Sort user answers by creation date
    user_answers.sort(key=lambda q: q.created_at, reverse=True)

    return [user_answer.to_json() for user_answer in user_answers]


def add_user_answer(data: Dict[str, Any], storage: Any) -> tuple:
    """
    Helper function to add a user answer.

    Args:
        data (dict): The data for the new user answer.
        storage (object): Storage instance to handle database operations.

    Returns:
        Response object: JSON response indicating success or error.
    """
    if not isinstance(data, dict):
        abort(400, description="The entire data must be in a dictionary")

    result_id = data.get('result_id')
    # This will either be a single answer or a list of answers
    answers = data.get('answers')
    user_id = data.get('user_id')
    quiz_id = data.get('quiz_id')

    if not user_id:
        abort(404, description="User ID is required")
    # Retrieve the user by ID
    user = storage.get(User, user_id)
    if not user:
        abort(404, description="User not found!")

    # Get the current authenticated user's details
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()['role']

    # If the user is not an admin, they can only update their own information
    if current_user_role != 'admin' and current_user_id != user_id:
        abort(403, description="You are not authorized to add answers for this user.")

    # Check if result exists
    result = get_result_by_id(result_id, storage)
    if not result:
        abort(404, description="Result not found")

    # Check if the quiz status is in-progress
    if current_user_role != 'admin' and result.status not in ["in-progress"]:
        abort(400, description="Quiz has already been completed or timed out.")

    # Check if the user ID from the JWT matches the user ID associated with the result
    if result.user_id != user_id and current_user_role != "admin":
        abort(403, description="You are not authorized to stop this quiz.")

    # Ensure the quiz_id from the request matches the quiz_id from the result
    if result.quiz_id != quiz_id:
        print(f"result.quiz_id: {result.quiz_id}, data.get('quiz_id'): {data.get('quiz_id')}")
        abort(400, description="The quiz ID does not match the result's associated quiz.")

    quiz = get_quiz_by_id(quiz_id, storage)
    if not quiz:
        abort(404, description="Quiz not found")
    # quiz_id = quiz.id

    # Convert the time limit from minutes to seconds
    time_limit_seconds = quiz.time_limit * 60  # Convert time limit in minutes to seconds

    # Convert start time and current time to seconds since epoch
    result_start_time = int(result.start_time.timestamp())  # Convert to seconds
    current_time_seconds = int(datetime.now(timezone.utc).timestamp())  # Convert current time to seconds (UTC)

    # Check if the quiz time has expired
    time_limit_expired = current_time_seconds > (result_start_time + time_limit_seconds)

    # Admins can submit answers at any time; non-admin users cannot after the time limit
    if current_user_role != "admin" and time_limit_expired:
        abort(403, description="Time limit exceeded: You can no longer submit answers.")

    # Check if answers is provided and is a list
    if not answers or not isinstance(answers, list):
        abort(400, description="answers must be in a list.")

    user_answers = []
    
    # Create UserAnswer entries for each answer in the list
    for answer in answers:
        question_id = answer.get('question_id')
        choice_id = answer.get('choice_id')

        question = get_question_by_id(question_id, storage)
        if not question:
            abort(404, description=f"Question {question_id}  not found")

        choice = get_choice_by_id(choice_id, storage)
        if not choice:
            abort(404, description="Choice not found")

        existing_user_answer = storage.filter_by(UserAnswer,
                                                 result_id=result_id,
                                                 user_id=user_id,
                                                 quiz_id=quiz_id,
                                                 question_id=question_id,
                                                 choice_id=choice_id)
        
        if existing_user_answer:
            abort(400, description=f"User Answer for question {question_id} and choice {choice_id} already exists for this user!")
        user_answer = UserAnswer(user_id=user.id,
                                 result_id=result.id,
                                 question_id=question.id,
                                 choice_id=choice.id,
                                 quiz_id=quiz_id)

        storage.new(user_answer)
        user_answers.append(user_answer)

    # Save all answers to the database at once
    storage.save()

    # Return the list of answers submitted
    return jsonify([user_answer.to_json() for user_answer in user_answers]), 201


def update_user_answer_by_id(data: Dict[str, Any], storage: Any, user_answer_id: str) -> tuple:
    """
    Update an existing user answer.

    Args:
        user_answer_id (str): ID of the UserAnswer to be updated.

    Returns:
        Response object: JSON response indicating success or error.
    """
    choice_id = data.get('choice_id')  # New choice to update the answer

    if not choice_id:
        abort(400, description="choice_id is required to update the answer.")

    # Get the UserAnswer by ID
    user_answer = get_user_answer_by_id(user_answer_id, storage)
    if not user_answer:
        abort(404, description="User Answer not found!")

    # Get the current authenticated user's details
    current_user_id = get_jwt_identity()
    current_user_role = get_jwt()['role']

    # If the user is not an admin, they can only update their own answers
    if current_user_role != 'admin' and current_user_id != user_answer.user_id:
        abort(403, description="You are not authorized to update this answer.")

    # Check if the quiz is still in-progress
    result = user_answer.result

    if result.status.value not in ["in-progress"] and current_user_role != 'admin':
        abort(400, description="Cannot update answers for a quiz that has been completed or timed out.")

    # Ensure the quiz time limit has not expired
    quiz = result.quiz
    print(quiz)
    print(f"quiz id: {quiz.id}")
    time_limit_seconds = quiz.time_limit * 60  # Convert to seconds
    result_start_time = int(result.start_time.timestamp())  # Convert to seconds
    current_time_seconds = int(datetime.now(timezone.utc).timestamp())  # Get current time in seconds

    time_limit_expired = current_time_seconds > (result_start_time + time_limit_seconds)

    # Admins can update answers at any time, but non-admin users cannot after the time limit
    if current_user_role != "admin" and time_limit_expired:
        abort(403, description="Time limit exceeded: You can no longer update answers.")

    # Ensure the new choice exists in the database
    choice = get_choice_by_id(choice_id, storage)
    if not choice:
        abort(404, description="Choice not found!")

    # Check if the choice belongs to the correct question
    question = choice.question  # Get the question related to the choice
    if question.id != user_answer.question_id:
        abort(400, description="The selected choice does not belong to the question being answered.")

    updated = False

    # Check if the choice is actually being updated
    if user_answer.choice_id != choice_id:
        # Update the UserAnswer with the new choice
        user_answer.choice_id = choice_id
        updated = True

    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the user answer"
    else:
        message = "User answer updated successfully"

        # Save updated user answer to the database
        user_answer.updated_at = datetime.now(timezone.utc)
        user_answer.save()
    print(user_answer.to_json())
    user_answer_data = user_answer.to_json()
    user_answer_data.pop("result", None)  # Remove the result key if it exists

    return jsonify({
        "message": message,
        "user_answer": user_answer_data
    }), 200
