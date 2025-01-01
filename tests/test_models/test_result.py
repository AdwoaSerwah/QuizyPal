#!/usr/bin/env python3
"""
Test suite for the Result class.
"""

import unittest
from unittest.mock import MagicMock
from decimal import Decimal
from models.result import Result, QuizSessionStatus


class TestResult(unittest.TestCase):
    """
    Test class for the Result model.
    """

    def setUp(self) -> None:
        """
        Sets up the test environment for each test case.
        """
        self.result = Result(
            user_id="user123",
            quiz_id="quiz123",
            score=Decimal("95.00"),
            time_taken=120,
            status=QuizSessionStatus.COMPLETED,
            submitted_at="2025-01-01T12:00:00Z",
            start_time="2025-01-01T11:00:00Z",
            end_time="2025-01-01T12:00:00Z"
        )

    def test_get_attempt_number(self) -> None:
        """
        Tests the get_attempt_number method.
        """
        # Mock the query filter and count method
        mock_query = MagicMock()
        mock_query.filter_by.return_value.count.return_value = 3

        # Assign the mock query to the Result class's query attribute
        Result.query = mock_query

        # Call the method and assert the expected result
        attempt_number = self.result.get_attempt_number("user123", "quiz123")
        self.assertEqual(attempt_number, 3)

    def test_str_method(self) -> None:
        """
        Tests the __str__ method.
        """
        expected_str = "[Result] (None) UserID: user123, QuizID: quiz123, Score: 95.00, " \
                       "Status: QuizSessionStatus.COMPLETED, Time Taken: 120s"  # Adjusted expected value
        self.assertEqual(str(self.result), expected_str)

    def test_repr_method(self) -> None:
        """
        Tests the __repr__ method.
        """
        expected_repr = ("Result(id=None, user_id=user123, quiz_id=quiz123, score=95.00, "
                         "time_taken=120, status=QuizSessionStatus.COMPLETED, submitted_at=2025-01-01T12:00:00Z, "
                         "start_time=2025-01-01T11:00:00Z, end_time=2025-01-01T12:00:00Z, "
                         "created_at=None, updated_at=None)")  # Adjusted expected value
        self.assertEqual(repr(self.result), expected_repr)


if __name__ == "__main__":
    unittest.main()
