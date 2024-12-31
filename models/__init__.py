#!/usr/bin/env python3
"""
Initializes the models package by setting up the storage engine and
loading any existing data into memory.
"""

# Import DBStorage class from the db_storage module in the
# engine subpackage
from models.engine.db_storage import DBStorage

# Initialize the storage engine, which will manage database operations
storage = DBStorage()
