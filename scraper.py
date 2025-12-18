"""
L&D Job Scraper with Smart Tagging and Enablement Bouncer.
Scrapes job listings and stores them in PostgreSQL.
"""

import time
from datetime import datetime

from jobspy import scrape_jobs
import pandas as pd

from database import init_db, get_session, Job, job_exists


# Search configuration
SEARCH_TERMS = [
    "Learning and Development",
    "Instructional Designer",
    "Corporate Trainer",
    "Sales Enablement",
    "Talent Development"
]

LOCATIONS = [
    "Remote",
    "Orlando, FL",
    "Maitland, FL",
    "Altamonte Springs, FL"
]

# Scraping parameters
HOURS_OLD = 720  # 30 days
RESULTS_WANTED = 20  # Per search term/location combo


# =============================================================================
# ENABLEMENT BOUNCER
# =============================================================================

def is_valid_enablement_role(title: str, description: str) -> bool:
    """
    Filter out Ops/Admin roles masquerading as Enablement.
    Returns True if the role is a valid L&D/Training enablement role.
    Only apply this check if 'enablement' is in the title.
    """
    # 1. Immediate Disqualification (Ops/Admin keywords)
    ops_keywords = [
        "deal desk", "revops", "revenue operations", "sales operations",
        "crm admin", "salesforce", "quota", "pipeline", "forecasting"
    ]
    title_lower = str(title).lower() if title else ""
    if any(k in title_lower for k in ops_keywords):
        return False

    # 2. Must have L&D keyword in title OR description
    learning_keywords = [
        "training", "learning", "facilitation", "coaching", "onboarding",
        "curriculum", "content", "instructional", "development"
    ]

    # Check title first
    if any(k in title_lower for k in learning_keywords):
        return True

    # Check description if provided
    if description:
        desc_lower = str(description).lower()
        if any(k in desc_lower for k in learning_keywords):
            return True

    return False


# =============================================================================
# SMART TAGGING
# =============================================================================

def get_level(title: str) -> str:
    """
    Determine job level based on title.
    Returns 'Management+' or 'Individual Contributor'.
    """
    if not title:
        return "Individual Contributor"

    title_lower = title.lower()
    level_keywords = ["manager", "director", "vp", "chief", "head", "lead"]

    if any(k in title_lower for k in level_keywords):
        return "Management+"

    return "Individual Contributor"


def get_category(title: str) -> str:
    """
    Categorize job based on title keywords.
    Returns one of 5 categories.
    """
    if not title:
        return "General L&D"

    title_lower = title.lower()

    # Check categories in order of specificity
    if any(k in title_lower for k in ["instructional", "curriculum", "elearning", "storyline"]):
        return "Instructional Design"

    if any(k in title_lower for k in ["trainer", "facilitation", "onboarding"]):
        return "Training Delivery"

    if "enablement" in title_lower:
        return "Enablement"

    if any(k in title_lower for k in ["analyst", "lms", "ops", "admin"]):
        return "Ops & Analytics"

    return "General L&D"


# =============================================================================
# SCRAPING LOGIC
# =============================================================================

def scrape_and_store():
    """Main function to scrape jobs and store in database."""
    print("=" * 60)
    print("L&D JOB SCRAPER")
    print("=" * 60)
    print(f"Search Terms: {len(SEARCH_TERMS)}")
    print(f"Locations: {len(LOCATIONS)}")
    print(f"Total Searches: {len(SEARCH_TERMS) * len(LOCATIONS)}")
    print(f"Lookback: {HOURS_OLD} hours ({HOURS_OLD // 24} days)")
    print("=" * 60)
    print()

    # Initialize database tables
    init_db()

    total_found = 0
    total_new = 0
    total_skipped_duplicate = 0
    total_skipped_bouncer = 0

    current_search = 0
    total_searches = len(SEARCH_TERMS) * len(LOCATIONS)

    with get_session() as session:
        for search_term in SEARCH_TERMS:
            for location in LOCATIONS:
                current_search += 1
                print(f"[{current_search}/{total_searches}] '{search_term}' in '{location}'...")

                try:
                    jobs_df = scrape_jobs(
                        site_name=["indeed", "linkedin", "glassdoor"],
                        search_term=search_term,
                        location=location,
                        hours_old=HOURS_OLD,
                        results_wanted=RESULTS_WANTED,
                        country_indeed='USA'
                    )

                    if jobs_df is None or jobs_df.empty:
                        print(f"    No jobs found")
                        continue

                    found_count = len(jobs_df)
                    total_found += found_count
                    print(f"    Found {found_count} jobs")

                    # Process each job
                    for _, row in jobs_df.iterrows():
                        job_url = row.get('job_url', '')
                        title = row.get('title', '')
                        description = row.get('description', '')

                        # Skip if no URL
                        if not job_url:
                            continue

                        # Check for duplicates
                        if job_exists(session, job_url):
                            total_skipped_duplicate += 1
                            continue

                        # Apply Enablement Bouncer if "enablement" in title
                        if title and "enablement" in str(title).lower():
                            if not is_valid_enablement_role(title, description):
                                total_skipped_bouncer += 1
                                continue

                        # Parse date_posted
                        date_posted = None
                        if pd.notna(row.get('date_posted')):
                            try:
                                date_posted = pd.to_datetime(row['date_posted']).date()
                            except Exception:
                                pass

                        # Create job record with smart tagging
                        job = Job(
                            title=str(title)[:500] if title else None,
                            company=str(row.get('company', ''))[:500] if row.get('company') else None,
                            location=str(row.get('location', ''))[:500] if row.get('location') else None,
                            date_posted=date_posted,
                            job_url=str(job_url)[:2000],
                            description=str(description) if description else None,
                            level=get_level(title),
                            category=get_category(title),
                            created_at=datetime.utcnow()
                        )

                        session.add(job)
                        total_new += 1

                except Exception as e:
                    print(f"    Error: {e}")
                    continue

                # Small delay between searches
                time.sleep(1)

        # Commit all new jobs
        session.commit()

    # Print summary
    print()
    print("=" * 60)
    print("SCRAPE COMPLETE")
    print("=" * 60)
    print(f"Total jobs found:           {total_found}")
    print(f"New jobs added to DB:       {total_new}")
    print(f"Skipped (duplicate):        {total_skipped_duplicate}")
    print(f"Skipped (Enablement filter):{total_skipped_bouncer}")
    print("=" * 60)


if __name__ == "__main__":
    scrape_and_store()
