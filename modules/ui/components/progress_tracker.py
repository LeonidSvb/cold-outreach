#!/usr/bin/env python3
"""
Universal progress tracker component
"""

import streamlit as st
from typing import Optional


def render_progress_tracker(
    total: int,
    processed: int,
    success: int = 0,
    failed: int = 0,
    current_item: Optional[str] = None,
    show_percentage: bool = True
):
    """
    Universal progress tracker with metrics.

    Args:
        total: Total items to process
        processed: Items processed so far
        success: Successful items
        failed: Failed items
        current_item: Currently processing item name
        show_percentage: Show percentage completed
    """
    # Progress bar
    progress = processed / total if total > 0 else 0

    if show_percentage:
        st.progress(progress, text=f"{progress*100:.1f}% complete")
    else:
        st.progress(progress)

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", total)

    with col2:
        st.metric("Processed", processed)

    with col3:
        success_rate = (success / processed * 100) if processed > 0 else 0
        st.metric("Success", success, delta=f"{success_rate:.1f}%")

    with col4:
        st.metric("Failed", failed)

    # Current item
    if current_item:
        st.caption(f"Currently processing: {current_item}")


def render_live_stats(stats: dict):
    """
    Render live statistics in styled boxes.

    Args:
        stats: Dict with statistics to display
    """
    for key, value in stats.items():
        st.markdown(
            f'<div class="live-stat"><strong>{key}:</strong> {value}</div>',
            unsafe_allow_html=True
        )
