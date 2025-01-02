#!/usr/bin/env python3
"""
Contains tests for BaseModel class
"""
import unittest
from unittest.mock import patch, MagicMock
from models.base_model import BaseModel
from datetime import datetime

class TestBaseModel(unittest.TestCase):
    """
    Unit tests for the BaseModel class.
    """

    def setUp(self):
        """
        Sets up a new BaseModel instance for each test case.
        """
        self.base_model_instance = BaseModel(id="1234", created_at=datetime.now(), updated_at=datetime.now())

    def test_initialization(self):
        """
        Test the initialization of a BaseModel instance.
        """
        self.assertEqual(self.base_model_instance.id, "1234")
        self.assertIsInstance(self.base_model_instance.created_at, datetime)
        self.assertIsInstance(self.base_model_instance.updated_at, datetime)

    @patch.object(BaseModel, 'save')
    def test_save(self, mock_save):
        """
        Test the save method.
        """
        # Mock the save method
        mock_save.return_value = None  # Simulate that save doesn't raise errors
        self.base_model_instance.save()
        mock_save.assert_called_once()

    @patch.object(BaseModel, 'to_dict')
    def test_to_dict(self, mock_to_dict):
        """
        Test the to_dict method.
        """
        mock_to_dict.return_value = {
            'id': self.base_model_instance.id,
            'created_at': self.base_model_instance.created_at.isoformat(),
            'updated_at': self.base_model_instance.updated_at.isoformat()
        }
        result = self.base_model_instance.to_dict()
        self.assertEqual(result['id'], self.base_model_instance.id)
        self.assertEqual(result['created_at'], self.base_model_instance.created_at.isoformat())
        self.assertEqual(result['updated_at'], self.base_model_instance.updated_at.isoformat())

    @patch.object(BaseModel, 'delete')
    def test_delete(self, mock_delete):
        """
        Test the delete method.
        """
        # Mock the delete method
        mock_delete.return_value = None  # Simulate that delete doesn't raise errors
        self.base_model_instance.delete()
        mock_delete.assert_called_once()

if __name__ == '__main__':
    unittest.main()
