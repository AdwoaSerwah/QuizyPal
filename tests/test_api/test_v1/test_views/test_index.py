#!/usr/bin/env python3
"""
This module defines test cases for the app_views endpoints of the Flask API.
It includes tests for various routes such as status, unauthorized, forbidden,
stats, and the home endpoint. The tests ensure the correct status codes and
responses are returned for each route.
"""
import unittest
from flask import Flask
from api.v1.views import app_views


class TestAppViews(unittest.TestCase):
    """Test cases for app_views endpoints."""

    def setUp(self):
        """Set up a test client for the Flask app."""
        self.app = Flask(__name__)
        self.app.register_blueprint(app_views, url_prefix='/api/v1')
        self.client = self.app.test_client()

    def test_status_endpoint(self):
        """Test the /api/v1/status endpoint."""
        response = self.client.get('/api/v1/status')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "OK"})

    def test_unauthorized_endpoint(self):
        """Test the /api/v1/unauthorized endpoint."""
        response = self.client.get('/api/v1/unauthorized')
        self.assertEqual(response.status_code, 401)
        self.assertIn("Unauthorized", response.get_data(as_text=True))

    def test_forbidden_endpoint(self):
        """Test the /api/v1/forbidden endpoint."""
        response = self.client.get('/api/v1/forbidden')
        self.assertEqual(response.status_code, 403)
        self.assertIn("Forbidden", response.get_data(as_text=True))

    def test_stats_endpoint(self):
        """Test the /api/v1/stats endpoint."""
        # Mocking the User.count method
        from unittest.mock import patch
        with patch('models.storage.count', return_value=10):
            response = self.client.get('/api/v1/stats')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {"users": 10})

    def test_home_endpoint(self):
        """Test the root / endpoint."""
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json,
                         {"message": "Welcome to the QuizyPal API!"})


if __name__ == "__main__":
    unittest.main()
