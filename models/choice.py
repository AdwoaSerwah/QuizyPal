#!/usr/bin/env python3
"""
Holds the class Choice, representing a choice for a question in the system.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from typing import Optional


class Choice(BaseModel, Base):
    """
    Represents a choice for a question in the system. Inherits from BaseModel
    and Base to enable database interaction using SQLAlchemy.

    Attributes:
        question_id (str): The ID of the question to which this choice belongs.
        choice_text (str): The text of the choice.
        is_correct (bool): A flag to indicate whether the choice is correct or not.
        created_at (datetime): The timestamp when the choice was created.
        updated_at (datetime): The timestamp when the choice was last updated.
    """

    __tablename__ = 'choices'

    question_id: str = Column(String(60), ForeignKey('questions.id'), nullable=False, index=True)
    choice_text: str = Column(String(255), nullable=False)
    is_correct: bool = Column(Boolean, nullable=False, default=False)
    order_number: int = Column(Integer, nullable=False)  # New field

    # Relationship with Question table
    question = relationship('Question', back_populates='choices')

    # Relationship with UserAnswer table
    user_answers = relationship('UserAnswer', back_populates='choice', cascade="all, delete-orphan")

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a choice object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        """
        Returns a string representation of the Choice instance.

        Returns:
            str: A detailed string representation of the instance.
        """
        return (f"Choice(id={self.id}, question_id={self.question_id}, choice_text={self.choice_text}, "
                f"is_correct={self.is_correct}, created_at={self.created_at}, updated_at={self.updated_at})")
