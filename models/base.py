#!/usr/bin/env python3
"""
Base module for managing object persistence and operations.

This module provides a base class that supports basic CRUD operations
and serialization for in-memory objects, with data stored in JSON files.
"""

from datetime import datetime
from typing import TypeVar, List, Iterable
from os import path
import json
import uuid

# Constants
# Format for date-time string serialization
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"
# Global in-memory storage for all objects
DATA = {}


class Base:
    """
    A base class for defining models with automatic persistence
    and basic CRUD operations.

    This class is intended to be inherited by other models in the application
    that need to be stored, retrieved, and manipulated. Objects of this class
    can be saved to a JSON file and retrieved from it.

    The class also supports equality checks, object serialization, and
    basic search functionality.
    """

    def __init__(self, *args: list, **kwargs: dict):
        """
        Initialize an instance of the Base class with attributes.

        Args:
            *args: Positional arguments, not used in this implementation but
                   can be extended by subclasses.

            **kwargs: Keyword arguments to initialize object attributes.
                      The 'id', 'created_at', and 'updated_at' attributes
                      are handled automatically. If they are not provided,
                      defaults are used.

                      - id (str): Unique identifier for the object (UUID).
                      - created_at (datetime): Timestamp when the object
                                               was created.
                      - updated_at (datetime): Timestamp when the object was
                                               last updated.
        """
        s_class = str(self.__class__.__name__)
        if DATA.get(s_class) is None:
            DATA[s_class] = {}

        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.created_at = datetime.strptime(kwargs.get(
            'created_at', datetime.utcnow().strftime(TIMESTAMP_FORMAT)),
            TIMESTAMP_FORMAT)
        self.updated_at = datetime.strptime(kwargs.get(
            'updated_at', datetime.utcnow().strftime(TIMESTAMP_FORMAT)),
            TIMESTAMP_FORMAT)

    def __eq__(self, other: TypeVar('Base')) -> bool:
        """
        Compare this instance with another instance for equality.

        Args:
            other: Another instance of the Base class to compare with.

        Returns:
            bool: True if both objects have the same class and the same id,
                  otherwise False.
        """
        if type(self) != type(other):
            return False
        if not isinstance(self, Base):
            return False
        return self.id == other.id

    def to_json(self, for_serialization: bool = False) -> dict:
        """
        Convert the object into a dictionary suitable for JSON serialization.

        Args:
            for_serialization (bool): If True, includes all attributes,
            including private ones (those starting with '_').

        Returns:
            dict: A dictionary representation of the object's attributes.
        """
        result = {}
        for key, value in self.__dict__.items():
            if not for_serialization and key[0] == '_':
                continue
            if isinstance(value, datetime):
                result[key] = value.strftime(TIMESTAMP_FORMAT)
            else:
                result[key] = value
        return result

    @classmethod
    def load_from_file(cls):
        """
        Load all objects of the class from the corresponding JSON file.

        The class data is loaded into the global `DATA` dictionary, where each
        object is indexed by its ID.

        This method reads the class-specific JSON file
        (e.g., `.db_ClassName.json`) and loads all stored objects into memory.
        """
        s_class = cls.__name__
        file_path = f".db_{s_class}.json"
        DATA[s_class] = {}

        if not path.exists(file_path):
            return

        with open(file_path, 'r') as f:
            objs_json = json.load(f)
            for obj_id, obj_json in objs_json.items():
                DATA[s_class][obj_id] = cls(**obj_json)

    @classmethod
    def save_to_file(cls):
        """
        Save all objects of the class to the corresponding JSON file.

        All objects of the class are serialized to JSON and written to a file
        (e.g., `.db_ClassName.json`). This method persists changes to the
        in-memory `DATA` dictionary to disk.
        """
        s_class = cls.__name__
        file_path = f".db_{s_class}.json"
        objs_json = {}
        for obj_id, obj in DATA[s_class].items():
            objs_json[obj_id] = obj.to_json(True)

        with open(file_path, 'w') as f:
            json.dump(objs_json, f)

    def save(self):
        """
        Save the current object to the global in-memory store and
        persist it to a file.

        The object's `updated_at` timestamp is updated, and
        the object is saved to the in-memory `DATA` dictionary.

        Changes are then saved to the corresponding JSON file.
        """
        s_class = self.__class__.__name__
        self.updated_at = datetime.utcnow()
        DATA[s_class][self.id] = self
        self.__class__.save_to_file()

    def remove(self):
        """
        Remove the object from the global in-memory store and
        delete it from the file.

        This method deletes the object from the `DATA` dictionary and persists
        the change to the JSON file.
        """
        s_class = self.__class__.__name__
        if self.id in DATA[s_class]:
            del DATA[s_class][self.id]
            self.__class__.save_to_file()

    @classmethod
    def count(cls) -> int:
        """
        Count the total number of objects of this class.

        Returns:
            int: The number of objects currently stored for this class.
        """
        s_class = cls.__name__
        return len(DATA[s_class])

    @classmethod
    def all(cls) -> Iterable[TypeVar('Base')]:
        """
        Retrieve all objects of this class.

        Returns:
            list: A list of all objects stored for this class.
        """
        return cls.search()

    @classmethod
    def get(cls, id: str) -> TypeVar('Base'):
        """
        Retrieve a single object by its ID.

        Args:
            id (str): The ID of the object to retrieve.

        Returns:
            Base: The object with the specified ID, or None if not found.
        """
        s_class = cls.__name__
        return DATA[s_class].get(id)

    @classmethod
    def search(cls, attributes: dict = {}) -> List[TypeVar('Base')]:
        """
        Search for objects that match a set of attributes.

        Args:
            attributes (dict): A dictionary of attribute-value
                               pairs to search for.

        Returns:
            list: A list of objects that match the specified attributes.
        """
        s_class = cls.__name__

        def _search(obj):
            if not attributes:
                return True
            for k, v in attributes.items():
                if getattr(obj, k) != v:
                    return False
            return True

        return [obj for obj in DATA[s_class].values() if _search(obj)]
