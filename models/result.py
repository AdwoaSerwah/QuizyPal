#!/usr/bin/env python3
"""
Holds the class Result, representing a result/quiz attempt for a user.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from decimal import Decimal
from sqlalchemy import Column, String, Integer, ForeignKey, Enum, DECIMAL, DateTime, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum  # Importing Python's Enum class
from datetime import datetime, timezone  # Missing imports


class QuizSessionStatus(PyEnum):
    """
    Enum for Quiz session status. Defines the possible statuses for the quiz attempt.
    """
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    TIMED_OUT = "timed-out"


class Result(BaseModel, Base):
    """
    Represents a result (quiz attempt) for a user. Inherits from BaseModel
    and Base to enable database interaction using SQLAlchemy.

    Attributes:
        user_id (str): The ID of the user who took the quiz.
        quiz_id (str): The ID of the quiz taken.
        score (decimal): The score the user obtained on this quiz attempt.
        time_taken (int): Time taken to complete the quiz in seconds.
        status (str): The status of the quiz attempt (in-progress/completed/timed-out).
        submitted_at (timestamp): The timestamp when the quiz was submitted.
        start_time (timestamp): The timestamp when the quiz session started.
        end_time (timestamp): The timestamp when the quiz session ended.
    """

    __tablename__ = 'results'

    # Foreign Keys to associate result with a user and a quiz
    user_id: str = Column(String(60), ForeignKey('users.id'), nullable=False)
    quiz_id: str = Column(String(60), ForeignKey('quizzes.id'), nullable=False)

    # Fields related to the result
    score: Decimal = Column(DECIMAL(5, 2), nullable=False)  # Score as DECIMAL(5,2)
    time_taken: int = Column(Integer, nullable=False)  # Time taken in seconds
    status: str = Column(Enum(QuizSessionStatus), nullable=False, default=QuizSessionStatus.IN_PROGRESS)  # Enum for status
    submitted_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Standardized timestamp
    start_time: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Start time
    end_time: datetime = Column(DateTime, nullable=True)  # End time for quiz session

    # Relationships to link to User and Quiz tables
    user = relationship('User', back_populates='results')
    quiz = relationship('Quiz', back_populates='results')

    # Composite index for user_id and quiz_id
    __table_args__ = (
        Index('idx_user_quiz', 'user_id', 'quiz_id'),
    )

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a result object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def get_attempt_number(self, user_id: str, quiz_id: str) -> int:
        """
        Counts the number of attempts a user has made for a specific quiz.

        Args:
            user_id (str): The ID of the user.
            quiz_id (str): The ID of the quiz.

        Returns:
            int: The number of attempts the user has made for the quiz.
        """
        return Result.query.filter_by(user_id=user_id, quiz_id=quiz_id).count()

    def __str__(self) -> str:
        """
        Returns a string representation of the Result instance.

        The string format is:
        [Result] (ID) UserID: user_id, QuizID: quiz_id, Attempt: attempt_number, Score: score

        Returns:
            str: String representation of the instance.
        """
        return f"[Result] ({self.id}) UserID: {self.user_id}, QuizID: {self.quiz_id}, " \
               f"Score: {self.score}, Status: {self.status}, Time Taken: {self.time_taken}s"

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Result instance.

        Returns:
            str: A more detailed string representation of the instance.
        """
        return (f"Result(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id}, "
                f"score={self.score}, time_taken={self.time_taken}, status={self.status}, "
                f"submitted_at={self.submitted_at}, start_time={self.start_time}, "
                f"end_time={self.end_time}, created_at={self.created_at}, "
                f"updated_at={self.updated_at})")
