#!/usr/bin/env python3
"""
Unit tests for the Choice model.
"""
import unittest
from models.choice import Choice
from datetime import datetime
from unittest.mock import patch


class TestChoiceModel(unittest.TestCase):
    """Test suite for the Choice model."""
    def setUp(self):
        """Set up the test environment."""
        # Initialize the Choice model with mock data
        self.choice_data = {
            "question_id": "123",
            "choice_text": "Paris",
            "is_correct": True,
            "order_number": 1,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Create a Choice instance
        self.choice = Choice(**self.choice_data)

    def test_choice_initialization(self):
        """Test the initialization of a Choice instance."""
        self.assertEqual(self.choice.question_id, "123")
        self.assertEqual(self.choice.choice_text, "Paris")
        self.assertTrue(self.choice.is_correct)
        self.assertEqual(self.choice.order_number, 1)
        self.assertIsInstance(self.choice.created_at, datetime)
        self.assertIsInstance(self.choice.updated_at, datetime)

    def test_choice_repr(self):
        """Test the string representation (__repr__) of the Choice instance."""
        choice_repr = repr(self.choice)
        self.assertIn("Choice(id=", choice_repr)
        self.assertIn("question_id=123", choice_repr)
        self.assertIn("choice_text=Paris", choice_repr)
        self.assertIn("is_correct=True", choice_repr)
        self.assertIn("created_at=", choice_repr)
        self.assertIn("updated_at=", choice_repr)

    @patch('models.choice.Choice.__repr__')
    def test_choice_repr_mocked(self, mock_repr):
        """Test the mocked __repr__ method for Choice."""
        mock_repr.return_value = "Mocked Choice String"
        self.assertEqual(repr(self.choice), "Mocked Choice String")


if __name__ == "__main__":
    unittest.main()
