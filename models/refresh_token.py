#!/usr/bin/env python3
"""
Defines the RefreshToken model for managing refresh tokens in the system.
Each token is linked to a specific user and includes expiration handling, as well as device identification.
"""

from models.base_model import BaseModel, Base
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import secrets
from typing import Optional


class RefreshToken(BaseModel, Base):
    """
    Represents a refresh token in the system. Each token is linked to a user
    and has an expiration date. Each token is also associated with a specific device.

    Attributes:
        token (str): The unique token string.
        user_id (str): Foreign key linking the token to a specific user.
        expires_at (datetime): The expiration time of the token.
        device_id (str): Unique identifier for the device associated with the token.
    """

    __tablename__ = 'refresh_tokens'

    token: str = Column(String(512), nullable=False, unique=True, index=True)
    user_id: str = Column(String(60), ForeignKey('users.id'), nullable=False, index=True)
    expires_at: datetime = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    # device_id: str = Column(String(128), nullable=False, unique=True)  # New field for device ID

    # Define a relationship back to the User model
    user = relationship('User', back_populates='refresh_tokens')
    
    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        """
        Initializes a user object, passing any arguments to the
        parent constructor.
        """
        super().__init__(*args, **kwargs)


    def generate_token(self, expiry_days: int = 7, device_id: Optional[str] = None) -> None:
        """
        Generates a new refresh token, sets its expiration time, and associates it with a device.

        Args:
            expiry_days (int): Number of days until the token expires.
            device_id (str, optional): A unique identifier for the device.
        """
        self.token = secrets.token_urlsafe(64)  # Generate a secure random token
        self.expires_at = datetime.now(timezone.utc) + timedelta(days=expiry_days)

        # If a device_id is provided, use it; otherwise, generate a new device ID
        self.device_id = device_id or self.generate_device_id()

    def generate_device_id(self) -> str:
        """
        Generates a unique device ID.

        Returns:
            str: The generated device ID.
        """
        return secrets.token_urlsafe(16)  # Generate a secure, random device ID

    def is_expired(self) -> bool:
        """
        Checks if the refresh token has expired.

        Returns:
            bool: True if the token has expired, False otherwise.
        """
        # Make sure both are timezone-aware
        now = datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None:  # If expires_at is naive
            self.expires_at = self.expires_at.replace(tzinfo=timezone.utc)
        
        return now > self.expires_at