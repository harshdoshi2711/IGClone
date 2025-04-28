# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your actual PostgreSQL details
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/igclone"

# SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency for getting DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
