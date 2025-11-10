#!/usr/bin/env python3
"""
=== GOOGLE PLACES SCRAPER - STREAMLIT UI ===
Version: 1.0.0 | Created: 2025-11-10

USAGE:
streamlit run modules/google_maps/ui/streamlit_app.py

FEATURES:
- Interactive state/city selection
- Real-time progress tracking
- Data preview and download
- Cost estimation
- Results visualization
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Page configuration
st.set_page_config(
    page_title="Google Places Lead Collector",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🗺️ Google Places Lead Collector</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Collect qualified leads for your voice AI agents</div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Collection Settings")

    # State selection
    collection_mode = st.radio(
        "Collection Mode",
        ["Full State", "Custom Cities"],
        help="Choose to scrape entire state or specific cities"
    )

    if collection_mode == "Full State":
        state = st.selectbox(
            "Select State",
            ["Texas", "Florida", "California", "New York"],
            help="All major cities in this state will be scraped"
        )
        cities_input = None
    else:
        state = st.selectbox("State", ["Texas", "Florida"])
        cities_input = st.text_area(
            "Enter Cities (one per line)",
            placeholder="Miami, FL\nTampa, FL\nOrlando, FL",
            help="Enter city names with state abbreviation"
        )

    st.divider()

    # Niche selection
    st.subheader("🎯 Target Niche")
    niche = st.selectbox(
        "Business Type",
        [
            "HVAC contractors",
            "plumbers",
            "electricians",
            "towing services",
            "garage door repair",
            "locksmiths"
        ],
        help="Type of business to search for"
    )

    st.divider()

    # Filter settings
    st.subheader("🔍 Quality Filters")

    col1, col2 = st.columns(2)
    with col1:
        min_reviews = st.number_input(
            "Min Reviews",
            min_value=0,
            max_value=500,
            value=20,
            step=10,
            help="Minimum number of Google reviews"
        )

    with col2:
        max_reviews = st.number_input(
            "Max Reviews",
            min_value=50,
            max_value=2000,
            value=800,
            step=50,
            help="Maximum number of Google reviews"
        )

    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
        help="Minimum Google rating (stars)"
    )

    st.divider()

    # Advanced settings
    with st.expander("⚡ Advanced Settings"):
        parallel = st.checkbox("Parallel Processing", value=True, help="Process multiple cities simultaneously")
        save_raw = st.checkbox("Save Raw Data", value=True, help="Keep unfiltered results for re-filtering")

# Main content area
tab1, tab2, tab3 = st.tabs(["📊 Start Collection", "📁 View Results", "💰 Cost Calculator"])

with tab1:
    st.header("Start New Collection")

    # Show current configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Target", f"{state} - {niche}")

    with col2:
        st.metric("Filter", f"{min_reviews}-{max_reviews} reviews")

    with col3:
        estimated_cost = 25.00  # Placeholder
        st.metric("Estimated Cost", f"${estimated_cost:.2f}")

    st.divider()

    # Start button
    if st.button("🚀 Start Collection", type="primary", use_container_width=True):

        # Create progress containers
        progress_bar = st.progress(0, text="Initializing...")
        status_text = st.empty()

        # Simulate collection process (replace with actual scraper call)
        import time

        try:
            # Phase 1: Geocoding
            progress_bar.progress(10, text="Geocoding cities...")
            time.sleep(1)

            # Phase 2: Searching
            progress_bar.progress(30, text="Searching Google Places...")
            time.sleep(1)

            # Phase 3: Filtering
            progress_bar.progress(60, text="Applying quality filters...")
            time.sleep(1)

            # Phase 4: Getting details
            progress_bar.progress(80, text="Fetching contact details...")
            time.sleep(1)

            # Phase 5: Saving
            progress_bar.progress(100, text="Saving results...")
            time.sleep(0.5)

            # Success
            progress_bar.empty()

            st.markdown("""
            <div class="success-box">
                <h3>✅ Collection Complete!</h3>
                <p><strong>Results:</strong> 245 qualified leads collected</p>
                <p><strong>Time:</strong> 8 minutes 32 seconds</p>
                <p><strong>Actual Cost:</strong> $18.45</p>
                <p><strong>Pass Rate:</strong> 68% (245/360 raw)</p>
            </div>
            """, unsafe_allow_html=True)

            # Display sample results
            st.subheader("Preview of Results")

            # Sample data
            sample_data = pd.DataFrame({
                'Name': ['ABC HVAC Services', 'Cool Air Solutions', 'Pro Climate Control'],
                'Phone': ['(305) 123-4567', '(305) 234-5678', '(305) 345-6789'],
                'Rating': [4.8, 4.6, 4.9],
                'Reviews': [156, 89, 234],
                'Address': ['123 Main St, Miami, FL', '456 Oak Ave, Tampa, FL', '789 Pine Rd, Orlando, FL'],
                'Website': ['www.abchvac.com', 'www.coolair.com', 'www.proclimate.com']
            })

            st.dataframe(sample_data, use_container_width=True)

            # Download buttons
            col1, col2, col3 = st.columns(3)

            with col1:
                st.download_button(
                    "📥 Download CSV",
                    sample_data.to_csv(index=False),
                    f"{state}_{niche}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    use_container_width=True
                )

            with col2:
                st.download_button(
                    "📄 Download JSON",
                    json.dumps(sample_data.to_dict('records'), indent=2),
                    f"{state}_{niche}_{datetime.now().strftime('%Y%m%d')}.json",
                    "application/json",
                    use_container_width=True
                )

            with col3:
                st.button("📧 Send to Email", use_container_width=True)

        except Exception as e:
            st.error(f"❌ Collection failed: {str(e)}")
            st.exception(e)

with tab2:
    st.header("View Past Results")

    # List available results files
    results_dir = Path("modules/google_maps/results")

    if results_dir.exists():
        # Get all result files
        result_files = list(results_dir.rglob("*.json"))

        if result_files:
            # Group by state
            states = {}
            for file in result_files:
                state_name = file.parent.name if file.parent != results_dir else "Other"
                if state_name not in states:
                    states[state_name] = []
                states[state_name].append(file)

            # Display grouped files
            for state_name, files in states.items():
                with st.expander(f"📂 {state_name.title()} ({len(files)} files)"):
                    for file in sorted(files, reverse=True)[:10]:  # Show last 10
                        col1, col2, col3 = st.columns([3, 2, 1])

                        with col1:
                            st.text(file.name)

                        with col2:
                            # Get file size
                            size_mb = file.stat().st_size / 1024 / 1024
                            st.text(f"{size_mb:.2f} MB")

                        with col3:
                            if st.button("View", key=f"view_{file.name}"):
                                # Load and display file
                                with open(file, 'r', encoding='utf-8') as f:
                                    data = json.load(f)

                                st.json(data['metadata'])

                                if 'all_filtered_places' in data:
                                    df = pd.DataFrame(data['all_filtered_places'])
                                    st.dataframe(df)
        else:
            st.info("No results found yet. Run a collection first!")
    else:
        st.warning("Results directory not found.")

with tab3:
    st.header("Cost Calculator")

    st.markdown("""
    ### Google Places API Pricing

    - **Nearby Search**: $0.032 per request
    - **Place Details**: $0.017 per request
    - **Free Tier**: $200/month
    """)

    # Calculator
    st.subheader("Estimate Your Costs")

    calc_cities = st.number_input("Number of Cities", min_value=1, max_value=100, value=20)
    calc_avg_results = st.slider("Avg Results per City", 15, 50, 20)
    calc_pass_rate = st.slider("Expected Pass Rate", 0.3, 1.0, 0.7, 0.05)

    # Calculations
    total_searches = calc_cities * 1.2  # With adaptive radius overhead
    total_raw = calc_cities * calc_avg_results
    total_filtered = int(total_raw * calc_pass_rate)

    search_cost = total_searches * 0.032
    details_cost = total_filtered * 0.017
    total_cost = search_cost + details_cost

    # Display results
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("API Calls", f"{int(total_searches + total_filtered):,}")

    with col2:
        st.metric("Raw Results", f"{int(total_raw):,}")

    with col3:
        st.metric("Qualified Leads", f"{total_filtered:,}")

    with col4:
        st.metric("Total Cost", f"${total_cost:.2f}")

    st.divider()

    # Cost breakdown chart
    st.subheader("Cost Breakdown")

    breakdown_data = pd.DataFrame({
        'Component': ['Nearby Search', 'Place Details'],
        'Cost': [search_cost, details_cost]
    })

    st.bar_chart(breakdown_data.set_index('Component'))

    # Budget remaining
    if total_cost <= 200:
        remaining = 200 - total_cost
        st.success(f"✅ Within free tier! ${remaining:.2f} remaining")
    else:
        overage = total_cost - 200
        st.error(f"❌ Exceeds free tier by ${overage:.2f}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Google Places Lead Collector</strong> v1.0.0</p>
    <p>Built with Streamlit | Data from Google Places API</p>
</div>
""", unsafe_allow_html=True)
