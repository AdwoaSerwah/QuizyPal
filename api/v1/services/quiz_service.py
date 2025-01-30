#!/usr/bin/env python3
"""
This module provides helper functions to handle various operations
related to quizzes. These operations include fetching quizzes,
adding, updating quizzes, validating input data, and fetching related
quiz questions. It interacts with the storage layer to perform
CRUD operations for quizzes, and validates input such as quiz titles,
descriptions, time limits, and topic IDs.

Functions:
    - get_all_quizzes: Retrieves all quizzes from the database.
    - get_quiz_by_id: Retrieves a quiz by its ID.
    - get_questions_for_quiz: Retrieves all questions for a specific quiz.
    - get_quiz_by_title_helper: Retrieves a quiz by its title.
    - add_quiz: Adds a new quiz to the database.
    - update_quiz_by_id: Updates quiz details by quiz ID.
    - validate_quiz_title: Validates the title of a quiz.
    - validate_time_limit: Validates the time limit of a quiz.
    - validate_quiz_description: Validates the description of a quiz.
    - validate_quiz_topic_id: Validates the topic ID associated with a quiz.
"""

from models.quiz import Quiz
from flask import jsonify, abort
from api.v1.utils.string_utils import format_text_to_title
from models.quiz import Quiz
from api.v1.services.topic_service import get_topic_by_id
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from models.question import Question


def get_all_quizzes(storage) -> List[Dict]:
    """
    Helper function to get all Quizzes.

    Args:
        storage (object): Storage instance to handle database operations.

    Returns:
        List of dicts: A list of all Quizzes in JSON serializable format.
    """
    all_quizzes = [quiz.to_json() for quiz in storage.all(Quiz).values()]
    return all_quizzes


def get_quiz_by_id(quiz_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a quiz by its ID.

    Args:
        quiz_id (str): The unique identifier for the quiz.
        storage (object): Storage instance to handle database operations.

    Returns:
        dict: A dictionary representing the quiz if found.
        None: If the quiz is not found.
    """
    if quiz_id is None:
        abort(400, description="Quiz ID is required")

    if not isinstance(quiz_id, str):
        abort(400, description="Quiz ID must be a string")
    quiz = storage.get(Quiz, quiz_id)

    return quiz


def get_questions_for_quiz(quiz_id: str, storage: Any) -> List[Question]:
    """
    Fetch all questions for a specific quiz.

    Args:
        quiz_id: The ID of the quiz.

    Returns:
        A list of Question objects for the quiz.
    """
    quiz = get_quiz_by_id(quiz_id, storage)
    if not quiz:
        abort(404, description="Quiz not found")

    # Fetch all questions for the quiz and sort them by order_number
    questions = storage.filter_by(Question, quiz_id=quiz_id)
    questions.sort(key=lambda q: q.order_number)

    question_list = [question.to_json() for question in questions]

    return question_list


def get_quiz_by_title_helper(quiz_title: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a quiz by its title.

    Args:
        quiz_title (str): The title of the quiz.
        storage (object): Storage instance to handle database operations.

    Returns:
        dict: A dictionary representing the quiz if found.
        None: If the quiz is not found.
    """
    if not isinstance(quiz_title, str):
        abort(400, description="Quiz title must be a string")

    if quiz_title.lower() in ["null", "none", ""]:
        abort(400, description="Quiz title must not be null or empty.")

    # Format the quiz title to match the storage format
    formatted_title = format_text_to_title(quiz_title)

    # Retrieve the quiz by its title
    quiz = storage.get_by_value(Quiz, "title", formatted_title)
    return quiz


def add_quiz(data: Dict[str, Any], storage: Any) -> tuple:
    """
    Helper function to add a quiz.

    Args:
        data (dict): The data for the new quiz.
                     Expected keys: 'title', 'description',
                     'time_limit', 'topic_id'.
        storage (object): Storage instance to handle database operations.

    Returns:
        Response object: JSON response indicating success or error.
    """
    # Validate quiz title
    title = data.get('title')
    if not title:
        abort(400, description="Quiz title is required!")

    formatted_title = validate_quiz_title(title, storage)

    # Check for existing quiz with the same title
    if storage.get_by_value(Quiz, 'title', formatted_title):
        abort(400, description="Quiz title already exists!")

    # Validate time limit
    time_limit = data.get('time_limit')
    validate_time_limit(time_limit)

    # Validate description
    description = data.get('description')
    if description is not None:
        validate_quiz_description(description)

    # Validate the topic ID (if provided)
    topic_id = data.get('topic_id')
    if topic_id is not None:
        topic_id = validate_quiz_topic_id(topic_id, storage)

    # Create the quiz object
    quiz = Quiz(
        title=formatted_title,
        description=description,
        time_limit=time_limit,
        topic_id=topic_id
    )

    # Save the quiz to the database
    quiz.save()

    return jsonify({
        "message": "Quiz created successfully",
        "quiz": quiz.to_json()
    }), 201


def update_quiz_by_id(data: Dict[str, Any],
                      storage: Any,
                      quiz_id: str) -> tuple:
    """
    Update quiz details by quiz ID.

    Args:
        data (dict): Dictionary containing fields to update.
        storage (object): Storage instance to handle database operations.
        quiz_id (str): The unique identifier of the quiz.

    Returns:
        tuple: A tuple containing a message and the updated quiz data.
    """
    # Fetch the quiz object by ID
    quiz = get_quiz_by_id(quiz_id, storage)
    if not quiz:
        abort(404, description="Quiz not found")

    # Update fields if provided
    if 'title' in data:
        title = data.get('title')
        if not title:
            abort(400, description="Quiz title is required!")
        data['title'] = validate_quiz_title(title, storage)
        if data['title'] != quiz.title and storage.get_by_value(
            Quiz, "title", data['title']
        ):
            abort(400, description="Quiz title already exists!")

    if 'description' in data:
        description = data.get('description')
        validate_quiz_description(description)

    if 'time_limit' in data:
        time_limit = data.get('time_limit')
        validate_time_limit(time_limit)

    if 'topic_id' in data:
        topic_id = data.get('topic_id')
        if topic_id is not None:
            data['topic_id'] = validate_quiz_topic_id(topic_id, storage)

    # Flag to check if any update was made
    updated = False

    for key, value in data.items():
        if key in ['title', 'description', 'time_limit', 'topic_id']:
            if value == getattr(quiz, key):
                continue
            setattr(quiz, key, value)
            updated = True

    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the quiz"
    else:
        message = "Quiz updated successfully"

        # Save updated quiz to the database
        quiz.updated_at = datetime.now(timezone.utc)
        quiz.save()

    return jsonify({
        "message": message,
        "quiz": quiz.to_json()
    }), 200


def validate_quiz_title(title, storage):
    """
    Validate the quiz title.

    Args:
        title (str): The title of the quiz.
        storage (object): Storage instance to handle database operations.

    Returns:
        str: The formatted title if valid.

    Raises:
        abort (400): If the title is invalid.
    """
    if not isinstance(title, str):
        abort(400, description="Quiz title must be a string")

    if title.lower() in {"none", "null", ""}:
        abort(400, description="Quiz title must not be empty or null.")

    if len(title) > 128:
        abort(400, description="Quiz title cannot exceed 128 characters!")

    # Format title for consistency
    formatted_title = format_text_to_title(title)
    if not formatted_title:
        abort(400, description=(
            "Quiz title must include alphabets and "
            "cannot be 'none' or 'null'."
        ))
    return formatted_title


def validate_time_limit(time_limit):
    """
    Validate the quiz time limit.

    Args:
        time_limit (int): The time limit for the quiz.

    Raises:
        abort (400): If the time limit is not a positive integer.
    """
    if not isinstance(time_limit, int) or time_limit <= 0:
        abort(400, description=(
            "A valid time limit (positive integer) "
            "is required!"
        ))


def validate_quiz_description(description):
    """
    Validate the quiz description.

    Args:
        description (str): The description of the quiz.

    Raises:
        abort (400): If the description is invalid.
    """
    if not isinstance(description, str):
        abort(400, description="Quiz description must be a string")
    if len(description) > 255:
        abort(400,
              description="Quiz description cannot exceed 255 characters!")


def validate_quiz_topic_id(topic_id, storage):
    """
    Validate the quiz topic ID.

    Args:
        topic_id (str): The topic ID for the quiz.
        storage (object): Storage instance to handle database operations.

    Returns:
        str: The valid topic ID.

    Raises:
        abort (404): If the topic is not found.
    """
    if not isinstance(topic_id, str):
        abort(400, description="Topic ID must be a string")
    if topic_id.lower() in {"none", "null", ""}:
        topic_id = None
    else:
        topic = get_topic_by_id(topic_id, storage)
        if not topic:
            abort(404, description="Topic not found")
    return topic_id
