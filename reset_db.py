"""Reset the jobs database - drops and recreates the table."""

from database import get_session, Job, init_db, engine, Base

def reset_jobs():
    """Drop and recreate the jobs table to handle schema changes."""
    print("Dropping existing jobs table...")
    Job.__table__.drop(engine, checkfirst=True)

    print("Creating new jobs table with updated schema...")
    Base.metadata.create_all(bind=engine)

    print("Database reset complete!")
    print("Run the scraper to populate with fresh data.")

if __name__ == "__main__":
    reset_jobs()
