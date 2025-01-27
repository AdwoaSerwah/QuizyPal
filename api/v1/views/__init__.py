#!/usr/bin/env python3
"""
App Views Blueprint

Defines the 'app_views' Blueprint for the API with the URL prefix '/api/v1'. 
It groups views related to user management, authentication, quizzes, topics, 
questions, and choices. Each view is registered under the '/api/v1' prefix for 
consistent API versioning.

Modules imported:
- index: Home or index page routes
- users: User management routes
- auth: Authentication routes
- refresh_tokens: Refresh token management routes
- topics: Quiz topic management routes
- quizzes: Quiz management routes
- questions: Question management routes
- choices: Answer choice management routes
- user_answers: User answer management routes
- results: Results management routes
"""
from flask import Blueprint

app_views = Blueprint("app_views", __name__, url_prefix="/api/v1")

from api.v1.views.index import *
from api.v1.views.users import *
from api.v1.views.auth import *
from api.v1.views.refresh_tokens import *
from api.v1.views.topics import *
from api.v1.views.quizzes import *
from api.v1.views.questions import *
from api.v1.views.choices import *
from api.v1.views.results import *
from api.v1.views.user_answers import *
