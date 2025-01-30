#!/usr/bin/env python3
"""
Holds the class Result, representing a result/quiz attempt for a user.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, Float, String, Integer, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from datetime import datetime, timezone



class QuizSessionStatus(PyEnum):
    """
    Enum for Quiz session status. Defines the possible statuses for the quiz attempt.
    """
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    TIMED_OUT = "timed-out"

    @classmethod
    def from_str(cls, status_str: str) -> 'QuizSessionStatus':
        """
        Convert a string to a Role enum member.

        Args:
            role_str (str): The string representation of the role.

        Returns:
            Role: Corresponding Role enum member.
        """
        for status in cls:
            if status.value == status_str.lower():
                return status
        raise ValueError(f"Invalid role: {status_str}. Must be one of {[s.value for s in cls]}")


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
    score: float = Column(Float, nullable=False, default=0.00)
    # score: Decimal = Column(DECIMAL(5, 2), nullable=False, default=Decimal('0.00'))
    time_taken: int = Column(Integer, nullable=False, default=0)  # Initially set to 0
    status: str = Column(Enum(QuizSessionStatus), nullable=False, default=QuizSessionStatus.IN_PROGRESS)  # Enum for status
    submitted_at: datetime = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))  # Standardized timestamp
    start_time: datetime = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))  # Start time
    end_time: datetime = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))  # End time for quiz session

    # Relationships to link to User and Quiz tables
    user = relationship('User', back_populates='results')
    quiz = relationship('Quiz', back_populates='results')
    user_answers = relationship('UserAnswer', back_populates='result', cascade="all, delete-orphan")

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

    @classmethod
    def get_attempt_number(cls, storage, user_id: str, quiz_id: str, filter_by_date: bool = False) -> int:
        """
        Counts the number of attempts a user has made for a specific quiz.

        Args:
            storage (Storage): The storage instance to interact with the database.
            user_id (str): The ID of the user.
            quiz_id (str): The ID of the quiz.
            filter_by_date (bool): If True, count only today's attempts (default is False for total attempts).

        Returns:
            int: The number of attempts the user has made for the quiz.
        """
        # Fetch all results for the user and quiz
        results = storage.filter_by(cls, user_id=user_id, quiz_id=quiz_id)

        if filter_by_date:
            # Get today's date (UTC)
            today_date = datetime.now(timezone.utc).date()
            # Filter manually for today's attempts
            results = [result for result in results if result.start_time.date() == today_date]

        # Return the count of filtered results
        return len(results)

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


