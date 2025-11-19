#!/usr/bin/env python3
"""
=== HOMEPAGE EMAIL SCRAPER - STREAMLIT UI (Enhanced) ===
Version: 3.0.0 | Created: 2025-11-19

FEATURES:
- Live real-time progress updates
- Flexible scraping modes (homepage-only vs deep search)
- Email extraction on/off toggle
- Multiple email output formats
- Session isolation
- Real-time statistics

USAGE:
streamlit run modules/scraping/ui/streamlit_homepage_scraper.py
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html, clean_html_to_text
    from modules.scraping.lib.sitemap_utils import SitemapParser
except ImportError:
    st.error("Failed to import scraping modules")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Homepage Email Scraper",
    page_icon="🔍",
    layout="wide"
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
    .success-metric {
        background: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">🔍 Homepage Email Scraper</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract emails from websites with real-time progress tracking</div>', unsafe_allow_html=True)

# Initialize session state
if 'scraping_active' not in st.session_state:
    st.session_state.scraping_active = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'stats' not in st.session_state:
    st.session_state.stats = {
        'total': 0,
        'processed': 0,
        'success': 0,
        'failed': 0,
        'emails_found': 0
    }

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("🎯 Scraping Mode")
    scraping_mode = st.radio(
        "Choose scraping depth",
        ["Homepage Only", "Deep Search (Homepage + 5 pages)"],
        help="Homepage Only: Fast, only main page\nDeep Search: Slower, checks contact/about/team pages if no email on homepage"
    )

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
                "One row per company (all emails in one cell)",
                "One row per company (primary email only)",
                "Separate row for each email"
            ],
            help="How to structure the output CSV when multiple emails are found"
        )
    else:
        email_output_format = None

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

            st.success(f"✅ Loaded {len(df)} rows")

            # Limit rows if needed
            if limit_rows and row_limit > 0:
                df = df.head(row_limit)
                st.warning(f"⚠️ Processing limited to first {row_limit} rows")

            # Preview
            st.subheader("Preview (first 10 rows)")
            st.dataframe(df[[name_col, url_col]].head(10), use_container_width=True)

            # Settings summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Rows to process", len(df))
                st.metric("Scraping mode", scraping_mode)
            with col2:
                st.metric("Workers", workers)
                st.metric("Extract emails", "Yes" if extract_emails else "No")

            # Run button
            if st.button("🚀 Run Scraper", type="primary", disabled=st.session_state.scraping_active):
                st.session_state.scraping_active = True
                st.session_state.stats = {
                    'total': len(df),
                    'processed': 0,
                    'success': 0,
                    'failed': 0,
                    'emails_found': 0
                }

                # Initialize HTTP client
                http_client = HTTPClient(timeout=15, retries=3)
                sitemap_parser = SitemapParser(timeout=15)

                # Progress containers
                st.write("### Running scraper...")
                progress_bar = st.progress(0)
                status_text = st.empty()
                live_stats = st.empty()

                # Results storage
                results = []
                lock = threading.Lock()

                # Scraping function
                def scrape_website(row_data):
                    website = row_data[url_col]
                    name = row_data.get(name_col, '')

                    result = {
                        'name': name,
                        'website': website,
                        'email': '',
                        'homepage_content': '',
                        'site_type': '',
                        'scrape_status': 'failed',
                        'error_message': '',
                        'email_source': ''
                    }

                    try:
                        # Fetch homepage
                        html, site_type = http_client.fetch_with_detection(website)
                        result['site_type'] = site_type

                        if not html:
                            result['error_message'] = 'Failed to fetch homepage'
                            return result

                        # Extract content
                        content = clean_html_to_text(html)
                        result['homepage_content'] = content[:15000] if content else ''

                        # Extract emails if enabled
                        if extract_emails:
                            emails = extract_emails_from_html(html)

                            # If no emails on homepage and deep search enabled
                            if not emails and scraping_mode == "Deep Search (Homepage + 5 pages)":
                                # Try additional pages
                                additional_pages = sitemap_parser.get_important_pages(website, max_pages=max_pages)
                                for page_url in additional_pages[:max_pages]:
                                    try:
                                        page_html, _ = http_client.fetch_with_detection(page_url)
                                        if page_html:
                                            page_emails = extract_emails_from_html(page_html)
                                            if page_emails:
                                                emails.extend(page_emails)
                                                result['email_source'] = f'deep_search_{page_url}'
                                                break
                                    except:
                                        continue

                            if emails:
                                # Handle different output formats
                                if email_output_format == "One row per company (all emails in one cell)":
                                    result['email'] = ', '.join(list(set(emails)))
                                    result['scrape_status'] = 'success'
                                    result['email_source'] = result['email_source'] or 'homepage'
                                    with lock:
                                        st.session_state.stats['emails_found'] += len(list(set(emails)))
                                    return [result]

                                elif email_output_format == "One row per company (primary email only)":
                                    result['email'] = emails[0]
                                    result['scrape_status'] = 'success'
                                    result['email_source'] = result['email_source'] or 'homepage'
                                    with lock:
                                        st.session_state.stats['emails_found'] += 1
                                    return [result]

                                else:  # Separate row for each email
                                    results_list = []
                                    for email in list(set(emails)):
                                        email_result = result.copy()
                                        email_result['email'] = email
                                        email_result['scrape_status'] = 'success'
                                        email_result['email_source'] = result['email_source'] or 'homepage'
                                        results_list.append(email_result)
                                    with lock:
                                        st.session_state.stats['emails_found'] += len(emails)
                                    return results_list
                            else:
                                result['error_message'] = 'No emails found'
                        else:
                            # No email extraction, just content
                            result['scrape_status'] = 'success'
                            return [result]

                    except Exception as e:
                        result['error_message'] = str(e)

                    return [result]

                # Process in parallel
                start_time = time.time()

                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {executor.submit(scrape_website, row.to_dict()): idx
                              for idx, row in df.iterrows()}

                    for future in as_completed(futures):
                        try:
                            row_results = future.result()
                            results.extend(row_results)

                            # Update stats
                            with lock:
                                st.session_state.stats['processed'] += 1
                                if any(r['scrape_status'] == 'success' for r in row_results):
                                    st.session_state.stats['success'] += 1
                                else:
                                    st.session_state.stats['failed'] += 1

                                # Update progress
                                progress = st.session_state.stats['processed'] / st.session_state.stats['total']
                                progress_bar.progress(progress)

                                elapsed = time.time() - start_time
                                rate = st.session_state.stats['processed'] / elapsed if elapsed > 0 else 0
                                remaining = (st.session_state.stats['total'] - st.session_state.stats['processed']) / rate if rate > 0 else 0

                                status_text.text(
                                    f"[{st.session_state.stats['processed']}/{st.session_state.stats['total']}] "
                                    f"Success: {st.session_state.stats['success']} | "
                                    f"Failed: {st.session_state.stats['failed']} | "
                                    f"Emails: {st.session_state.stats['emails_found']} | "
                                    f"Rate: {rate:.1f}/s | ETA: {remaining:.0f}s"
                                )

                                # Live stats display
                                live_stats.markdown(f"""
                                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 1rem 0;">
                                    <div class="live-stat">
                                        <div style="font-size: 2rem; font-weight: 700;">{st.session_state.stats['processed']}</div>
                                        <div>Processed</div>
                                    </div>
                                    <div class="live-stat">
                                        <div style="font-size: 2rem; font-weight: 700;">{st.session_state.stats['success']}</div>
                                        <div>Success</div>
                                    </div>
                                    <div class="live-stat">
                                        <div style="font-size: 2rem; font-weight: 700;">{st.session_state.stats['emails_found']}</div>
                                        <div>Emails Found</div>
                                    </div>
                                    <div class="live-stat">
                                        <div style="font-size: 2rem; font-weight: 700;">{rate:.1f}</div>
                                        <div>Per Second</div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                        except Exception as e:
                            st.error(f"Error processing row: {e}")

                # Save results
                st.session_state.results = pd.DataFrame(results)
                st.session_state.scraping_active = False

                duration = time.time() - start_time

                st.success(f"✅ Scraping complete in {duration:.1f} seconds!")
                st.balloons()

                # Final stats
                st.subheader("Final Statistics")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total Processed", st.session_state.stats['processed'])
                col2.metric("Success", st.session_state.stats['success'])
                col3.metric("Failed", st.session_state.stats['failed'])
                col4.metric("Emails Found", st.session_state.stats['emails_found'])

        except Exception as e:
            st.error(f"❌ Error loading CSV: {e}")

with tab2:
    st.header("Results")

    if st.session_state.results is not None and len(st.session_state.results) > 0:
        st.write(f"**Total results:** {len(st.session_state.results)} rows")

        # Show results
        st.dataframe(st.session_state.results, use_container_width=True)

        # Download button
        csv = st.session_state.results.to_csv(index=False, encoding='utf-8-sig')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_results_{timestamp}.csv"

        st.download_button(
            label="⬇️ Download Results CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )

        # Separate success/failed
        success_df = st.session_state.results[st.session_state.results['scrape_status'] == 'success']
        failed_df = st.session_state.results[st.session_state.results['scrape_status'] != 'success']

        if len(success_df) > 0:
            st.subheader(f"✅ Success ({len(success_df)} rows)")
            st.download_button(
                label="⬇️ Download Success Only",
                data=success_df.to_csv(index=False, encoding='utf-8-sig'),
                file_name=f"success_{timestamp}.csv",
                mime="text/csv"
            )

        if len(failed_df) > 0:
            st.subheader(f"❌ Failed ({len(failed_df)} rows)")
            st.download_button(
                label="⬇️ Download Failed Only",
                data=failed_df.to_csv(index=False, encoding='utf-8-sig'),
                file_name=f"failed_{timestamp}.csv",
                mime="text/csv"
            )
    else:
        st.info("👆 No results yet. Upload a CSV and run the scraper in the 'Upload & Run' tab.")

        st.markdown("""
        ### How it works:
        1. **Upload CSV** (only 'website' required)
        2. **Configure parameters** (mode, workers, email format)
        3. **Run scraper**
        4. **View results** here

        ### Output files:
        - `success_emails.csv` - Websites with emails found
        - `failed_static.csv` - Static sites without emails
        - `failed_dynamic.csv` - Dynamic sites without emails
        - `failed_other.csv` - Errors
        - `scraping_analytics.json` - Performance metrics
        """)
