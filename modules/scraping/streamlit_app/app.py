#!/usr/bin/env python3
"""
=== HOMEPAGE SCRAPER - STREAMLIT UI ===
Version: 1.0.0

Real UI for running simple_homepage_scraper.py
"""

import streamlit as st
import pandas as pd
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Homepage Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paths
SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "simple_homepage_scraper.py"
RESULTS_DIR = Path(__file__).parent.parent / "results"

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to:",
        ["📤 Upload & Run", "📊 View Results"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("""
    ### How it works:
    1. Upload CSV (only 'website' required)
    2. Configure parameters
    3. Run scraper
    4. View results

    ### Output files:
    - success_emails.csv
    - failed_static.csv
    - failed_dynamic.csv
    - failed_other.csv
    - scraping_analytics.json
    """)

# PAGE 1: Upload & Run
if page == "📤 Upload & Run":
    st.title("🔍 Homepage Email Scraper")
    st.markdown("Upload CSV and run scraper")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV with websites",
        type=['csv'],
        help="CSV must have 'website' column. 'name' is optional (auto-generated from domain if missing)"
    )

    if uploaded_file:
        # Load and validate
        df = pd.read_csv(uploaded_file)

        # Validate only website column is required
        if 'website' not in df.columns:
            st.error("Missing required column: 'website'")
        else:
            # Auto-generate name if not present
            if 'name' not in df.columns:
                df['name'] = df['website'].apply(lambda x: x.split('//')[-1].split('/')[0] if isinstance(x, str) else 'Unknown')
                st.info("Generated 'name' column from website domains")

            st.success(f"Loaded {len(df)} rows")

            # Preview
            preview_cols = ['name', 'website'] if 'name' in df.columns else ['website']
            with st.expander("Preview (first 10 rows)"):
                st.dataframe(df[preview_cols].head(10), width='stretch')

            # Settings
            st.subheader("Settings")
            col1, col2, col3 = st.columns(3)

            with col1:
                workers = st.number_input("Workers", 1, 100, 50)

            with col2:
                max_pages = st.number_input("Max pages", 1, 10, 5)

            with col3:
                limit = st.number_input("Limit (0=all)", 0, len(df), 0)

            st.divider()

            # Run button
            if st.button("🚀 Start Scraping", type="primary", use_container_width=True):
                # Save uploaded file
                temp_input = RESULTS_DIR / f"temp_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                temp_input.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(temp_input, index=False, encoding='utf-8-sig')

                # Build command
                cmd = [
                    "py",
                    str(SCRIPT_PATH),
                    "--input", str(temp_input),
                    "--workers", str(workers),
                    "--max-pages", str(max_pages)
                ]

                if limit > 0:
                    cmd.extend(["--limit", str(limit)])

                # Run scraper
                with st.spinner("Running scraper..."):
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=3600  # 1 hour max
                        )

                        if result.returncode == 0:
                            st.success("Scraping completed!")

                            # Show output
                            with st.expander("Scraper output"):
                                st.code(result.stdout, language="text")

                            # Find results folder
                            result_folders = sorted(
                                [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('scraped_')],
                                reverse=True
                            )

                            if result_folders:
                                st.info(f"Results saved to: {result_folders[0].name}")
                                st.markdown("Go to **View Results** page to see analytics")
                        else:
                            st.error("Scraping failed!")
                            st.code(result.stderr, language="text")

                    except subprocess.TimeoutExpired:
                        st.error("Scraping timeout (>1 hour)")
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        # Cleanup temp file
                        if temp_input.exists():
                            temp_input.unlink()

# PAGE 2: View Results
elif page == "📊 View Results":
    st.title("📊 View Results")

    # List result folders
    if RESULTS_DIR.exists():
        result_folders = sorted(
            [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('scraped_')],
            reverse=True
        )

        if result_folders:
            # Select folder
            selected = st.selectbox(
                "Select results:",
                options=result_folders,
                format_func=lambda x: x.name
            )

            # Load analytics
            analytics_file = selected / "scraping_analytics.json"

            if analytics_file.exists():
                with open(analytics_file) as f:
                    analytics = json.load(f)

                # Metrics
                st.subheader("Summary")
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

                # Breakdown
                st.subheader("Breakdown")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Success:**")
                    success = analytics['results']['success']
                    st.write(f"- Total emails: {success['total_emails']}")
                    st.write(f"- Homepage: {success['from_homepage']}")
                    st.write(f"- Deep search: {success['from_deep_search']}")

                with col2:
                    st.markdown("**Failed:**")
                    failed = analytics['results']['failed']
                    st.write(f"- Static: {failed['static_no_email']['count']}")
                    st.write(f"- Dynamic: {failed['dynamic_no_email']['count']}")
                    st.write(f"- Other: {failed['other_errors']['count']}")

                st.divider()

                # Download files
                st.subheader("Download Files")

                csv_files = list(selected.glob("*.csv"))

                for csv_file in csv_files:
                    df = pd.read_csv(csv_file)

                    col1, col2 = st.columns([4, 1])

                    with col1:
                        st.write(f"**{csv_file.name}** - {len(df)} rows")

                    with col2:
                        st.download_button(
                            "Download",
                            data=csv_file.read_bytes(),
                            file_name=csv_file.name,
                            mime="text/csv",
                            key=f"download_{csv_file.name}"
                        )

                    # Preview data
                    with st.expander(f"Preview {csv_file.name} (first 10 rows)"):
                        st.dataframe(df.head(10), use_container_width=True)
            else:
                st.warning("No analytics found for this folder")
        else:
            st.info("No results yet. Run scraper first!")
    else:
        st.info("No results yet. Run scraper first!")

st.divider()
st.caption("Homepage Scraper v1.0.0")
