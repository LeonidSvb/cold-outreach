#!/usr/bin/env python3
"""
Streamlit Frontend for Website Content Parser
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

st.set_page_config(
    page_title="Website Content Parser",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Website Content Parser (OpenAI)")
st.markdown("Extract business data from website content using AI")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# OpenAI settings
st.sidebar.subheader("OpenAI API")
api_key = st.sidebar.text_input("API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
model = st.sidebar.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
max_workers = st.sidebar.slider("Parallel Workers", 1, 100, 50)

# File upload
st.sidebar.subheader("📁 Upload CSV")
uploaded_file = st.sidebar.file_uploader("Choose CSV file", type=['csv'])

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
        suggested_col = max(avg_lengths, key=avg_lengths.get)

        st.write(f"**Suggested content column:**")
        st.info(f"**{suggested_col}** (avg {avg_lengths[suggested_col]:.0f} chars)")

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
    st.subheader("✏️ Customize Extraction Prompt")

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

    # Custom prompt template
    st.subheader("📝 Prompt Template")

    default_prompt = """You are an expert data extractor. Analyze this website content and extract business information.

COMPANY: {company_name}

WEBSITE CONTENT:
{content}

Extract the following variables (return "N/A" if not found):

{variables}

Return ONLY valid JSON format with these exact keys:
{json_template}"""

    custom_prompt = st.text_area(
        "Edit prompt template (use {company_name}, {content}, {variables}, {json_template} placeholders)",
        value=default_prompt,
        height=250
    )

    # Preview
    st.subheader("👁️ Preview")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Sample content:**")
        sample_content = str(df.iloc[0][content_col])[:500]
        st.code(sample_content + "...", language="text")

    with col2:
        st.write("**Sample company name:**")
        sample_company = str(df.iloc[0][company_col])
        st.code(sample_company, language="text")

    # Processing options
    st.subheader("⚡ Processing Options")

    col1, col2, col3 = st.columns(3)

    with col1:
        process_all = st.checkbox("Process all rows", value=False)
        if not process_all:
            sample_size = st.number_input("Sample size", min_value=1, max_value=len(df), value=min(10, len(df)))

    with col2:
        skip_empty = st.checkbox("Skip rows with empty content", value=True)

    with col3:
        show_progress = st.checkbox("Show real-time progress", value=True)

    # Estimated cost and time
    rows_to_process = len(df) if process_all else sample_size
    estimated_time = rows_to_process / max_workers / 2
    estimated_cost = rows_to_process * 0.002

    st.info(f"⏱️ Estimated time: **{estimated_time:.1f} minutes** | 💰 Estimated cost: **${estimated_cost:.2f} USD**")

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
                final_prompt = custom_prompt.format(
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

                        if show_progress:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            rate = completed_count / elapsed if elapsed > 0 else 0
                            remaining = (len(df_to_process) - completed_count) / rate if rate > 0 else 0

                            status_text.text(f"[{completed_count}/{len(df_to_process)}] {progress*100:.1f}% | "
                                           f"Rate: {rate:.1f}/s | ETA: {remaining:.0f}s")

            duration = (datetime.now() - start_time).total_seconds()

            st.success(f"✅ **Processing complete!** ({duration:.1f} seconds)")

            # Display results
            st.subheader("📊 Results")

            # Statistics
            col1, col2, col3 = st.columns(3)

            with col1:
                success_count = len(df_to_process[~df_to_process[variables_list[0]].str.contains("ERROR", na=False)])
                st.metric("Success", success_count)

            with col2:
                error_count = len(df_to_process[df_to_process[variables_list[0]].str.contains("ERROR", na=False)])
                st.metric("Errors", error_count)

            with col3:
                st.metric("Total Cost", f"${completed_count * 0.002:.2f}")

            # Show dataframe
            st.dataframe(df_to_process, use_container_width=True)

            # Download button
            csv = df_to_process.to_csv(index=False, encoding='utf-8-sig')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parsed_content_{timestamp}.csv"

            st.download_button(
                label="⬇️ Download Results CSV",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )

else:
    st.info("👆 Please upload a CSV file to get started")

    # Sample data instructions
    st.markdown("""
    ### 📋 Instructions

    1. **Upload CSV** with website content
    2. **Select columns** for content and company name
    3. **Customize prompt** and variables to extract
    4. **Adjust settings** (workers, sample size)
    5. **Click 'Start Processing'** and wait for results
    6. **Download** the enriched CSV file

    ### ✨ Features

    - 🔄 **Auto-detection** of content columns
    - ✏️ **Fully customizable** prompts and variables
    - ⚡ **Parallel processing** (up to 100 workers)
    - 💰 **Cost estimation** before running
    - 📊 **Real-time progress** tracking
    - ⬇️ **Instant download** of results

    ### 📁 Expected CSV Format

    Your CSV should have:
    - **Company name column** (e.g., "name", "company")
    - **Website content column** (e.g., "homepage_content", "website_content")
    """)
