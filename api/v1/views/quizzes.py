#!/usr/bin/env python3
"""
This module handles routes for managing quizzes in the QuizyPal application.

Routes:
    - GET /api/v1/quizzes: Retrieve all quizzes.
    - GET /api/v1/quizzes/<quiz_id>: Retrieve a quiz by its ID.
    - GET /api/v1/quizzes/title/<quiz_title>: Retrieve a quiz by its title.
    - DELETE /api/v1/quizzes/<quiz_id>: Delete a quiz (admin-only).
    - POST /api/v1/quizzes: Create a new quiz (admin-only).
    - PUT /api/v1/quizzes/<quiz_id>: Update a quiz (admin-only).
    - GET /api/v1/quizzes/topic/<topic_id>: Fetch quizzes by topic ID.
    - GET /api/v1/quizzes/topic_name/<name>: Fetch quizzes by topic name.
    - GET /api/v1/quizzes/<quiz_id>/details: Get a quiz with questions and choices.

Dependencies:
    - Flask for routing.
    - Flask-JWT-Extended for authentication.
    - Models: Quiz, Topic.
    - Services: Auth and quiz utilities.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models.quiz import Quiz
from models import storage
from flask_jwt_extended import jwt_required
from api.v1.services.auth_service import admin_required
from api.v1.utils.string_utils import format_text_to_title
from api.v1.services.quiz_service import add_quiz, get_all_quizzes, get_quiz_by_id, get_quiz_by_title_helper, validate_quiz_title, validate_quiz_description, validate_time_limit, validate_quiz_topic_id, update_quiz_by_id, get_questions_for_quiz
from api.v1.utils.pagination_utils import get_paginated_data
from models.topic import Topic
from models.choice import Choice
from models.question import Question
from api.v1.services.result_service import add_result, get_result_by_id
from api.v1.services.topic_service import add_topic, get_topic_by_name_helper, get_topic_by_id
from api.v1.services.question_service import add_question, validate_question_text, get_choices_for_question, update_question_by_id
from api.v1.services.choice_service import validate_choice_text, validate_correct_answers, ensure_no_answer_choice, validate_is_correct, update_choice_by_id, add_choices
from datetime import datetime, timezone, timedelta
from flask.typing import ResponseReturnValue
from typing import Dict, Any, Tuple, List
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.quiz import Quiz
from models.result import Result, QuizSessionStatus
from models.user import User


@app_views.route('/quizzes', methods=['GET'], strict_slashes=False)
def get_quizzes() -> ResponseReturnValue:
    """
    GET /api/v1/quizzes

    Get all quizzes with pagination.
    This route retrieves quizzes from the storage and returns them
    with pagination metadata.

    Query Parameters:
        - page (int): The page number (default is 1).
        - page_size (int): The number of items per page (default is 10).
    
    Returns:
        A JSON object containing:
        - page: Current page number.
        - page_size: Number of items in the current page.
        - data: List of quizzes for the current page.
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

    # Use the helper function to get paginated quizzes
    result = get_paginated_data(storage, Quiz, page=page, page_size=page_size)

    # Change the "data" key to "quizzes"
    result["quizzes"] = result.pop("data")
    return jsonify(result)


@app_views.route('/quizzes/<quiz_id>', methods=['GET'], strict_slashes=False)
def get_quiz(quiz_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/quizzes/:id

    Get a specific quiz by their quiz_id.
    This route retrieves a single quiz based on the provided quiz_id.
    
    Parameters:
        quiz_id (str): The unique identifier for the quiz.
        
    Return:
        A JSON object representing the quiz if found.
        If the quiz is not found, returns a 404 error.
    """
    # Call the helper function `get_quiz_by_id` to retrieve the quiz by its ID.
    quiz = get_quiz_by_id(quiz_id, storage)

    # If the quiz is not found, abort with a 404 error and message "quiz not found".
    if quiz is None:
        abort(404, description="Quiz not found")

    # If the quiz is found, return it as a JSON object.
    return jsonify(quiz.to_json())


@app_views.route('/quizzes/title', methods=['GET'], strict_slashes=False)
def handle_no_title() -> ResponseReturnValue:
    """Error handler for /quizzes/title route"""
    abort(400, description="Quiz title is required")


@app_views.route('/quizzes/title/<quiz_title>', methods=['GET'], strict_slashes=False)
def get_quiz_by_title(quiz_title: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/quizzes/:quiz_title

    Get a specific quiz by their title.
    This route retrieves a single quiz based on the provided quiz_title.

    Parameters:
        quiz_title (str): The title of the quiz.
        
    Return:
        A JSON object representing the quiz if found.
        If the quiz is not found, returns a 404 error.
    """
    # Call the helper function to get the quiz by title
    quiz = get_quiz_by_title_helper(quiz_title, storage)

    if quiz is None:
        abort(404, description="Quiz not found")

    return jsonify(quiz.to_json())


@app_views.route('/quizzes/<quiz_id>/questions', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_quiz_questions(quiz_id: str = None) -> ResponseReturnValue:
    """
    Get all questions for a specific quiz or a specific question based on its ID,
    ensuring the user has an in-progress quiz for the specified quiz.

    Args:
        quiz_id: The ID of the quiz whose questions are to be retrieved.

    Returns:
        A JSON response containing either a list of questions (if no question_id is provided)
        or a single question (if question_id is provided).
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]


    # Retrieve query parameter for specific question_id (if provided)
    question_id = request.args.get('question_id')

    # Check if the user has an in-progress result for the specified quiz
    result = storage.filter_by(Result, quiz_id=quiz_id, user_id=user_id, status="in-progress")
    if not result and current_user_role != "admin":
        abort(403, description="You do not have an in-progress quiz for the specified quiz.")

    if question_id:
        # Fetch the specific question if question_id is provided
        question = storage.get(Question, question_id)
        if not question or question.quiz_id != quiz_id:
            abort(404, description="Question not found or does not belong to the specified quiz.")

        # Return the specific question
        return jsonify(question.to_json()), 200

    # Fetch all questions for the quiz and sort them by order_number
    questions = storage.filter_by(Question, quiz_id=quiz_id)
    questions.sort(key=lambda q: q.order_number)

    # Convert questions to JSON format
    question_list = [question.to_json() for question in questions]

    return jsonify(question_list), 200


@app_views.route('/quizzes/<quiz_id>/questions-and-choices', methods=['GET'], strict_slashes=False)
@jwt_required()
def get_quiz_questions_and_choices(quiz_id: str = None) -> ResponseReturnValue:
    """
    Get all questions and their choices for a specific quiz, or a single question with its choices
    if question_id is provided, ensuring the user has an in-progress quiz for the specified quiz.

    Args:
        quiz_id: The ID of the quiz.
    
    Query Parameters:
        question_id: (Optional) The ID of a specific question to retrieve.

    Returns:
        A JSON response containing either:
        - A single question and its choices (if question_id is provided).
        - All questions and their choices for the quiz (if question_id is not provided).
    """
    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]

    # Retrieve query parameter for specific question_id (if provided)
    question_id = request.args.get('question_id')

    # Check if the user has an in-progress result for the specified quiz
    result = storage.filter_by(Result, quiz_id=quiz_id, user_id=user_id, status="in-progress")
    if not result and current_user_role != "admin":
        abort(403, description="You do not have an in-progress quiz for the specified quiz.")

    if question_id:
        # Fetch the specific question
        question = storage.get(Question, question_id)
        if not question or question.quiz_id != quiz_id:
            abort(404, description="Question not found or does not belong to the specified quiz.")

        # Fetch and include choices for the specific question
        choices = get_choices_for_question(question_id, storage)
        question_data = question.to_json()
        question_data['choices'] = choices

        return jsonify(question_data), 200

    # Fetch all questions for the quiz
    question_list = get_questions_for_quiz(quiz_id, storage)

    for question in question_list:
        # Fetch and include choices for each question
        choices = get_choices_for_question(question['id'], storage)
        question['choices'] = choices

    return jsonify(question_list), 200



@app_views.route('/quizzes/<quiz_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_quiz(quiz_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/quizzes/:id

    Delete a specific quiz by their quiz_id.
    This route deletes a quiz after verifying the identity of the quiz making the request.
    
    Parameters:
        quiz_id (str): The unique identifier of the quiz to be deleted.
        
    Return:
        A JSON response indicating whether the deletion was successful.
        If the quiz does not exist or the current quiz is unauthorized, it returns an error.
    """
    quiz = get_quiz_by_id(quiz_id, storage)

    if quiz is None:
        abort(404, description="Quiz not found")

    # Delete the quiz
    quiz.delete()
    storage.save()

    return jsonify({"message": "Quiz successfully deleted."}), 200


@app_views.route('/quizzes', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_quiz() -> ResponseReturnValue:
    """
    POST /api/v1/quizzes/

    Create a new quiz.
    This route allows admins to create a new quiz by accepting the necessary information 
    in a JSON payload. The input is validated, and duplicate quizzes or invalid data are rejected.

    JSON body:
        - title (str): The title of the quiz (must be unique and not empty).
        - description (Optional[str]): A brief description of the quiz.
        - time_limit (int): The time limit for the quiz in seconds.
        - topic_id (Optional[str]): The ID of the topic associated with this quiz (can be empty).

    Return:
        A JSON response with the created quiz object or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate quiz creation to the helper function
    return add_quiz(data, storage)


@app_views.route('/quizzes/<quiz_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_quiz(quiz_id: str = None) -> ResponseReturnValue:
    """
    PUT /api/v1/quizzes/<quiz_id>

    Update an existing quiz.

    This route allows admins to update an existing quiz by providing updated 
    information in a JSON payload. Validations ensure updates are consistent with 
    the business rules.

    URL Params:
        - quiz_id (str): The ID of the quiz to update.

    JSON body:
        - title (Optional[str]): The new title of the quiz.
        - description (Optional[str]): The new description of the quiz.
        - time_limit (Optional[int]): The new time limit for the quiz in seconds.
        - topic_id (Optional[str]): The new topic ID associated with the quiz.

    Returns:
        A JSON response with the updated quiz object or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate quiz creation to the helper function
    return update_quiz_by_id(data, storage, quiz_id)


@app_views.route('/quizzes/complete', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_complete_quiz() -> ResponseReturnValue:
    """
    Create a complete quiz with optional topic, quiz details, questions, and choices.

    Request JSON Body:
        {
            "topic": { "name": "Topic Name", "parent_id": "Parent Topic ID (optional)" },
            "quiz": { "title": "Quiz Title", "description": "Quiz Description", "time_limit": 12 },
            "questions": [
                {
                    "question_text": "Question 1 text",
                    "allow_multiple_answers": false,
                    "choices": [
                        { "choice_text": "Choice 1", "is_correct": false },
                        { "choice_text": "Choice 2", "is_correct": true }
                    ]
                }
            ]
        }

    Returns:
        JSON response with the created quiz and associated entities.
    """
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()
    topics = data.get('topic', [])
    quiz_data = data.get('quiz')
    questions_data = data.get('questions', [])

    # Validate Quiz data
    if not quiz_data or 'title' not in quiz_data or 'time_limit' not in quiz_data:
        abort(400, description="Quiz details must include 'title' and 'time_limit'")

    # Create or retrieve topics in order
    last_topic_id = None  # This will hold the parent ID for the next topic
    for index, topic_name in enumerate(topics):
        topic = get_topic_by_name_helper(topic_name, storage)
        
        if topic:  # Topic exists in the database
            # Use the existing topic's parent_id as the parent for the current topic
            if index != 0 and topic.parent_id != last_topic_id:
                topic.parent_id = last_topic_id
                topic.updated_at = datetime.now(timezone.utc)
                topic.save()

            last_topic_id = topic.id
        else:  # Topic does not exist in the database
            # Set the parent_id based on whether it's the first topic or not
            parent_id = None if index == 0 else last_topic_id

            # Add or update the topic with the calculated parent_id
            topic_data = {
                'name': topic_name,
                'parent_id': parent_id
            }
            topic_response, _ = add_topic(topic_data, storage)

            # Update the last_topic_id for the next iteration
            last_topic_id = topic_response.get_json().get('topic')['id']

    # Validate time_limit
    time_limit = quiz_data.get('time_limit')
    validate_time_limit(time_limit)
    
    # Check if the quiz title already exists
    existing_quiz = get_quiz_by_title_helper(quiz_data['title'], storage)

    if existing_quiz:
        quiz_data['topic_id'] = last_topic_id
        quiz_response, _ = update_quiz_by_id(quiz_data, storage, existing_quiz.id)
        quiz = quiz_response.get_json().get('quiz')
        print(quiz)
    else:
        # Create the Quiz
        quiz_data['topic_id'] = last_topic_id
        quiz_response, _ = add_quiz(quiz_data, storage)
        quiz = quiz_response.get_json().get('quiz')
        print(quiz)

    # Add or Retrieve Questions
    for question_data in questions_data:
        question_text = question_data.get('question_text')
        question_text = validate_question_text(question_text)
        
        # Check for existing question in the same quiz
        existing_question = storage.filter_by(Question, quiz_id=quiz['id'], question_text=question_text)
        if existing_question:
            question_response, _ = update_question_by_id(question_data, storage, existing_question[0].id)
            question = question_response.get_json().get('question')
        else:
            # Create the question
            question_response, _ = add_question({
                'quiz_id': quiz['id'],
                'question_text': question_text,
                'allow_multiple_answers': question_data.get('allow_multiple_answers', False)
            }, storage)
            question = question_response.get_json().get('question')

        # Add Choices to the Question
        choices_data = question_data.get('choices', [])
        # Retrieving existing choices for the question if any
        existing_choices = storage.filter_by(Choice, question_id=question['id'])

        # Collect existing choice texts and choices themselves
        existing_choice_texts = [choice.choice_text for choice in existing_choices]
        existing_choices_dict = {choice.choice_text: choice for choice in existing_choices}

        existing_choices_data = []
        new_choices_data = []

        # Process and classify choices as new or existing
        for choice in choices_data:
            is_correct = choice.get('is_correct', False)
            choice['choice_text'] = validate_choice_text(choice.get('choice_text'))
            validate_is_correct(is_correct)
            choice['is_correct'] = is_correct
            if choice['choice_text'] in existing_choice_texts:
                existing_choices_data.append(choice)
            else:
                new_choices_data.append(choice)

        # Add new choices
        if new_choices_data:
            data = {
                "question_id": question['id'],
                "choices": new_choices_data}

            _, _ = add_choices(data, storage)

        # Update existing choices
        for existing_choice_data in existing_choices_data:
            choice = existing_choices_dict[existing_choice_data['choice_text']]  # Get choice directly from dictionary
            _, _ = update_choice_by_id(existing_choice_data, storage, choice.id)

    return jsonify({
        'message': 'Complete quiz created successfully',
        'quiz': quiz,
    }), 201


@app_views.route('/start-quiz', methods=['POST'], strict_slashes=False)
@jwt_required()
def start_quiz() -> ResponseReturnValue:
    """
    Start a quiz attempt for a user.

    This route initializes a new quiz session for the user, checks if the quiz exists,
    ensures the user hasn't exceeded the maximum number of attempts for the quiz on the same day,
    and ensures the user doesn't already have another quiz in progress.

    Returns:
        Tuple: A JSON response with the details of the quiz attempt and an HTTP status code.
            - result_id (str): The ID of the quiz result record.
            - quiz_id (str): The ID of the quiz being attempted.
            - time_limit (int): The time limit for the quiz (in minutes).
            - start_time (str): The timestamp when the quiz attempt started.
            - status (str): The current status of the quiz attempt (in_progress).

    Raises:
        404: If the quiz is not found in the database.
        400: If the user has exceeded the maximum number of attempts for the quiz today
             or already has another quiz in progress.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    # Get the user ID from the JWT token
    user_id = get_jwt_identity()
    current_user_role = get_jwt()["role"]


    # Get the quiz ID from the request body
    quiz_id = request.json.get('quiz_id')
    if not quiz_id:
        abort(400, description="Quiz ID is required.")

    # Fetch the quiz from the database
    quiz = get_quiz_by_id(quiz_id, storage)
    if not quiz:
        abort(404, description="Quiz not found")

    user = storage.get(User, user_id)
    if not user:
        abort(404, description="User not found")

    # Check if the user already has an in-progress quiz
    in_progress_quiz = storage.filter_by(Result, user_id=user_id, status="in-progress")
    if in_progress_quiz and current_user_role != "admin":
        abort(400, description="You already have an in-progress quiz. Please complete it before starting another quiz.")

    # Check the number of attempts the user has made today for this quiz
    attempts_today = Result.get_attempt_number(storage, user_id, quiz_id, filter_by_date=True)
    # Check the number of attempts the user has made today for this quiz
    """attempts_today = Result.get_attempt_number(
        storage=storage,  # Pass the storage instance
        user_id=user_id,
        quiz_id=quiz_id,
        filter_by_date=True  # Only count today's attempts
    )"""
    print(f"Total attempts today: {attempts_today}")
    max_attempts_per_day = 3  # Set your max attempts per day limit

    if attempts_today >= max_attempts_per_day and current_user_role != "admin":
        abort(400, description=f"You've reached the maximum number of attempts ({max_attempts_per_day}) for today.")

    # Create a result record for this quiz attempt
    data = {
        "user_id": user_id,
        "quiz_id": quiz_id
    }

    result, _ = add_result(data, storage)
    result_data = result.get_json()
    result_id = result_data.get('id')
    status = result_data.get('status')
    start_time = result_data.get('start_time')
    #start_time_str = datetime.fromisoformat(start_time_str)  # Convert string to datetime object
    #start_time_iso = start_time.isoformat()  # Now call isoformat()
    # start_time = result_data.get('start_time').isoformat()
    # last_topic_id = topic_response.get_json().get('topic')['id']
    """result = Result(
        user_id=user_id,
        quiz_id=quiz_id,
        status=QuizSessionStatus.IN_PROGRESS.value,  # Use enum value explicitly
        start_time=datetime.now(timezone.utc),
    )
    storage.new(result)
    storage.save()"""

    # Include the time limit in the response
    response = {
        "result_id": result_id,
        "quiz_id": quiz.id,
        "time_limit": quiz.time_limit,  # Add the time limit (in minutes)
        "start_time": start_time,  # Format start time as ISO string
        "status": status,  # The status of the quiz (initially 'in-progress')
    }

    # Return the response with status code 201 (Created)
    return jsonify(response), 201


@app_views.route('/stop-quiz', methods=['POST'], strict_slashes=False)
@jwt_required()
def stop_quiz():
    """
    End the quiz, update the necessary result details (minus score calculations).
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    # Get the current time
    current_time = datetime.now(timezone.utc)  # Use time zone-aware current time
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    user_id = get_jwt_identity()  # Get the user ID from the JWT token
    current_user_role = get_jwt()["role"]
    result_id = request.json.get('result_id')

    # Fetch the result object
    print(f"result_id: {result_id}")
    result = get_result_by_id(result_id, storage)
    if not result:
        abort(404, description="Result not found")

    # Check if the user ID from the JWT matches the user ID associated with the result
    if result.user_id != user_id and current_user_role != "admin":
        abort(403, description="You are not authorized to stop this quiz.")

    # Check if the quiz status is in-progress
    if result.status not in ["in-progress"] and current_user_role != "admin":
        abort(400, description="Quiz has already been completed or timed out.")

    # Fetch the associated quiz from the result object (no need for another storage call)
    quiz = result.quiz
    print(f"result.quiz: {result.quiz}")
    if not quiz:
        abort(404, description="Quiz not found")

    # Ensure result.start_time is timezone-aware (if it isn't already)
    if result.start_time.tzinfo is None:
        result.start_time = result.start_time.replace(tzinfo=timezone.utc)

    # Check if the quiz time has expired
    time_limit_expired = current_time > (result.start_time + timedelta(minutes=quiz.time_limit))


    # Determine the result status
    if time_limit_expired:
        result.status = QuizSessionStatus.TIMED_OUT
    else:
        result.status = QuizSessionStatus.COMPLETED

    # Calculate completion time (time difference between submitted_at and start_time)
    completion_time_seconds = (current_time - result.start_time).total_seconds()
    completion_time_minutes = round(completion_time_seconds / 60)

    # Update the result object to mark the quiz as ended
    result.submitted_at = current_time  # Timestamp when the quiz is stopped
    result.end_time = datetime.now(timezone.utc)  # End time of the quiz
    result.time_taken = completion_time_seconds  # Total time taken in seconds
    result.updated_at = datetime.now(timezone.utc)  # Updated timestamp

    # Save the updated result
    storage.save()
    print(f"result.start_time: {result.start_time}")
    print(f"current_time: {current_time}")
    print(f"{current_time} - {result.start_time} = {current_time - result.start_time}")
    print(f"completion_time_seconds: {completion_time_seconds}")

    # Final response indicating the quiz has been stopped
    return jsonify({
        "quiz_title": quiz.title,
        "result_id": result.id,
        "status": result.status.value,
        "time_limit": f"{quiz.time_limit} minutes",
        "completion_time": f"{completion_time_minutes} minutes",  # Display time taken
        "date": result.created_at.strftime("%d-%m-%y")
    }), 200
