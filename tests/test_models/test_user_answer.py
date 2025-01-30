#!/usr/bin/env python3
import unittest
from models.user_answer import UserAnswer
from datetime import datetime
from unittest.mock import patch
"""
Unit tests for the UserAnswer model, which represents the answers provided
by users in a quiz. The tests ensure that the initialization, string
representation, and mocked behavior of the UserAnswer model work as expected.

Key tests included in this module:
- Verifying the correct initialization of a UserAnswer instance with the
  expected attributes (user_id, quiz_id, question_id, choice_id, created_at,
  and updated_at).
- Ensuring the __repr__ method of UserAnswer provides a meaningful string
  representation of the object.
- Testing the mocked __repr__ method to ensure mocking functionality works
  as expected.

Mocking of the __repr__ method is used to isolate the behavior and avoid
depending on the actual implementation.
"""


class TestUserAnswerModel(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Initialize the UserAnswer model with mock data
        self.user_answer_data = {
            "user_id": "user123",
            "quiz_id": "quiz123",
            "question_id": "question123",
            "choice_id": "choice123",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Create a UserAnswer instance
        self.user_answer = UserAnswer(**self.user_answer_data)

    def test_user_answer_initialization(self):
        """Test the initialization of a UserAnswer instance."""
        self.assertEqual(self.user_answer.user_id, "user123")
        self.assertEqual(self.user_answer.quiz_id, "quiz123")
        self.assertEqual(self.user_answer.question_id, "question123")
        self.assertEqual(self.user_answer.choice_id, "choice123")
        self.assertIsInstance(self.user_answer.created_at, datetime)
        self.assertIsInstance(self.user_answer.updated_at, datetime)

    def test_user_answer_repr(self):
        """Test the string representation (__repr__) of UserAnswer instance."""
        user_answer_repr = repr(self.user_answer)
        self.assertIn("UserAnswer(user_id=user123", user_answer_repr)
        self.assertIn("quiz_id=quiz123", user_answer_repr)
        self.assertIn("question_id=question123", user_answer_repr)
        self.assertIn("choice_id=choice123", user_answer_repr)

    @patch('models.user_answer.UserAnswer.__repr__')
    def test_user_answer_repr_mocked(self, mock_repr):
        """Test the mocked __repr__ method for UserAnswer."""
        mock_repr.return_value = "Mocked UserAnswer String"
        self.assertEqual(repr(self.user_answer), "Mocked UserAnswer String")


if __name__ == "__main__":
    unittest.main()
