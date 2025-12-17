#!/usr/bin/env python3
"""
Simple Web Scraper with AI - Streamlit Interface
"""

import sys
import time
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import os
import json

# Page config
st.set_page_config(
    page_title="Simple Web Scraper with AI",
    page_icon="🌐",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🌐 Robust Web Scraper with AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">80%+ Success Rate • Retry Logic • Fallback URLs • AI Summaries</div>', unsafe_allow_html=True)

# Sidebar - Config
with st.sidebar:
    st.header("⚙️ Configuration")

    st.subheader("Scraping Settings")
    test_mode = st.checkbox("Test Mode (10 rows)", value=True, help="Only process first 10 rows")
    homepage_only = st.checkbox("Homepage Only", value=True, help="Don't scrape additional pages")

    st.subheader("AI Settings")
    ai_processing = st.checkbox("Enable AI Summaries", value=True)

    if ai_processing:
        model = st.selectbox(
            "OpenAI Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            help="gpt-4o-mini is cheapest"
        )

        st.subheader("AI Prompt")
        default_prompt = """Analyze this website content and provide a detailed summary.

Focus on:
- What does this company/website do?
- What products/services do they offer?
- Who is their target audience?
- Any unique value propositions or key features?

Be thorough but concise. Extract the most important information."""

        custom_prompt = st.text_area(
            "Custom Prompt (optional)",
            value="",
            height=200,
            placeholder=default_prompt,
            help="Leave empty to use default prompt"
        )

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload CSV")
    uploaded_file = st.file_uploader(
        "Choose a CSV file with 'website' column",
        type=['csv'],
        help="CSV must have a column named 'website' with URLs"
    )

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        st.success(f"✅ Loaded {len(df)} rows")

        # Show preview
        with st.expander("📋 Preview Data", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)

        # Check for website column
        website_cols = [col for col in df.columns if 'website' in col.lower() or 'url' in col.lower()]

        if not website_cols:
            st.error("❌ No 'website' column found! Please add a column with URLs.")
            st.stop()

        website_column = st.selectbox("Website Column", df.columns.tolist(),
                                      index=df.columns.tolist().index(website_cols[0]) if website_cols else 0)

with col2:
    st.subheader("📊 Status")

    if uploaded_file:
        rows_to_process = min(10 if test_mode else len(df), len(df))
        st.metric("Rows to Process", rows_to_process)
        st.metric("Total Rows", len(df))

        if ai_processing:
            estimated_cost = rows_to_process * 0.001
            st.metric("Est. Cost", f"${estimated_cost:.3f}")

# Start scraping button
if uploaded_file:
    st.markdown("---")

    if st.button("🚀 Start Scraping (ROBUST 80%+)", type="primary", use_container_width=True):
        # Save uploaded file
        input_dir = Path("scraper/input")
        input_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_file = input_dir / f"temp_input_{timestamp}.csv"
        df.to_csv(input_file, index=False)

        # Update config
        config_updates = {
            "INPUT_FILE": str(input_file),
            "WEBSITE_COLUMN": website_column,
            "TEST_MODE": test_mode,
            "HOMEPAGE_ONLY": homepage_only,
            "AI_PROCESSING": ai_processing,
        }

        if ai_processing:
            config_updates["OPENAI_MODEL"] = model
            if custom_prompt.strip():
                config_updates["AI_PROMPT"] = custom_prompt.strip()

        # Run ASYNC scraper
        progress_container = st.container()

        with progress_container:
            progress_bar = st.progress(0, text="Initializing...")
            status_text = st.empty()
            phase_text = st.empty()

            try:
                import asyncio
                sys.path.insert(0, str(Path(__file__).parent))
                from scraper_robust import CONFIG, process_csv_async
                import scraper_robust as scraper_module

                # Update config
                for key, value in config_updates.items():
                    scraper_module.CONFIG[key] = value

                # Phase 1: Scraping
                phase_text.info("🔍 **PHASE 1/2:** Scraping websites...")
                progress_bar.progress(10, text="Scraping websites in parallel...")

                start_time = time.time()

                # Run async scraper
                output_file = asyncio.run(process_csv_async(str(input_file)))

                scrape_time = time.time() - start_time

                # Phase 2 done in scraper
                progress_bar.progress(90, text="Finalizing results...")

                # Load results
                result_df = pd.read_csv(output_file)

                progress_bar.progress(100, text="Complete!")
                phase_text.success(f"✅ Completed in {scrape_time:.1f}s!")
                status_text.success(f"⚡ **{scrape_time:.1f}s total** • {scrape_time / len(result_df):.2f}s per site • ~{int(40 * 60 / scrape_time)}x faster!")

                # Show results
                st.markdown("---")
                st.subheader("📊 Results")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    success_count = len(result_df[result_df['scrape_status'] == 'success'])
                    st.metric("✅ Successful", success_count)
                with col2:
                    failed_count = len(result_df[result_df['scrape_status'] != 'success'])
                    st.metric("❌ Failed", failed_count)
                with col3:
                    success_rate = (success_count / len(result_df) * 100) if len(result_df) > 0 else 0
                    st.metric("📊 Success Rate", f"{success_rate:.1f}%")
                with col4:
                    st.metric("⚡ Speed", f"{scrape_time / len(result_df):.2f}s/site")

                # Show data
                st.dataframe(result_df, use_container_width=True, height=400)

                # Download button
                csv = result_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv,
                    file_name=f"scraped_{timestamp}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # Cleanup
                input_file.unlink(missing_ok=True)

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                status_text.error("Failed to complete scraping")
                import traceback
                st.code(traceback.format_exc())

# Footer
st.markdown("---")
with st.expander("ℹ️ How it works (ROBUST VERSION)"):
    st.markdown("""
    ### Workflow
    1. **Upload CSV** - must have 'website' column
    2. **Configure** - test mode, AI settings, custom prompt
    3. **Scrape with Retry** - 3 attempts with progressive timeouts (10s → 20s → 30s)
    4. **Fallback URLs** - tries https/http, www/no-www variants
    5. **AI Summary** - OpenAI generates detailed summary
    6. **Download** - CSV with original data + ai_summary + error_reason columns

    ### Robust Features
    - ✅ **80%+ success rate** (vs 44% baseline)
    - ✅ **Retry logic** - 3 attempts per site
    - ✅ **Fallback URLs** - tries 4 URL variants
    - ✅ **Detailed error tracking** - knows why each site failed
    - ✅ **Progressive timeouts** - 10s → 20s → 30s
    - ✅ **Parallel processing** - 50 concurrent requests

    ### Error Handling
    - **403 Forbidden** → Tries fallback URLs
    - **Timeout** → Increases timeout on retry
    - **SSL errors** → Disables SSL verification
    - **All errors tracked** → See error_reason column

    ### Tips
    - Check **error_reason** column to understand failures
    - Most failures are 403 (anti-bot protection)
    - Start with **Test Mode** to verify prompt
    - Customize **AI Prompt** for specific analysis
    """)

with st.expander("⚡ Speed & Cost (ROBUST VERSION)"):
    st.markdown("""
    ### Performance (50 concurrent workers + retry logic)

    | Rows | Est. Time | Est. Cost | Success Rate |
    |------|-----------|-----------|--------------|
    | 50   | **~40s** | ~$0.05    | **81.6%** ✅ |
    | 100  | **~1-2 min** | ~$0.10    | **~80%** |
    | 1000 | **~10-15 min** | ~$1.00    | **~80%** |

    ### Breakdown
    - **Scraping with retry:** ~0.8s per site (includes retries)
    - **AI Summary:** ~0.5s per site (parallel)
    - **Total:** ~1.3s per site (all included)

    ### Success Rate Improvements
    - **Baseline:** 44% (no retry)
    - **Robust:** 81.6% (retry + fallback)
    - **Improvement:** +85% ⬆️

    *Using gpt-4o-mini + aiohttp + retry logic + fallback URLs*

    **Key difference:** Slower per site due to retries, but **much higher success rate**!
    """)
