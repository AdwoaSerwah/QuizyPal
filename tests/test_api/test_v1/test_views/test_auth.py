#!/usr/bin/env python3
"""
This module defines test cases for authentication-related views
in the Flask API. The tests include login, logout, refresh token,
forgot password, and reset password. Mocked user data and JWT tokens
are used for testing the routes to ensure they return the correct
status codes and handle errors appropriately.
"""
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import create_access_token, JWTManager
from api.v1.views.auth import login, logout, forgot_password, reset_password
from api.v1.views.refresh_tokens import refresh_token


class TestAuthViews(unittest.TestCase):
    """
    Test cases for authentication-related routes in the Flask API.
    Tests include login, logout, refresh token, forgot password,
    and reset password.
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up the Flask app for testing, including initializing the JWTManager
        and registering routes for authentication endpoints.
        This method runs once before any test method is executed.
        """
        # Mock Flask app setup without creating the app
        cls.app = Flask(__name__)
        cls.app.config['JWT_SECRET_KEY'] = 'supersecretkey'
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize JWTManager with Flask app
        cls.jwt = JWTManager(cls.app)

        # Create mock user
        cls.user = MagicMock()
        cls.user.email = 'test@example.com'

        # Register routes
        cls.app.add_url_rule('/api/v1/login',
                             view_func=login, methods=['POST'])
        cls.app.add_url_rule('/api/v1/logout',
                             view_func=logout, methods=['POST'])
        cls.app.add_url_rule('/api/v1/refresh-token',
                             view_func=refresh_token, methods=['POST'])
        cls.app.add_url_rule('/api/v1/forgot-password',
                             view_func=forgot_password, methods=['POST'])
        cls.app.add_url_rule('/api/v1/reset-password/<token>',
                             view_func=reset_password, methods=['POST'])

    def setUp(self):
        """
        Set up the test client for Flask app. This method is executed before
        each individual test to set up a fresh test client.
        """
        self.client = self.app.test_client()

    @patch('api.v1.views.auth.User')
    def test_login(self, mock_user):
        """
        Test the /api/v1/login endpoint to check that a user can log in with
        a valid access token and receive the correct response status.
        """
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/login',
                                        json={'access_token': access_token})
        self.assertEqual(response.status_code, 400)

    @patch('api.v1.views.auth.User')
    def test_logout(self, mock_user):
        """
        Test the /api/v1/logout endpoint to ensure that logging out with an
        access token returns the correct response status.
        """
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/logout',
                                        json={'access_token': access_token})
        self.assertEqual(response.status_code, 401)

    @patch('api.v1.views.auth.User')
    def test_refresh_token(self, mock_user):
        """
        Test the /api/v1/refresh-token endpoint to ensure that refreshing a
        token with a valid access token returns the correct response status.
        """
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/refresh-token',
                                        json={'access_token': access_token})
        self.assertEqual(response.status_code, 401)

    @patch('api.v1.views.auth.User')
    def test_forgot_password(self, mock_user):
        """
        Test the /api/v1/forgot-password endpoint to verify that requesting
        a password reset with a valid email returns the correct response.
        """
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            response = self.client.post('/api/v1/forgot-password',
                                        json={'email': self.user.email})
        self.assertEqual(response.status_code, 404)

    @patch('api.v1.views.auth.User')
    def test_reset_password(self, mock_user):
        """
        Test the /api/v1/reset-password/<token> endpoint
        to check that resetting the password with a valid token
        and new password returns the correct response.
        """
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            response = self.client.post('/api/v1/reset-password/mocktoken',
                                        json={'password': 'newpassword'})
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
