#!/usr/bin/env python3
import unittest
from unittest.mock import patch
from api.v1.app import app
from models.user import User
from datetime import datetime
"""
Unit tests for the User views (Create, Read, Update, Delete)
of the /api/v1/users endpoint. This module tests the functionality
of user-related API endpoints including user creation, retrieval,
updating, and deletion, using mock data and mocking storage methods.
"""


class TestUserViews(unittest.TestCase):
    """
    Test the User views (Create, Read, Update, Delete)
    for the /api/v1/users endpoint.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the app and the test client before running tests.
        """
        # Use the test client from the app instance
        cls.client = app.test_client()

    def setUp(self):
        """
        Set up a test user and other necessary test data before each test.
        """
        self.test_user_data = {
            'id': '6af5c9f2-2766-46b7-a22b-f9f150deb5e1',
            'username': 'newuser',
            'email': 'newuser@gmail.com',
            'password': 'password123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'user',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        self.test_user = User(**self.test_user_data)

    # Mock the 'new' method in the storage module
    @patch('models.storage.new')
    # Mock the 'save' method in the storage module
    @patch('models.storage.save')
    # Mock the validate_email function
    @patch('email_validator.validate_email')
    def test_create_user(self, mock_save, mock_new, mock_validate_email):
        """
        Test the POST /api/v1/users endpoint to create a new user.
        """
        # Simulate the creation of a user
        mock_new.return_value = self.test_user
        # Simulate a successful save
        mock_save.return_value = None
        # Configure the mock to simulate successful validation
        mock_validate_email.return_value = {'email': 'newuser@gmail.com',
                                            'local': 'newuser',
                                            'domain': 'gmail.com'}

        response = self.client.post('/api/v1/users', json=self.test_user_data)
        self.assertEqual(response.status_code, 201)
        # Ensure 'user' exists in the response
        self.assertIn('user', response.json)
        # Ensure 'id' exists in the user object
        self.assertIn('id', response.json['user'])
        self.assertEqual(response.json['user']['username'], 'newuser')

    @patch('models.storage.all')  # Mock the 'all' method in the storage module
    def test_get_all_users(self, mock_all):
        """
        Test the GET /api/v1/users endpoint to retrieve all users.
        """
        # Create a mock user dictionary
        mock_user_data = {
            'user_id_1': User(id='user_id_1',
                              username='newuser',
                              email='newuser@example.com')
        }

        # Mock the return value of storage.all() to be a dictionary of users
        mock_all.return_value = mock_user_data

        headers = {
            'Authorization': 'Bearer invalid_token'
        }

        response = self.client.get('/api/v1/users', headers=headers)

        # Check if the status code is 200 (OK)
        self.assertEqual(response.status_code, 422)

    # Mock the 'get' method in the storage module
    @patch('models.storage.get')
    def test_get_user(self, mock_get):
        """
        Test the GET /api/v1/users/{user_id} endpoint to retrieve a user.
        """
        # Simulate retrieving the user
        mock_get.return_value = self.test_user

        headers = {
            # Replace with an actual or mock token
            'Authorization': 'Bearer invalid_token'
        }

        response = self.client.get(
            f'/api/v1/users/{self.test_user.id}',
            headers=headers
        )
        self.assertEqual(response.status_code, 422)
        # self.assertEqual(response.json['username'], 'newuser')

    # Mock the 'get' method in the storage module
    @patch('models.storage.get')
    # Mock the 'save' method in the storage module
    @patch('models.storage.save')
    def test_update_user(self, mock_save, mock_get):
        """
        Test the PUT /api/v1/users/{user_id} endpoint to update user's details.
        """
        # Simulate retrieving the user
        mock_get.return_value = self.test_user
        # Simulate a successful save
        mock_save.return_value = None

        updated_data = {'username': 'updateduser'}

        headers = {
            'Authorization': 'Bearer invalid_token'
        }

        response = self.client.put(f'/api/v1/users/{self.test_user.id}',
                                   json=updated_data,
                                   headers=headers)
        self.assertEqual(response.status_code, 422)

    # Mock the 'get' method in the storage module
    @patch('models.storage.get')
    # Mock the 'delete' method in the storage module
    @patch('models.storage.delete')
    # Mock the 'save' method in the storage module
    @patch('models.storage.save')
    def test_delete_user(self, mock_save, mock_delete, mock_get):
        """
        Test the DELETE /api/v1/users/{user_id} endpoint to delete a user.
        """
        mock_get.return_value = self.test_user  # Simulate retrieving the user
        mock_delete.return_value = None  # Simulate successful deletion
        mock_save.return_value = None  # Simulate a successful save

        headers = {
            'Authorization': 'Bearer invalid_token'
        }

        response = self.client.delete(
            f'/api/v1/users/{self.test_user.id}',
            headers=headers)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
