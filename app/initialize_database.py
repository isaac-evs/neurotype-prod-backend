import sys
import os

# Add the root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.init_db import init_db

if __name__ == "__main__":
    print("Initializing the database...")
    init_db()
    print("Database initialized successfully!")
