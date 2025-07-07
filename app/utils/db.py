# app/utils/db.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# SQLite connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./splitx.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ✅ Add this function to fix the ImportError
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
