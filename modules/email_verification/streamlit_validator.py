#!/usr/bin/env python3
"""
=== STREAMLIT EMAIL VALIDATOR COMPONENT ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Reusable Streamlit component for email validation

FEATURES:
- File upload or select from results
- Batch validation
- Real-time progress
- Results download
- Can be embedded in any Streamlit app

USAGE:
from modules.email_verification.streamlit_validator import render_validation_tab

# In your Streamlit app:
with st.tabs(["Tab1", "Tab2", "Validation"])[2]:
    render_validation_tab(results_dir="path/to/results")
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from validator import MailsValidator


def render_validation_tab(results_dir: Optional[str] = None, api_key: Optional[str] = None):
    """
    Render email validation tab (reusable component)

    Args:
        results_dir: Optional path to results directory for quick access
        api_key: Optional API key (if None, reads from .env)
    """

    st.header("Email Validation")

    # Get API key
    if not api_key:
        api_key = os.getenv('MAILS_API_KEY')

    # API Key configuration section
    st.subheader("🔑 API Configuration")

    if not api_key:
        st.warning("⚠️ API key not found in environment variables")

        col1, col2 = st.columns([3, 1])

        with col1:
            api_key_input = st.text_input(
                "Enter Mails.so API Key",
                type="password",
                placeholder="Enter your API key here...",
                help="Get your API key from https://mails.so"
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            save_to_env = st.checkbox("Save to .env", value=False, help="Save API key to .env file for future use")

        if api_key_input:
            api_key = api_key_input

            # Save to .env if requested
            if save_to_env:
                try:
                    env_path = Path(__file__).parent.parent.parent / ".env"

                    # Read existing .env
                    if env_path.exists():
                        with open(env_path, 'r') as f:
                            env_content = f.read()
                    else:
                        env_content = ""

                    # Check if MAILS_API_KEY already exists
                    if 'MAILS_API_KEY' in env_content:
                        # Update existing key
                        import re
                        env_content = re.sub(
                            r'MAILS_API_KEY=.*',
                            f'MAILS_API_KEY={api_key}',
                            env_content
                        )
                    else:
                        # Add new key
                        env_content += f"\n\nMAILS_API_KEY={api_key}\n"

                    # Write back
                    with open(env_path, 'w') as f:
                        f.write(env_content)

                    st.success("✅ API key saved to .env file!")
                    os.environ['MAILS_API_KEY'] = api_key

                except Exception as e:
                    st.error(f"Failed to save to .env: {e}")
        else:
            st.info("👆 Please enter your API key above to continue")
            return
    else:
        st.success(f"✅ API key loaded from environment")

        # Show option to change API key
        with st.expander("🔄 Change API Key"):
            new_api_key = st.text_input(
                "Enter new API key",
                type="password",
                placeholder="Enter new API key...",
                key="change_api_key"
            )

            if new_api_key and st.button("Update API Key"):
                api_key = new_api_key
                st.success("✅ API key updated for this session")
                st.rerun()

    st.divider()

    # Initialize validator
    validator = MailsValidator(api_key)

    # Initialize session state
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = None
    if 'batch_id' not in st.session_state:
        st.session_state.batch_id = None

    # File source selection
    st.subheader("1. Select Data Source")

    source_option = st.radio(
        "Choose source:",
        ["Upload CSV file", "Select from results folder"],
        horizontal=True
    )

    df_to_validate = None

    if source_option == "Upload CSV file":
        uploaded_file = st.file_uploader("Upload CSV with emails", type=['csv'])

        if uploaded_file:
            df_to_validate = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(df_to_validate)} rows")

    else:
        # Select from results
        if results_dir and Path(results_dir).exists():
            results_path = Path(results_dir)
            csv_files = list(results_path.glob('**/*.csv'))

            if csv_files:
                file_options = {str(f.relative_to(results_path)): f for f in csv_files}

                selected_file = st.selectbox(
                    "Select results file:",
                    options=list(file_options.keys())
                )

                if selected_file:
                    df_to_validate = pd.read_csv(file_options[selected_file])
                    st.success(f"Loaded {len(df_to_validate)} rows from {selected_file}")
            else:
                st.warning("No CSV files found in results directory")
        else:
            st.warning("Results directory not specified or doesn't exist")

    # Email column detection
    if df_to_validate is not None:
        st.subheader("2. Configure Validation")

        # Detect email column
        email_cols = [col for col in df_to_validate.columns if 'email' in col.lower()]

        if not email_cols:
            st.error("No email column found in CSV!")
            st.info("CSV must have column with 'email' in name")
            return

        email_column = st.selectbox("Email column:", email_cols)

        # Extract unique emails
        emails = df_to_validate[email_column].dropna().unique().tolist()

        st.info(f"Found {len(emails)} unique emails to validate")

        # Preview
        with st.expander("Preview emails"):
            st.write(emails[:20])
            if len(emails) > 20:
                st.caption(f"... and {len(emails) - 20} more")

        # Submit button
        if st.button("Submit for Validation", type="primary", use_container_width=True):
            with st.spinner("Submitting batch..."):
                result = validator.submit_batch(emails)

                if result['success']:
                    st.session_state.batch_id = result['batch_id']

                    st.success(f"Batch submitted! ID: {result['batch_id']}")
                    st.info(f"Size: {result['size']} emails")

                    # Auto-start polling
                    st.rerun()
                else:
                    st.error(f"Submission failed: {result.get('error')}")

    # Polling for results
    if st.session_state.batch_id and not st.session_state.validation_results:
        st.subheader("3. Validation in Progress")

        st.info(f"Batch ID: {st.session_state.batch_id}")

        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        def progress_callback(iteration, elapsed):
            progress_placeholder.write(f"Check #{iteration} (elapsed: {elapsed}s)")

        with st.spinner("Waiting for validation to complete..."):
            results = validator.poll_results(
                st.session_state.batch_id,
                max_wait_minutes=10,
                callback=progress_callback
            )

            if results:
                st.session_state.validation_results = results
                status_placeholder.success("Validation complete!")
                st.rerun()
            else:
                status_placeholder.error("Validation timed out. Try checking status later.")

    # Display results
    if st.session_state.validation_results:
        st.subheader("4. Validation Results")

        results_df = validator.process_results(st.session_state.validation_results)

        # Statistics
        stats = validator.get_statistics(results_df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total", stats['total'])

        with col2:
            st.metric("Deliverable",
                     stats['deliverable'],
                     f"{stats['deliverable_pct']:.1f}%")

        with col3:
            st.metric("Unknown",
                     stats['unknown'],
                     f"{stats['unknown_pct']:.1f}%")

        with col4:
            st.metric("Undeliverable",
                     stats['undeliverable'],
                     f"{stats['undeliverable_pct']:.1f}%")

        # Merge with original data if available
        if df_to_validate is not None and email_column:
            merged_df = validator.merge_with_original(results_df, df_to_validate)
        else:
            merged_df = results_df

        # Preview
        st.write("**Preview Results:**")
        st.dataframe(merged_df.head(20), use_container_width=True)

        # Filters
        st.write("**Download Options:**")

        col1, col2 = st.columns(2)

        with col1:
            # Download all
            csv_all = merged_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Download All Results",
                data=csv_all,
                file_name=f"validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Download deliverable only
            df_deliverable = validator.filter_by_result(merged_df, 'deliverable')
            csv_deliverable = df_deliverable.to_csv(index=False).encode('utf-8-sig')

            st.download_button(
                label=f"Download Deliverable Only ({len(df_deliverable)})",
                data=csv_deliverable,
                file_name=f"deliverable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Additional filters
        with st.expander("Advanced Filters"):
            filter_type = st.selectbox(
                "Filter by result:",
                ["All", "deliverable", "unknown", "risky", "undeliverable"]
            )

            corporate_only = st.checkbox("Corporate emails only (exclude Gmail, Yahoo, etc)")

            filtered_df = merged_df.copy()

            if filter_type != "All":
                filtered_df = validator.filter_by_result(filtered_df, filter_type)

            if corporate_only:
                filtered_df = validator.filter_corporate_only(filtered_df)

            st.write(f"Filtered results: {len(filtered_df)} rows")

            csv_filtered = filtered_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label=f"Download Filtered ({len(filtered_df)} rows)",
                data=csv_filtered,
                file_name=f"filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        # Reset button
        if st.button("Start New Validation"):
            st.session_state.validation_results = None
            st.session_state.batch_id = None
            st.rerun()
