from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from backend.db_models import Base
import os

# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(__file__), "app.db")
DATABASE_URL = f"sqlite:///{db_path}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Get a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e 