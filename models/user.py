#!/usr/bin/env python3
"""
Holds the class User, representing a user in the system.
This class includes methods for password encryption and password
validation. It interacts with the database via SQLAlchemy for data persistence.
"""

import models
from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, Boolean  # Include Boolean
from sqlalchemy.orm import relationship
from bcrypt import gensalt, hashpw, checkpw
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
        is_admin (bool): Indicates if the user is an admin.
    """

    __tablename__ = 'users'

    first_name: str = Column(String(128), nullable=False)
    last_name: str = Column(String(128), nullable=False)
    username: str = Column(String(128), unique=True, nullable=False, index=True)
    email: str = Column(String(128), unique=True, nullable=False, index=True)
    password: str = Column(String(128), nullable=False)
    is_admin: bool = Column(Boolean, default=False, nullable=False)

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

    def set_password(self, raw_password: str) -> None:
        """
        Sets and encrypts the user's password using bcrypt.

        Args:
            raw_password (str): The raw password to be set for the user.

        Saves the new password and updates the user record in the database.
        """
        self.password = raw_password  # Set the new password
        self.save()  # Save the user with the updated password
