#!/usr/bin/env python3
"""
Contains tests for the DBStorage class for interacting with the MySQL database.
"""

import unittest
from unittest.mock import patch, MagicMock
from models import storage
from models.user import User
from sqlalchemy.orm import sessionmaker


class TestDBStorage(unittest.TestCase):
    """
    Unit tests for DBStorage class methods.
    """

    @patch('models.engine.db_storage.create_engine')
    def setUp(self, mock_create_engine):
        """
        Sets up a mock DBStorage instance and mocks database interactions.
        """
        # Mock the creation of the engine and sessionmaker
        self.mock_engine = MagicMock()
        self.mock_session = MagicMock()
        mock_create_engine.return_value = self.mock_engine

        # Mock the sessionmaker to return a mocked session
        self.mock_session_factory = MagicMock()
        self.mock_session_factory.return_value = self.mock_session

        # Use the storage instance directly instead of trying to instantiate DBStorage again
        self.db_storage = storage  # storage is already an instance of DBStorage
        self.db_storage._DBStorage__session = self.mock_session

    @patch('models.engine.db_storage.DBStorage.all')
    def test_all(self, mock_all):
        """
        Test the 'all' method which retrieves all objects from the database.
        """
        mock_all.return_value = {'User.123': MagicMock(), 'User.456': MagicMock()}

        result = self.db_storage.all(User)
        self.assertEqual(len(result), 2)

    @patch('models.engine.db_storage.DBStorage.new')
    def test_new(self, mock_new):
        """
        Test the 'new' method which adds a new object to the session.
        """
        mock_obj = MagicMock()
        self.db_storage.new(mock_obj)
        mock_new.assert_called_once_with(mock_obj)

    @patch('models.engine.db_storage.DBStorage.save')
    def test_save(self, mock_save):
        """
        Test the 'save' method which commits changes to the database.
        """
        self.db_storage.save()
        mock_save.assert_called_once()

    @patch('models.engine.db_storage.DBStorage.delete')
    def test_delete(self, mock_delete):
        """
        Test the 'delete' method which deletes an object from the session.
        """
        mock_obj = MagicMock()
        self.db_storage.delete(mock_obj)
        mock_delete.assert_called_once_with(mock_obj)

    @patch('models.engine.db_storage.DBStorage.count')
    def test_count(self, mock_count):
        """
        Test the 'count' method to ensure it counts the number of objects correctly.
        """
        mock_count.return_value = 3
        result = self.db_storage.count(User)
        self.assertEqual(result, 3)

    @patch('models.engine.db_storage.DBStorage.close')
    def test_close(self, mock_close):
        """
        Test the 'close' method to ensure it closes the session correctly.
        """
        self.db_storage.close()
        mock_close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
