#!/usr/bin/env python3
"""
Universal file uploader component with results browser
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, List


def render_file_uploader(
    label: str = "Upload CSV",
    accepted_types: List[str] = None,
    with_results_browser: bool = True,
    results_dir: Optional[str] = None,
    key_prefix: str = "uploader"
) -> Optional[pd.DataFrame]:
    """
    Universal file uploader with option to select from previous results.

    Args:
        label: Upload button label
        accepted_types: List of accepted file extensions
        with_results_browser: Show "Or select from results" option
        results_dir: Path to results directory
        key_prefix: Unique key prefix for widgets

    Returns:
        DataFrame if file uploaded/selected, None otherwise
    """
    if accepted_types is None:
        accepted_types = ['csv']

    # File upload
    uploaded_file = st.file_uploader(
        label,
        type=accepted_types,
        key=f"{key_prefix}_upload"
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"Loaded {len(df)} rows, {len(df.columns)} columns")

            # Preview
            with st.expander("Preview data"):
                st.dataframe(df.head(10))

            return df
        except Exception as e:
            st.error(f"Failed to load file: {e}")
            return None

    # Results browser
    if with_results_browser and results_dir:
        st.markdown("---")
        st.markdown("**Or select from previous results:**")

        results_path = Path(results_dir)
        if results_path.exists():
            # Find all CSV files in results subdirectories
            csv_files = list(results_path.rglob("*.csv"))

            if csv_files:
                # Sort by modification time (newest first)
                csv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # Format filenames for display
                file_options = {
                    str(f.relative_to(results_path)): f
                    for f in csv_files[:20]  # Show last 20 files
                }

                selected = st.selectbox(
                    "Choose file:",
                    options=list(file_options.keys()),
                    key=f"{key_prefix}_select"
                )

                if st.button("Load selected file", key=f"{key_prefix}_load"):
                    try:
                        df = pd.read_csv(file_options[selected])
                        st.success(f"Loaded {len(df)} rows from {selected}")

                        with st.expander("Preview data"):
                            st.dataframe(df.head(10))

                        return df
                    except Exception as e:
                        st.error(f"Failed to load file: {e}")
                        return None
            else:
                st.info("No previous results found")
        else:
            st.info(f"Results directory not found: {results_dir}")

    return None
