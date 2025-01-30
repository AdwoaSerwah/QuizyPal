#!/usr/bin/env python3
"""
This module provides helper functions for managing quiz questions and choices.

It includes functionality for:
- Retrieving all questions and choices for a specific question.
- Adding and updating questions in a quiz.
- Validating question text and the 'allow_multiple_answers' flag.
- Interfacing with the database through a storage object.

Functions:
- get_all_questions: Retrieves all questions.
- get_question_by_id: Retrieves a question by its ID.
- get_choices_for_question: Fetches choices for a specific question.
- add_question: Adds a new question to a quiz.
- update_question_by_id: Updates an existing question.
- validate_question_text: Validates the text of a question.
- validate_allow_multiple_answers: Validates the 'allow_multiple_answers' flag.
"""
from models.choice import Choice
from models.question import Question
from api.v1.services.quiz_service import get_quiz_by_id
from flask import jsonify, abort
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timezone


def get_all_questions(storage) -> List[Dict]:
    """
    Helper function to get all Questions.

    Args:
        storage (object): Storage instance to handle database operations.

    Returns:
        List of dicts: A list of all Questions in JSON serializable format.
    """
    all_questions = [
        question.to_json()
        for question in storage.all(Question).values()
    ]
    return all_questions


def get_question_by_id(question_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a question by its ID.

    Args:
        question_id (str): The unique identifier for the question.
        storage (object): Storage instance to handle database operations.

    Returns:
        dict: A dictionary representing the question if found.
        None: If the question is not found.
    """
    if not question_id:
        abort(400, description="Question ID is required")

    if not isinstance(question_id, str):
        abort(400, description="Question ID must be a string")
    question = storage.get(Question, question_id)

    return question


def get_choices_for_question(question_id: str, storage: Any) -> List[Choice]:
    """
    Fetch all choices for a specific question.

    Args:
        question_id: The ID of the question.

    Returns:
        A list of Choice objects for the question.
    """
    question = get_question_by_id(question_id, storage)
    if not question:
        abort(404, description="Question not found")

    # Fetch all choices for the question and sort them by order_number
    choices = storage.filter_by(Choice, question_id=question_id)
    choices.sort(key=lambda c: c.order_number)

    # Remove choices with choice_text == 'no_answer'
    choices = [
        choice for choice in choices
        if choice.choice_text != 'no_answer'
    ]

    # Convert the remaining choices to JSON
    choice_list = [choice.to_json() for choice in choices]

    return choice_list


def add_question(data: Dict[str, Any], storage) -> Tuple:
    """
    Helper function to add a question.

    Args:
        data (dict): The data for the new question.
                     Expected keys: 'quiz_id', 'question_text',
                     'allow_multiple_answers'.
        storage (object): Storage instance to handle database operations.

    Returns:
        tuple: JSON response indicating success or error.
    """
    # Validate quiz_id
    quiz_id = data.get('quiz_id')
    quiz = get_quiz_by_id(quiz_id, storage)
    if not quiz:
        abort(404, description="Quiz not found")

    # Validate question_text
    question_text = data.get('question_text')
    question_text = validate_question_text(question_text)
    # Check if a question with the same text already exists in the quiz
    existing_questions = storage.filter_by(Question,
                                           quiz_id=quiz_id,
                                           question_text=question_text)
    if existing_questions:
        abort(404, description=(
            f"The question '{question_text}' already exists in this quiz!"
        ))

    # Validate allow_multiple_answers
    allow_multiple_answers = data.get('allow_multiple_answers', False)
    validate_allow_multiple_answers(allow_multiple_answers)
    # Get the next order number for the question
    order_number = Question.get_next_order_number(storage, quiz_id)

    # Create the question object
    question = Question(
        quiz_id=quiz_id,
        question_text=question_text,
        order_number=order_number,
        allow_multiple_answers=allow_multiple_answers
    )

    # Save the question to the database
    question.save()

    return jsonify({
        "message": "Question created successfully",
        "question": question.to_json()
    }), 201


def update_question_by_id(data: Dict[str, Any],
                          storage: Any,
                          question_id: str) -> tuple:
    """
    Updates a question's details by its ID.

    Args:
        data (dict): Dictionary containing the fields to update.
        storage (object): Storage instance to handle database operations.
        question_id (str): The unique identifier of the question.

    Returns:
        tuple: A tuple containing the response message and
               updated question in JSON format.

    Raises:
        404: If the question or quiz is not found.
        400: If the data is invalid.
    """
    # Fetch the question object by ID
    question = get_question_by_id(question_id, storage)
    if not question:
        abort(404, description="Question not found")

    if 'quiz_id' in data:
        # Validate quiz_id
        quiz_id = data.get('quiz_id')
        quiz = get_quiz_by_id(quiz_id, storage)
        if not quiz:
            abort(404, description="Quiz not found")

    if 'question_text' in data:
        # Validate question_text
        question_text = data.get('question_text')
        question_text = validate_question_text(question_text)
        # Check if a question with the same text already exists in the quiz
        existing_question = storage.filter_by(Question,
                                              quiz_id=question.quiz_id,
                                              question_text=question_text)
        if existing_question and question.question_text != question_text:
            abort(404, description=(
                f"The question '{question_text}' "
                "already exists in this quiz!"
            ))
        data['question_text'] = question_text

    if 'allow_multiple_answers' in data:
        # Validate allow_multiple_answers
        allow_multiple_answers = data.get('allow_multiple_answers', False)
        validate_allow_multiple_answers(allow_multiple_answers)
        data['allow_multiple_answers'] = allow_multiple_answers

    # Flag to check if any update was made
    updated = False

    for key, value in data.items():
        if key in ['quiz_id', 'question_text', 'allow_multiple_answers']:
            if value == getattr(question, key):
                continue
            setattr(question, key, value)
            updated = True

    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the question"
    else:
        message = "Quiz updated successfully"

        # Save updated question to the database
        question.updated_at = datetime.now(timezone.utc)
        question.save()

    return jsonify({
        "message": message,
        "question": question.to_json()
    }), 200


def validate_question_text(question_text):
    """
    Validates the question text.

    Args:
        question_text (str): The text of the question.

    Returns:
        str: The validated and formatted question text.

    Raises:
        400: If the question text is invalid
            (empty, null, not a string, or exceeds length).
    """
    if not question_text:
        abort(400, description="Question text is required!")

    if not isinstance(question_text, str):
        abort(400, description="Question text must be a string")

    if question_text.lower() in {"none", "null", ""}:
        abort(400, description="Question text must not be empty or null.")

    if len(question_text) > 255:
        abort(400, description="Question text cannot exceed 255 characters!")

    question_text = question_text.strip().capitalize()
    return question_text


def validate_allow_multiple_answers(allow_multiple_answers):
    """
    Validates the allow_multiple_answers field.

    Args:
        allow_multiple_answers (bool): The flag indicating
                                       if multiple answers are allowed.

    Raises:
        400: If the value is not a boolean.
    """
    if not isinstance(allow_multiple_answers, bool):
        abort(400,
              description="allow_multiple_answers must be a boolean value!")
