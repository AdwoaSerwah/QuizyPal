#!/usr/bin/env python3
"""
Contains the BaseModel class, which serves as the base for all model classes.
This class provides common functionality like saving instances to the database,
converting objects to dictionaries, and managing instance IDs and timestamps.
"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime, timezone
import models
from typing import Optional, Dict, Any, TypeVar
from enum import Enum

# Format for converting datetime objects to string
time_format = "%Y-%m-%dT%H:%M:%S.%f"
# time_format = "%Y-%m-%dT%H:%M:%S"
Base = declarative_base()


class BaseModel():
    """
    BaseModel class that serves as the foundation for all model classes.
    It provides default functionality such as auto-generated IDs,
    timestamp management (created_at, updated_at), and methods for saving
    instances, converting to dictionaries, and deleting records from storage.
    """

    # Define columns for the model
    id: str = Column(String(60),
                     primary_key=True,
                     default=lambda: str(uuid.uuid4()))

    created_at: datetime = Column(DateTime,
                                  default=lambda: datetime.now(timezone.utc))

    updated_at: datetime = Column(DateTime,
                                  default=lambda: datetime.now(timezone.utc))

    def __init__(self, *args: Any, **kwargs: Optional[Dict[str, Any]]):
        """
        Initializes a new BaseModel instance,
        either from arguments or defaults.

        If keyword arguments are provided, they are used to set attributes.
        The 'created_at' and 'updated_at' fields are converted from string
        if passed as strings.

        Args:
            *args: Positional arguments (not used in this base class).
            **kwargs: Keyword arguments to set instance attributes.
        """
        if kwargs:
            for k, v in kwargs.items():
                if k != '__class__':  # Prevents setting class name
                    # Convert date fields from string if necessary
                    if k in ('created_at', 'updated_at') and isinstance(v, str):  # noqa
                        v = datetime.strptime(
                            v, time_format).replace(tzinfo=timezone.utc)
                    setattr(self, k, v)
        else:
            # Set default values if no kwargs are passed
            self.id = str(uuid.uuid4())
            self.created_at = datetime.now(timezone.utc)
            self.updated_at = self.created_at

    def __eq__(self, other: TypeVar('Base')) -> bool:
        """ Equality
        """
        if type(self) != type(other):
            return False
        if not isinstance(self, Base):
            return False
        return (self.id == other.id)

    def __str__(self) -> str:
        """
        Returns a string representation of the BaseModel instance.

        The string format is:
        [ClassName] (ID) {attributes}

        Returns:
            str: String representation of the instance.
        """
        return "[{:s}] ({:s}) {}".format(
            self.__class__.__name__, self.id, self.__dict__)

    def __repr__(self) -> str:
        """
        Returns a string representation of the BaseModel instance that can be
        used for debugging and logging purposes. This representation should be
        more unambiguous and detailed than the user-facing string
        representation.

        Returns:
            str: A string representation of the instance.
        """
        return (f"BaseModel(id={self.id}, "
                f"created_at={self.created_at}, "
                f"updated_at={self.updated_at})")

    def save(self) -> None:
        """
        Saves the current instance by updating the 'updated_at' timestamp
        and committing the changes to the database.

        This method also registers the instance with the storage system
        for persistence.

        Usage:
            After modifying an instance, call this method to update the record
            in the database.
        """
        self.updated_at = datetime.now(timezone.utc)
        models.storage.new(self)  # Register the instance in storage
        models.storage.save()  # Commit changes to the database

    def to_json(self, for_serialization: bool = False) -> dict:
        """ Convert the object to a JSON dictionary """
        # from models.user import Role

        result = {}
        for key, value in self.__dict__.items():
            if not for_serialization:
                if (
                    key in ['password', 'reset_token', 'token_expiry', 'is_correct']
                    or (key == 'choice_text' and value == 'no_answer')
                    or key[0] == '_'
                    ):  # noqa
                    continue

            if key == '_sa_instance_state':
                continue
            if key == "time_limit":
                key = "time_limit (in mins)"
            if type(value) is datetime:
                result[key] = value.strftime(time_format)
            elif isinstance(value, Enum):  # Check for enum and convert to string
                result[key] = value.value
            else:
                result[key] = value
        return result

    def delete(self) -> None:
        """
        Deletes the current instance from the storage system, permanently
        removing it from the database.

        This method should be used when an object needs to be deleted from
        the persistent storage.

        Usage:
            Call this method to delete an instance when it is no longer
            needed in the system.
        """
        models.storage.delete(self)  # Remove the instance from storage
