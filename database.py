"""
Database module for L&D Job Board.
Handles PostgreSQL connection and Job model using SQLAlchemy.
"""

import os
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# Get database URL from environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")

# Handle Render's postgres:// vs postgresql:// issue
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine and session factory
engine = create_engine(DATABASE_URL) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine) if engine else None

# Base class for models
Base = declarative_base()


class Job(Base):
    """Job listing model."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(500))
    location = Column(String(500))
    date_posted = Column(Date)
    job_url = Column(String(2000), unique=True, nullable=False)
    description = Column(Text)
    level = Column(String(50))  # "Management+" or "Individual Contributor"
    category = Column(String(100))  # One of 5 categories
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"


def init_db():
    """Create all tables in the database."""
    if engine:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
    else:
        print("Warning: DATABASE_URL not set. Skipping database initialization.")


@contextmanager
def get_session():
    """Context manager for database sessions."""
    if not SessionLocal:
        raise RuntimeError("Database not configured. Set DATABASE_URL environment variable.")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def job_exists(session, job_url: str) -> bool:
    """Check if a job with the given URL already exists."""
    return session.query(Job).filter(Job.job_url == job_url).first() is not None


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
