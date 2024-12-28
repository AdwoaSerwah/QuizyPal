#!/usr/bin/env python3
"""
Contains the class DBStorage for interacting with the MySQL database.
"""

import models
from models.base_model import Base
from models.user import User
from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from typing import Optional, Dict, Type, Any

classes = {"User": User}


class DBStorage:
    """
    Interacts with the MySQL database to perform CRUD operations
    and manage sessions.
    """
    __engine: Optional[Any] = None
    __session: Optional[Any] = None

    def __init__(self) -> None:
        """
        Instantiates a DBStorage object, creates the database engine,
        and sets up a session based on the environment settings.

        If the environment is set to 'test', it drops all tables in
        the database.
        """
        FLASK_ENV = getenv('FLASK_ENV')
        DATABASE_URL = getenv('DATABASE_URL')
        self.__engine = create_engine(DATABASE_URL)

        if FLASK_ENV == "test":
            Base.metadata.drop_all(self.__engine)

    def all(self, cls: Optional[Type[Base]] = None) -> Dict[str, Base]:
        """
        Queries all objects of the given class from the database.

        If no class is specified, it returns all objects from all
        registered classes.

        Args:
            cls (Type[Base], optional): The class to filter by.

        Returns:
            Dict[str, Base]: A dictionary with keys as '<class_name>.<id>'
                             and values as the corresponding object instances.
        """
        new_dict: Dict[str, Base] = {}
        for clss in classes:
            if cls is None or cls is classes[clss] or cls is clss:
                objs = self.__session.query(classes[clss]).all()
                for obj in objs:
                    key = f"{obj.__class__.__name__}.{obj.id}"
                    new_dict[key] = obj
        return new_dict

    def new(self, obj: Base) -> None:
        """
        Adds a new object to the current database session.

        Args:
            obj (Base): The object to add to the session.
        """
        self.__session.add(obj)

    def save(self) -> None:
        """
        Commits all changes of the current database session to the database.
        """
        self.__session.commit()

    def delete(self, obj: Optional[Base] = None) -> None:
        """
        Deletes the given object from the current database session.

        Args:
            obj (Base, optional): The object to delete.
        """
        if obj is not None:
            self.__session.delete(obj)

    def reload(self) -> None:
        """
        Reloads data from the database and creates all tables defined in
        the Base model.

        Sets up a session factory and a scoped session.
        """
        Base.metadata.create_all(self.__engine)
        sess_factory = sessionmaker(bind=self.__engine, expire_on_commit=False)
        Session = scoped_session(sess_factory)
        self.__session = Session

    def close(self) -> None:
        """
        Closes the current session by calling the remove method on the
        scoped session.
        """
        self.__session.remove()

    def get(self, cls: Type[Base], id: str) -> Optional[Base]:
        """
        Retrieves an object based on the class name and its ID.

        Args:
            cls (Type[Base]): The class type to search for.
            id (str): The ID of the object to retrieve.

        Returns:
            Optional[Base]: The object if found, otherwise None.
        """
        if cls not in classes.values():
            return None

        all_cls = models.storage.all(cls)
        for value in all_cls.values():
            if value.id == id:
                return value

        return None

    def get_by_email(self, cls: Type[Base], email: str) -> Optional[Base]:
        """
        Retrieves an object based on the class name and email.

        Args:
            cls (Type[Base]): The class type to search for.
            email (str): The email to search for.

        Returns:
            Optional[Base]: The object if found, otherwise None.
        """
        if cls not in classes.values() or not hasattr(cls, 'email'):
            return None

        all_cls = self.all(cls)
        for value in all_cls.values():
            if getattr(value, 'email', None) == email:
                return value

        return None

    def get_by_username(self, cls: Type[Base], username: str) -> Optional[Base]:  # noqa
        """
        Retrieves an object based on the class name and username.

        Args:
            cls (Type[Base]): The class type to search for.
            username (str): The username to search for.

        Returns:
            Optional[Base]: The object if found, otherwise None.
        """
        if cls not in classes.values() or not hasattr(cls, 'username'):
            return None

        all_cls = self.all(cls)
        for value in all_cls.values():
            if getattr(value, 'username', None) == username:
                return value

        return None

    def get_by_token(self, token: str) -> Optional[User]:
        """
        Retrieves a user object by reset token.

        Args:
            token (str): The reset token to search for.

        Returns:
            Optional[User]: The user if found, otherwise None.
        """
        users = self.all(User).values()
        for user in users:
            if user.reset_token == token:
                return user
        return None

    def count(self, cls: Optional[Type[Base]] = None) -> int:
        """
        Counts the number of objects in storage, optionally filtering by class.

        Args:
            cls (Type[Base], optional): The class to filter by.

        Returns:
            int: The number of objects in storage.
        """
        all_class = classes.values()

        if not cls:
            count = 0
            for clas in all_class:
                count += len(models.storage.all(clas).values())
        else:
            count = len(models.storage.all(cls).values())

        return count
