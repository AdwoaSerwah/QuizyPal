#!/usr/bin/env python3
"""
Holds the class UserAnswer, representing a user's answer to a question.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from typing import Optional


class UserAnswer(BaseModel, Base):
    """
    Represents a user's answer to a quiz question. Inherits from BaseModel
    and Base to enable database interaction using SQLAlchemy.

    Attributes:
        user_id (str): The ID of the user answering the quiz.
        quiz_id (str): The ID of the quiz the question belongs to.
        question_id (str): The ID of the question being answered.
        choice_id (str): The ID of the choice selected by the user.
    """

    __tablename__ = 'user_answers'

    user_id: str = Column(String(60), ForeignKey('users.id'), nullable=False)
    quiz_id: str = Column(String(60), ForeignKey('quizzes.id'), nullable=False)
    question_id: str = Column(String(60), ForeignKey('questions.id'), nullable=False)
    choice_id: str = Column(String(60), ForeignKey('choices.id'), nullable=False, index=True)

    # Relationships with other tables
    user = relationship('User', back_populates='user_answers')
    quiz = relationship('Quiz', back_populates='user_answers')
    question = relationship('Question', back_populates='user_answers')
    choice = relationship('Choice', back_populates='user_answers')

    # Add composite index for quick lookups
    __table_args__ = (
        Index('idx_user_quiz_question', 'user_id', 'quiz_id', 'question_id'),
    )

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a user answer object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Returns a string representation of the UserAnswer instance.

        Returns:
            str: A detailed string representation of the instance.
        """
        return (f"UserAnswer(user_id={self.user_id}, quiz_id={self.quiz_id}, "
                f"question_id={self.question_id}, choice_id={self.choice_id})")
