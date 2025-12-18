"""Reset the jobs database - clears all jobs."""

from database import get_session, Job, init_db

def reset_jobs():
    """Delete all jobs from the database."""
    init_db()

    with get_session() as session:
        count = session.query(Job).count()
        session.query(Job).delete()
        session.commit()
        print(f"Deleted {count} jobs from database.")
        print("Database is now empty. Run the scraper to repopulate.")

if __name__ == "__main__":
    reset_jobs()
