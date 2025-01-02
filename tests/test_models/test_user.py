#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock
from models.user import User  # Import the User class

class TestUser(unittest.TestCase):
    """
    Test case for the User class, ensuring that password encryption and validation
    methods function correctly.
    """

    def setUp(self):
        """
        Setup mock data and initialize a User instance for testing.
        """
        self.user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'email': 'johndoe@example.com',
            'password': 'plainpassword'
        }
        self.user = User(**self.user_data)

    @patch('models.user.hashpw')  # Mocking bcrypt's hashpw function
    @patch('models.user.gensalt')  # Mocking bcrypt's gensalt function
    def test_password_encryption(self, mock_gensalt, mock_hashpw):
        """
        Test the encryption of the password when it is set.
        """
        # Mock the output of gensalt and hashpw
        mock_salt = b'$2b$12$abcdefghijklmnoabcdefghi'
        mock_gensalt.return_value = mock_salt
        mock_hashpw.return_value = b'$2b$12$abcdefghijklmnoabcdefghi$hashedpassword'

        # Set the password and check if it gets encrypted correctly
        self.user.password = 'plainpassword'

        # Assert that bcrypt functions were called
        mock_gensalt.assert_called_once()
        mock_hashpw.assert_called_once_with(b'plainpassword', mock_salt)

        # Assert the encrypted password is stored in the User object
        self.assertEqual(self.user.password, '$2b$12$abcdefghijklmnoabcdefghi$hashedpassword')

    def test_check_password_valid(self):
        """
        Test the check_password method with a valid password.
        """
        # Set the password directly to simulate an encrypted password
        self.user.password = '$2b$12$abcdefghijklmnoabcdefghi$hashedpassword'

        # Mock checkpw to return True for the correct password
        with patch('models.user.checkpw', return_value=True):
            self.assertTrue(self.user.check_password('plainpassword'))

    def test_check_password_invalid(self):
        """
        Test the check_password method with an invalid password.
        """
        # Set the password directly to simulate an encrypted password
        self.user.password = '$2b$12$abcdefghijklmnoabcdefghi$hashedpassword'

        # Mock checkpw to return False for an incorrect password
        with patch('models.user.checkpw', return_value=False):
            self.assertFalse(self.user.check_password('wrongpassword'))

    @patch('models.user.User.save')  # Mock the save method to avoid database interaction
    @patch('models.user.hashpw')  # Mocking bcrypt's hashpw function
    @patch('models.user.gensalt')  # Mocking bcrypt's gensalt function
    def test_set_password(self, mock_gensalt, mock_hashpw, mock_save):
        """
        Test the set_password method.
        """
        # Mock the output of gensalt and hashpw
        mock_salt = b'$2b$12$abcdefghijklmnoabcdefghi'
        mock_gensalt.return_value = mock_salt
        mock_hashpw.return_value = b'$2b$12$abcdefghijklmnoabcdefghi$hashedpassword'

        # Call set_password and check if the password is set and saved correctly
        self.user.set_password('newpassword')

        # Assert that the password is hashed correctly
        mock_hashpw.assert_called_once_with(b'newpassword', mock_salt)

        # Assert the encrypted password is stored in the User object
        self.assertEqual(self.user.password, '$2b$12$abcdefghijklmnoabcdefghi$hashedpassword')

        # Ensure save method was called to persist the user with the new password
        mock_save.assert_called_once()

if __name__ == '__main__':
    unittest.main()
