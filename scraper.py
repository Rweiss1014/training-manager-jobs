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
# L&D ROLE VALIDATOR - Filters out non-L&D jobs
# =============================================================================

def is_valid_ld_role(title: str) -> bool:
    """
    Check if a job title is actually an L&D role.
    Returns True only if the title contains L&D-specific keywords.
    This filters out irrelevant results like 'Software Developer', 'Sales Rep', etc.
    """
    if not title:
        return False

    title_lower = title.lower()

    # Must contain at least one of these L&D-specific keywords
    ld_keywords = [
        # Training & Learning
        "training", "trainer", "learning", "l&d",
        # Instructional Design
        "instructional", "curriculum", "elearning", "e-learning", "courseware",
        # Enablement
        "enablement",
        # Development (but specifically L&D context)
        "talent development", "organizational development", "professional development",
        "leadership development", "employee development",
        # Facilitation & Coaching
        "facilitator", "facilitation", "coach", "coaching",
        # Onboarding
        "onboarding",
        # LMS & Learning Tech
        "lms", "learning management",
        # Education (corporate context)
        "corporate education", "education manager", "education director",
    ]

    # Check if any L&D keyword is in the title
    for keyword in ld_keywords:
        if keyword in title_lower:
            return True

    return False


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


def get_salary(row) -> str:
    """
    Extract and format salary from job data.
    Returns formatted salary string or None if not listed.
    """
    min_amt = row.get('min_amount')
    max_amt = row.get('max_amount')
    interval = row.get('interval')
    currency = row.get('currency', 'USD')

    # Check if we have salary data
    if pd.isna(min_amt) and pd.isna(max_amt):
        return None

    # Format the salary
    def format_amount(amt):
        if pd.isna(amt):
            return None
        amt = float(amt)
        if amt >= 1000:
            return f"${amt/1000:.0f}K"
        return f"${amt:.0f}"

    min_str = format_amount(min_amt)
    max_str = format_amount(max_amt)

    # Build salary string
    if min_str and max_str:
        salary = f"{min_str} - {max_str}"
    elif min_str:
        salary = f"{min_str}+"
    elif max_str:
        salary = f"Up to {max_str}"
    else:
        return None

    # Add interval if available
    if interval and not pd.isna(interval):
        interval_str = str(interval).lower()
        if 'year' in interval_str:
            salary += "/yr"
        elif 'hour' in interval_str:
            salary += "/hr"
        elif 'month' in interval_str:
            salary += "/mo"

    return salary


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
    total_skipped_not_ld = 0
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
                        site_name=["indeed", "linkedin", "zip_recruiter"],
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

                        # STRICT L&D FILTER - Must be an actual L&D role
                        if not is_valid_ld_role(title):
                            total_skipped_not_ld += 1
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
                            salary=get_salary(row),
                            location=str(row.get('location', ''))[:500] if row.get('location') else None,
                            date_posted=date_posted,
                            job_url=str(job_url)[:2000],
                            description=str(description) if description else None,
                            level=get_level(title),
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
    print(f"Skipped (not L&D role):     {total_skipped_not_ld}")
    print(f"Skipped (Enablement filter):{total_skipped_bouncer}")
    print("=" * 60)


if __name__ == "__main__":
    scrape_and_store()
