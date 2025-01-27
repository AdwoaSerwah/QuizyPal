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
    if not isinstance(topic_id, str):
        abort(400, description='Topic ID must be a string')
    topic = storage.get(Topic, topic_id)
    return topic


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
        abort(400, description="Topic name is required")

    if not isinstance(topic_name, str):
        abort(400, description='Topic name must be a string')

    if topic_name.lower() in ["null", "none", ""]:
        abort(400, description='Topic name must not be null or empty.')

    # Format the topic name to match the storage format
    formatted_name = format_text_to_title(topic_name)
    
    # Retrieve the topic by its name
    topic = storage.get_by_value(Topic, "name", formatted_name)
    return topic


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
    if parent_id is not None:
        parent_id = validate_parent_id(parent_id, storage)
    data['parent_id'] = parent_id
    
    # Validate topic name
    name = data.get('name')
    data['name'] = validate_topic_name(name)
    if storage.get_by_value(Topic, "name", data['name']):
        abort(400, description=f"Topic name already exists!")

    # Create and save topic
    topic_obj = Topic(**data)
    topic_obj.save()

    return jsonify({
        "message": "Topic added successfully",
        "topic": topic_obj.to_json()
    }), 201


def validate_parent_id(parent_id, storage):
        if not isinstance(parent_id, str):
            abort(400, description="Parent ID must be a string")
        if str(parent_id).lower() in ["none", "null", ""]:
            parent_id = None

        if parent_id is not None:
            parent = storage.get(Topic, parent_id)
            if not parent:
                abort(404, description="Parent not found")

        return parent_id


def validate_topic_name(name):
    if not isinstance(name, str):
        abort(400, description="Topic name must be a string")

    if not name or name.lower() in {"none", "null", ""}:
        abort(400, description="Topic name must not be empty or null.")
    
    if len(name) > 128:
        abort(400, description="Topic name cannot be longer than 128 characters.")

    # Update the field with the converted string value
    formatted_text = format_text_to_title(name)

    # Check for existing topic name
    if not formatted_text:
        abort(400, description="Topic name must include alphabets and cannot be 'none' or 'null'.")
    return formatted_text
