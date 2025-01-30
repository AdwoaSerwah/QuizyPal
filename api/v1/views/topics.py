#!/usr/bin/env python3
"""
This module contains routes and functionality for managing
topics in the QuizyPal application.

It includes endpoints for:
- Retrieving all topics
- Retrieving a specific topic by its ID or name
- Creating, updating, and deleting topics
- Retrieving quizzes associated with specific topics

The module interacts with the storage system to perform CRUD operations
on topics and their relationships with quizzes. It also supports pagination
for listing topics and requires JWT authentication and admin privileges for
creating, updating, and deleting topics.

Functions:
- get_topics: Retrieves all topics with pagination.
- get_topic: Retrieves a specific topic by its ID.
- handle_no_name: Handles requests to the '/topics/name' route.
- get_topic_by_name: Retrieves a specific topic by its name.
- get_topic_quizzes: Retrieves quizzes associated with a topic and
  its subtopics.
- delete_topic: Deletes a specific topic by its ID.
- create_topic: Creates a new topic.
- update_topic: Updates an existing topic by its ID.
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from models.topic import Topic
from models.quiz import Quiz
from models import storage
from flask_jwt_extended import jwt_required
from api.v1.services.auth_service import admin_required
from api.v1.utils.pagination_utils import get_paginated_data
from api.v1.services.topic_service import add_topic, get_topic_by_name_helper
from api.v1.services.topic_service import get_topic_by_id, validate_parent_id
from api.v1.services.topic_service import validate_topic_name
from datetime import datetime, timezone
from flask.typing import ResponseReturnValue
from typing import List, Dict


@app_views.route('/topics', methods=['GET'], strict_slashes=False)
def get_topics() -> ResponseReturnValue:
    """
    GET /api/v1/topics

    Get all topics.
    This route retrieves all topic records from the storage and
    returns them as a JSON list.

    Return:
        A JSON array containing all topic objects.
        If no topics are found, it returns an empty list.
    """
    # Get query parameters with defaults and validate
    try:
        # Convert query parameters to integers with defaults
        page = int(request.args.get('page', 1))  # Default page is 1
        # Default page_size is 10
        page_size = int(request.args.get('page_size', 10))

        # Ensure both values are positive integers
        if page <= 0 or page_size <= 0:
            raise ValueError

    except (ValueError, TypeError):
        abort(400, description="page and page_size must be positive integers")

    # Use the helper function to get paginated quizzes
    result = get_paginated_data(storage, Topic, page=page, page_size=page_size)

    # Change the "data" key to "quizzes"
    result["topics"] = result.pop("data")
    return jsonify(result)


@app_views.route('/topics/<topic_id>', methods=['GET'], strict_slashes=False)
def get_topic(topic_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/topics/:id

    Get a specific topic by their topic_id.
    This route retrieves a single topic based on the provided topic_id.

    Parameters:
        topic_id (str): The unique identifier for the topic.

    Return:
        A JSON object representing the topic if found.
        If the topic is not found, returns a 404 error.
    """
    # Call the helper function to retrieve the topic by its ID.
    topic = get_topic_by_id(topic_id, storage)

    # If the topic is not found, abort with a 404 error
    if topic is None:
        abort(404, description="Topic not found")
    # If the topic is found, return it as a JSON object.
    return jsonify(topic.to_json())


@app_views.route('/topics/name', methods=['GET'], strict_slashes=False)
def handle_no_name() -> ResponseReturnValue:
    """Error handler for /topics/name route"""
    abort(400, description="Topic name is required")


@app_views.route('/topics/name/<topic_name>',
                 methods=['GET'], strict_slashes=False)
def get_topic_by_name(topic_name: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/topics/:topic_name

    Get a specific topic by their name.
    This route retrieves a single topic based on the provided topic_name.

    Parameters:
        topic_name (str): The name of the topic.

    Return:
        A JSON object representing the topic if found.
        If the topic is not found, returns a 404 error.
    """
    # Call the helper function to get the topic by name
    topic = get_topic_by_name_helper(topic_name, storage)

    if topic is None:
        abort(404, description="Topic not found")

    return jsonify(topic.to_json())


@app_views.route('/topics/<topic_id>/quizzes',
                 methods=['GET'], strict_slashes=False)
def get_topic_quizzes(topic_id: str = None) -> ResponseReturnValue:
    """
    GET /api/v1/quizzes/topic/<topic_id>

    Retrieve all quizzes associated with a specific topic, grouped by the topic
    and its subtopics. Only subtopics with quizzes are included.
    """
    # Check if the topic exists
    if not topic_id:
        abort(400, description="Topic ID is required")
    topic = get_topic_by_id(topic_id, storage)
    if not topic:
        abort(404, description="Topic not found")

    def fetch_quizzes_by_topic(topic: Topic) -> List[Dict]:
        """
        Recursively fetch quizzes grouped by the topic and its subtopics,
        filtering out topics or subtopics without quizzes.
        """
        # Fetch quizzes for the current topic
        topic_quizzes = storage.get_by_value(Quiz, 'topic_id', topic.id)
        quizzes = []
        if topic_quizzes:
            if isinstance(topic_quizzes, Quiz):
                topic_quizzes = [topic_quizzes]
            quizzes = [quiz.to_json() for quiz in topic_quizzes]

        # Recursively fetch subtopics with quizzes
        subtopic_data = []
        for subtopic in topic.subtopics:
            subtopic_quizzes = fetch_quizzes_by_topic(subtopic)
            # Include only if subtopic has quizzes
            if subtopic_quizzes:
                subtopic_data.append(subtopic_quizzes)

        # Include current topic only if it has quizzes
        # or subtopics with quizzes
        if quizzes or subtopic_data:
            return {topic.name: quizzes + subtopic_data}

        return None  # Exclude topics without quizzes

    # Fetch quizzes grouped by topics and subtopics
    all_quizzes_grouped = fetch_quizzes_by_topic(topic)

    # Ensure the response starts with the root topic as the key
    if not all_quizzes_grouped:
        return jsonify({topic.name: []}), 200

    response = {topic.name: all_quizzes_grouped[topic.name]}

    return jsonify(response), 200


@app_views.route('/topics/<topic_id>',
                 methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
def delete_topic(topic_id: str = None) -> ResponseReturnValue:
    """
    DELETE /api/v1/topics/:id

    Delete a specific topic by their topic_id.
    This route deletes a topic after verifying the identity of the
    topic making the request.

    Parameters:
        topic_id (str): The unique identifier of the topic to be deleted.

    Return:
        A JSON response indicating whether the deletion was successful.
        If the topic does not exist or the current topic is unauthorized,
        it returns an error.
    """
    topic = get_topic_by_id(topic_id, storage)
    # If the topic is not found, abort with a 404 error.
    if topic is None:
        abort(404, description="Topic not found")

    # Delete the topic
    topic.delete()
    storage.save()

    return jsonify({"message": "Topic successfully deleted."}), 200


@app_views.route('/topics', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
def create_topic() -> ResponseReturnValue:
    """
    POST /api/v1/topics/

    Create a new topic.
    This route allows the creation of a new topic by accepting
    the necessary information in a JSON payload. The input is
    validated, and duplicate topics or invalid data are rejected.

    JSON body:
        - name (str): The name of the topic.
        - parent_id (Optional[int]): The ID of the parent topic

    Return:
        A JSON response with the created topic object, or error
        messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    # Delegate topic creation to the helper function
    return add_topic(data, storage)


@app_views.route('/topics/<topic_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
def update_topic(topic_id: str = None) -> ResponseReturnValue:
    """
    PUT /api/v1/topics/:id

    Update an existing topic.
    This route allows the update of an existing topic by accepting
    the necessary information in a JSON payload. The input is validated,
    and duplicate topics or invalid data are rejected.

    JSON body:
        - name (str): The name of the topic.
        - parent_id (Optional[int]): The ID of the parent topic

    Return:
        A JSON response with the updated topic object, or error messages
        for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        abort(400, description="No JSON data provided in the request!")

    data = request.get_json()

    topic = get_topic_by_id(topic_id, storage)

    if topic is None:
        abort(404, description="Topic not found")

    # Convert "null" or "None" strings to None for parent_id
    if 'parent_id' in data:
        parent_id = data.get('parent_id')
        if parent_id is not None:
            parent_id = validate_parent_id(parent_id, storage)
        data['parent_id'] = parent_id

    # Validate topic name
    if 'name' in data:
        name = data.get('name')
        data['name'] = validate_topic_name(name)
        if data['name'] != topic.name and storage.get_by_value(
            Topic, "name", data['name']
        ):
            abort(400, description="Topic name already exists!")

    # Update the topic object with new data
    updated = False

    for key, value in data.items():
        if key in ['parent_id', 'name']:
            if value == getattr(topic, key):
                continue
            setattr(topic, key, value)
            updated = True

    if not updated:
        message = "No changes made to the topic"
    else:
        message = "Topic updated successfully"
        topic.updated_at = datetime.now(timezone.utc)
        topic.save()

    return jsonify({
        "message": message,
        "topic": topic.to_json()
    }), 200
