#!/usr/bin/env python3
from typing import Dict, Any, List, Optional
from flask import jsonify, abort
from models.refresh_token import RefreshToken
"""
Module for managing Refresh Tokens.

This module provides helper functions to interact
with the Refresh Tokens stored in the database.

It includes functions to retrieve all refresh tokens, as well as
fetch individual refresh tokens by their unique identifier.

Functions:
    - get_all_refresh_tokens(storage): Retrieves a list of all
      refresh tokens in a JSON serializable format.

    - get_refresh_token_by_id(refresh_token_id, storage): Retrieves a refresh
      token by its unique ID.
"""


def get_all_refresh_tokens(storage) -> List[Dict]:
    """
    Helper function to get all Refresh Tokens.

    Args:
        storage (object): Storage instance to handle
                          database operations.

    Returns:
        List of dicts: A list of all Refresh Tokens in JSON
                       serializable format.
    """
    all_refresh_tokens = [
        refresh_token.to_json()
        for refresh_token in storage.all(RefreshToken).values()
    ]

    return all_refresh_tokens


def get_refresh_token_by_id(
        refresh_token_id: str,
        storage: Any) -> Optional[dict]:
    """
    Helper function to retrieve a refresh token by its ID.

    Args:
        refresh_token_id (str): The unique identifier for the refresh token.
        storage (object): Storage instance to handle database operations.

    Returns:
        dict: A dictionary representing the refresh token if found.
        None: If the refresh token is not found.
    """
    if not refresh_token_id:
        abort(400, description="Refresh Token ID is required")

    if not isinstance(refresh_token_id, str):
        abort(400, description="Refresh Token ID must be a string")
    refresh_token = storage.get(RefreshToken, refresh_token_id)

    return refresh_token
