import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from flask_jwt_extended import create_access_token, JWTManager
from api.v1.views.auth import login, logout, refresh_token, forgot_password, reset_password

class TestAuthViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        cls.app.add_url_rule('/api/v1/login', view_func=login, methods=['POST'])
        cls.app.add_url_rule('/api/v1/logout', view_func=logout, methods=['POST'])
        cls.app.add_url_rule('/api/v1/refresh-token', view_func=refresh_token, methods=['POST'])
        cls.app.add_url_rule('/api/v1/forgot-password', view_func=forgot_password, methods=['POST'])
        cls.app.add_url_rule('/api/v1/reset-password/<token>', view_func=reset_password, methods=['POST'])

    def setUp(self):
        self.client = self.app.test_client()

    @patch('api.v1.views.auth.User')
    def test_login(self, mock_user):
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/login', json={'access_token': access_token})
        self.assertEqual(response.status_code, 400)

    @patch('api.v1.views.auth.User')
    def test_logout(self, mock_user):
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/logout', json={'access_token': access_token})
        self.assertEqual(response.status_code, 401)

    @patch('api.v1.views.auth.User')
    def test_refresh_token(self, mock_user):
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            access_token = create_access_token(identity=self.user.email)
            response = self.client.post('/api/v1/refresh-token', json={'access_token': access_token})
        self.assertEqual(response.status_code, 401)

    @patch('api.v1.views.auth.User')
    def test_forgot_password(self, mock_user):
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            response = self.client.post('/api/v1/forgot-password', json={'email': self.user.email})
        self.assertEqual(response.status_code, 404)

    @patch('api.v1.views.auth.User')
    def test_reset_password(self, mock_user):
        mock_user.return_value.email = self.user.email
        with self.app.app_context():
            response = self.client.post('/api/v1/reset-password/mocktoken', json={'password': 'newpassword'})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
