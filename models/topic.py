#!/usr/bin/env python3
"""
Holds the class Topic, representing a topic in the system.
This class interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional


class Topic(BaseModel, Base):
    """
    Represents a topic in the system. Inherits from BaseModel and Base
    to enable database interaction using SQLAlchemy.

    Attributes:
        name (str): The name of the topic.
        parent_id (Optional[int]): The ID of the parent topic, allowing for a hierarchical structure.
    """

    __tablename__ = 'topics'

    # Column for the topic name, unique and not nullable
    name: str = Column(String(128), nullable=False, unique=True, index=True)

    # Column for the parent topic ID to establish hierarchy (nullable to allow top-level topics)
    parent_id: Optional[str] = Column(
        String(60), 
        ForeignKey('topics.id', ondelete='CASCADE'), 
        nullable=True
    )

    # Relationship to self to represent parent-child relationship
    # parent = relationship('Topic', remote_side=[Topic.id], backref='subtopics')
    # parent = relationship('Topic', remote_side=['id'], backref='subtopics')
    parent = relationship('Topic', remote_side=lambda: [Topic.id], backref='subtopics')

    # Relationship with the Quiz table
    quizzes = relationship('Quiz', back_populates='topic', passive_deletes=True)

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a topic object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        """
        Returns a string representation of the Topic instance.

        The string format is:
        [Topic] (ID) Name: name, Parent ID: parent_id

        Returns:
            str: String representation of the instance.
        """
        return f"[Topic] ({self.id}) Name: {self.name}, Parent ID: {self.parent_id}"

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Topic instance.

        Returns:
            str: A more detailed string representation of the instance.
        """
        return (f"Topic(id={self.id}, name={self.name}, parent_id={self.parent_id}, "
                f"created_at={self.created_at}, updated_at={self.updated_at})")
