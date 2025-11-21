#!/usr/bin/env python3
"""
Universal results viewer component
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional


def render_results_viewer(
    df: pd.DataFrame,
    title: str = "Results",
    show_download: bool = True,
    download_filename: Optional[str] = None,
    show_stats: bool = True
):
    """
    Universal results viewer with download option.

    Args:
        df: DataFrame to display
        title: Title for results section
        show_download: Show download button
        download_filename: Filename for download (auto-generated if None)
        show_stats: Show basic statistics
    """
    st.subheader(title)

    # Statistics
    if show_stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Rows", len(df))

        with col2:
            st.metric("Columns", len(df.columns))

        with col3:
            # Check for common result indicators
            if 'verification_result' in df.columns:
                deliverable = len(df[df['verification_result'] == 'deliverable'])
                st.metric("Deliverable", deliverable)
            elif 'email' in df.columns:
                with_email = len(df[df['email'].notna()])
                st.metric("With Email", with_email)
            else:
                st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

    # Data preview
    st.dataframe(df, use_container_width=True, height=400)

    # Download button
    if show_download:
        if download_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"results_{timestamp}.csv"

        csv = df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download as CSV ({len(df)} rows)",
            data=csv,
            file_name=download_filename,
            mime="text/csv"
        )


def render_split_results(
    results_dict: dict,
    result_type_descriptions: Optional[dict] = None
):
    """
    Render multiple result DataFrames in tabs.

    Args:
        results_dict: Dict of {result_name: DataFrame}
        result_type_descriptions: Optional descriptions for each result type
    """
    if not results_dict:
        st.warning("No results to display")
        return

    tabs = st.tabs(list(results_dict.keys()))

    for tab, (name, df) in zip(tabs, results_dict.items()):
        with tab:
            description = result_type_descriptions.get(name) if result_type_descriptions else None

            if description:
                st.info(description)

            render_results_viewer(
                df,
                title=f"{name} ({len(df)} rows)",
                download_filename=f"{name.lower().replace(' ', '_')}.csv"
            )
