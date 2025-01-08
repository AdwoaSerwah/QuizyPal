#!/usr/bin/env python3
"""
Topic Service Module

This module provides helper functions for managing topics, such as adding a new topic 
with input validation, formatting, and database interaction.

Functions:
    - add_topic: Validates input data, ensures topic uniqueness, and saves topics to the database.

Dependencies:
    - models.topic.Topic: The Topic model.
    - flask: For JSON responses and error handling.
    - api.v1.utils.string_utils: For text formatting utilities.
"""
from models.topic import Topic
from flask import jsonify, abort
from api.v1.utils.string_utils import format_text_to_title
from models.topic import Topic
from typing import List, Dict, Any, Optional


def get_all_topics(storage) -> List[Dict]:
    """
    Helper function to get all topics.

    Args:
        storage (object): Storage instance to handle database operations.
    
    Returns:
        List of dicts: A list of all topics in JSON serializable format.
    """
    all_topics = [topic.to_json() for topic in storage.all(Topic).values()]
    return all_topics


def get_topic_by_id(topic_id: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a topic by its ID.

    Args:
        topic_id (str): The unique identifier for the topic.
        storage (object): Storage instance to handle database operations.
    
    Returns:
        dict: A dictionary representing the topic if found.
        None: If the topic is not found.
    """
    if not topic_id:
        abort(404, description="Topic ID is required")

    topic = storage.get(Topic, topic_id)

    # If the topic is not found, abort with a 404 error and message "Topic not found".
    if topic is None:
        abort(404, description="Topic not found")

    return topic.to_json()


def get_topic_by_name_helper(topic_name: str, storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a topic by its name.

    Args:
        topic_name (str): The name of the topic.
        storage (object): Storage instance to handle database operations.
    
    Returns:
        dict: A dictionary representing the topic if found.
        None: If the topic is not found.
    """
    if not topic_name:
        abort(404, description="Topic name is required")

    # Format the topic name to match the storage format
    formatted_name = format_text_to_title(topic_name)
    
    # Retrieve the topic by its name
    topic = storage.get_by_value(Topic, "name", formatted_name)
    
    if topic is None:
        abort(404, description="Topic not found")

    return topic.to_json()


def add_topic(data: Dict[str, Any], storage: Any) -> tuple:
    """
    Helper function to add a topic.
    
    Args:
        data (dict): The data for the new topic. Expected keys: 'name', 'parent_id'.
        storage (object): Storage instance to handle database operations.
    
    Returns:
        Response object: JSON response indicating success or error.
    """
    # Convert "null" or "None" strings to None for parent_id
    parent_id = data.get('parent_id')
    if parent_id and str(parent_id).lower() in ["none", "null"]:
        data["parent_id"] = None
        parent_id = None

    # Check for missing required fields
    if 'name' not in data:
        return jsonify({'message': 'Missing topic name'}), 400
    
    print(f"Parent id: {parent_id}")
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

    # Create and save topic
    topic_obj = Topic(**data)
    topic_obj.save()

    return jsonify({
        "message": "Topic added successfully",
        "topic": topic_obj.to_json()
    }), 201
