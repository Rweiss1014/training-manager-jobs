"""
Broad Search Job Scraper for Training Manager and related roles.
Searches multiple job titles across multiple locations, then applies smart filtering.
"""

from jobspy import scrape_jobs
import pandas as pd
import time

# Search parameters
search_terms = [
    "Training Manager",
    "Learning and Development Manager",
    "L&D Manager",
    "Talent Development Manager",
    "Sales Enablement Manager",
    "Organizational Development Manager",
    "Manager of Corporate Training",
    "Instructional Design Manager"
]

locations = [
    "Remote",
    "Orlando, FL",
    "Maitland, FL",
    "Altamonte Springs, FL"
]

# Filter word lists (all lowercase for case-insensitive matching)
TOPIC_WORDS = ['training', 'learning', 'l&d', 'development', 'enablement', 'instructional', 'education']
LEVEL_WORDS = ['manager', 'director', 'head', 'lead', 'principal', 'vp']


def smart_filter(title: str) -> bool:
    """
    Check if title contains at least one Topic word AND at least one Level word.
    Case-insensitive matching.
    """
    if pd.isna(title):
        return False

    title_lower = title.lower()

    has_topic = any(word in title_lower for word in TOPIC_WORDS)
    has_level = any(word in title_lower for word in LEVEL_WORDS)

    return has_topic and has_level


def scrape_all_jobs():
    """
    Scrape jobs for all search terms and locations.
    Returns a combined DataFrame of all results.
    """
    all_jobs = []
    total_searches = len(search_terms) * len(locations)
    current_search = 0

    for search_term in search_terms:
        for location in locations:
            current_search += 1
            print(f"[{current_search}/{total_searches}] Searching: '{search_term}' in '{location}'...")

            try:
                jobs = scrape_jobs(
                    site_name=["indeed", "linkedin", "glassdoor"],
                    search_term=search_term,
                    location=location,
                    hours_old=720,  # 30 days
                    results_wanted=30,
                    country_indeed='USA'
                )

                if jobs is not None and len(jobs) > 0:
                    print(f"    Found {len(jobs)} jobs")
                    all_jobs.append(jobs)
                else:
                    print(f"    No jobs found")

            except Exception as e:
                print(f"    Error: {e}")
                continue

            # Small delay to be respectful to job sites
            time.sleep(1)

    if not all_jobs:
        return pd.DataFrame()

    return pd.concat(all_jobs, ignore_index=True)


def main():
    print("=" * 60)
    print("BROAD SEARCH JOB SCRAPER")
    print("=" * 60)
    print(f"Search Terms: {len(search_terms)}")
    print(f"Locations: {len(locations)}")
    print(f"Total Searches: {len(search_terms) * len(locations)}")
    print("=" * 60)
    print()

    # Scrape all jobs
    print("Starting job scrape...")
    raw_df = scrape_all_jobs()

    if raw_df.empty:
        print("\nNo jobs were found. Please check your search parameters.")
        return

    raw_count = len(raw_df)
    print(f"\n{'=' * 60}")
    print(f"TOTAL RAW JOBS FOUND: {raw_count}")
    print("=" * 60)

    # Deduplicate by job_url
    print("\nRemoving duplicates...")
    df = raw_df.drop_duplicates(subset=['job_url'], keep='first')
    deduped_count = len(df)
    print(f"After deduplication: {deduped_count} jobs (removed {raw_count - deduped_count} duplicates)")

    # Apply smart filter
    print("\nApplying smart filter (Topic + Level words)...")
    df['passes_filter'] = df['title'].apply(smart_filter)
    filtered_df = df[df['passes_filter']].drop(columns=['passes_filter'])
    filtered_count = len(filtered_df)
    print(f"After filtering: {filtered_count} jobs (removed {deduped_count - filtered_count} non-matching)")

    # Save to CSV
    output_file = "broad_training_leads.csv"
    filtered_df.to_csv(output_file, index=False)
    print(f"\nSaved {filtered_count} jobs to '{output_file}'")

    # Print summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Total raw jobs found:      {raw_count}")
    print(f"After deduplication:       {deduped_count}")
    print(f"After smart filtering:     {filtered_count}")
    print("=" * 60)

    # Print top 10 jobs
    if filtered_count > 0:
        print("\nTOP 10 JOBS:")
        print("-" * 60)

        display_cols = ['title', 'company', 'location', 'job_url']
        available_cols = [col for col in display_cols if col in filtered_df.columns]

        top_10 = filtered_df.head(10)[available_cols]

        for idx, row in top_10.iterrows():
            print(f"\n{top_10.index.get_loc(idx) + 1}. {row.get('title', 'N/A')}")
            print(f"   Company:  {row.get('company', 'N/A')}")
            print(f"   Location: {row.get('location', 'N/A')}")
            print(f"   URL:      {row.get('job_url', 'N/A')}")

    print("\n" + "=" * 60)
    print("SCRAPE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
