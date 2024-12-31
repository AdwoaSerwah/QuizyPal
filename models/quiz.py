#!/usr/bin/env python3
"""
Holds the class Quiz, representing a quiz in the system.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from typing import Optional


class Quiz(BaseModel, Base):
    """
    Represents a quiz in the system. Inherits from BaseModel and Base
    to enable database interaction using SQLAlchemy.

    Attributes:
        topic_id (str): The ID of the topic associated with this quiz.
        title (str): The title of the quiz.
        description (str): A brief description of the quiz (can be empty).
        created_at (datetime): The timestamp when the quiz was created.
        updated_at (datetime): The timestamp when the quiz was last updated.
    """

    __tablename__ = 'quizzes'

    # Foreign Key to associate quiz with a topic (optional, since a quiz may have no topic)
    topic_id: Optional[str] = Column(String(60), ForeignKey('topics.id', ondelete='SET NULL'), nullable=True)
    
    # Fields related to the quiz
    title: str = Column(String(128), nullable=False, unique=True)  # Ensure quiz title is unique
    description: Optional[str] = Column(String(256), nullable=True)
    time_limit: int = Column(Integer, nullable=False)

    # Relationships to link to Topic and Result tables
    topic = relationship('Topic', back_populates='quizzes')
    results = relationship('Result', back_populates='quiz', cascade="all, delete-orphan")
    questions = relationship('Question', back_populates='quiz', cascade="all, delete-orphan")
    
    # Optional relationship with UserAnswer (if needed)
    user_answers = relationship('UserAnswer', back_populates='quiz', cascade="all, delete-orphan")

    # Add indexes for optimized searches
    __table_args__ = (
        # Composite index on topic_id and id
        Index('idx_topic_id_id', 'topic_id', 'id'),
        Index('idx_title', 'title'),
    )

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a quiz object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns a string representation of the Quiz instance.

        The string format is:
        [Quiz] (ID) TopicID: topic_id, Title: title, Time Limit: time_limit

        Returns:
            str: String representation of the instance.
        """
        return f"[Quiz] ({self.id}) TopicID: {self.topic_id}, Title: {self.title}, Time Limit: {self.time_limit}s"


    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Quiz instance.

        Returns:
            str: A detailed string representation of the instance.
        """
        return (f"Quiz(id={self.id}, topic_id={self.topic_id}, title={self.title}, "
                f"description={self.description}, time_limit={self.time_limit}, "
                f"created_at={self.created_at}, updated_at={self.updated_at})")
