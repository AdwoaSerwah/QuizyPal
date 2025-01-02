#!/usr/bin/env python3
"""
Holds the class Question, representing a question in the system.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Boolean, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from typing import Optional


class Question(BaseModel, Base):
    """
    Represents a question in the system. Inherits from BaseModel and Base
    to enable database interaction using SQLAlchemy.

    Attributes:
        quiz_id (str): The ID of the quiz to which the question belongs.
        question_text (str): The text of the question.
        order_number (int): The position of the question in the quiz.
        allow_multiple_answers (bool): Whether the question allows multiple answers.
        created_at (datetime): The timestamp when the question was created.
        updated_at (datetime): The timestamp when the question was last updated.
    """

    __tablename__ = 'questions'

    quiz_id: str = Column(String(60), ForeignKey('quizzes.id'), nullable=False)
    question_text: str = Column(String(255), nullable=False)
    order_number: int = Column(Integer, nullable=False)
    allow_multiple_answers: bool = Column(Boolean, default=False, nullable=False)

    # Relationship with Quiz table
    quiz = relationship('Quiz', back_populates='questions')

    # Relationship with Choice table
    choices = relationship('Choice', back_populates='question', cascade="all, delete-orphan")

    # Relationship with UserAnswer table
    user_answers = relationship('UserAnswer', back_populates='question', cascade="all, delete-orphan")

    # Add indexes for optimized searches and constraints for uniqueness
    __table_args__ = (
        Index('idx_quiz_id_id', 'quiz_id', 'id'),  # Composite index
        UniqueConstraint('quiz_id', 'question_text', name='uq_quiz_question_text'),  # Unique constraint
    )

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a question object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Returns a string representation of the Question instance.

        Returns:
            str: A detailed string representation of the instance.
        """
        return (f"Question(id={self.id}, quiz_id={self.quiz_id}, question_text={self.question_text}, "
                f"allow_multiple_answers={self.allow_multiple_answers}, created_at={self.created_at}, "
                f"updated_at={self.updated_at})")
