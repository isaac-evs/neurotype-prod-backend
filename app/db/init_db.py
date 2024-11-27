from app.db.session import engine
from app.db.base import Base

def init_db():
    """
    Initialize the database with all models.
    If tables already exist, this will not recreate them.
    """
    Base.metadata.create_all(bind=engine)
