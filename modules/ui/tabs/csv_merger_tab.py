"""
CSV Merger Tab - Streamlit UI for merging multiple CSV files
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.csv_merge.services.csv_merger_service import CSVMergerService
from modules.csv_merge.lib.csv_key_detector import detect_key_columns, suggest_primary_key
from modules.csv_merge.lib.csv_loader import get_all_columns, load_csv


def render_csv_merger_tab():
    """Render CSV Merger tab UI"""

    st.header("🔗 CSV Merger")
    st.markdown("Merge multiple CSV files by a common key (email, website, or custom)")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload CSV files to merge",
        type=['csv'],
        accept_multiple_files=True,
        key='csv_merger_uploader'
    )

    if not uploaded_files:
        st.info("📤 Upload 2 or more CSV files to get started")
        return

    st.success(f"✅ {len(uploaded_files)} files loaded")

    # Load all CSVs and analyze
    try:
        temp_files = []
        dataframes = []

        # Save uploaded files temporarily and load
        for uploaded_file in uploaded_files:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
                tmp.write(uploaded_file.getvalue())
                temp_files.append(tmp.name)
                df = load_csv(tmp.name)
                dataframes.append(df)

        # Get all unique columns
        all_columns = get_all_columns(dataframes)

        # Detect key columns
        detected = detect_key_columns(all_columns)
        suggested_key = suggest_primary_key(all_columns)

        # Display file info
        with st.expander("📋 File Information", expanded=True):
            for i, (file, df) in enumerate(zip(uploaded_files, dataframes), 1):
                st.text(f"{i}. {file.name} - {len(df)} rows, {len(df.columns)} columns")

        # Key selection
        st.subheader("🔑 Select Merge Key")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Key column selector
            primary_key = st.selectbox(
                "Primary Key Column",
                options=all_columns,
                index=all_columns.index(suggested_key) if suggested_key in all_columns else 0,
                help="Column to use for merging files (must exist in all files)"
            )

        with col2:
            # Key type selector
            if primary_key in detected['email']:
                default_type = 'email'
            elif primary_key in detected['website']:
                default_type = 'website'
            else:
                default_type = 'generic'

            key_type = st.selectbox(
                "Key Type",
                options=['email', 'website', 'generic'],
                index=['email', 'website', 'generic'].index(default_type),
                help="How to normalize the key column"
            )

        # Normalization options
        st.subheader("⚙️ Normalization Options")

        normalize_key = st.checkbox(
            "Normalize key column",
            value=True,
            help="Clean and standardize key values before merging"
        )

        if normalize_key:
            if key_type == 'email':
                st.info("📧 Email normalization: lowercase, trim, remove mailto:, validate @")
            elif key_type == 'website':
                st.info("🌐 Website normalization: remove protocol, www, path, params → clean domain")
            else:
                st.info("🔤 Generic normalization: lowercase, trim whitespace")

        # Merge button
        if st.button("🔗 Merge Files", type="primary", use_container_width=True):
            with st.spinner("Merging files..."):
                try:
                    # Initialize merger service
                    merger = CSVMergerService(
                        key_column=primary_key,
                        key_type=key_type,
                        normalize=normalize_key
                    )

                    # Add all files
                    for temp_file in temp_files:
                        merger.add_csv(temp_file)

                    # Perform merge
                    merged_df = merger.merge()
                    stats = merger.get_stats(merged_df)

                    # Store in session state
                    st.session_state['merged_df'] = merged_df
                    st.session_state['merge_stats'] = stats

                    st.success("✅ Merge completed!")

                except Exception as e:
                    st.error(f"❌ Merge failed: {str(e)}")
                    return

        # Show results if available
        if 'merged_df' in st.session_state and st.session_state['merged_df'] is not None:
            merged_df = st.session_state['merged_df']
            stats = st.session_state['merge_stats']

            # Statistics
            st.subheader("📊 Merge Statistics")

            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            with metric_col1:
                st.metric("Files Merged", stats['total_files'])
            with metric_col2:
                st.metric("Unique Keys", stats['unique_keys'])
            with metric_col3:
                st.metric("Total Rows", stats['total_rows'])
            with metric_col4:
                st.metric("Total Columns", stats['total_columns'])

            # Preview
            st.subheader("👁️ Preview (first 50 rows)")
            st.dataframe(merged_df.head(50), use_container_width=True)

            # Download
            st.subheader("💾 Download")

            csv_data = merged_df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="📥 Download Merged CSV",
                data=csv_data,
                file_name=f"merged_{primary_key}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
