#!/usr/bin/env python3
"""
This module provides functions for managing choices in a quiz system.

Functions include:
- `get_all_choices`: Retrieves all available choices from the database.

- `get_choice_by_id`: Fetches a specific choice by its ID.

- `add_choices`: Adds multiple choices for a given question,
                 including validation and duplicate checks.

- `update_choice_by_id`: Updates a choice's information by its ID, with
                         validation to ensure correct answers are maintained.

- `validate_correct_answers`: Validates the number of correct answers based on
                              the settings of the associated question.

- `validate_choice_text`: Validates the format of the choice text to ensure
                          it's a non-empty string and within the character
                          limit.

- `validate_is_correct`: Ensures that the `is_correct` flag is a boolean.

- `ensure_no_answer_choice`: Ensures a default "no_answer" choice exists
                             for the given question.

The module interacts with a storage instance to handle database operations
for the `Choice` model and relies on the `Question` model for validation
where needed. It uses Flask's `abort` method to handle errors and returns
responses in JSON format.
"""

from typing import Dict, Tuple, Any, List, Optional
from flask import jsonify, abort
from models.choice import Choice
from api.v1.services.question_service import get_question_by_id
from datetime import datetime, timezone


def get_all_choices(storage) -> List[Dict]:
    """
    Helper function to get all Choices.

    Args:
        storage (object): Storage instance to handle database operations.

    Returns:
        List of dicts: A list of all Choices in JSON serializable format.
    """
    all_choices = [choice.to_json() for choice in storage.all(Choice).values()]
    return all_choices


def get_choice_by_id(choice_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a choice by its ID.

    Args:
        choice_id (str): The unique identifier for the choice.
        storage (object): Storage instance to handle database operations.

    Returns:
        dict: A dictionary representing the choice if found.
        None: If the choice is not found.
    """
    if not choice_id:
        abort(400, description="Choice ID is required")

    if not isinstance(choice_id, str):
        abort(400, description="Choice ID must be a string")
    choice = storage.get(Choice, choice_id)

    return choice


def add_choices(data: List[Dict[str, Any]], storage) -> Tuple:
    """
    Add multiple choices for a question.

    Args:
        data (list): A list of dictionaries, each representing a choice.
            Expected keys:
            - question_id (str): The ID of the question.
            - choice_text (str): The text of the choice.
            - is_correct (bool): Whether the choice is the correct answer.
        storage (object): Storage instance to handle database operations.

    Returns:
        Tuple: Response object and HTTP status code.
    """
    question_id = data.get('question_id')
    # Validate and check if question exists
    question = get_question_by_id(question_id, storage)
    if not question:
        abort(404, description="Question not found")

    # Retrieve allow_multiple_answers from question object
    allow_multiple_answers = question.allow_multiple_answers

    choices_data = data.get('choices', [])

    choices = []
    choice_texts = []
    for choice in choices_data:
        is_correct = choice.get('is_correct', False)
        choice['choice_text'] = validate_choice_text(choice.get('choice_text'))
        validate_is_correct(is_correct)
        choice['is_correct'] = is_correct
        choices.append(choice)
        choice_texts.append(choice['choice_text'])

    # choice_texts = [choice.get('choice_text') for choice in choices_data]
    # choices = [choice for choice in choices_data]

    # Retrieving existing choices for the question if any
    existing_choices = storage.filter_by(Choice, question_id=question_id)

    # Collect existing choice texts
    existing_choice_texts = [choice.choice_text for choice in existing_choices]

    # Combine existing and new choice texts
    all_choice_texts = existing_choice_texts + choice_texts

    # Check for any duplicate texts before entering the loop
    for choice_text in choice_texts:
        if choice_text in existing_choice_texts:
            abort(400, description=(
                f"The choice '{choice_text}' already exists in this question!"
            ))

    # Add existing choices to the new choices list (before validation)
    all_choices = existing_choices + choices

    # Validate the correct answers based on question settings
    validate_correct_answers(all_choices,
                             False,
                             allow_multiple_answers,
                             question.question_text)

    added_choices = []
    if all_choice_texts and "no_answer" not in all_choice_texts:
        no_answer_choice = ensure_no_answer_choice(question_id, storage)
        added_choices.append(no_answer_choice)

    for choice_data in choices_data:
        # Get the next order number for the choice
        order_number = Choice.get_next_order_number(storage, question_id)

        # Create and save the choice
        new_choice = Choice(
            question_id=question_id,
            choice_text=choice_data['choice_text'],
            is_correct=choice_data['is_correct'],
            order_number=order_number
        )
        new_choice.save()
        added_choices.append(new_choice.to_json())

    return jsonify({
        'message': 'Choices added successfully',
        'choices': added_choices
    }), 201


def update_choice_by_id(data: Dict[str, Any],
                        storage: Any,
                        choice_id: str) -> tuple:
    """
    Updates a choice in the database by its ID.

    Args:
        data (dict): A dictionary containing the fields to update.
        storage (object): Storage instance to handle database operations.
        choice_id (str): The ID of the choice to update.

    Returns:
        tuple: A JSON response containing a message and the updated choice.
    """
    # Fetch the choice object by ID
    choice = get_choice_by_id(choice_id, storage)
    if not choice:
        abort(404, description="Choice not found")
    if choice.choice_text == "no_answer":
        abort(400, description="The 'no_answer' choice cannot be updated.")

    if 'question_id' in data:
        # Validate question_id
        question_id = data.get('question_id')
    else:
        question_id = choice.question_id

    question = get_question_by_id(question_id, storage)
    if not question:
        abort(404, description="Question not found")

    if 'choice_text' in data:
        # Validate choice_text
        choice_text = data.get('choice_text')
        choice_text = validate_choice_text(choice_text)
        # Check if a choice with the same text already exists in the question
        existing_choice = storage.filter_by(Choice,
                                            question_id=question_id,
                                            choice_text=choice_text)
        if existing_choice and choice.choice_text != choice_text:
            abort(404, description=(
                f"The choice '{choice_text}' "
                "already exists in this question!"
            ))
        data['choice_text'] = choice_text

    if 'is_correct' in data:
        # Validate is_correct
        is_correct = data.get('is_correct', False)
        validate_is_correct(is_correct)
        if is_correct != choice.is_correct:

            # Retrieve allow_multiple_answers from question object
            allow_multiple_answers = question.allow_multiple_answers

            # Retrieving existing choices for the question if any
            existing_choices = storage.filter_by(Choice,
                                                 question_id=question_id)
            # Remove the 'no_answer' choice from the existing_choices
            if existing_choices:
                existing_choices = [
                    ch for ch in existing_choices if ch.id != choice.id
                ]

            # Validate the correct answers based on question settings
            validate_correct_answers(existing_choices,
                                     is_correct,
                                     allow_multiple_answers,
                                     question.question_text)
        data['is_correct'] = is_correct

    # Flag to check if any update was made
    updated = False

    for key, value in data.items():
        if key in ['question_id', 'choice_text', 'is_correct']:
            if value == getattr(choice, key):
                continue
            setattr(choice, key, value)
            updated = True

    # If no update was made, return a message indicating so
    if not updated:
        message = "No changes made to the choice"
    else:
        message = "Quiz updated successfully"

        # Save updated choice to the database
        choice.updated_at = datetime.now(timezone.utc)
        choice.save()

    return jsonify({
        "message": message,
        "choices": choice.to_json()
    }), 200


def validate_correct_answers(existing_choices,
                             is_correct,
                             allow_multiple_answers,
                             question_text):
    """
    Helper function to validate the number of correct answers
    based on the question's settings.

    Args:
        existing_choices (list): List of existing choice objects
                                 or dictionaries.
        is_correct (bool): Whether the new choice is correct.
        allow_multiple_answers (bool): Whether multiple correct
                                       answers are allowed.
        question_text (str): The text of the question to be used
                             in error messages.

    Returns:
        None: Calls abort if validation fails.
    """
    correct_answers_count = 0

    # Iterate through existing_choices to count the correct answers
    for choice in existing_choices:
        if isinstance(choice, dict):
            # If the choice is a dictionary
            if choice.get('is_correct', False):
                correct_answers_count += 1
        elif hasattr(choice, 'is_correct'):
            # If the choice is an object (instance of Choice class)
            if choice.is_correct:
                correct_answers_count += 1
    # Add the new choice's `is_correct` value to the count (if it's correct)
    if is_correct:
        correct_answers_count += 1

    # Validation based on whether multiple answers are allowed
    if allow_multiple_answers:
        if correct_answers_count < 1:
            abort(400, description=(
                f"At least one correct choice is required for question "
                f"'{question_text}'."
            ))
    else:
        if correct_answers_count != 1:
            abort(400, description=(
                f"Exactly one correct choice is required for question "
                f"'{question_text}'."
            ))


def validate_choice_text(choice_text):
    """
    Validates the provided choice text.

    Args:
        choice_text (str): The text of the choice to validate.

    Returns:
        str: The formatted choice text if valid.

    Raises:
        abort: If choice_text is invalid, aborts the request with a 400 status.
    """
    if not choice_text:
        abort(400, description="Choice text is required!")

    if not isinstance(choice_text, str):
        abort(400, description="Choice text must be a string")

    if len(choice_text) > 255:
        abort(400, description="Choice text cannot exceed 255 characters!")

    # Format choice text
    formatted_text = choice_text.strip()
    return formatted_text


def validate_is_correct(is_correct):
    """"""
    if not isinstance(is_correct, bool):
        abort(400, description=(
            f"is_correct '{is_correct}' must be a "
            "boolean value!"
        ))


def ensure_no_answer_choice(question_id: str, storage) -> dict:
    """
    Ensures that a 'no_answer' choice exists for the given question.

    Args:
        question_id (str): The ID of the question.
        storage (object): Storage instance to handle database operations.

    Returns:
        New object
    """
    # Get the next order number for the "no_answer" choice
    order_number = Choice.get_next_order_number(storage, question_id)

    # Create and save the "no_answer" choice
    no_answer_choice = Choice(
        question_id=question_id,
        choice_text="no_answer",
        is_correct=False,
        order_number=order_number
    )
    no_answer_choice.save()
    return no_answer_choice.to_json()
