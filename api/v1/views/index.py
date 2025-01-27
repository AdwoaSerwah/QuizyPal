#!/usr/bin/env python3
""" Module of Index views
"""
from flask import jsonify, abort
from api.v1.views import app_views
from models import storage
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.v1.services.auth_service import admin_required
from flask.typing import ResponseReturnValue


@app_views.route('/unauthorized', methods=['GET'], strict_slashes=False)
def authorized() -> ResponseReturnValue:
    """ 
    Raise a 401 error
    """
    abort(401, description="Unauthorized")


@app_views.route('/not-found', methods=['GET'], strict_slashes=False)
def not_found() -> ResponseReturnValue:
    """
    Raise a 401 error
    """
    abort(404, description="Not found")


@app_views.route('/forbidden', methods=['GET'], strict_slashes=False)
def forbid() -> ResponseReturnValue:
    """
    Raise a 403 error
    """
    abort(403, description="Forbidden")


@app_views.route('/status', methods=['GET'], strict_slashes=False)
def status() -> ResponseReturnValue:
    """
    Return the status of the API
    """
    return jsonify({"status": "OK"})


@app_views.route('/stats/', strict_slashes=False)
def stats() -> ResponseReturnValue:
    """
    Returns the number of each objects
    """
    stats = {}
    stats['users'] = storage.count(User)
    return jsonify(stats)


@app_views.route('/', methods=['GET'])
def home() -> ResponseReturnValue:
    """Root endpoint"""
    return jsonify({"message": "Welcome to the QuizyPal API!"})


@app_views.route('/protected', methods=['GET'])
@jwt_required()
def protected() -> ResponseReturnValue:
    """Get the current user ID from the token"""
    current_user_id = get_jwt_identity()
    
    return jsonify(logged_in_as=current_user_id)


@app_views.route('/admin/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def admin_dashboard() -> ResponseReturnValue:
    """Admin dashboard logic"""
    return jsonify({"message": "Welcome to the admin dashboard!"})


@app_views.route('/admin/users', methods=['GET'])
@jwt_required()
@admin_required
def admin_users() -> ResponseReturnValue:
    """Admin users management logic"""
    return jsonify({"message": "List of users!"})


@app_views.route('/admin', methods=['GET'])
@jwt_required()
@admin_required
def admin() -> ResponseReturnValue:
    """Welcome Admin"""
    return jsonify(message="Welcome Admin"), 200
