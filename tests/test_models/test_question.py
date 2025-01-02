#!/usr/bin/env python3
import unittest
from models.question import Question
from datetime import datetime
from unittest.mock import patch

class TestQuestionModel(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Initialize the Question model with mock data
        self.question_data = {
            "quiz_id": "123",
            "question_text": "What is the capital of France?",
            "order_number": 1,
            "allow_multiple_answers": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Create a Question instance
        self.question = Question(**self.question_data)

    def test_question_initialization(self):
        """Test the initialization of a Question instance."""
        self.assertEqual(self.question.quiz_id, "123")
        self.assertEqual(self.question.question_text, "What is the capital of France?")
        self.assertEqual(self.question.order_number, 1)
        self.assertFalse(self.question.allow_multiple_answers)
        self.assertIsInstance(self.question.created_at, datetime)
        self.assertIsInstance(self.question.updated_at, datetime)

    def test_question_repr(self):
        """Test the string representation (__repr__) of the Question instance."""
        question_repr = repr(self.question)
        self.assertIn("Question(id=", question_repr)
        self.assertIn("quiz_id=123", question_repr)
        self.assertIn("question_text=What is the capital of France?", question_repr)
        self.assertIn("allow_multiple_answers=False", question_repr)
        self.assertIn("created_at=", question_repr)
        self.assertIn("updated_at=", question_repr)

    @patch('models.question.Question.__repr__')
    def test_question_repr_mocked(self, mock_repr):
        """Test the mocked __repr__ method for Question."""
        mock_repr.return_value = "Mocked Question String"
        self.assertEqual(repr(self.question), "Mocked Question String")

if __name__ == "__main__":
    unittest.main()
