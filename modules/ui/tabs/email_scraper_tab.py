#!/usr/bin/env python3
"""
Email Scraper Tab - integrates with homepage_email_scraper module
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.ui.components import (
    render_file_uploader,
    render_column_selector,
    render_progress_tracker,
    render_results_viewer
)


def render_email_scraper_tab():
    """
    Email scraper tab with homepage_email_scraper integration
    """
    st.header("📧 Email Scraper")
    st.markdown("Extract emails from websites with multi-page fallback")

    # File upload
    df = render_file_uploader(
        label="Upload CSV with websites",
        with_results_browser=True,
        results_dir="modules/ui/results/scraper",
        key_prefix="scraper_upload"
    )

    if df is not None:
        # Column selection
        st.subheader("⚙️ Configuration")

        col1, col2 = st.columns(2)

        with col1:
            # Auto-detect website column
            website_col_candidates = [col for col in df.columns if 'website' in col.lower() or 'url' in col.lower() or 'domain' in col.lower()]
            default_website = website_col_candidates[0] if website_col_candidates else None

            website_column = st.selectbox(
                "Website column",
                options=df.columns.tolist(),
                index=df.columns.tolist().index(default_website) if default_website else 0
            )

        with col2:
            # Auto-detect name column
            name_col_candidates = [col for col in df.columns if 'name' in col.lower() or 'company' in col.lower()]
            default_name = name_col_candidates[0] if name_col_candidates else None

            name_column = st.selectbox(
                "Name column (optional)",
                options=["-- Auto-generate --"] + df.columns.tolist(),
                index=df.columns.tolist().index(default_name) + 1 if default_name else 0
            )

        # Scraping options
        with st.expander("🔧 Advanced Options"):
            col1, col2, col3 = st.columns(3)

            with col1:
                workers = st.number_input("Parallel workers", min_value=1, max_value=100, value=50)
                max_pages = st.number_input("Max pages to search", min_value=1, max_value=20, value=5)

            with col2:
                scraping_mode = st.selectbox(
                    "Scraping mode",
                    options=["deep_search", "homepage_only"],
                    index=0
                )

                email_format = st.selectbox(
                    "Email output format",
                    options=["separate", "all", "primary"],
                    help="separate: one row per email | all: comma-separated | primary: first email only"
                )

            with col3:
                extract_emails = st.checkbox("Extract emails", value=True)
                limit = st.number_input("Limit rows (0 = all)", min_value=0, value=0)

        # Start scraping
        if st.button("🚀 Start Scraping", type="primary"):
            # Save uploaded file temporarily
            temp_dir = Path("temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_input = temp_dir / f"temp_input_{timestamp}.csv"

            df.to_csv(temp_input, index=False)

            # Build command
            cmd = [
                "python",
                "modules/scraping/homepage_email_scraper/scraper.py",
                "--input", str(temp_input),
                "--website-column", website_column,
                "--workers", str(workers),
                "--max-pages", str(max_pages),
                "--scraping-mode", scraping_mode,
                "--email-format", email_format
            ]

            if name_column != "-- Auto-generate --":
                cmd.extend(["--name-column", name_column])

            if not extract_emails:
                cmd.append("--no-emails")

            if limit > 0:
                cmd.extend(["--limit", str(limit)])

            # Show processing indicator
            with st.spinner(f"🚀 Scraping {len(df)} websites... This may take a few minutes."):
                try:
                    # Start scraper
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    # Wait for completion
                    stdout, stderr = process.communicate()
                    result_code = process.returncode

                    if result_code == 0:
                        st.success("✅ Scraping completed!")

                        # Parse output to find results directory
                        output_lines = stdout.split('\n')
                        results_dir = None

                        for line in output_lines:
                            if "Results saved to:" in line:
                                results_dir = line.split("Results saved to:")[-1].strip()
                                break

                        if results_dir:
                            # Load success results
                            success_file = Path(results_dir) / "success_emails.csv"

                            if success_file.exists():
                                success_df = pd.read_csv(success_file)

                                # Save to session state
                                st.session_state['scraped_data'] = success_df

                                # Show results
                                render_results_viewer(
                                    success_df,
                                    title=f"✅ Success Results ({len(success_df)} rows)",
                                    download_filename="scraped_emails.csv"
                                )

                                # Show option to proceed to validation
                                st.markdown("---")
                                st.info("💡 Results saved to session. Go to 'Email Validator' tab to validate these emails!")

                            else:
                                st.warning("Success file not found")
                        else:
                            st.warning("Could not parse results directory from output")

                    else:
                        st.error(f"Scraping failed: {stderr}")

                except Exception as e:
                    st.error(f"Error running scraper: {e}")

    # Show data from session state if available
    elif 'scraped_data' in st.session_state and st.session_state['scraped_data'] is not None:
        st.info("📊 Showing previously scraped data from session")

        render_results_viewer(
            st.session_state['scraped_data'],
            title="Scraped Results",
            download_filename="scraped_emails.csv"
        )
