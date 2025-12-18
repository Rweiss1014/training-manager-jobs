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
    page_title="L&D Job Board",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
LEVELS = ["Management+", "Individual Contributor"]
CATEGORIES = [
    "Instructional Design",
    "Training Delivery",
    "Enablement",
    "Ops & Analytics",
    "General L&D"
]

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
                'location': job.location,
                'date_posted': job.date_posted,
                'job_url': job.job_url,
                'description': job.description,
                'level': job.level,
                'category': job.category,
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


def main():
    # Header
    st.title("L&D Job Board")
    st.markdown("*Find your next Learning & Development opportunity*")
    st.divider()

    # Load data
    df = load_jobs()

    if df.empty:
        st.warning("No jobs in database yet. The scraper will populate jobs automatically, or you can trigger it manually in Render.")
        st.info("Once jobs are loaded, you'll see filters and job listings here.")
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

    # Category filter
    selected_categories = st.sidebar.multiselect(
        "Category",
        options=CATEGORIES,
        default=[],
        placeholder="All categories"
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

    # Category filter
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]

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
    display_columns = ['title', 'company', 'location', 'level', 'category', 'job_url']
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    display_df = filtered_df[available_columns].copy()

    # Rename columns for display
    column_labels = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'level': 'Level',
        'category': 'Category',
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
        "Location": st.column_config.TextColumn("Location", width="medium"),
        "Level": st.column_config.TextColumn("Level", width="small"),
        "Category": st.column_config.TextColumn("Category", width="medium"),
        "Apply": st.column_config.LinkColumn("Apply", display_text="Apply 🚀", width="small")
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
            st.markdown("**Jobs by Category:**")
            if 'category' in filtered_df.columns:
                cat_counts = filtered_df['category'].value_counts()
                st.dataframe(cat_counts, use_container_width=True)

        with col2:
            st.markdown("**Jobs by Level:**")
            if 'level' in filtered_df.columns:
                level_counts = filtered_df['level'].value_counts()
                st.dataframe(level_counts, use_container_width=True)

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


if __name__ == "__main__":
    main()
