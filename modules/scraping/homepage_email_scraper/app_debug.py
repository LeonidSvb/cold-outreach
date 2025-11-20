#!/usr/bin/env python3
"""
DEBUG VERSION - Find performance bottleneck
"""

import streamlit as st
import pandas as pd
import time
from pathlib import Path

st.set_page_config(
    page_title="Debug Homepage Scraper",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 DEBUG: Homepage Email Scraper")

# Time each section
sections = {}

# Section 1: Paths
start = time.time()
SCRIPT_PATH = Path(__file__).parent / "scraper.py"
RESULTS_DIR = Path(__file__).parent / "results"
sections['Paths setup'] = time.time() - start

# Section 2: Session state
start = time.time()
if 'scraping_active' not in st.session_state:
    st.session_state.scraping_active = False
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
sections['Session state init'] = time.time() - start

# Section 3: Check results dir
start = time.time()
results_exists = RESULTS_DIR.exists()
sections['Check results dir exists'] = time.time() - start

# Section 4: List folders
start = time.time()
if results_exists:
    try:
        result_folders = sorted(
            [f for f in RESULTS_DIR.iterdir() if f.is_dir() and f.name.startswith('scraped_')],
            reverse=True
        )
        folder_count = len(result_folders)
    except Exception as e:
        result_folders = []
        folder_count = f"ERROR: {e}"
else:
    result_folders = []
    folder_count = 0
sections['List result folders'] = time.time() - start

# Section 5: Show file uploader
start = time.time()
uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
sections['File uploader widget'] = time.time() - start

# Display timing
st.subheader("⏱️ Performance Timing")
for section, duration in sections.items():
    color = "🟢" if duration < 0.1 else "🟡" if duration < 0.5 else "🔴"
    st.write(f"{color} **{section}**: {duration*1000:.2f}ms")

st.divider()

# Display info
st.subheader("📊 Diagnostics")
st.write(f"- **Results dir exists**: {results_exists}")
st.write(f"- **Result folders count**: {folder_count}")
st.write(f"- **Script path**: {SCRIPT_PATH}")
st.write(f"- **Results path**: {RESULTS_DIR}")

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")

    start = time.time()
    df = pd.read_csv(uploaded_file)
    load_time = time.time() - start

    st.write(f"- **CSV load time**: {load_time*1000:.2f}ms")
    st.write(f"- **Rows**: {len(df)}")
    st.write(f"- **Columns**: {list(df.columns)}")
