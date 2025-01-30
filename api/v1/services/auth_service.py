#!/usr/bin/env python3
"""
This module contains a custom decorator function,
`admin_required`, which ensures that a user has 'admin'
privileges before allowing access to the decorated route.

It uses JWT tokens to verify the role of the user and
restricts access to the route if the user does not have
the 'admin' role.
"""
from flask import jsonify
from flask_jwt_extended import get_jwt
from functools import wraps
from typing import Callable, Any


def admin_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that ensures the current user has 'admin' privileges.

    This decorator checks the role of the current user in the JWT token.
    Args:
        fn (Callable[..., Any]): The function to be decorated.

    Returns:
        Callable[..., Any]: A wrapped version of the input function with
                            added authorization check.
    """
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Retrieve the JWT claims
        jwt_data = get_jwt()
        # Get the 'role' claim from the token
        user_role = jwt_data.get('role')

        if user_role is None:
            return jsonify({"error": "Missing role in token"}), 403

        if user_role != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        return fn(*args, **kwargs)

    return wrapper
