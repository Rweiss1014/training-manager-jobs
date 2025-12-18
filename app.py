"""
Training Manager Job Scraper Dashboard
A Streamlit frontend for browsing and filtering job leads.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Training Manager Jobs Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants for scoring
TOPIC_WORDS = ['training', 'learning', 'l&d', 'development', 'enablement', 'instructional', 'education']
LEVEL_WORDS = ['manager', 'director', 'head', 'lead', 'principal', 'vp', 'vice president', 'senior']


def calculate_match_score(title: str) -> int:
    """
    Calculate a match score (0-100) based on topic and level word matches.
    """
    if pd.isna(title) or not title:
        return 0

    title_lower = title.lower()

    # Count topic word matches (max 3 points)
    topic_matches = sum(1 for word in TOPIC_WORDS if word in title_lower)
    topic_score = min(topic_matches, 3) * 20  # 0, 20, 40, or 60

    # Count level word matches (max 2 points)
    level_matches = sum(1 for word in LEVEL_WORDS if word in title_lower)
    level_score = min(level_matches, 2) * 20  # 0, 20, or 40

    return min(topic_score + level_score, 100)


@st.cache_data
def load_data():
    """Load and preprocess the job data."""
    csv_path = Path("broad_training_leads.csv")

    if not csv_path.exists():
        return None

    df = pd.read_csv(csv_path)

    # Calculate match scores
    df['match_score'] = df['title'].apply(calculate_match_score)

    # Clean up location data
    df['location'] = df['location'].fillna('Not Specified')

    # Ensure job_url exists
    if 'job_url' not in df.columns:
        df['job_url'] = ''

    return df


def categorize_location(location: str) -> str:
    """Categorize location as Remote, Florida, or Other."""
    if pd.isna(location):
        return 'Other'
    loc_lower = location.lower()
    if 'remote' in loc_lower:
        return 'Remote'
    elif 'fl' in loc_lower or 'florida' in loc_lower:
        return 'Florida'
    return 'Other'


def main():
    # Header
    st.title("Training Manager Jobs Dashboard")
    st.markdown("*Find your next Learning & Development opportunity*")
    st.divider()

    # Load data
    df = load_data()

    if df is None or df.empty:
        st.error("No data found! Please run `scrape_training.py` first to generate job leads.")
        st.code('"C:\\Training Manager Jobs\\venv\\Scripts\\python.exe" "C:\\Training Manager Jobs\\scrape_training.py"')
        return

    # Add location category for metrics
    df['location_category'] = df['location'].apply(categorize_location)

    # ============== SIDEBAR FILTERS ==============
    st.sidebar.header("🔍 Filters")

    # Location filter
    unique_locations = sorted(df['location'].unique().tolist())
    selected_locations = st.sidebar.multiselect(
        "📍 Location",
        options=unique_locations,
        default=[],
        placeholder="All locations"
    )

    # Search filter
    search_query = st.sidebar.text_input(
        "🔎 Search Title/Company",
        placeholder="e.g., Training Manager, Zillow"
    )

    # Score slider
    min_score = st.sidebar.slider(
        "⭐ Minimum Match Score",
        min_value=0,
        max_value=100,
        value=0,
        step=10,
        help="Filter by relevance score (higher = better match)"
    )

    st.sidebar.divider()
    st.sidebar.markdown("### About Match Scores")
    st.sidebar.markdown("""
    - **80-100**: Excellent match
    - **60-79**: Good match
    - **40-59**: Moderate match
    - **0-39**: Weak match
    """)

    # ============== APPLY FILTERS ==============
    filtered_df = df.copy()

    # Location filter
    if selected_locations:
        filtered_df = filtered_df[filtered_df['location'].isin(selected_locations)]

    # Search filter
    if search_query:
        query_lower = search_query.lower()
        mask = (
            filtered_df['title'].str.lower().str.contains(query_lower, na=False) |
            filtered_df['company'].str.lower().str.contains(query_lower, na=False)
        )
        filtered_df = filtered_df[mask]

    # Score filter
    filtered_df = filtered_df[filtered_df['match_score'] >= min_score]

    # ============== METRICS HEADER ==============
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📊 Total Jobs",
            value=len(filtered_df),
            delta=f"of {len(df)} total" if len(filtered_df) != len(df) else None
        )

    with col2:
        remote_count = len(filtered_df[filtered_df['location_category'] == 'Remote'])
        st.metric(
            label="🏠 Remote Roles",
            value=remote_count
        )

    with col3:
        florida_count = len(filtered_df[filtered_df['location_category'] == 'Florida'])
        st.metric(
            label="🌴 Florida Roles",
            value=florida_count
        )

    with col4:
        avg_score = filtered_df['match_score'].mean() if len(filtered_df) > 0 else 0
        st.metric(
            label="⭐ Avg Match Score",
            value=f"{avg_score:.0f}"
        )

    st.divider()

    # ============== MAIN DATA VIEW ==============
    if len(filtered_df) == 0:
        st.warning("No jobs match your current filters. Try adjusting your criteria.")
        return

    # Prepare display dataframe
    display_columns = ['title', 'company', 'location', 'match_score', 'job_url']
    available_columns = [col for col in display_columns if col in filtered_df.columns]

    display_df = filtered_df[available_columns].copy()

    # Rename columns for display
    column_labels = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'match_score': 'Match Score',
        'job_url': 'Apply'
    }
    display_df = display_df.rename(columns=column_labels)

    # Sort by match score descending
    display_df = display_df.sort_values('Match Score', ascending=False).reset_index(drop=True)

    # Configure column display
    column_config = {
        "Job Title": st.column_config.TextColumn(
            "Job Title",
            width="large"
        ),
        "Company": st.column_config.TextColumn(
            "Company",
            width="medium"
        ),
        "Location": st.column_config.TextColumn(
            "Location",
            width="medium"
        ),
        "Match Score": st.column_config.ProgressColumn(
            "Match Score",
            help="Relevance score based on title keywords",
            format="%d",
            min_value=0,
            max_value=100,
        ),
        "Apply": st.column_config.LinkColumn(
            "Apply",
            display_text="Apply Now 🚀",
            width="small"
        )
    }

    st.subheader(f"📋 Job Listings ({len(display_df)} results)")

    st.dataframe(
        display_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=500
    )

    # ============== EXPANDER: RAW DATA & LOGS ==============
    with st.expander("📁 View Raw Data & Details"):
        st.markdown("### Full Dataset Preview")

        # Show all columns
        all_columns = filtered_df.columns.tolist()
        selected_cols = st.multiselect(
            "Select columns to display:",
            options=all_columns,
            default=['title', 'company', 'location', 'date_posted', 'job_type', 'match_score']
        )

        if selected_cols:
            st.dataframe(
                filtered_df[selected_cols],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("### Data Statistics")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Top Companies:**")
            company_counts = filtered_df['company'].value_counts().head(10)
            st.dataframe(company_counts, use_container_width=True)

        with col2:
            st.markdown("**Location Distribution:**")
            location_counts = filtered_df['location_category'].value_counts()
            st.dataframe(location_counts, use_container_width=True)

        st.markdown("### Export Options")
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Results (CSV)",
            data=csv_data,
            file_name="filtered_training_jobs.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
