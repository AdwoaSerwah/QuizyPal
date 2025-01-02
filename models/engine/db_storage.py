#!/usr/bin/env python3
"""
Contains the class DBStorage for interacting with the MySQL database.
"""
from os import getenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from typing import Optional, Any, Union, List, Type, Dict

from models.base_model import Base
from models.user import User
from models.topic import Topic
from models.quiz import Quiz
from models.question import Question
from models.choice import Choice
from models.user_answer import UserAnswer
from models.result import Result
import models
# from sqlalchemy.exc import OperationalError


classes = {"User": User,
           "Topic": Topic,
           "Quiz": Quiz,
           "Question": Question,
           "Choice": Choice,
           "UserAnswer": UserAnswer,
           "Result": Result}


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
        if FLASK_ENV == "test":
            DATABASE_URL = getenv('DATABASE_TEST_URL')
        else:
            DATABASE_URL = getenv('DATABASE_URL')
        
        self.__engine = create_engine(DATABASE_URL)

        if FLASK_ENV == "test":
            # Drop all tables in the test database
            Base.metadata.drop_all(self.__engine)

    def query(self, cls):
        """Query the database using the current session."""
        return self.__session.query(cls)


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
        new_dict = {}
        if cls:
            objs = self.__session.query(cls).all()
        else:
            objs = []
            for clss in classes.values():
                objs.extend(self.__session.query(clss).all())
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

    def get_by_value(
        self, cls: Type[Base], field: str, value: Any
    ) -> Union[Optional[Any], List[Any]]:
        """
        Retrieves an object or objects based on the class name and the specified field's value.

        Args:
            cls (Type[Base]): The class type to search for.
            field (str): The field to search by (e.g., 'id', 'username', 'email').
            value (Any): The value to search for in the specified field.

        Returns:
            Union[Optional[Any], List[Any]]: A single object if exactly one match is found,
                                             a list of objects if multiple matches are found,
                                             or None if no matches are found.
        """
        if cls not in classes.values() or not hasattr(cls, field):
            return None
        try:
            query = self.__session.query(cls).filter(getattr(cls, field) == value)
            results = query.all()

            if not results:
                return None
            if len(results) == 1:
                return results[0]
            return results
        except Exception as e:
            print(f"Error querying {cls.__name__} by {field}={value}: {e}")
            return None


    def count(self, cls: Optional[Type[Base]] = None) -> int:
        """
        Counts the number of objects in storage, optionally filtering by class.

        Args:
            cls (Type[Base], optional): The class to filter by.

        Returns:
            int: The number of objects in storage.
        """
        if cls and cls in classes.values():
            return self.__session.query(cls).count()
        elif cls is None:
            count = 0
            for clss in classes.values():
                count += self.__session.query(clss).count()
            return count
        return 0
    
    def filter_by(self, cls: Type[Base], **filters) -> list:
        """
        Filters objects by specified criteria.

        Args:
            cls (Type[Base]): The class to filter.
            **filters: Field-value pairs to filter by.

        Returns:
            list: List of matching objects.
        """
        if cls not in classes.values():
            return []

        query = self.__session.query(cls)
        for field, value in filters.items():
            if hasattr(cls, field):
                query = query.filter(getattr(cls, field) == value)
        return query.all()

