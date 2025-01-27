#!/usr/bin/env python3
"""
Holds the class User, representing a user in the system.
This class includes methods for password encryption and password
validation. It interacts with the database via SQLAlchemy for data persistence.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Enum, DateTime  # Import Enum
from sqlalchemy.orm import relationship
from bcrypt import gensalt, hashpw, checkpw
from datetime import datetime, timezone, timedelta
import secrets
from typing import Optional
import enum


class Role(enum.Enum):
    """
    Enum for User roles. It defines the possible roles in the system.
    """
    USER = "user"
    ADMIN = "admin"

    @classmethod
    def from_str(cls, role_str: str) -> 'Role':
        """
        Convert a string to a Role enum member.

        Args:
            role_str (str): The string representation of the role.

        Returns:
            Role: Corresponding Role enum member.
        """
        for role in cls:
            if role.value == role_str.lower():
                return role
        raise ValueError(f"Invalid role: {role_str}. Must be one of {[r.value for r in cls]}")


class User(BaseModel, Base):
    """
    Represents a user in the system. Inherits from BaseModel and Base to enable
    database interaction using SQLAlchemy.

    Attributes:
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        username (str): The user's unique username (max length 10).
        email (str): The user's unique email address.
        password (str): The user's encrypted password.
        role (str): The user's role, defined using the Role Enum.
    """

    __tablename__ = 'users'

    first_name: str = Column(String(128), nullable=False)
    last_name: str = Column(String(128), nullable=False)
    username: str = Column(String(128), unique=True, nullable=False, index=True)
    email: str = Column(String(128), unique=True, nullable=False, index=True)
    password: str = Column(String(128), nullable=False)
    role: Role = Column(Enum(Role), default=Role.USER, nullable=False, index=True)
    reset_token: Optional[str] = Column(String(128), unique=True, nullable=True)
    token_expiry: Optional[datetime] = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))

    # One-to-many relationships with cascade delete
    results: list = relationship('Result', back_populates='user', cascade="all, delete-orphan")
    user_answers: list = relationship('UserAnswer', back_populates='user', cascade="all, delete-orphan")
    # Update the User model to include the relationship
    refresh_tokens = relationship('RefreshToken', back_populates='user', cascade="all, delete-orphan")


    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a user object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)

    def __setattr__(self, name: str, value: str) -> None:
        """
        Encrypts the password when setting the 'password' attribute.
        The password is hashed using bcrypt with a salt for secure storage.

        Args:
            name (str): The name of the attribute being set.
            value (str): The value being assigned to the attribute.
        """
        if name == "password":
            # Check if the value is already hashed
            if not value.startswith("$2b$"):
                # Encrypt the password using bcrypt
                salt = gensalt()
                value = hashpw(value.encode('utf-8'), salt).decode('utf-8')

        # Call the parent class's __setattr__ method to store the value
        super().__setattr__(name, value)

    def check_password(self, password: str) -> bool:
        """
        Checks if the provided password matches the stored hashed password.

        Args:
            password (str): The password to be checked.

        Returns:
            bool: True if the password matches the stored hash,
                  False otherwise.
        """
        if self.password:
            return checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        return False

    def set_password(self, raw_password: str) -> None:
        """
        Sets and encrypts the user's password using bcrypt.

        Args:
            raw_password (str): The raw password to be set for the user.

        Saves the new password and updates the user record in the database.
        """
        self.password = raw_password  # Set the new password
        self.save()  # Save the user with the updated password

    def generate_reset_token(self) -> None:
        """
        Generates a password reset token and sets its expiration.

        The token is a secure random string and expires in 1 hour.
        """
        self.reset_token = secrets.token_urlsafe(64)
        self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
        self.save()  # Save to the database
