import sys
import os

# Ensure the correct module path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import the necessary modules
from app.db.session import engine
from app.db.base import Base

def delete_and_recreate_database():
    """
    Drops all tables and recreates the database schema.
    """
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped successfully!")

    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    print("Starting database deletion and recreation...")
    delete_and_recreate_database()
    print("Database operations completed successfully!")
