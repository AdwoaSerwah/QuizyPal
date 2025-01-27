from typing import Dict, Tuple, Any, List, Optional
from flask import jsonify, abort
from models.refresh_token import RefreshToken
from datetime import datetime, timezone


def get_all_refresh_tokens(storage) -> List[Dict]:
    """
    Helper function to get all Refresh Tokens.

    Args:
        storage (object): Storage instance to handle database operations.
    
    Returns:
        List of dicts: A list of all Refresh Tokens in JSON serializable format.
    """
    all_refresh_tokens = [refresh_token.to_json() for refresh_token in storage.all(RefreshToken).values()]
    return all_refresh_tokens


def get_refresh_token_by_id(refresh_token_id: str, storage: Any) -> Optional[dict]:
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
