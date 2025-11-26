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
import time
import json

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
            progress_file = temp_dir / f"scraping_progress_{timestamp}.json"

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
                "--email-format", email_format,
                "--progress-file", str(progress_file)
            ]

            if name_column != "-- Auto-generate --":
                cmd.extend(["--name-column", name_column])

            if not extract_emails:
                cmd.append("--no-emails")

            if limit > 0:
                cmd.extend(["--limit", str(limit)])

            # Real-time progress tracking
            progress_bar = st.progress(0)
            status_container = st.container()

            with status_container:
                col1, col2, col3, col4 = st.columns(4)
                processed_metric = col1.empty()
                emails_metric = col2.empty()
                speed_metric = col3.empty()
                eta_metric = col4.empty()

                stats_expander = st.expander("📊 Detailed Stats", expanded=False)
                with stats_expander:
                    stats_text = st.empty()

            try:
                # Start scraper in background
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Monitor progress in real-time
                while process.poll() is None:
                    # Read progress file
                    if progress_file.exists():
                        try:
                            with open(progress_file, 'r') as f:
                                progress_data = json.load(f)

                            # Update progress bar
                            progress_pct = progress_data.get('progress_pct', 0) / 100
                            progress_bar.progress(min(progress_pct, 1.0))

                            # Update metrics
                            processed = progress_data.get('processed', 0)
                            total = progress_data.get('total', 0)
                            processed_metric.metric(
                                "Processed",
                                f"{processed}/{total}",
                                delta=f"{progress_data.get('progress_pct', 0):.1f}%"
                            )

                            custom_stats = progress_data.get('custom_stats', {})
                            emails_metric.metric(
                                "Emails Found",
                                custom_stats.get('emails_found', 0)
                            )

                            speed_metric.metric(
                                "Speed",
                                f"{progress_data.get('speed', 0):.1f}/sec"
                            )

                            eta_metric.metric(
                                "ETA",
                                progress_data.get('eta_str', 'Calculating...')
                            )

                            # Detailed stats
                            stats_text.markdown(f"""
**Status:** {progress_data.get('status', 'running')}
**Elapsed Time:** {progress_data.get('elapsed_str', '0:00:00')}
**Success:** {custom_stats.get('success', 0)}
**Failed:** {custom_stats.get('failed', 0)}
**Static Sites:** {custom_stats.get('static_sites', 0)}
**Dynamic Sites:** {custom_stats.get('dynamic_sites', 0)}
                            """)

                        except (json.JSONDecodeError, IOError):
                            pass

                    # Wait before next check
                    time.sleep(0.5)

                # Get final result
                stdout, stderr = process.communicate()
                result_code = process.returncode

                # Clean up progress file
                if progress_file.exists():
                    try:
                        progress_file.unlink()
                    except:
                        pass

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
