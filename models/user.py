#!/usr/bin/env python3
"""
Holds the class User, representing a user in the system.
This class includes methods for password encryption, password
validation, and generating reset tokens. It interacts with the
database via SQLAlchemy for data persistence.
"""

import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from bcrypt import gensalt, hashpw, checkpw
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


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
        reset_token (Optional[str]): A token used to reset the user's password.
        token_expiry (Optional[datetime]): The expiry time for the reset token.
    """

    __tablename__ = 'users'

    first_name: str = Column(String(128), nullable=False)
    last_name: str = Column(String(128), nullable=False)
    username: str = Column(String(128), nullable=False, unique=True)
    email: str = Column(String(128), nullable=False, unique=True)
    password: str = Column(String(128), nullable=False)
    reset_token: Optional[str] = Column(String(128), nullable=True)
    token_expiry: Optional[DateTime] = Column(DateTime, nullable=True)

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
            return checkpw(password.encode('utf-8'),
                           self.password.encode('utf-8'))
        return False

    def generate_reset_token(self) -> None:
        """
        Generates a secure token for password reset. The token is
        valid for 1 hour. The generated token and its expiry time
        are saved in the user's record.

        Generates a random URL-safe token and sets the expiry time to 1 hour.
        Saves the generated token and expiry time in the database.
        """
        # Generate secure reset token
        self.reset_token = secrets.token_urlsafe(64)
        # Set token expiry to 1 hour
        self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        # Save the user with the new reset token and expiry
        self.save()

    def set_password(self, raw_password: str) -> None:
        """
        Sets and encrypts the user's password using bcrypt.

        Args:
            raw_password (str): The raw password to be set for the user.

        Saves the new password and updates the user record in the database.
        """
        self.password = raw_password  # Set the new password
        self.save()  # Save the user with the updated password
