"""
L&D Job Board Dashboard
A Streamlit frontend for browsing and filtering L&D job listings from PostgreSQL.
"""

import streamlit as st
import pandas as pd
from datetime import date

from database import get_session, Job

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="L&D Exchange - Job Board",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for landing page styling
st.markdown("""
<style>
    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Stats section */
    .stat-card {
        text-align: center;
        padding: 1rem;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #0066FF;
        margin-bottom: 0;
    }
    .stat-number.green { color: #00C853; }
    .stat-number.purple { color: #7C4DFF; }
    .stat-number.orange { color: #FF6D00; }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0;
    }

    /* Specialty cards */
    .specialty-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #0066FF;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .specialty-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .specialty-card.purple { border-left-color: #7C4DFF; }
    .specialty-card.green { border-left-color: #00C853; }
    .specialty-card.orange { border-left-color: #FF6D00; }
    .specialty-card.pink { border-left-color: #E91E63; }
    .specialty-card.teal { border-left-color: #00BCD4; }
    .specialty-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 0.3rem;
    }
    .specialty-count {
        font-size: 0.85rem;
        color: #888;
    }

    /* Section headers */
    .section-header {
        text-align: center;
        margin: 3rem 0 2rem 0;
    }
    .section-header h2 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #222;
        margin-bottom: 0.5rem;
    }
    .section-header p {
        color: #666;
        font-size: 1rem;
    }

    /* Value prop cards */
    .value-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 2rem;
        height: 100%;
    }
    .value-card h3 {
        font-size: 1.3rem;
        font-weight: 700;
        color: #222;
        margin-bottom: 1.5rem;
    }
    .value-card ul {
        list-style: none;
        padding: 0;
        margin: 0 0 1.5rem 0;
    }
    .value-card li {
        padding: 0.5rem 0;
        color: #555;
        display: flex;
        align-items: center;
    }
    .value-card li::before {
        content: "•";
        color: #0066FF;
        font-weight: bold;
        margin-right: 0.75rem;
    }

    /* Buttons */
    .btn-primary {
        background: linear-gradient(135deg, #FF6B35 0%, #F7931A 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        text-align: center;
        display: block;
        text-decoration: none;
    }
    .btn-secondary {
        background: white;
        color: #333;
        border: 1px solid #ddd;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        text-align: center;
        display: block;
        text-decoration: none;
    }

    /* Footer */
    .footer {
        background: #f8f9fa;
        padding: 3rem 0 2rem 0;
        margin-top: 4rem;
        border-top: 1px solid #e0e0e0;
    }
    .footer-col h4 {
        font-size: 0.9rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 1rem;
    }
    .footer-col p, .footer-col a {
        font-size: 0.85rem;
        color: #666;
        text-decoration: none;
        display: block;
        margin-bottom: 0.5rem;
    }
    .footer-col a:hover {
        color: #0066FF;
    }
    .footer-copyright {
        text-align: center;
        color: #999;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }

    /* Navigation style */
    .nav-button {
        background: #0066FF;
        color: white !important;
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        text-decoration: none;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Constants
LEVELS = ["Management+", "Individual Contributor"]

# Broad location terms that should always be included when filtering
BROAD_LOCATIONS = ["united states", "usa", "remote", "nationwide", "anywhere"]


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_jobs():
    """Load all jobs from the database."""
    try:
        with get_session() as session:
            jobs = session.query(Job).all()

            if not jobs:
                return pd.DataFrame()

            data = [{
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'salary': job.salary,
                'location': job.location,
                'date_posted': job.date_posted,
                'job_url': job.job_url,
                'description': job.description,
                'level': job.level,
                'created_at': job.created_at
            } for job in jobs]

            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame()


def is_broad_location(location: str) -> bool:
    """Check if location is a broad/generic term."""
    if not location:
        return False
    loc_lower = location.lower()
    return any(broad in loc_lower for broad in BROAD_LOCATIONS)


def get_state_from_location(location: str) -> str:
    """Extract state abbreviation from location string."""
    if not location:
        return ""
    # Common patterns: "City, FL" or "City, Florida"
    loc_lower = location.lower()
    if ", fl" in loc_lower or "florida" in loc_lower:
        return "florida"
    return ""


def filter_by_location(df: pd.DataFrame, selected_locations: list) -> pd.DataFrame:
    """
    Filter dataframe by selected locations.
    CRITICAL: Also include broad listings (Remote, USA, etc.) when specific cities selected.
    """
    if not selected_locations:
        return df

    def location_matches(row_location):
        if pd.isna(row_location):
            return False

        row_loc_lower = str(row_location).lower()

        # Always include broad locations
        if is_broad_location(row_location):
            return True

        # Check if row location matches any selected location
        for sel_loc in selected_locations:
            sel_loc_lower = sel_loc.lower()

            # Direct match
            if sel_loc_lower in row_loc_lower:
                return True

            # If user selected a Florida city, also include "Florida" listings
            sel_state = get_state_from_location(sel_loc)
            row_state = get_state_from_location(row_location)
            if sel_state and sel_state == row_state:
                return True

        return False

    return df[df['location'].apply(location_matches)]


def count_jobs_by_specialty(df: pd.DataFrame) -> dict:
    """Count jobs by L&D specialty based on title keywords."""
    specialties = {
        "Instructional Design": ["instructional design", "id ", "curriculum design"],
        "E-Learning Development": ["e-learning", "elearning", "digital learning", "online learning"],
        "Training & Facilitation": ["training", "facilitator", "trainer", "facilitation"],
        "Learning Management": ["learning management", "lms", "learning admin"],
        "Curriculum Development": ["curriculum", "course design", "content develop"],
        "Corporate Training": ["corporate training", "corporate learning", "workplace learning"],
        "Learning Technology": ["learning tech", "edtech", "learning system", "learning platform"],
        "Talent Development": ["talent develop", "talent management", "l&d manager", "learning director"]
    }

    counts = {}
    for specialty, keywords in specialties.items():
        count = 0
        for _, row in df.iterrows():
            title = str(row.get('title', '')).lower()
            desc = str(row.get('description', '')).lower() if row.get('description') else ''
            if any(kw in title or kw in desc for kw in keywords):
                count += 1
        counts[specialty] = count
    return counts


def render_landing_page(df: pd.DataFrame):
    """Render the landing page with stats and specialty cards."""

    # Calculate stats
    total_jobs = len(df)
    companies = df['company'].nunique() if not df.empty else 0
    remote_jobs = len(df[df['location'].str.lower().str.contains('remote', na=False)]) if not df.empty else 0

    # ============== STATS ROW ==============
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-number">{total_jobs}+</p>
            <p class="stat-label">Active Jobs</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-number green">{companies}+</p>
            <p class="stat-label">Companies Hiring</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <p class="stat-number purple">{remote_jobs}+</p>
            <p class="stat-label">Remote Positions</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="stat-card">
            <p class="stat-number orange">100%</p>
            <p class="stat-label">L&D Focused</p>
        </div>
        """, unsafe_allow_html=True)

    # ============== BROWSE BY SPECIALTY ==============
    st.markdown("""
    <div class="section-header">
        <h2>Browse by L&D Specialty</h2>
        <p>Find opportunities across all areas of Learning & Development</p>
    </div>
    """, unsafe_allow_html=True)

    # Get specialty counts
    specialty_counts = count_jobs_by_specialty(df)

    # Specialty cards in 4 columns
    specialties_config = [
        ("Instructional Design", "blue", specialty_counts.get("Instructional Design", 0)),
        ("E-Learning Development", "purple", specialty_counts.get("E-Learning Development", 0)),
        ("Training & Facilitation", "green", specialty_counts.get("Training & Facilitation", 0)),
        ("Learning Management", "orange", specialty_counts.get("Learning Management", 0)),
        ("Curriculum Development", "teal", specialty_counts.get("Curriculum Development", 0)),
        ("Corporate Training", "pink", specialty_counts.get("Corporate Training", 0)),
        ("Learning Technology", "blue", specialty_counts.get("Learning Technology", 0)),
        ("Talent Development", "purple", specialty_counts.get("Talent Development", 0)),
    ]

    # First row of 4
    cols = st.columns(4)
    for i, (name, color, count) in enumerate(specialties_config[:4]):
        with cols[i]:
            st.markdown(f"""
            <div class="specialty-card {color}">
                <div class="specialty-title">{name}</div>
                <div class="specialty-count">{count} jobs</div>
            </div>
            """, unsafe_allow_html=True)

    # Second row of 4
    cols = st.columns(4)
    for i, (name, color, count) in enumerate(specialties_config[4:]):
        with cols[i]:
            st.markdown(f"""
            <div class="specialty-card {color}">
                <div class="specialty-title">{name}</div>
                <div class="specialty-count">{count} jobs</div>
            </div>
            """, unsafe_allow_html=True)

    # ============== VALUE PROPOSITION CARDS ==============
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="value-card">
            <h3>For L&D Professionals</h3>
            <ul>
                <li>Access curated jobs from top L&D job boards</li>
                <li>Filter by specialty, location, and level</li>
                <li>Get discovered by employers seeking L&D talent</li>
                <li>Updated daily with fresh opportunities</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Browse All Jobs", type="primary", use_container_width=True):
            st.session_state.page = "jobs"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="value-card">
            <h3>For Employers & Agencies</h3>
            <ul>
                <li>Browse verified L&D professionals</li>
                <li>Post job listings to reach L&D talent</li>
                <li>Filter by skills, experience, and availability</li>
                <li>Connect directly with specialized L&D talent</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Job Listings", type="secondary", use_container_width=True):
            st.session_state.page = "jobs"
            st.rerun()

    # ============== FOOTER ==============
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.divider()

    footer_cols = st.columns(4)

    with footer_cols[0]:
        st.markdown("**L&D Exchange**")
        st.caption("The L&D Industry's Premier Job Board & Talent Network")

    with footer_cols[1]:
        st.markdown("**For Job Seekers**")
        st.caption("Browse Jobs")
        st.caption("Job Directory")
        st.caption("Job Alerts")

    with footer_cols[2]:
        st.markdown("**For Employers**")
        st.caption("Post a Job")
        st.caption("Browse Talent")
        st.caption("Pricing")

    with footer_cols[3]:
        st.markdown("**Resources**")
        st.caption("Blog")
        st.caption("About Us")
        st.caption("Contact")

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("© 2024 L&D Exchange. All rights reserved.")


def render_jobs_page(df: pd.DataFrame):
    """Render the job listings page with filters."""

    # Back to home button
    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.title("Job Listings")
    st.divider()

    if df.empty:
        st.warning("No jobs in database yet. The scraper will populate jobs automatically.")
        return

    # ============== SIDEBAR FILTERS ==============
    st.sidebar.header("Filters")

    # Level filter
    selected_levels = st.sidebar.multiselect(
        "Job Level",
        options=LEVELS,
        default=[],
        placeholder="All levels"
    )

    # Location filter
    unique_locations = sorted(df['location'].dropna().unique().tolist())
    selected_locations = st.sidebar.multiselect(
        "Location",
        options=unique_locations,
        default=[],
        placeholder="All locations",
        help="Selecting a city also shows Remote/USA/nationwide listings"
    )

    # Search filter
    search_query = st.sidebar.text_input(
        "Search Title/Company",
        placeholder="e.g., Training Manager"
    )

    # ============== APPLY FILTERS ==============
    filtered_df = df.copy()

    # Level filter
    if selected_levels:
        filtered_df = filtered_df[filtered_df['level'].isin(selected_levels)]

    # Location filter (with smart broad location logic)
    if selected_locations:
        filtered_df = filter_by_location(filtered_df, selected_locations)

    # Search filter
    if search_query:
        query_lower = search_query.lower()
        mask = (
            filtered_df['title'].str.lower().str.contains(query_lower, na=False) |
            filtered_df['company'].str.lower().str.contains(query_lower, na=False)
        )
        filtered_df = filtered_df[mask]

    # ============== METRICS HEADER ==============
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Jobs",
            value=len(filtered_df)
        )

    with col2:
        # Count jobs added today
        today = date.today()
        if 'created_at' in filtered_df.columns:
            new_today = filtered_df[
                filtered_df['created_at'].apply(
                    lambda x: x.date() == today if pd.notna(x) else False
                )
            ]
            st.metric(label="New Today", value=len(new_today))
        else:
            st.metric(label="New Today", value=0)

    with col3:
        mgmt_count = len(filtered_df[filtered_df['level'] == "Management+"])
        st.metric(label="Management+", value=mgmt_count)

    with col4:
        remote_count = len(filtered_df[
            filtered_df['location'].str.lower().str.contains('remote', na=False)
        ])
        st.metric(label="Remote", value=remote_count)

    st.divider()

    # ============== MAIN DATA VIEW ==============
    if len(filtered_df) == 0:
        st.warning("No jobs match your current filters. Try adjusting your criteria.")
        return

    # Prepare display dataframe
    display_columns = ['title', 'company', 'salary', 'location', 'level', 'job_url']
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    display_df = filtered_df[available_columns].copy()

    # Rename columns for display
    column_labels = {
        'title': 'Job Title',
        'company': 'Company',
        'salary': 'Salary',
        'location': 'Location',
        'level': 'Level',
        'job_url': 'Apply'
    }
    display_df = display_df.rename(columns=column_labels)

    # Sort by created_at (newest first) if available
    if 'created_at' in filtered_df.columns:
        display_df = display_df.iloc[filtered_df['created_at'].argsort()[::-1]]

    display_df = display_df.reset_index(drop=True)

    # Configure column display
    column_config = {
        "Job Title": st.column_config.TextColumn("Job Title", width="large"),
        "Company": st.column_config.TextColumn("Company", width="medium"),
        "Salary": st.column_config.TextColumn("Salary", width="small"),
        "Location": st.column_config.TextColumn("Location", width="medium"),
        "Level": st.column_config.TextColumn("Level", width="small"),
        "Apply": st.column_config.LinkColumn("Apply", display_text="Apply →", width="small")
    }

    st.subheader(f"Job Listings ({len(display_df)} results)")

    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    # ============== EXPANDER: STATS ==============
    with st.expander("View Statistics"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Jobs by Level:**")
            if 'level' in filtered_df.columns:
                level_counts = filtered_df['level'].value_counts()
                st.dataframe(level_counts, use_container_width=True)

        with col2:
            st.markdown("**Jobs with Salary Listed:**")
            if 'salary' in filtered_df.columns:
                has_salary = filtered_df['salary'].notna().sum()
                no_salary = filtered_df['salary'].isna().sum()
                st.metric("With Salary", has_salary)
                st.metric("No Salary", no_salary)

        st.markdown("**Top Companies:**")
        company_counts = filtered_df['company'].value_counts().head(10)
        st.dataframe(company_counts, use_container_width=True)

        # Export option
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Results (CSV)",
            data=csv_data,
            file_name="ld_jobs_export.csv",
            mime="text/csv"
        )


def main():
    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = "home"

    # Load data
    df = load_jobs()

    # Render appropriate page
    if st.session_state.page == "home":
        render_landing_page(df)
    else:
        render_jobs_page(df)


if __name__ == "__main__":
    main()
