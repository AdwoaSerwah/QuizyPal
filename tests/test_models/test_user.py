#!/usr/bin/env python3
import unittest
from unittest.mock import patch
from models.user import User
from bcrypt import checkpw
from datetime import datetime, timezone


class TestUser(unittest.TestCase):
    """
    Test case for the User class, testing password encryption,
    password check, and token generation.
    """

    def setUp(self):
        """
        Creates a User instance for testing.
        """
        self.user = User(first_name="John", last_name="Doe", username="johndoe", email="johndoe@example.com", password="rawpassword")

    def test_check_password(self):
        """
        Test the check_password method.
        """
        # Mock bcrypt's checkpw to return True for the correct password
        with patch('bcrypt.checkpw', return_value=True):
            self.assertTrue(self.user.check_password("rawpassword"))

        # Test incorrect password
        with patch('bcrypt.checkpw', return_value=False):
            self.assertFalse(self.user.check_password("wrongpassword"))

    def test_set_password(self):
        """
        Test the set_password method.
        """
        # Set a new password
        with patch.object(self.user, 'save', return_value=None):
            self.user.set_password("newpassword")

        # Test if password was hashed and saved
        self.assertNotEqual(self.user.password, "newpassword")
        self.assertTrue(checkpw("newpassword".encode('utf-8'), self.user.password.encode('utf-8')))

if __name__ == '__main__':
    unittest.main()
