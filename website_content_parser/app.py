#!/usr/bin/env python3
"""
=== WEBSITE CONTENT PARSER ===
Version: 2.0.0 | Updated: 2025-11-20

Extract business variables from website content using OpenAI GPT

FEATURES:
- AI-powered content parsing (GPT-4o-mini)
- Parallel processing (up to 100 workers)
- Session state for immediate results
- Results history with browse & download
- Real-time progress tracking
- Cost estimation
- Customizable prompts and variables

DEPLOYMENT:
- Streamlit Cloud ready
- Auto-saves results with timestamps
- Browse historical runs
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json
import os
from datetime import datetime
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Paths
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Website Content Parser",
    page_icon="🔍",
    layout="wide"
)

# Session state initialization
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

st.title("🔍 Website Content Parser (OpenAI)")
st.markdown("Extract business variables from website content using AI")

# Main tabs
tab1, tab2 = st.tabs(["📤 Upload & Process", "📊 View Results"])

with tab1:
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # OpenAI settings
        st.subheader("OpenAI API")
        api_key = st.text_input("API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
        max_workers = st.slider("Parallel Workers", 1, 100, 50)

        st.divider()

        # Processing options
        st.subheader("⚡ Processing Options")

        process_all = st.checkbox("Process all rows", value=False)
        if not process_all:
            sample_size = st.number_input("Sample size", min_value=1, max_value=1000, value=10)

        skip_empty = st.checkbox("Skip rows with empty content", value=True)

    # File upload
    st.subheader("📁 Upload CSV")
    uploaded_file = st.file_uploader("Choose CSV file with website content", type=['csv'])

    if uploaded_file:
        # Read CSV
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')

        st.success(f"✅ Loaded {len(df)} rows")

        # Auto-detect content column
        st.subheader("🔍 Column Detection")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Available columns:**")
            st.write(list(df.columns))

        with col2:
            # Auto-detect
            text_cols = df.select_dtypes(include=['object']).columns
            avg_lengths = {col: df[col].astype(str).str.len().mean() for col in text_cols}
            suggested_col = max(avg_lengths, key=avg_lengths.get) if avg_lengths else df.columns[0]

            st.write(f"**Suggested content column:**")
            st.info(f"**{suggested_col}** (avg {avg_lengths.get(suggested_col, 0):.0f} chars)")

        # Manual column selection
        content_col = st.selectbox(
            "Select content column",
            options=df.columns,
            index=list(df.columns).index(suggested_col) if suggested_col in df.columns else 0
        )

        company_col = st.selectbox(
            "Select company name column",
            options=df.columns,
            index=list(df.columns).index('name') if 'name' in df.columns else 0
        )

        # Prompt customization
        st.subheader("✏️ Customize Extraction")

        # Default variables
        default_variables = [
            "owner_first_name",
            "tagline",
            "value_proposition",
            "guarantees",
            "certifications",
            "awards_badges",
            "special_offers",
            "is_hiring",
            "hiring_roles",
            "is_family_owned",
            "emergency_24_7",
            "free_estimate",
            "license_number",
            "testimonial_snippet",
            "corporate_clients",
            "creative_insights"
        ]

        # Editable variables list
        variables_text = st.text_area(
            "Variables to extract (one per line)",
            value="\n".join(default_variables),
            height=300
        )

        variables_list = [v.strip() for v in variables_text.split("\n") if v.strip()]

        st.info(f"**{len(variables_list)} variables** will be extracted")

        # Estimated cost and time
        rows_to_process = len(df) if process_all else (sample_size if not process_all else 0)
        estimated_time = rows_to_process / max_workers / 2
        estimated_cost = rows_to_process * 0.002

        col1, col2 = st.columns(2)
        with col1:
            st.metric("⏱️ Estimated time", f"{estimated_time:.1f} min")
        with col2:
            st.metric("💰 Estimated cost", f"${estimated_cost:.2f}")

        # Start processing button
        if st.button("🚀 Start Processing", type="primary"):
            if not api_key:
                st.error("❌ Please provide OpenAI API key")
            else:
                # Initialize OpenAI client
                client = OpenAI(api_key=api_key)

                # Prepare prompt
                variables_desc = "\n".join([f"{i+1}. {v}" for i, v in enumerate(variables_list)])
                json_template = "{" + ", ".join([f'"{v}": "..."' for v in variables_list]) + "}"

                prompt_template = """You are an expert data extractor. Analyze this website content and extract business information.

COMPANY: {company_name}

WEBSITE CONTENT:
{content}

Extract the following variables (return "N/A" if not found):

{variables}

Return ONLY valid JSON format with these exact keys:
{json_template}"""

                # Select rows to process
                if process_all:
                    df_to_process = df.copy()
                else:
                    df_to_process = df.head(sample_size).copy()

                # Filter empty content if needed
                if skip_empty:
                    df_to_process = df_to_process[df_to_process[content_col].notna() & (df_to_process[content_col] != '')].copy()

                st.write(f"Processing **{len(df_to_process)}** rows...")

                # Initialize result columns
                for var in variables_list:
                    df_to_process[var] = ""

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                completed_count = 0
                lock = threading.Lock()

                # Processing function
                def process_row(idx, row_data):
                    content = str(row_data[content_col])[:8000]
                    company_name = str(row_data[company_col])

                    # Build prompt
                    final_prompt = prompt_template.format(
                        company_name=company_name,
                        content=content,
                        variables=variables_desc,
                        json_template=json_template
                    )

                    try:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": final_prompt}],
                            temperature=0.3,
                            max_tokens=800,
                            response_format={"type": "json_object"}
                        )

                        result = response.choices[0].message.content.strip()
                        parsed = json.loads(result)

                        return {'idx': idx, 'data': parsed, 'status': 'success'}

                    except Exception as e:
                        return {
                            'idx': idx,
                            'data': {v: f"ERROR: {str(e)}" for v in variables_list},
                            'status': 'error'
                        }

                # Parallel execution
                start_time = datetime.now()

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(process_row, idx, row_data.to_dict()): idx
                              for idx, row_data in df_to_process.iterrows()}

                    for future in as_completed(futures):
                        result = future.result()

                        # Update dataframe
                        for key, value in result['data'].items():
                            if key in df_to_process.columns:
                                df_to_process.at[result['idx'], key] = value

                        # Progress update
                        with lock:
                            completed_count += 1
                            progress = completed_count / len(df_to_process)
                            progress_bar.progress(progress)

                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = completed_count / elapsed if elapsed > 0 else 0
                            remaining = (len(df_to_process) - completed_count) / rate if rate > 0 else 0

                            status_text.text(f"[{completed_count}/{len(df_to_process)}] {progress*100:.1f}% | "
                                           f"Rate: {rate:.1f}/s | ETA: {remaining:.0f}s")

                duration = (datetime.now() - start_time).total_seconds()

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_folder = RESULTS_DIR / f"parsed_{timestamp}"
                result_folder.mkdir(exist_ok=True)

                result_csv = result_folder / "parsed_content.csv"
                df_to_process.to_csv(result_csv, index=False, encoding='utf-8-sig')

                # Save analytics
                success_count = len(df_to_process[~df_to_process[variables_list[0]].str.contains("ERROR", na=False)])
                error_count = len(df_to_process[df_to_process[variables_list[0]].str.contains("ERROR", na=False)])

                analytics = {
                    "timestamp": timestamp,
                    "duration_seconds": round(duration, 1),
                    "total_rows": len(df_to_process),
                    "success": success_count,
                    "errors": error_count,
                    "success_rate": round(success_count / len(df_to_process) * 100, 1) if len(df_to_process) > 0 else 0,
                    "total_cost": round(completed_count * 0.002, 2),
                    "model": model,
                    "workers": max_workers,
                    "variables": variables_list
                }

                with open(result_folder / "analytics.json", 'w') as f:
                    json.dump(analytics, f, indent=2)

                # Update session state
                st.session_state.current_results = result_folder
                st.session_state.processing_complete = True

                st.success(f"✅ **Processing complete!** ({duration:.1f} seconds)")

                # Display results
                st.markdown("### 🎉 Processing Complete!")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("⏱️ Duration", f"{duration:.1f}s", f"{completed_count/duration:.1f} rows/s")
                with col2:
                    st.metric("✅ Success", success_count, f"{analytics['success_rate']}%")
                with col3:
                    st.metric("❌ Errors", error_count)
                with col4:
                    st.metric("💰 Total Cost", f"${analytics['total_cost']}")

                # Show dataframe
                st.dataframe(df_to_process, use_container_width=True)

                # Download button
                st.download_button(
                    label="⬇️ Download Results CSV",
                    data=df_to_process.to_csv(index=False, encoding='utf-8-sig'),
                    file_name=f"parsed_content_{timestamp}.csv",
                    mime="text/csv"
                )

    else:
        st.info("👆 Please upload a CSV file to get started")

        # Sample data instructions
        st.markdown("""
        ### 📋 Instructions

        1. **Upload CSV** with website content (from Homepage Scraper)
        2. **Select columns** for content and company name
        3. **Customize variables** to extract
        4. **Adjust settings** (workers, sample size)
        5. **Click 'Start Processing'** and wait for results
        6. **Download** the enriched CSV file

        ### ✨ Features

        - 🔄 **Auto-detection** of content columns
        - ✏️ **Fully customizable** variables
        - ⚡ **Parallel processing** (up to 100 workers)
        - 💰 **Cost estimation** before running
        - 📊 **Real-time progress** tracking
        - 💾 **Results history** with browse & download

        ### 📁 Expected CSV Format

        Your CSV should have:
        - **Company name column** (e.g., "name", "company")
        - **Website content column** (e.g., "homepage_content", "website_content")

        Tip: Use Homepage Email Scraper first to collect website content!
        """)

# View Results Tab
with tab2:
    st.subheader("📊 Processing History")

    # Get all result folders
    result_folders = sorted(
        [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('parsed_')],
        reverse=True
    )

    if not result_folders:
        st.info("No results yet. Process some files first!")
    else:
        # Folder selection
        folder_names = [f.name for f in result_folders]
        selected_folder_name = st.selectbox(
            "Select result folder",
            options=folder_names,
            index=0  # Default to latest
        )

        selected_folder = RESULTS_DIR / selected_folder_name

        # Load analytics
        analytics_file = selected_folder / "analytics.json"
        if analytics_file.exists():
            with open(analytics_file) as f:
                analytics = json.load(f)

            # Summary stats
            st.markdown("### 📈 Summary")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("⏱️ Duration", f"{analytics['duration_seconds']}s")
            with col2:
                st.metric("✅ Success", analytics['success'], f"{analytics['success_rate']}%")
            with col3:
                st.metric("❌ Errors", analytics['errors'])
            with col4:
                st.metric("💰 Cost", f"${analytics['total_cost']}")

            # Settings used
            st.markdown("### ⚙️ Settings Used")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Model:** {analytics['model']}")
            with col2:
                st.write(f"**Workers:** {analytics['workers']}")
            with col3:
                st.write(f"**Variables:** {len(analytics['variables'])}")

            # Variables extracted
            with st.expander("📝 Variables Extracted"):
                st.write(analytics['variables'])

        # Load and display CSV
        csv_file = selected_folder / "parsed_content.csv"
        if csv_file.exists():
            df_results = pd.read_csv(csv_file, encoding='utf-8-sig')

            st.markdown("### 📄 Data Preview")
            st.dataframe(df_results, use_container_width=True)

            # Download button
            st.download_button(
                label="⬇️ Download CSV",
                data=df_results.to_csv(index=False, encoding='utf-8-sig'),
                file_name=csv_file.name,
                mime="text/csv"
            )
        else:
            st.warning("CSV file not found in this folder")
