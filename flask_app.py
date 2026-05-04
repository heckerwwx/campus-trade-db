# This file is required by PythonAnywhere WSGI configuration
# It exposes the 'application' variable that PythonAnywhere expects

import os
import sys

# Add the project directory to the Python path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.insert(0, path)

# Initialize database before importing app
from db import init_db

db_path = os.path.join(path, 'campus_trade.db')
if not os.path.exists(db_path):
    init_db()

from app import app as application
