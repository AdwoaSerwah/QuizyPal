#!/usr/bin/env python3
"""
Initializes the models package by setting up the storage engine and
loading any existing data into memory.

The DBStorage instance is responsible for interacting with the database
and handling the persistence of model data.

Attributes:
    storage (DBStorage): An instance of the DBStorage class used for
    database interactions and loading data.
"""

# Import DBStorage class from the db_storage module in the
# engine subpackage
from models.engine.db_storage import DBStorage

# Initialize the storage engine, which will manage database operations
storage = DBStorage()

# Reload data into memory by loading existing data from the database
storage.reload()
