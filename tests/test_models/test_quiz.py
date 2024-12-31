import unittest
from datetime import datetime, timezone
from models.quiz import Quiz  # Adjust the import based on your file structure

class TestQuiz(unittest.TestCase):
    def setUp(self):
        """Set up the test environment."""
        # Create a sample Quiz instance
        self.quiz = Quiz(
            id="123",
            topic_id="456",
            title="Sample Quiz",
            description="A test quiz",
            time_limit=30,
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        )

    def test_init(self):
        """Test the initialization of a Quiz instance."""
        # Check if the attributes are set correctly
        self.assertEqual(self.quiz.id, "123")
        self.assertEqual(self.quiz.topic_id, "456")
        self.assertEqual(self.quiz.title, "Sample Quiz")
        self.assertEqual(self.quiz.description, "A test quiz")
        self.assertEqual(self.quiz.time_limit, 30)
        self.assertEqual(self.quiz.created_at, datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(self.quiz.updated_at, datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc))

    def test_str_method(self):
        """Test the __str__ method of the Quiz class."""
        expected_str = "[Quiz] (123) TopicID: 456, Title: Sample Quiz, Time Limit: 30s"
        self.assertEqual(str(self.quiz), expected_str)

    def test_repr_method(self):
        """Test the __repr__ method of the Quiz class."""
        expected_repr = (
            "Quiz(id=123, topic_id=456, title=Sample Quiz, description=A test quiz, "
            "time_limit=30, created_at=2024-01-01 00:00:00+00:00, updated_at=2024-01-01 01:00:00+00:00)"
        )
        self.assertEqual(repr(self.quiz), expected_repr)

if __name__ == "__main__":
    unittest.main()
