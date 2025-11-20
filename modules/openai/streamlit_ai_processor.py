#!/usr/bin/env python3
"""
=== UNIVERSAL AI DATA PROCESSOR ===
Version: 1.0.0 | Created: 2025-01-20

PURPOSE:
Iterative OpenAI processing with full control.
Select columns, customize prompts, run multiple times, add columns progressively.

FEATURES:
- Column selector: Choose which columns to send to OpenAI
- Editable prompt library: Add/edit/delete prompts directly in UI
- Iterative processing: Run multiple times, each adds new columns
- Column manager: Delete unwanted columns between runs
- Real-time cost tracking and progress
- Session state persistence
- Export/import prompt library

USAGE:
1. Upload CSV
2. Select input columns for OpenAI
3. Choose preset or create custom prompt
4. Edit prompt if needed
5. Run processing
6. Review new columns added
7. Repeat or download results
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Dict, List, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment
load_dotenv()

# Import shared styles
from modules.shared.streamlit_styles import (
    apply_common_styles,
    create_header,
    success_box,
    warning_box,
    init_page_config
)

# Page configuration
init_page_config(
    title="Universal AI Processor",
    icon="🤖",
    layout="wide",
    sidebar_state="expanded"
)

# Apply common styles
apply_common_styles()

# Header
create_header(
    "Universal AI Data Processor",
    "Iterative OpenAI processing with full control over prompts and columns",
    icon="🤖"
)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None

if 'original_df' not in st.session_state:
    st.session_state.original_df = None

if 'prompt_library' not in st.session_state:
    st.session_state.prompt_library = {
        "Icebreaker Generator": {
            "prompt": """You are an expert cold email writer.

Generate a SHORT, casual icebreaker (max 35 words) that:
- Shows you researched the company
- Sounds natural and conversational
- Creates curiosity

Return only the icebreaker text, no formatting.""",
            "description": "Generate short icebreaker (max 35 words)",
            "output_columns": ["icebreaker"],
            "model": "gpt-4o-mini",
            "temperature": 0.7
        },
        "Email Sequence (3 emails)": {
            "prompt": """You are an expert outreach copywriter.

Generate 3 emails (initial + 2 follow-ups) for cold outreach.

Return ONLY valid JSON:
{
  "email_1": "...",
  "email_2": "...",
  "email_3": "...",
  "subject_line": "..."
}""",
            "description": "Generate 3-email sequence with subject line",
            "output_columns": ["email_1", "email_2", "email_3", "subject_line"],
            "model": "gpt-4o-mini",
            "temperature": 0.7
        },
        "Content Parser": {
            "prompt": """Extract business information from this website content.

Return ONLY valid JSON:
{
  "business_type": "...",
  "services": "...",
  "value_proposition": "...",
  "target_audience": "..."
}""",
            "description": "Parse website content to extract business data",
            "output_columns": ["business_type", "services", "value_proposition", "target_audience"],
            "model": "gpt-4o-mini",
            "temperature": 0.3
        }
    }

if 'selected_input_columns' not in st.session_state:
    st.session_state.selected_input_columns = []

if 'selected_columns_snapshot' not in st.session_state:
    st.session_state.selected_columns_snapshot = []

if 'processing_active' not in st.session_state:
    st.session_state.processing_active = False

if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0.0

if 'editing_prompt' not in st.session_state:
    st.session_state.editing_prompt = None

if 'adding_new_prompt' not in st.session_state:
    st.session_state.adding_new_prompt = False

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # File upload
    st.subheader("📤 Upload CSV")
    uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])

    if uploaded_file and st.session_state.df is None:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        st.session_state.df = df.copy()
        st.session_state.original_df = df.copy()
        success_box(f"Loaded {len(df)} rows")

    if st.session_state.df is not None:
        st.divider()

        # OpenAI settings
        st.subheader("🔧 OpenAI Settings")
        api_key = st.text_input("API Key", value=os.getenv("OPENAI_API_KEY", ""), type="password")
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"], index=0)
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
        max_workers = st.slider("Parallel Workers", 1, 100, 50, 5)

        st.divider()

        # DataFrame info
        st.subheader("📊 Current Data")
        st.metric("Rows", len(st.session_state.df))
        st.metric("Columns", len(st.session_state.df.columns))
        st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")

        if st.button("🔄 Reset to Original", help="Reset DataFrame to uploaded CSV"):
            st.session_state.df = st.session_state.original_df.copy()
            st.session_state.total_cost = 0.0
            st.rerun()

# Main content
tab1, tab2, tab3 = st.tabs(["📚 Prompt Library", "🚀 Process Data", "📊 Results & Columns"])

# TAB 1: Prompt Library Manager
with tab1:
    st.header("Prompt Library Manager")
    st.caption("Add, edit, or delete prompts. Changes are saved in session.")

    # List existing prompts
    st.subheader("Saved Prompts")

    for prompt_name, config in st.session_state.prompt_library.items():
        with st.expander(f"📝 {prompt_name}", expanded=(st.session_state.editing_prompt == prompt_name)):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Description:** {config['description']}")
                st.write(f"**Output columns:** {', '.join(config['output_columns'])}")
                st.write(f"**Model:** {config['model']} | **Temperature:** {config['temperature']}")

            with col2:
                if st.button("Edit", key=f"edit_{prompt_name}"):
                    st.session_state.editing_prompt = prompt_name
                    st.rerun()

                if st.button("Delete", key=f"del_{prompt_name}"):
                    del st.session_state.prompt_library[prompt_name]
                    st.rerun()

            if st.session_state.editing_prompt == prompt_name:
                st.subheader("Edit Prompt")

                new_prompt = st.text_area(
                    "Prompt template",
                    value=config['prompt'],
                    height=200,
                    key=f"prompt_edit_{prompt_name}"
                )

                new_desc = st.text_input(
                    "Description",
                    value=config['description'],
                    key=f"desc_edit_{prompt_name}"
                )

                new_cols = st.text_input(
                    "Output columns (comma separated)",
                    value=", ".join(config['output_columns']),
                    key=f"cols_edit_{prompt_name}"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes", key=f"save_{prompt_name}"):
                        st.session_state.prompt_library[prompt_name]['prompt'] = new_prompt
                        st.session_state.prompt_library[prompt_name]['description'] = new_desc
                        st.session_state.prompt_library[prompt_name]['output_columns'] = [c.strip() for c in new_cols.split(',')]
                        st.session_state.editing_prompt = None
                        st.success("Saved!")
                        st.rerun()

                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{prompt_name}"):
                        st.session_state.editing_prompt = None
                        st.rerun()

    st.divider()

    # Add new prompt
    st.subheader("➕ Add New Prompt")

    if st.button("Create New Prompt"):
        st.session_state.adding_new_prompt = True

    if st.session_state.adding_new_prompt:
        new_name = st.text_input("Prompt name", placeholder="e.g., Priority Scorer")
        new_prompt = st.text_area("Prompt template", height=200, placeholder="Use {{column_name}} for placeholders")
        new_desc = st.text_input("Description", placeholder="Short description of what this prompt does")
        new_cols = st.text_input("Output columns (comma separated)", placeholder="e.g., priority_score, reason")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Prompt") and new_name:
                st.session_state.prompt_library[new_name] = {
                    "prompt": new_prompt,
                    "description": new_desc,
                    "output_columns": [c.strip() for c in new_cols.split(',') if c.strip()],
                    "model": "gpt-4o-mini",
                    "temperature": 0.7
                }
                st.session_state.adding_new_prompt = False
                st.success(f"Created: {new_name}")
                st.rerun()

        with col2:
            if st.button("❌ Cancel"):
                st.session_state.adding_new_prompt = False
                st.rerun()

    st.divider()

    # Export/Import library
    st.subheader("📦 Export/Import Library")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📥 Export Library"):
            library_json = json.dumps(st.session_state.prompt_library, indent=2)
            st.download_button(
                "Download JSON",
                data=library_json,
                file_name=f"prompt_library_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

    with col2:
        import_file = st.file_uploader("Import Library JSON", type=['json'], key="import_library")
        if import_file:
            try:
                imported = json.load(import_file)
                st.session_state.prompt_library.update(imported)
                st.success(f"Imported {len(imported)} prompts!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

# TAB 2: Process Data
with tab2:
    if st.session_state.df is None:
        st.info("👆 Please upload a CSV file in the sidebar to get started")
    else:
        st.header("Process Data with OpenAI")

        # Column Selection with checkboxes
        st.subheader("☑️ Select Input Columns")
        st.caption("Selected columns are automatically passed to the prompt")

        available_columns = list(st.session_state.df.columns)

        # Initialize selected columns (default: all selected)
        if 'column_checkboxes' not in st.session_state:
            st.session_state.column_checkboxes = {col: True for col in available_columns}

        # Select All / Clear All buttons
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 6])
        with col_btn1:
            if st.button("✅ Select All"):
                st.session_state.column_checkboxes = {col: True for col in available_columns}
                st.rerun()
        with col_btn2:
            if st.button("❌ Clear All"):
                st.session_state.column_checkboxes = {col: False for col in available_columns}
                st.rerun()

        # Checkboxes for each column (horizontal layout)
        st.write("**Columns:**")

        # Create rows of checkboxes (4 per row for readability)
        cols_per_row = 4
        for i in range(0, len(available_columns), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col_name in enumerate(available_columns[i:i+cols_per_row]):
                with cols[j]:
                    st.session_state.column_checkboxes[col_name] = st.checkbox(
                        col_name,
                        value=st.session_state.column_checkboxes.get(col_name, True),
                        key=f"cb_{col_name}"
                    )

        # Update selected_input_columns from checkboxes
        st.session_state.selected_input_columns = [
            col for col, checked in st.session_state.column_checkboxes.items() if checked
        ]

        if st.session_state.selected_input_columns:
            st.success(f"✅ {len(st.session_state.selected_input_columns)} columns selected")
            st.caption("🤖 Data is passed automatically - NO placeholders needed!")
        else:
            st.warning("⚠️ Select at least one column")

        # Preview Table
        st.subheader("👁️ Preview (first 10 rows)")
        if st.session_state.selected_input_columns:
            preview_cols = st.session_state.selected_input_columns
            st.dataframe(st.session_state.df[preview_cols].head(10), use_container_width=True)
        else:
            st.dataframe(st.session_state.df.head(10), use_container_width=True)

        st.divider()

        if not st.session_state.selected_input_columns:
            warning_box("Please select input columns above")
        else:
            # Select preset
            st.subheader("1️⃣ Select Prompt")

            preset_names = list(st.session_state.prompt_library.keys())
            selected_preset = st.selectbox(
                "Choose preset prompt",
                options=["Custom"] + preset_names,
                help="Select a preset or use custom prompt"
            )

            if selected_preset != "Custom":
                preset_config = st.session_state.prompt_library[selected_preset]

                st.info(f"**Description:** {preset_config['description']}")
                st.info(f"**Output columns:** {', '.join(preset_config['output_columns'])}")

                # Show and allow editing
                st.subheader("2️⃣ Review/Edit Prompt")

                current_prompt = st.text_area(
                    "Prompt template (editable)",
                    value=preset_config['prompt'],
                    height=250,
                    help="Edit prompt before running. Changes won't save to library."
                )

                output_cols_str = st.text_input(
                    "Output columns (comma separated)",
                    value=", ".join(preset_config['output_columns']),
                    help="Columns that will be added to DataFrame"
                )

                output_cols = [c.strip() for c in output_cols_str.split(',') if c.strip()]

            else:
                # Custom prompt
                st.subheader("2️⃣ Custom Prompt")

                current_prompt = st.text_area(
                    "Enter your prompt",
                    height=250,
                    placeholder="Just write what you want OpenAI to do. Selected columns data will be added automatically.",
                    help="NO placeholders needed! Selected columns are automatically added at the beginning of the prompt."
                )

                output_cols_str = st.text_input(
                    "Output columns (comma separated)",
                    placeholder="e.g., result, analysis, score"
                )

                output_cols = [c.strip() for c in output_cols_str.split(',') if c.strip()]

            # Processing options
            st.subheader("3️⃣ Processing Options")

            col1, col2, col3 = st.columns(3)

            with col1:
                process_all = st.checkbox("Process all rows", value=True)
                if not process_all:
                    sample_size = st.number_input("Sample size", 1, len(st.session_state.df), min(100, len(st.session_state.df)))

            with col2:
                use_json_mode = st.checkbox("JSON response format", value=True, help="Force OpenAI to return valid JSON")

            with col3:
                show_progress = st.checkbox("Show real-time progress", value=True)

            # Estimate cost
            rows_to_process = len(st.session_state.df) if process_all else sample_size
            estimated_cost = rows_to_process * 0.002
            estimated_time = rows_to_process / max_workers / 2

            st.info(f"⏱️ Estimated time: **{estimated_time:.1f} minutes** | 💰 Estimated cost: **${estimated_cost:.2f}**")

            # PREVIEW like n8n
            st.subheader("👁️ Preview (like n8n)")
            st.caption("Shows how the prompt will look with real data from the first row")

            if len(st.session_state.df) > 0 and st.session_state.selected_input_columns:
                sample_row = st.session_state.df.iloc[0].to_dict()

                # Build preview with auto data
                data_section = "=== COMPANY DATA ===\n"
                for col in st.session_state.selected_input_columns:
                    value = str(sample_row.get(col, 'N/A'))
                    data_section += f"{col}: {value}\n"
                data_section += "===================\n\n"

                preview_full = data_section + current_prompt

                st.code(preview_full, language="text")
            elif not st.session_state.selected_input_columns:
                st.warning("⚠️ Select columns above to see preview")

            # Run button
            st.subheader("4️⃣ Run Processing")

            if not api_key:
                st.error("❌ Please provide OpenAI API key in sidebar")
            elif not current_prompt:
                st.error("❌ Please enter a prompt")
            elif not output_cols:
                st.error("❌ Please specify output columns")
            else:
                run_button = st.button(
                    "🚀 Run Processing",
                    type="primary",
                    disabled=st.session_state.processing_active,
                    use_container_width=True
                )

                if run_button:
                    st.session_state.processing_active = True

                    # Initialize OpenAI
                    client = OpenAI(api_key=api_key)

                    # Select rows
                    df_to_process = st.session_state.df.copy()
                    if not process_all:
                        df_to_process = df_to_process.head(sample_size)

                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    cost_display = st.empty()

                    # Use dict for mutable state
                    state = {
                        'completed_count': 0,
                        'run_cost': 0.0
                    }
                    lock = threading.Lock()

                    results = []

                    # Save snapshot of selected columns for thread safety
                    selected_cols_snapshot = st.session_state.selected_input_columns.copy()

                    # Processing function
                    def process_row(idx, row_data):
                        # AUTO-BUILD PROMPT: Add data section automatically
                        data_section = "=== COMPANY DATA ===\n"
                        for col in selected_cols_snapshot:
                            value = str(row_data.get(col, 'N/A'))
                            data_section += f"{col}: {value}\n"
                        data_section += "===================\n\n"

                        # Full prompt = data + user prompt
                        prompt = data_section + current_prompt

                        try:
                            # OpenAI call
                            response_params = {
                                "model": model,
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": temperature,
                                "max_tokens": 1000
                            }

                            if use_json_mode:
                                response_params["response_format"] = {"type": "json_object"}

                            response = client.chat.completions.create(**response_params)

                            result_text = response.choices[0].message.content.strip()

                            # Calculate cost (simplified)
                            tokens = response.usage.total_tokens
                            cost = tokens * 0.0002 / 1000

                            with lock:
                                state['run_cost'] += cost

                            # Parse result
                            if use_json_mode:
                                parsed = json.loads(result_text)
                            else:
                                parsed = {output_cols[0]: result_text}

                            return {'idx': idx, 'data': parsed, 'status': 'success'}

                        except Exception as e:
                            return {
                                'idx': idx,
                                'data': {col: f"ERROR: {str(e)}" for col in output_cols},
                                'status': 'error'
                            }

                    # Parallel execution
                    start_time = time.time()

                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(process_row, idx, row.to_dict()): idx
                            for idx, row in df_to_process.iterrows()
                        }

                        for future in as_completed(futures):
                            result = future.result()
                            results.append(result)

                            # Progress update
                            with lock:
                                state['completed_count'] += 1
                                progress = state['completed_count'] / len(df_to_process)
                                progress_bar.progress(progress)

                                if show_progress:
                                    elapsed = time.time() - start_time
                                    rate = state['completed_count'] / elapsed if elapsed > 0 else 0
                                    remaining = (len(df_to_process) - state['completed_count']) / rate if rate > 0 else 0

                                    status_text.text(f"[{state['completed_count']}/{len(df_to_process)}] {progress*100:.1f}% | "
                                                   f"Rate: {rate:.1f}/s | ETA: {remaining:.0f}s")

                                    cost_display.markdown(f"**💰 Cost: ${state['run_cost']:.4f}**")

                    # Add new columns to DataFrame
                    for col_name in output_cols:
                        if col_name not in st.session_state.df.columns:
                            st.session_state.df[col_name] = ""

                    for result in results:
                        for col_name, value in result['data'].items():
                            if col_name in st.session_state.df.columns:
                                st.session_state.df.at[result['idx'], col_name] = value

                    # Update total cost
                    st.session_state.total_cost += state['run_cost']

                    duration = time.time() - start_time

                    st.session_state.processing_active = False

                    success_box(f"Processing complete! {duration:.1f}s | Cost: ${state['run_cost']:.4f}")
                    st.info(f"✅ Added {len(output_cols)} new columns: {', '.join(output_cols)}")

                    st.rerun()

# TAB 3: Results & Column Manager
with tab3:
    if st.session_state.df is None:
        st.info("👆 Please upload a CSV file to get started")
    else:
        st.header("Results & Column Manager")

        # DataFrame stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", len(st.session_state.df))
        with col2:
            st.metric("Total Columns", len(st.session_state.df.columns))
        with col3:
            st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")

        st.divider()

        # Column manager
        st.subheader("🗑️ Column Manager")

        current_cols = list(st.session_state.df.columns)
        original_cols = list(st.session_state.original_df.columns) if st.session_state.original_df is not None else []

        added_cols = [c for c in current_cols if c not in original_cols]

        if added_cols:
            st.info(f"✅ Added columns ({len(added_cols)}): {', '.join(added_cols)}")

        cols_to_delete = st.multiselect(
            "Select columns to DELETE",
            options=current_cols,
            help="Select columns you want to remove from the DataFrame"
        )

        if cols_to_delete:
            if st.button(f"🗑️ Delete {len(cols_to_delete)} column(s)", type="secondary"):
                st.session_state.df = st.session_state.df.drop(columns=cols_to_delete)
                st.success(f"Deleted {len(cols_to_delete)} columns")
                st.rerun()

        st.divider()

        # Preview data
        st.subheader("📊 Data Preview")

        display_rows = st.slider("Rows to display", 5, min(100, len(st.session_state.df)), 10)
        st.dataframe(st.session_state.df.head(display_rows), use_container_width=True)

        st.divider()

        # Download
        st.subheader("⬇️ Download Results")

        csv = st.session_state.df.to_csv(index=False, encoding='utf-8-sig')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_processed_{timestamp}.csv"

        st.download_button(
            "📥 Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
