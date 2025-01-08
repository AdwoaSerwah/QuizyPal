#!/usr/bin/env python3
from api.v1.views import app_views
from flask import abort, jsonify, request
from models.topic import Topic
from models import storage
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from flasgger.utils import swag_from
from api.v1.services.auth_service import admin_required
from api.v1.utils.string_utils import format_text_to_title
from api.v1.services.topic_service import add_topic, get_all_topics, get_topic_by_name_helper, get_topic_by_id


@app_views.route('/topics', methods=['GET'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/topic/get_topics.yml')
def get_topics() -> str:
    """
    GET /api/v1/topics

    Get all topics.
    This route retrieves all topic records from the storage and
    returns them as a JSON list.
    
    Return:
        A JSON array containing all topic objects.
        If no topics are found, it returns an empty list.
    """
    # Using the helper function here
    all_topics = get_all_topics(storage)
    return jsonify(all_topics)


@app_views.route('/topics/<topic_id>', methods=['GET'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/topic/get_topic.yml', methods=['GET'])
def get_topic(topic_id: str = None) -> str:
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
    # Check if topic_id is provided. If not, return 404 with a relevant message.
    if topic_id is None:
        abort(404, description="Topic ID is required")

    # Call the helper function `get_topic_by_id` to retrieve the topic by its ID.
    topic = get_topic_by_id(topic_id, storage)

    # If the topic is found, return it as a JSON object.
    return jsonify(topic)


@app_views.route('/topics/name/<topic_name>', methods=['GET'], strict_slashes=False)
@jwt_required()
@swag_from('documentation/topic/get_topic_by_name.yml', methods=['GET'])
def get_topic_by_name(topic_name: str = None) -> str:
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
    if not topic_name:
        abort(404, description="Topic name is required")

    # Call the helper function to get the topic by name
    topic = get_topic_by_name_helper(topic_name, storage)

    return jsonify(topic)


@app_views.route('/topics/<topic_id>', methods=['DELETE'], strict_slashes=False)
@jwt_required()
@admin_required
@swag_from('documentation/topic/delete_topic.yml', methods=['DELETE'])
def delete_topic(topic_id: str = None) -> str:
    """
    DELETE /api/v1/topics/:id

    Delete a specific topic by their topic_id.
    This route deletes a topic after verifying the identity of the topic making the request.
    
    Parameters:
        topic_id (str): The unique identifier of the topic to be deleted.
        
    Return:
        A JSON response indicating whether the deletion was successful.
        If the topic does not exist or the current topic is unauthorized, it returns an error.
    """
    if topic_id is None:
        abort(404, description="Topic ID is required")

    topic = storage.get(Topic, topic_id)
    if topic is None:
        abort(404, description="Topic not found")

    # Delete the topic
    topic.delete()
    storage.save()

    return jsonify({"message": "Topic successfully deleted."}), 200


@app_views.route('/topics', methods=['POST'], strict_slashes=False)
@jwt_required()
@admin_required
@swag_from('documentation/topic/create_topic.yml', methods=['POST'])
def create_topic() -> str:
    """ 
    POST /api/v1/topics/

    Create a new topic.
    This route allows the creation of a new topic by accepting the necessary information 
    in a JSON payload. The input is validated, and duplicate topics or invalid data are rejected.

    JSON body:
        - name (str): The name of the topic.
        - parent_id (Optional[int]): The ID of the parent topic

    Return:
        A JSON response with the created topic object, or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        return jsonify({'message': 'No data provided!'}), 400

    data = request.get_json()

    # Delegate topic creation to the helper function
    return add_topic(data, storage)


@app_views.route('/topics/<topic_id>', methods=['PUT'], strict_slashes=False)
@jwt_required()
@admin_required
@swag_from('documentation/topic/update_topic.yml', methods=['PUT'])
def update_topic(topic_id: str) -> str:
    """ 
    PUT /api/v1/topics/:id

    Update an existing topic.
    This route allows the update of an existing topic by accepting the necessary 
    information in a JSON payload. The input is validated, and duplicate topics 
    or invalid data are rejected.

    JSON body:
        - name (str): The name of the topic.
        - parent_id (Optional[int]): The ID of the parent topic

    Return:
        A JSON response with the updated topic object, or error messages for invalid input.
    """
    # Ensure request data is JSON
    if not request.get_json():
        return jsonify({'message': 'No data provided!'}), 400

    data = request.get_json()

    # Convert "null" or "None" strings to None for parent_id
    parent_id = data.get('parent_id')
    if parent_id and str(parent_id).lower() in ["none", "null"]:
        data["parent_id"] = None
        parent_id = None

    # Check if the topic exists
    topic = storage.get(Topic, topic_id)
    if topic is None:
        abort(404, description="Topic not found")

    if parent_id is not None:
        parent = storage.get_by_value(Topic, "parent_id", parent_id)
        if not parent:
            abort(404, description="Parent not found")
    
    # Validate fields (attempt to convert to string and max length of 128)
    value = data.get('name')
    try:
        # Attempt to convert to string
        if value:
            value = str(value)
            # Check for max length of 128 characters for topic name
            if len(value) > 128:
                return jsonify(
                    {'message': 'Topic name cannot be longer than 128 characters.'}
                    ), 400
    except (ValueError, TypeError):
        return jsonify(
            {'message': 'Topic name must be a string.'}), 400

    # Update the field with the converted string value
    if value:
        formatted_text = format_text_to_title(value)
        
        data['name'] = formatted_text

    # Check for max length of 128 characters
    if parent_id is not None:
        if len(parent_id) > 60:
            return jsonify(
                {'message': 'Parent ID cannot be longer than 128 characters.'}
                ), 400

    # Check for existing topic name
    name = data.get('name')
    if storage.get_by_value(Topic, "name", name):
        return jsonify({'message': 'Topic name already exists!'}), 400

    # Update the topic object with new data
    for key, value in data.items():
        setattr(topic, key, value)

    topic.save()

    return jsonify({
        "message": "Topic updated successfully",
        "topic": topic.to_json()
    }), 200