#!/usr/bin/env python3
"""
Email Validator Tab - integrates with email_verification module
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.ui.components import (
    render_file_uploader,
    render_column_selector,
    render_progress_tracker,
    render_results_viewer
)

# Import validator
try:
    from modules.email_verification.validator import MailsValidator
except ImportError:
    st.error("Email verification module not found")
    MailsValidator = None


def render_email_validator_tab():
    """
    Email validator tab with mails.so API integration
    """
    st.header("✅ Email Validator")
    st.markdown("Validate emails using Mails.so API")

    # Check for data from scraper tab
    data_source = None

    if 'scraped_data' in st.session_state and st.session_state['scraped_data'] is not None:
        st.success(f"📊 Found {len(st.session_state['scraped_data'])} rows from Email Scraper tab")

        if st.button("Use scraped data"):
            data_source = st.session_state['scraped_data']

    # Or upload file manually
    if data_source is None:
        st.markdown("**Or upload CSV manually:**")

        df = render_file_uploader(
            label="Upload CSV with emails",
            with_results_browser=True,
            results_dir="modules/email_verification/results",
            key_prefix="validator_upload"
        )

        if df is not None:
            data_source = df

    # Validation workflow
    if data_source is not None:
        df = data_source

        # API Key configuration
        st.subheader("🔑 API Configuration")

        api_key = os.getenv('MAILS_API_KEY')

        if not api_key:
            st.warning("⚠️ API key not found in environment")

            col1, col2 = st.columns([3, 1])

            with col1:
                api_key_input = st.text_input(
                    "Enter Mails.so API Key",
                    type="password",
                    placeholder="Enter your API key..."
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                save_to_env = st.checkbox("Save to .env", help="Save for future use")

            if api_key_input:
                api_key = api_key_input

                # Save if requested
                if save_to_env:
                    env_path = Path(__file__).parent.parent.parent.parent / ".env"

                    try:
                        if env_path.exists():
                            with open(env_path, 'r') as f:
                                env_content = f.read()
                        else:
                            env_content = ""

                        import re
                        if 'MAILS_API_KEY' in env_content:
                            env_content = re.sub(r'MAILS_API_KEY=.*', f'MAILS_API_KEY={api_key}', env_content)
                        else:
                            env_content += f"\n\nMAILS_API_KEY={api_key}\n"

                        with open(env_path, 'w') as f:
                            f.write(env_content)

                        st.success("✅ API key saved to .env")

                    except Exception as e:
                        st.error(f"Failed to save API key: {e}")

        # Column selection
        st.subheader("⚙️ Configuration")

        email_col_candidates = [col for col in df.columns if 'email' in col.lower()]
        default_email = email_col_candidates[0] if email_col_candidates else None

        email_column = st.selectbox(
            "Email column",
            options=df.columns.tolist(),
            index=df.columns.tolist().index(default_email) if default_email else 0
        )

        # Validation options
        with st.expander("🔧 Advanced Options"):
            batch_size = st.number_input("Batch size", min_value=1, max_value=100, value=10)
            delay = st.slider("Delay between requests (seconds)", 0.1, 5.0, 0.5, 0.1)

        # Start validation
        if api_key and st.button("🚀 Start Validation", type="primary"):
            if MailsValidator is None:
                st.error("Email verification module not available")
                return

            # Initialize validator
            validator = MailsValidator(api_key=api_key)

            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            stats_container = st.container()

            emails_to_validate = df[email_column].dropna().tolist()
            total = len(emails_to_validate)

            validated_results = []

            try:
                for i, email in enumerate(emails_to_validate):
                    # Update progress
                    progress = (i + 1) / total
                    progress_bar.progress(progress)
                    status_text.text(f"Validating: {email} ({i+1}/{total})")

                    # Validate
                    result = validator.validate_email(email)
                    validated_results.append(result)

                    # Delay
                    import time
                    time.sleep(delay)

                # Create results DataFrame
                validated_df = df.copy()
                results_df = pd.DataFrame(validated_results)

                # Merge results
                validated_df = validated_df.merge(
                    results_df,
                    left_on=email_column,
                    right_on='email',
                    how='left'
                )

                # Save to session state
                st.session_state['validated_data'] = validated_df

                # Show results
                st.success("✅ Validation completed!")

                # Statistics
                deliverable_count = len(validated_df[validated_df['verification_result'] == 'deliverable'])
                undeliverable_count = len(validated_df[validated_df['verification_result'] == 'undeliverable'])
                unknown_count = len(validated_df[validated_df['verification_result'] == 'unknown'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Deliverable", deliverable_count, delta=f"{deliverable_count/total*100:.1f}%")
                with col2:
                    st.metric("Undeliverable", undeliverable_count)
                with col3:
                    st.metric("Unknown", unknown_count)

                # Show results
                render_results_viewer(
                    validated_df,
                    title="Validation Results",
                    download_filename="validated_emails.csv"
                )

                # Option to proceed
                st.markdown("---")
                st.info("💡 Results saved to session. Go to 'AI Processor' tab to generate icebreakers for deliverable emails!")

            except Exception as e:
                st.error(f"Validation failed: {e}")

    # Show data from session state
    elif 'validated_data' in st.session_state and st.session_state['validated_data'] is not None:
        st.info("📊 Showing previously validated data from session")

        render_results_viewer(
            st.session_state['validated_data'],
            title="Validated Results",
            download_filename="validated_emails.csv"
        )
