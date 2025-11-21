#!/usr/bin/env python3
"""
AI Processor Tab - OpenAI processing with prompt library
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

load_dotenv()

from modules.ui.components import (
    render_file_uploader,
    render_column_selector,
    render_progress_tracker,
    render_results_viewer
)

# Prompt library
DEFAULT_PROMPTS = {
    "Icebreaker Generator": {
        "prompt": """You are an expert cold email writer.

Generate a SHORT, casual icebreaker (max 35 words) that:
- Shows you researched the company
- Sounds natural and conversational
- Creates curiosity

Return only the icebreaker text, no formatting.""",
        "description": "Generate short icebreaker (max 35 words)",
        "output_column": "icebreaker",
        "model": "gpt-4o-mini",
        "temperature": 0.7
    },
    "Company Summary": {
        "prompt": """Summarize this company in 2-3 sentences.
Focus on: what they do, their target market, and unique value proposition.
Be concise and factual.""",
        "description": "Generate company summary",
        "output_column": "company_summary",
        "model": "gpt-4o-mini",
        "temperature": 0.3
    },
    "Value Proposition": {
        "prompt": """Based on this company's profile, write a personalized value proposition for our service.
Max 50 words. Focus on their specific pain points and how we solve them.""",
        "description": "Generate personalized value prop",
        "output_column": "value_proposition",
        "model": "gpt-4o-mini",
        "temperature": 0.7
    }
}


def render_ai_processor_tab():
    """
    AI processor tab with iterative OpenAI processing
    """
    st.header("🤖 AI Processor")
    st.markdown("Process data with OpenAI - iterative, column-based approach")

    # Check for data from validator tab
    data_source = None

    if 'validated_data' in st.session_state and st.session_state['validated_data'] is not None:
        df = st.session_state['validated_data']

        # Filter deliverable
        if 'verification_result' in df.columns:
            deliverable = df[df['verification_result'] == 'deliverable']
            st.success(f"📊 Found {len(deliverable)} deliverable emails from Validator tab")

            if st.button("Use deliverable emails"):
                data_source = deliverable
        else:
            st.success(f"📊 Found {len(df)} rows from previous tab")
            if st.button("Use this data"):
                data_source = df

    elif 'scraped_data' in st.session_state and st.session_state['scraped_data'] is not None:
        st.info("💡 You have scraped data. Consider validating first in 'Email Validator' tab.")

    # Or upload manually
    if data_source is None:
        st.markdown("**Or upload CSV manually:**")

        df = render_file_uploader(
            label="Upload CSV",
            with_results_browser=True,
            results_dir="modules/openai/results",
            key_prefix="ai_upload"
        )

        if df is not None:
            data_source = df

    # AI Processing workflow
    if data_source is not None:
        df = data_source.copy()

        # Store in session for iterative processing
        if 'ai_working_data' not in st.session_state:
            st.session_state['ai_working_data'] = df
        else:
            df = st.session_state['ai_working_data']

        # API Key check
        st.subheader("🔑 OpenAI Configuration")

        api_key = os.getenv('OPENAI_API_KEY')

        if not api_key:
            st.warning("⚠️ OpenAI API key not found")
            api_key = st.text_input("Enter OpenAI API Key", type="password")

        if api_key:
            # Column selection
            st.subheader("📋 Select Input Columns")
            st.caption("Choose which columns to send to OpenAI for processing")

            selected_columns = render_column_selector(
                columns=df.columns.tolist(),
                label="Input columns for AI",
                multiselect=True,
                default_selection=[],
                key_prefix="ai_col_select"
            )

            # Prompt library
            st.subheader("📝 Prompt Library")

            # Load saved prompts
            prompt_library_path = Path(__file__).parent.parent / "prompt_library.json"

            if prompt_library_path.exists():
                with open(prompt_library_path, 'r') as f:
                    prompt_library = json.load(f)
            else:
                prompt_library = DEFAULT_PROMPTS.copy()

            # Prompt selection
            preset_names = list(prompt_library.keys())
            selected_preset = st.selectbox(
                "Choose preset",
                options=["-- Custom --"] + preset_names
            )

            if selected_preset != "-- Custom --":
                preset = prompt_library[selected_preset]

                st.info(f"📖 {preset['description']}")

                # Show/edit prompt
                with st.expander("View/Edit Prompt"):
                    prompt_text = st.text_area(
                        "Prompt template",
                        value=preset['prompt'],
                        height=200
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        output_column = st.text_input("Output column name", value=preset['output_column'])

                    with col2:
                        model = st.selectbox(
                            "Model",
                            options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                            index=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"].index(preset['model'])
                        )

                    with col3:
                        temperature = st.slider("Temperature", 0.0, 1.0, preset['temperature'], 0.1)

            else:
                # Custom prompt
                prompt_text = st.text_area(
                    "Custom prompt",
                    placeholder="Enter your prompt here...",
                    height=200
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    output_column = st.text_input("Output column name", value="ai_output")

                with col2:
                    model = st.selectbox("Model", options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"])

                with col3:
                    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)

            # Processing options
            with st.expander("🔧 Processing Options"):
                col1, col2 = st.columns(2)

                with col1:
                    batch_size = st.number_input("Concurrent requests", 1, 10, 3)
                    limit = st.number_input("Process first N rows (0=all)", 0, 10000, 0)

                with col2:
                    cost_per_1k_input = st.number_input("Cost per 1K input tokens ($)", 0.0, 1.0, 0.00015, format="%.6f")
                    cost_per_1k_output = st.number_input("Cost per 1K output tokens ($)", 0.0, 1.0, 0.0006, format="%.6f")

            # Start processing
            if selected_columns and prompt_text and st.button("🚀 Start AI Processing", type="primary"):
                client = OpenAI(api_key=api_key)

                # Determine rows to process
                rows_to_process = df.head(limit) if limit > 0 else df

                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                cost_text = st.empty()

                total_cost = 0
                results = []

                try:
                    # Process in batches
                    for i in range(0, len(rows_to_process), batch_size):
                        batch = rows_to_process.iloc[i:i+batch_size]

                        with ThreadPoolExecutor(max_workers=batch_size) as executor:
                            futures = []

                            for idx, row in batch.iterrows():
                                # Build context from selected columns
                                context = "\n".join([f"{col}: {row[col]}" for col in selected_columns if pd.notna(row[col])])

                                future = executor.submit(
                                    process_with_openai,
                                    client,
                                    prompt_text,
                                    context,
                                    model,
                                    temperature
                                )
                                futures.append((idx, future))

                            # Collect results
                            for idx, future in futures:
                                result, tokens_used = future.result()
                                results.append({'index': idx, 'result': result, 'tokens': tokens_used})

                                # Calculate cost
                                input_cost = tokens_used['input'] / 1000 * cost_per_1k_input
                                output_cost = tokens_used['output'] / 1000 * cost_per_1k_output
                                total_cost += input_cost + output_cost

                        # Update progress
                        progress = min((i + batch_size) / len(rows_to_process), 1.0)
                        progress_bar.progress(progress)
                        status_text.text(f"Processed: {min(i + batch_size, len(rows_to_process))}/{len(rows_to_process)}")
                        cost_text.text(f"💰 Total cost: ${total_cost:.4f}")

                    # Add results to DataFrame
                    result_dict = {r['index']: r['result'] for r in results}
                    df[output_column] = df.index.map(lambda idx: result_dict.get(idx, None))

                    # Update working data
                    st.session_state['ai_working_data'] = df
                    st.session_state['ai_processed_data'] = df

                    # Show results
                    st.success(f"✅ Processing completed! Added column: {output_column}")
                    st.info(f"💰 Total cost: ${total_cost:.4f}")

                    render_results_viewer(
                        df,
                        title="AI Processed Results",
                        download_filename="ai_processed.csv"
                    )

                    # Option for iterative processing
                    st.markdown("---")
                    st.info("💡 Want to add more columns? Adjust settings and run again!")

                except Exception as e:
                    st.error(f"Processing failed: {e}")

        # Column management
        if 'ai_working_data' in st.session_state:
            st.markdown("---")
            st.subheader("🗂️ Column Management")

            current_df = st.session_state['ai_working_data']

            st.caption(f"Current columns: {', '.join(current_df.columns.tolist())}")

            # Delete columns
            with st.expander("🗑️ Delete Columns"):
                columns_to_delete = st.multiselect(
                    "Select columns to remove",
                    options=current_df.columns.tolist()
                )

                if columns_to_delete and st.button("Delete selected columns"):
                    st.session_state['ai_working_data'] = current_df.drop(columns=columns_to_delete)
                    st.success(f"Deleted: {', '.join(columns_to_delete)}")
                    st.rerun()

    # Show data from session
    elif 'ai_processed_data' in st.session_state and st.session_state['ai_processed_data'] is not None:
        st.info("📊 Showing previously processed data from session")

        render_results_viewer(
            st.session_state['ai_processed_data'],
            title="AI Processed Results",
            download_filename="ai_processed.csv"
        )


def process_with_openai(client, prompt, context, model, temperature):
    """
    Process single item with OpenAI
    """
    full_prompt = f"{prompt}\n\nContext:\n{context}"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": full_prompt}],
        temperature=temperature,
        max_tokens=500
    )

    result = response.choices[0].message.content.strip()
    tokens_used = {
        'input': response.usage.prompt_tokens,
        'output': response.usage.completion_tokens
    }

    return result, tokens_used
