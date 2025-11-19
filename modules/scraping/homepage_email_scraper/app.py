#!/usr/bin/env python3
"""
=== HOMEPAGE SCRAPER - UNIFIED STREAMLIT UI ===
Version: 4.1.0 | Updated: 2025-11-20

FEATURES:
- Live real-time progress from subprocess
- Flexible scraping modes (homepage-only vs deep search)
- Email extraction toggle + 3 output formats
- Auto-detect + manual column selection
- URL validation before processing
- Persistent results with historical browsing
- Session state for immediate results
- JSON analytics and detailed breakdowns

NEW (v4.1.0):
- Beautiful completion stats: duration, success rate, emails found
- Detailed breakdown: email sources, site types, failure reasons
- Fixed results folder path (parent instead of parent.parent in scraper.py)

FIXES (v4.0.3):
- Added working directory (cwd) for subprocess
- Debug info shows exact command and working dir
- Should fix path resolution issues

FIXES (v4.0.2):
- Fixed duplicate subprocess runs using run_clicked flag
- Optimized log updates (every 2 sec instead of every line)
- Using st.empty() for logs to prevent full reruns
- Better session state management

FIXES (v4.0.1):
- Fixed slow initial load by adding error handling
- Optimized CSV preview (read only 10 rows)
- Better exception handling in results tab
"""

import streamlit as st
import pandas as pd
import subprocess
import json
import time
import re
from pathlib import Path
from datetime import datetime
from threading import Thread
from queue import Queue

# Page configuration
st.set_page_config(
    page_title="Homepage Email Scraper",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .live-stat {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Paths
SCRIPT_PATH = Path(__file__).parent / "scraper.py"
RESULTS_DIR = Path(__file__).parent / "results"

# Initialize session state
if 'scraping_active' not in st.session_state:
    st.session_state.scraping_active = False
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'live_stats' not in st.session_state:
    st.session_state.live_stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'emails_found': 0,
        'rate': 0.0
    }
if 'run_clicked' not in st.session_state:
    st.session_state.run_clicked = False

# Helper function: Validate URL
def validate_url(url):
    """Check if string looks like a valid URL"""
    if not url or pd.isna(url):
        return False
    url_str = str(url).strip().lower()
    if not url_str:
        return False
    has_domain = ('.' in url_str and len(url_str) > 4)
    has_protocol = url_str.startswith(('http://', 'https://'))
    looks_like_url = any(x in url_str for x in ['www.', '.com', '.org', '.net', '.io', '.co'])
    return has_domain and (has_protocol or looks_like_url)

# Header
st.markdown('<div class="big-title">🔍 Homepage Email Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract emails from websites with real-time progress tracking</div>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("🎯 Scraping Mode")
    scraping_mode = st.radio(
        "Choose scraping depth",
        ["Homepage Only", "Deep Search (Homepage + 5 pages)"],
        help="Homepage Only: Fast, only main page\nDeep Search: Slower, checks contact/about/team pages if no email on homepage"
    )
    scraping_mode_param = 'homepage_only' if scraping_mode == "Homepage Only" else 'deep_search'

    st.divider()

    st.subheader("📧 Email Extraction")
    extract_emails = st.checkbox(
        "Extract emails",
        value=True,
        help="Turn off if you only want website content without emails"
    )

    if extract_emails:
        email_output_format = st.radio(
            "Email output format",
            [
                "Separate row for each email",
                "One row per company (all emails in one cell)",
                "One row per company (primary email only)"
            ],
            help="How to structure the output CSV when multiple emails are found"
        )
        if "Separate" in email_output_format:
            email_format_param = 'separate'
        elif "all emails" in email_output_format:
            email_format_param = 'all'
        else:
            email_format_param = 'primary'
    else:
        email_format_param = 'separate'

    st.divider()

    st.subheader("⚡ Performance")
    workers = st.slider(
        "Parallel workers",
        min_value=10,
        max_value=100,
        value=50,
        step=10,
        help="Higher = faster but more resource intensive"
    )

    max_pages = st.slider(
        "Max pages to check (Deep Search)",
        min_value=1,
        max_value=10,
        value=5,
        help="Only applies to Deep Search mode"
    )

    st.divider()

    st.subheader("💾 Data to Save")
    save_content = st.checkbox(
        "Save homepage content",
        value=True,
        help="Save full text content from website (disable to save space)"
    )

    save_sitemap = st.checkbox(
        "Save sitemap links",
        value=False,
        help="Extract and save all pages from sitemap"
    )

    save_social = st.checkbox(
        "Save social media links",
        value=False,
        help="Extract Facebook, Twitter, LinkedIn, Instagram links"
    )

    save_links = st.checkbox(
        "Save other links",
        value=False,
        help="Extract all other links from homepage"
    )

    save_deep_content = st.checkbox(
        "Save deep pages content",
        value=False,
        help="Save raw content from all pages visited during deep search (requires Deep Search mode)"
    )

    st.divider()

    st.subheader("🔢 Processing Limit")
    limit_rows = st.checkbox("Limit rows to process", value=False)
    if limit_rows:
        row_limit = st.number_input(
            "Process first N rows",
            min_value=1,
            max_value=10000,
            value=100,
            help="Useful for testing"
        )
    else:
        row_limit = 0

# Main content
tab1, tab2 = st.tabs(["📤 Upload & Run", "📊 View Results"])

with tab1:
    st.header("Upload CSV and run scraper")

    st.info("""
    **📋 CSV Requirements:**
    - Must have a column with website URLs (will auto-detect: 'website', 'url', 'domain', etc.)
    - Optional: 'name' or 'company_name' column
    - All original columns will be preserved in output
    """)

    uploaded_file = st.file_uploader(
        "Upload CSV with websites",
        type=['csv'],
        help="CSV file containing website URLs"
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

            # Auto-detect website column
            url_col_candidates = ['website', 'url', 'domain', 'link', 'site']
            auto_url_col = None
            for col in url_col_candidates:
                if col in df.columns:
                    auto_url_col = col
                    break

            if not auto_url_col:
                # Find column with most URLs
                for col in df.columns:
                    if df[col].astype(str).str.contains('http|www', case=False, na=False).sum() > len(df) * 0.5:
                        auto_url_col = col
                        break

            # Manual column selection
            st.subheader("🔍 Column Selection")
            col1, col2 = st.columns(2)

            with col1:
                if auto_url_col:
                    st.success(f"✅ Auto-detected URL column: **{auto_url_col}**")
                    default_url_idx = list(df.columns).index(auto_url_col)
                else:
                    st.warning("⚠️ Could not auto-detect URL column")
                    default_url_idx = 0

                url_col = st.selectbox(
                    "Select website column",
                    options=df.columns,
                    index=default_url_idx,
                    help="Column containing website URLs"
                )

            with col2:
                # Auto-detect or create name column
                auto_name_col = None
                name_candidates = ['name', 'company_name', 'company', 'business_name']
                for col in name_candidates:
                    if col in df.columns:
                        auto_name_col = col
                        break

                if not auto_name_col:
                    # Generate name from website
                    df['name'] = df[url_col].apply(lambda x: str(x).replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0] if pd.notna(x) else '')
                    auto_name_col = 'name'
                    st.info(f"✅ Generated 'name' column")

                default_name_idx = list(df.columns).index(auto_name_col) if auto_name_col in df.columns else 0

                name_col = st.selectbox(
                    "Select name column",
                    options=df.columns,
                    index=default_name_idx,
                    help="Column containing company/business name"
                )

            # Validate URLs
            st.subheader("🔍 URL Validation")
            df['_url_valid'] = df[url_col].apply(validate_url)
            valid_count = df['_url_valid'].sum()
            invalid_count = len(df) - valid_count

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Loaded", len(df))
            with col2:
                st.metric("Valid URLs", valid_count, delta=None if invalid_count == 0 else f"-{invalid_count} invalid")
            with col3:
                valid_percentage = (valid_count / len(df) * 100) if len(df) > 0 else 0
                st.metric("Valid %", f"{valid_percentage:.1f}%")

            if invalid_count > 0:
                with st.expander(f"⚠️ Show {invalid_count} invalid URLs"):
                    invalid_df = df[~df['_url_valid']][[name_col, url_col]]
                    st.dataframe(invalid_df, use_container_width=True)

            # Filter to valid URLs
            df_valid = df[df['_url_valid']].copy()
            df_valid = df_valid.drop(columns=['_url_valid'])

            if len(df_valid) == 0:
                st.error("❌ No valid URLs found! Please check your data.")
                st.stop()

            # Limit rows if needed
            if limit_rows and row_limit > 0:
                df_valid = df_valid.head(row_limit)
                st.warning(f"⚠️ Processing limited to first {row_limit} rows")

            # Preview
            st.subheader("Preview (first 10 rows)")
            preview_cols = [name_col, url_col]
            st.dataframe(df_valid[preview_cols].head(10), use_container_width=True)

            # Settings summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rows to process", len(df_valid))
            with col2:
                st.metric("Scraping mode", scraping_mode.split()[0])
            with col3:
                st.metric("Workers", workers)
            with col4:
                st.metric("Extract emails", "Yes" if extract_emails else "No")

            # Run button
            run_button = st.button("🚀 Run Scraper", type="primary", disabled=st.session_state.scraping_active, use_container_width=True)

            if run_button and not st.session_state.run_clicked:
                st.session_state.run_clicked = True
                st.session_state.scraping_active = True

                # Save uploaded file
                temp_input = RESULTS_DIR / f"temp_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                temp_input.parent.mkdir(parents=True, exist_ok=True)
                df_valid.to_csv(temp_input, index=False, encoding='utf-8-sig')

                # Build command
                cmd = [
                    "py",
                    str(SCRIPT_PATH),
                    "--input", str(temp_input),
                    "--workers", str(workers),
                    "--max-pages", str(max_pages),
                    "--scraping-mode", scraping_mode_param,
                    "--email-format", email_format_param,
                    "--website-column", url_col,
                    "--name-column", name_col
                ]

                if not extract_emails:
                    cmd.append("--no-emails")

                if not save_content:
                    cmd.append("--no-content")

                if save_sitemap:
                    cmd.append("--save-sitemap")

                if save_social:
                    cmd.append("--save-social")

                if save_links:
                    cmd.append("--save-links")

                if save_deep_content:
                    cmd.append("--save-deep-content")

                if row_limit > 0:
                    cmd.extend(["--limit", str(row_limit)])

                # Progress containers
                st.write("### 🚀 Running scraper...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                live_stats_container = st.empty()

                # Log container with empty placeholder for updates without reruns
                with st.expander("📋 Scraper logs (updates every 2sec)", expanded=False):
                    log_placeholder = st.empty()

                # Run scraper with real-time output
                try:
                    # Set working directory to scraper location for proper path resolution
                    scraper_dir = SCRIPT_PATH.parent

                    # Debug: show command
                    st.info(f"**Command:**  \n`{' '.join(cmd)}`")
                    st.info(f"**Working dir:** `{scraper_dir}`")

                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        cwd=str(scraper_dir)  # Set working directory
                    )

                    logs = []
                    last_update = time.time()

                    for line in process.stdout:
                        logs.append(line)
                        current_time = time.time()

                        # Parse progress from logs
                        if "Progress:" in line:
                            match = re.search(r'(\d+)/(\d+)', line)
                            if match:
                                processed = int(match.group(1))
                                total = int(match.group(2))
                                progress = processed / total
                                progress_bar.progress(progress)
                                status_text.text(f"Processing: {processed}/{total} websites...")

                        # Parse stats
                        if "Success:" in line:
                            success_match = re.search(r'Success: (\d+)', line)
                            failed_match = re.search(r'Failed: (\d+)', line)
                            emails_match = re.search(r'Total emails found: (\d+)', line)

                            if success_match:
                                st.session_state.live_stats['success'] = int(success_match.group(1))
                            if failed_match:
                                st.session_state.live_stats['failed'] = int(failed_match.group(1))
                            if emails_match:
                                st.session_state.live_stats['emails_found'] = int(emails_match.group(1))

                        # Update log display only every 2 seconds to reduce reruns
                        if current_time - last_update > 2.0:
                            log_placeholder.code('\n'.join(logs[-30:]), language="text")  # Show last 30 lines
                            last_update = current_time

                    # Show final logs after completion
                    log_placeholder.code('\n'.join(logs[-100:]), language="text")

                    process.wait()

                    if process.returncode == 0:
                        progress_bar.progress(1.0)
                        st.success("✅ Scraping completed successfully!")

                        # Find results folder
                        result_folders = sorted(
                            [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('scraped_')],
                            reverse=True
                        )

                        if result_folders:
                            latest_result = result_folders[0]
                            st.session_state.current_results = latest_result

                            # Load analytics for detailed stats
                            analytics_file = latest_result / "scraping_analytics.json"
                            if analytics_file.exists():
                                with open(analytics_file) as f:
                                    analytics = json.load(f)

                                # Beautiful completion summary
                                st.markdown("### 🎉 Scraping Complete!")

                                # Main metrics in columns
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric(
                                        "⏱️ Duration",
                                        f"{analytics['summary']['duration_seconds']}s",
                                        f"{analytics['summary']['sites_per_second']} sites/sec"
                                    )
                                with col2:
                                    st.metric(
                                        "✅ Success",
                                        analytics['results']['success']['count'],
                                        f"{analytics['results']['success']['percentage']}"
                                    )
                                with col3:
                                    st.metric(
                                        "📧 Emails Found",
                                        analytics['results']['success']['total_emails'],
                                        delta_color="off"
                                    )
                                with col4:
                                    st.metric(
                                        "❌ Failed",
                                        analytics['results']['failed']['total'],
                                        delta_color="inverse"
                                    )

                                # Detailed breakdown
                                with st.expander("📊 Detailed Breakdown"):
                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.markdown("**Email Sources:**")
                                        st.write(f"- From homepage: {analytics['results']['success']['from_homepage']}")
                                        st.write(f"- From deep search: {analytics['results']['success']['from_deep_search']}")

                                        st.markdown("**Site Types:**")
                                        st.write(f"- Static: {analytics['site_types']['static']}")
                                        st.write(f"- Dynamic: {analytics['site_types']['dynamic']}")

                                    with col2:
                                        st.markdown("**Failure Reasons:**")
                                        st.write(f"- Static (no email): {analytics['results']['failed']['static_no_email']['count']}")
                                        st.write(f"- Dynamic (no email): {analytics['results']['failed']['dynamic_no_email']['count']}")
                                        st.write(f"- Other errors: {analytics['results']['failed']['other_errors']['count']}")

                            st.markdown(f"""
                            <div class="success-box">
                                <strong>📁 Results saved to:</strong> {latest_result.name}<br>
                                <strong>👉 Switch to "View Results" tab to see full analytics and download files</strong>
                            </div>
                            """, unsafe_allow_html=True)

                    else:
                        st.error("❌ Scraping failed! Check logs above for details.")

                except Exception as e:
                    st.error(f"❌ Error: {e}")

                finally:
                    st.session_state.scraping_active = False
                    st.session_state.run_clicked = False
                    # Cleanup temp file
                    if temp_input.exists():
                        temp_input.unlink()

        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")

with tab2:
    st.header("📊 View Results")

    # List result folders with error handling
    try:
        if not RESULTS_DIR.exists():
            st.info("📂 No results yet. Run scraper first in the 'Upload & Run' tab!")
        else:
            result_folders = sorted(
                [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('scraped_')],
                reverse=True
            )

        if result_folders:
            # Select folder
            default_idx = 0
            if st.session_state.current_results:
                try:
                    default_idx = result_folders.index(st.session_state.current_results)
                except ValueError:
                    default_idx = 0

            selected = st.selectbox(
                "Select results:",
                options=result_folders,
                format_func=lambda x: x.name,
                index=default_idx
            )

            # Load analytics
            analytics_file = selected / "scraping_analytics.json"

            if analytics_file.exists():
                with open(analytics_file) as f:
                    analytics = json.load(f)

                # Summary metrics
                st.subheader("📈 Summary")
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

                # Detailed breakdown
                st.subheader("🔍 Breakdown")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**✅ Success:**")
                    success = analytics['results']['success']
                    st.write(f"- Companies with emails: **{success['count']}**")
                    st.write(f"- Total emails found: **{success['total_emails']}**")
                    st.write(f"- From homepage: **{success['from_homepage']}**")
                    st.write(f"- From deep search: **{success['from_deep_search']}**")

                with col2:
                    st.markdown("**❌ Failed:**")
                    failed = analytics['results']['failed']
                    st.write(f"- Static sites (no email): **{failed['static_no_email']['count']}**")
                    st.write(f"- Dynamic sites (no email): **{failed['dynamic_no_email']['count']}**")
                    st.write(f"- Other errors: **{failed['other_errors']['count']}**")

                st.divider()

                # Site types
                st.subheader("🌐 Site Types Detected")
                site_types = analytics['site_types']
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Static Sites", site_types['static'])
                with col2:
                    st.metric("Dynamic Sites (React/Vue/etc)", site_types['dynamic'])

                st.divider()

                # Download files
                st.subheader("⬇️ Download Files")

                csv_files = [f for f in selected.glob("*.csv") if 'temp_input' not in f.name]

                for csv_file in csv_files:
                    try:
                        df_file = pd.read_csv(csv_file, nrows=10)  # Read only first 10 rows for preview
                        full_row_count = sum(1 for _ in open(csv_file, encoding='utf-8-sig')) - 1  # Count total rows

                        col1, col2, col3 = st.columns([3, 1, 1])

                        with col1:
                            # Determine file type icon
                            if 'success' in csv_file.name.lower():
                                icon = "✅"
                            elif 'failed' in csv_file.name.lower():
                                icon = "❌"
                            else:
                                icon = "📄"

                            st.write(f"{icon} **{csv_file.name}** - {full_row_count} rows")

                        with col2:
                            st.download_button(
                                "Download",
                                data=csv_file.read_bytes(),
                                file_name=csv_file.name,
                                mime="text/csv",
                                key=f"download_{csv_file.name}",
                                use_container_width=True
                            )

                        with col3:
                            with st.expander("👁️ Preview"):
                                st.dataframe(df_file.head(10), use_container_width=True)

                    except Exception as csv_error:
                        st.warning(f"⚠️ Could not load {csv_file.name}: {csv_error}")

            else:
                st.warning("⚠️ No analytics found for this folder")

            if not result_folders:
                st.info("📂 No results yet. Run scraper first in the 'Upload & Run' tab!")

    except Exception as e:
        st.error(f"❌ Error loading results: {e}")
        st.info("Try refreshing the page or check the results folder manually.")

st.divider()
st.caption("Homepage Scraper v4.1.0 (Beautiful Stats) | 2025-11-20")
