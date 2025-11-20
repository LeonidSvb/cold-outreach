#!/usr/bin/env python3
"""
=== EMAIL VALIDATION STANDALONE APP ===
Version: 1.0.0 | Created: 2025-11-20

Standalone Streamlit app for email validation
Uses reusable validation component
"""

import sys
import streamlit as st
from pathlib import Path

# Import from same directory
from streamlit_validator import render_validation_tab

# Page configuration
st.set_page_config(
    page_title="Email Validator",
    page_icon="✅",
    layout="wide"
)

# Custom CSS
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
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="big-title">✅ Email Validator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Validate emails using Mails.so API</div>', unsafe_allow_html=True)

st.divider()

# Render validation component
# Path to scraping results
scraping_results = Path(__file__).parent.parent / "scraping" / "homepage_email_scraper" / "results"
if scraping_results.exists():
    render_validation_tab(results_dir=str(scraping_results))
else:
    render_validation_tab()

st.divider()
st.caption("Email Validator v1.0.0 | Powered by Mails.so")
