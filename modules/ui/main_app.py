#!/usr/bin/env python3
"""
=== UNIFIED COLD OUTREACH PLATFORM ===
Version: 1.0.0 | Created: 2025-11-21

Single entry point for all cold outreach tools.
Modular tabs with session state data sharing.

USAGE:
    streamlit run modules/ui/main_app.py
"""

import sys
from pathlib import Path
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.shared.streamlit_styles import (
    init_page_config,
    apply_common_styles,
    create_header
)

from modules.ui.components.pipeline_status import render_pipeline_status

from modules.ui.tabs import (
    render_email_scraper_tab,
    render_email_validator_tab,
    render_ai_processor_tab,
    render_csv_merger_tab
)

# ========================
# PAGE CONFIGURATION
# ========================

init_page_config(
    title="Cold Outreach Platform",
    icon="🚀",
    layout="wide",
    sidebar_state="expanded"
)

apply_common_styles()

# ========================
# HEADER
# ========================

create_header(
    "Cold Outreach Platform",
    "All-in-one lead processing: Scrape → Validate → Generate",
    icon="🚀"
)

# ========================
# INITIALIZE SESSION STATE
# ========================

# Scraper data
if 'scraped_data' not in st.session_state:
    st.session_state['scraped_data'] = None

# Validated data
if 'validated_data' not in st.session_state:
    st.session_state['validated_data'] = None

# AI processed data
if 'ai_processed_data' not in st.session_state:
    st.session_state['ai_processed_data'] = None

# AI working data (for iterative processing)
if 'ai_working_data' not in st.session_state:
    st.session_state['ai_working_data'] = None

# ========================
# SIDEBAR: PIPELINE STATUS
# ========================

render_pipeline_status()

# ========================
# MAIN TABS
# ========================

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "📧 Email Scraper",
    "✅ Email Validator",
    "🤖 AI Processor",
    "🔗 CSV Merger"
])

with tab1:
    render_email_scraper_tab()

with tab2:
    render_email_validator_tab()

with tab3:
    render_ai_processor_tab()

with tab4:
    render_csv_merger_tab()

# ========================
# FOOTER
# ========================

st.markdown("---")
st.caption("🚀 Cold Outreach Platform v1.0.0 | Powered by Claude Code")
