import os
import sys

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from db import init_db

# Initialize DB if not exists
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_trade.db')
if not os.path.exists(db_path):
    init_db()

if __name__ == '__main__':
    app.run()
