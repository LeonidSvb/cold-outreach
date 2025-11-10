#!/usr/bin/env python3
"""
=== UNIVERSAL WEBSITE SCRAPER - STREAMLIT UI ===
Version: 1.0.0 | Created: 2025-11-10

USAGE:
streamlit run modules/scraping/ui/streamlit_app.py

FEATURES:
- CSV upload with URL validation
- Flexible scraping configuration
- Real-time progress tracking
- Results preview and download
- Time and cost estimation
- Batch processing
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import subprocess
import tempfile
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.scraping.lib.stats_tracker import estimate_time
    from modules.scraping.scripts.website_scraper import process_website
except ImportError:
    st.error("Failed to import scraping modules. Make sure you're running from project root.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Website Scraper",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
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

# Header
st.markdown('<div class="main-header">🌐 Universal Website Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Extract emails, phones, and content from websites at scale</div>', unsafe_allow_html=True)

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'scraping_complete' not in st.session_state:
    st.session_state.scraping_complete = False

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Scraping Settings")

    # Processing mode
    mode = st.selectbox(
        "Processing Mode",
        ["quick", "standard", "full", "custom"],
        help="""
        quick: Only static/dynamic detection (~0.05 sec/site)
        standard: Scraping + emails/phones (~0.5 sec/site)
        full: Everything including AI (~3.0 sec/site)
        custom: Fine-tune individual settings
        """
    )

    st.divider()

    # Custom settings (show if mode is custom)
    if mode == "custom":
        st.subheader("🔧 Custom Configuration")

        check_static = st.checkbox(
            "Check Static/Dynamic",
            value=True,
            help="Detect if website is static or dynamic"
        )

        extract_emails = st.checkbox(
            "Extract Emails",
            value=True,
            help="Find all email addresses on the website"
        )

        extract_phones = st.checkbox(
            "Extract Phones",
            value=True,
            help="Find all phone numbers"
        )

        scrape_mode = st.selectbox(
            "Scraping Mode",
            ["single", "smart", "all"],
            index=1,
            help="""
            single: Homepage only
            smart: Important pages (contact, about, team)
            all: All accessible pages
            """
        )

        ai_analysis = st.checkbox(
            "AI Analysis",
            value=False,
            help="Run AI analysis on scraped content (slower, costs money)"
        )
    else:
        # Auto-configure based on mode
        if mode == "quick":
            check_static = True
            extract_emails = False
            extract_phones = False
            scrape_mode = "single"
            ai_analysis = False
        elif mode == "standard":
            check_static = True
            extract_emails = True
            extract_phones = True
            scrape_mode = "smart"
            ai_analysis = False
        else:  # full
            check_static = True
            extract_emails = True
            extract_phones = True
            scrape_mode = "smart"
            ai_analysis = True

    st.divider()

    # Performance settings
    st.subheader("⚡ Performance")

    workers = st.slider(
        "Parallel Workers",
        min_value=5,
        max_value=100,
        value=25,
        step=5,
        help="Number of concurrent threads. More = faster but higher load"
    )

    timeout = st.slider(
        "Request Timeout (sec)",
        min_value=5,
        max_value=30,
        value=15,
        help="Max time to wait for website response"
    )

    st.divider()

    # Advanced settings
    with st.expander("🔬 Advanced"):
        max_text_length = st.number_input(
            "Max Text Length",
            min_value=5000,
            max_value=50000,
            value=15000,
            step=5000,
            help="Maximum text length for AI processing"
        )

# Main content area
tab1, tab2, tab3 = st.tabs(["📊 Start Scraping", "📁 View Results", "💰 Estimator"])

with tab1:
    st.header("Upload CSV and Start Scraping")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV file with URLs",
        type=['csv'],
        help="CSV must contain a column named: 'url', 'website', 'Website', or 'URL'"
    )

    if uploaded_file is not None:
        # Load and preview
        df = pd.read_csv(uploaded_file)

        # Find URL column
        url_column = None
        for col in ['url', 'website', 'Website', 'URL']:
            if col in df.columns:
                url_column = col
                break

        if url_column is None:
            st.error("❌ No URL column found. Expected columns: 'url', 'website', 'Website', or 'URL'")
            st.stop()

        # Show preview
        st.subheader("Data Preview")
        st.dataframe(df.head(10), use_container_width=True)

        # Stats
        total_urls = df[url_column].notna().sum()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Rows", len(df))
        with col2:
            st.metric("Valid URLs", total_urls)
        with col3:
            st.metric("Workers", workers)
        with col4:
            # Estimate time
            estimation = estimate_time(total_urls, mode if mode != "custom" else "standard", workers)
            est_minutes = estimation['estimated_minutes']
            st.metric("Est. Time", f"{est_minutes} min")

        st.divider()

        # Configuration summary
        st.subheader("Current Configuration")
        config_col1, config_col2 = st.columns(2)

        with config_col1:
            st.markdown(f"""
            **Mode:** {mode}
            **Workers:** {workers}
            **Timeout:** {timeout}s
            """)

        with config_col2:
            st.markdown(f"""
            **Check Static:** {'✅' if check_static else '❌'}
            **Extract Emails:** {'✅' if extract_emails else '❌'}
            **Extract Phones:** {'✅' if extract_phones else '❌'}
            **Scrape Mode:** {scrape_mode}
            **AI Analysis:** {'✅' if ai_analysis else '❌'}
            """)

        st.divider()

        # Start button
        if st.button("🚀 Start Scraping", type="primary", use_container_width=True):

            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_input:
                df.to_csv(tmp_input.name, index=False)
                input_path = tmp_input.name

            # Create output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = Path(f"modules/scraping/results/scraped_{timestamp}.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build command
            cmd = [
                sys.executable,
                "modules/scraping/scripts/website_scraper.py",
                "--input", input_path,
                "--output", str(output_path),
                "--workers", str(workers),
                "--timeout", str(timeout),
                "--max-text-length", str(max_text_length)
            ]

            # Add mode or individual flags
            if mode != "custom":
                cmd.extend(["--mode", mode])
            else:
                if check_static:
                    cmd.append("--check-static")
                if extract_emails:
                    cmd.append("--extract-emails")
                if extract_phones:
                    cmd.append("--extract-phones")
                if ai_analysis:
                    cmd.append("--ai-analysis")
                cmd.extend(["--scrape-mode", scrape_mode])

            # Create progress containers
            progress_bar = st.progress(0, text="Initializing scraper...")
            status_container = st.container()
            metrics_container = st.container()

            try:
                # Run scraper
                with status_container:
                    st.info(f"🔄 Processing {total_urls} URLs with {workers} workers...")

                start_time = time.time()

                # Run subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Track progress
                processed = 0
                last_update = time.time()

                for line in process.stdout:
                    # Parse progress from output
                    if "Processed" in line or "/" in line:
                        # Update progress bar
                        processed += 1
                        progress = min(processed / total_urls, 1.0)
                        progress_bar.progress(progress, text=f"Processing... {processed}/{total_urls}")

                        # Update every 2 seconds to avoid too many updates
                        if time.time() - last_update > 2:
                            elapsed = time.time() - start_time
                            rate = processed / elapsed if elapsed > 0 else 0
                            remaining = (total_urls - processed) / rate if rate > 0 else 0

                            with metrics_container:
                                met_col1, met_col2, met_col3 = st.columns(3)
                                with met_col1:
                                    st.metric("Processed", f"{processed}/{total_urls}")
                                with met_col2:
                                    st.metric("Rate", f"{rate:.1f}/sec")
                                with met_col3:
                                    st.metric("Remaining", f"{remaining/60:.1f} min")

                            last_update = time.time()

                process.wait()

                if process.returncode == 0:
                    # Success
                    progress_bar.progress(1.0, text="Complete!")

                    elapsed_time = time.time() - start_time
                    elapsed_minutes = int(elapsed_time / 60)
                    elapsed_seconds = int(elapsed_time % 60)

                    st.markdown(f"""
                    <div class="success-box">
                        <h3>✅ Scraping Complete!</h3>
                        <p><strong>Total URLs:</strong> {total_urls}</p>
                        <p><strong>Time:</strong> {elapsed_minutes}m {elapsed_seconds}s</p>
                        <p><strong>Results:</strong> {str(output_path)}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Load and display results
                    if output_path.exists():
                        results_df = pd.read_csv(output_path)
                        st.session_state.results = results_df
                        st.session_state.scraping_complete = True

                        st.subheader("Preview of Results")
                        st.dataframe(results_df.head(20), use_container_width=True)

                        # Download buttons
                        col1, col2 = st.columns(2)

                        with col1:
                            csv_data = results_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download CSV",
                                csv_data,
                                f"scraped_results_{timestamp}.csv",
                                "text/csv",
                                use_container_width=True
                            )

                        with col2:
                            json_data = results_df.to_json(orient='records', indent=2)
                            st.download_button(
                                "📄 Download JSON",
                                json_data,
                                f"scraped_results_{timestamp}.json",
                                "application/json",
                                use_container_width=True
                            )

                        # Show statistics
                        st.subheader("Statistics")
                        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

                        with stats_col1:
                            success_count = (results_df['status'] == 'success').sum()
                            st.metric("Success", success_count)

                        with stats_col2:
                            if 'emails_count' in results_df.columns:
                                email_count = results_df['emails_count'].sum()
                                st.metric("Emails Found", int(email_count))

                        with stats_col3:
                            if 'phones_count' in results_df.columns:
                                phone_count = results_df['phones_count'].sum()
                                st.metric("Phones Found", int(phone_count))

                        with stats_col4:
                            avg_time = results_df['processing_time'].mean()
                            st.metric("Avg Time/URL", f"{avg_time:.2f}s")

                else:
                    # Error
                    stderr_output = process.stderr.read()
                    st.error(f"❌ Scraping failed with return code {process.returncode}")
                    st.code(stderr_output)

            except Exception as e:
                st.error(f"❌ Error during scraping: {str(e)}")
                st.exception(e)

            finally:
                # Cleanup temp file
                try:
                    Path(input_path).unlink()
                except:
                    pass

    else:
        st.info("👆 Upload a CSV file to get started")

with tab2:
    st.header("View Past Results")

    # List available results files
    results_dir = Path("modules/scraping/results")

    if results_dir.exists():
        result_files = sorted(list(results_dir.glob("*.csv")), reverse=True)

        if result_files:
            st.info(f"Found {len(result_files)} result files")

            # Show most recent files
            for file in result_files[:20]:  # Show last 20
                with st.expander(f"📄 {file.name}"):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        # File info
                        size_mb = file.stat().st_size / 1024 / 1024
                        modified = datetime.fromtimestamp(file.stat().st_mtime)
                        st.text(f"Size: {size_mb:.2f} MB")
                        st.text(f"Modified: {modified.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        # Load data
                        if st.button("👁️ Preview", key=f"preview_{file.name}"):
                            df = pd.read_csv(file)
                            st.dataframe(df.head(10))

                    with col3:
                        # Download
                        df = pd.read_csv(file)
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download",
                            csv_data,
                            file.name,
                            "text/csv",
                            key=f"download_{file.name}"
                        )
        else:
            st.info("No results found yet. Run a scraping job first!")
    else:
        st.warning("Results directory not found.")

with tab3:
    st.header("Time & Cost Estimator")

    st.markdown("""
    ### Estimation Tool
    Plan your scraping jobs with accurate time and cost estimates.
    """)

    # Calculator inputs
    calc_col1, calc_col2 = st.columns(2)

    with calc_col1:
        calc_urls = st.number_input(
            "Number of URLs",
            min_value=1,
            max_value=100000,
            value=1000,
            step=100
        )

        calc_mode = st.selectbox(
            "Mode",
            ["quick", "standard", "full"],
            index=1
        )

    with calc_col2:
        calc_workers = st.slider(
            "Workers",
            min_value=5,
            max_value=100,
            value=25,
            step=5
        )

    # Calculate estimation
    estimation = estimate_time(calc_urls, calc_mode, calc_workers)

    st.divider()

    # Display results
    st.subheader("Estimated Results")

    result_col1, result_col2, result_col3 = st.columns(3)

    with result_col1:
        st.metric(
            "Total Time",
            f"{estimation['estimated_minutes']} minutes"
        )

    with result_col2:
        rate_per_sec = calc_urls / estimation['estimated_seconds']
        st.metric(
            "Processing Rate",
            f"{rate_per_sec:.1f} URLs/sec"
        )

    with result_col3:
        per_url_time = estimation['estimated_seconds'] / calc_urls
        st.metric(
            "Time per URL",
            f"{per_url_time:.2f} sec"
        )

    st.divider()

    # Mode comparison
    st.subheader("Mode Comparison")

    comparison_data = []
    for compare_mode in ["quick", "standard", "full"]:
        est = estimate_time(calc_urls, compare_mode, calc_workers)
        comparison_data.append({
            'Mode': compare_mode.title(),
            'Time (min)': est['estimated_minutes'],
            'Time per URL (sec)': est['estimated_seconds'] / calc_urls,
            'Features': {
                'quick': 'Detection only',
                'standard': 'Scraping + Emails + Phones',
                'full': 'Everything + AI'
            }[compare_mode]
        })

    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)

    st.divider()

    # Tips
    st.subheader("💡 Optimization Tips")
    st.markdown("""
    - **Quick mode** for filtering static/dynamic sites before heavy scraping
    - **Standard mode** for most lead generation tasks (best balance)
    - **Full mode** only when you need AI analysis (expensive)
    - Increase workers for faster processing (but watch your system resources)
    - Use timeout wisely: too low = missed data, too high = slow on dead sites
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Universal Website Scraper</strong> v1.0.0</p>
    <p>Built with Streamlit | HTTP-only scraping</p>
</div>
""", unsafe_allow_html=True)
