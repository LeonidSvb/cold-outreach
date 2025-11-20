#!/usr/bin/env python3
"""
=== SHARED STREAMLIT STYLES ===
Version: 1.0.0 | Created: 2025-01-20

PURPOSE:
Unified styles and components for all Streamlit applications.
Ensures consistency across all UIs without duplicating CSS.

USAGE:
    from modules.shared.streamlit_styles import apply_common_styles, create_header

    st.set_page_config(...)
    apply_common_styles()
    create_header("My App Title", "Subtitle description")
"""

import streamlit as st


def apply_common_styles():
    """
    Apply common CSS styles to Streamlit app.
    Styles taken from homepage_email_scraper (proven design).
    Call this once at the start of your app after st.set_page_config()
    """
    st.markdown("""
    <style>
        .big-title {
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .live-stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
            text-align: center;
        }
        .success-box {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)


def create_header(title: str, subtitle: str = "", icon: str = "🤖"):
    """
    Create consistent header for all Streamlit apps.

    Args:
        title: Main title text
        subtitle: Optional subtitle text
        icon: Optional emoji icon
    """
    st.markdown(f'<div class="big-title">{icon} {title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


def success_box(message: str):
    """Display success message in styled box"""
    st.markdown(f'<div class="success-box">✅ {message}</div>', unsafe_allow_html=True)


def warning_box(message: str):
    """Display warning message in styled box"""
    st.markdown(f'<div class="warning-box">⚠️ {message}</div>', unsafe_allow_html=True)


def init_page_config(
    title: str = "Streamlit App",
    icon: str = "🤖",
    layout: str = "wide",
    sidebar_state: str = "expanded"
):
    """
    Initialize page config with consistent settings.
    Call this FIRST before anything else.

    Args:
        title: Page title shown in browser tab
        icon: Page icon emoji
        layout: "wide" or "centered"
        sidebar_state: "expanded" or "collapsed"
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=sidebar_state
    )
