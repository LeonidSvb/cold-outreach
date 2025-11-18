#!/usr/bin/env python3
"""
=== HOMEPAGE SCRAPER - STREAMLIT UI ===
Version: 1.0.0

Simple minimalist UI for running homepage scraper
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Homepage Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'scraper_running' not in st.session_state:
    st.session_state.scraper_running = False

if 'results_path' not in st.session_state:
    st.session_state.results_path = None

# Main page
st.title("🔍 Homepage Email Scraper")
st.markdown("Simple HTTP-based email scraper with multi-page fallback")

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")

    page = st.radio(
        "Go to:",
        ["📤 Upload & Run", "📊 View Results", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("""
    ### How it works:
    1. Upload CSV with websites
    2. Configure scraping parameters
    3. Run scraper with live progress
    4. View results & analytics
    """)

# Route to pages
if page == "📤 Upload & Run":
    st.header("📤 Upload & Run Scraper")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV with websites",
        type=['csv'],
        help="CSV must have 'name' and 'website' columns"
    )

    if uploaded_file:
        # Preview data
        df = pd.read_csv(uploaded_file)

        st.success(f"✓ Loaded {len(df)} rows")

        # Validate columns
        required_cols = ['name', 'website']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        else:
            # Show preview
            with st.expander("Preview data (first 10 rows)"):
                st.dataframe(df[['name', 'website']].head(10))

            # Settings
            col1, col2, col3 = st.columns(3)

            with col1:
                workers = st.number_input(
                    "Workers",
                    min_value=1,
                    max_value=100,
                    value=50,
                    help="Parallel workers for scraping"
                )

            with col2:
                max_pages = st.number_input(
                    "Max pages per site",
                    min_value=1,
                    max_value=10,
                    value=5,
                    help="Pages to search if homepage has no email"
                )

            with col3:
                limit = st.number_input(
                    "Limit (0 = all)",
                    min_value=0,
                    max_value=len(df),
                    value=0,
                    help="Limit for testing (0 = process all)"
                )

            st.divider()

            # Run button
            if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
                st.session_state.scraper_running = True
                st.info("Scraping started! Check terminal for live progress...")
                st.markdown("*Note: Progress updates appear in terminal where Streamlit is running*")

elif page == "📊 View Results":
    st.header("📊 View Results")

    # List available results
    results_dir = Path(__file__).parent.parent / "results"

    if results_dir.exists():
        result_folders = sorted([f for f in results_dir.iterdir() if f.is_dir()], reverse=True)

        if result_folders:
            selected_folder = st.selectbox(
                "Select results:",
                options=result_folders,
                format_func=lambda x: x.name
            )

            if selected_folder:
                # Load analytics
                analytics_file = selected_folder / "scraping_analytics.json"
                if analytics_file.exists():
                    import json
                    with open(analytics_file) as f:
                        analytics = json.load(f)

                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Sites", analytics['summary']['total_sites'])

                    with col2:
                        st.metric("Success Rate", analytics['summary']['success_rate'])

                    with col3:
                        st.metric("Duration", f"{analytics['summary']['duration_minutes']} min")

                    with col4:
                        st.metric("Speed", f"{analytics['summary']['sites_per_second']} sites/sec")

                    st.divider()

                    # Results breakdown
                    st.subheader("Results Breakdown")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Success:**")
                        st.write(f"- Total emails: {analytics['results']['success']['total_emails']}")
                        st.write(f"- From homepage: {analytics['results']['success']['from_homepage']}")
                        st.write(f"- From deep search: {analytics['results']['success']['from_deep_search']}")

                    with col2:
                        st.markdown("**Failed:**")
                        st.write(f"- Static (no email): {analytics['results']['failed']['static_no_email']['count']}")
                        st.write(f"- Dynamic (no email): {analytics['results']['failed']['dynamic_no_email']['count']}")
                        st.write(f"- Other errors: {analytics['results']['failed']['other_errors']['count']}")

                    st.divider()

                    # Load and display CSV files
                    st.subheader("Download Results")

                    csv_files = list(selected_folder.glob("*.csv"))

                    for csv_file in csv_files:
                        df = pd.read_csv(csv_file)

                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**{csv_file.name}** - {len(df)} rows")

                        with col2:
                            st.download_button(
                                "Download",
                                data=csv_file.read_bytes(),
                                file_name=csv_file.name,
                                mime="text/csv"
                            )
        else:
            st.info("No results yet. Run scraper first!")
    else:
        st.info("No results yet. Run scraper first!")

elif page == "⚙️ Settings":
    st.header("⚙️ Settings")

    st.markdown("""
    ### Email Cleaning Rules

    Automatic filters applied:
    - ✓ Remove NPS generic emails (abli_*@nps.gov)
    - ✓ Remove webmaster/postmaster emails
    - ✓ Fix truncated emails (.co → .com)
    - ✓ Remove duplicate emails
    - ✓ Validate email format

    ### Scraping Strategy

    1. Try homepage first (fast)
    2. If no email → deep search (5 pages)
    3. Clean & deduplicate results
    4. Split into 4 files (success, failed_static, failed_dynamic, failed_other)

    ### File Outputs

    - `success_emails.csv` - Found emails with content
    - `failed_static.csv` - Static sites without email
    - `failed_dynamic.csv` - Dynamic sites without email
    - `failed_other.csv` - Connection errors
    - `scraping_analytics.json` - Detailed metrics
    """)

st.divider()
st.caption("Built with Streamlit | Homepage Scraper v1.0.0")
