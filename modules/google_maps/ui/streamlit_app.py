#!/usr/bin/env python3
"""
=== GOOGLE PLACES SCRAPER - STREAMLIT UI ===
Version: 2.0.0 | Created: 2025-11-10 | Updated: 2025-11-10

USAGE:
streamlit run modules/google_maps/ui/streamlit_app.py

FEATURES:
- Two modes: Personal (your API key) & Shared (user API keys)
- Interactive state/city selection with custom inputs
- Real-time progress tracking
- Data preview and download
- Cost estimation
- File isolation per session (Shared mode)
- API key security (session-only storage)
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Google Places API integration
from modules.google_maps.ui.google_places_integration import search_multiple_locations

# Load environment variables from project root
env_path = project_root / '.env'
# Force override existing environment variables
load_dotenv(dotenv_path=env_path, override=True)

# Debug: Check if .env was loaded
if not env_path.exists():
    st.error(f"⚠️ .env file not found at: {env_path}")
    st.info(f"Project root: {project_root}")
else:
    # Verify we can read the file
    try:
        with open(env_path, 'r') as f:
            env_content = f.read()
            if 'GOOGLE_MAPS_API_KEY' not in env_content:
                st.error("GOOGLE_MAPS_API_KEY not found in .env file content!")
    except Exception as e:
        st.error(f"Error reading .env: {e}")

# Page configuration
st.set_page_config(
    page_title="Google Places Lead Collector",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

# Custom CSS
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
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
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

# Header
st.markdown('<div class="main-header">🗺️ Google Places Lead Collector</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Collect qualified leads for your voice AI agents</div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")

    # MODE SWITCHER
    st.subheader("🔐 Operation Mode")
    mode = st.radio(
        "Select Mode",
        ["Personal", "Shared"],
        help="""
        Personal: Use your configured API key (secure, all features)
        Shared: Users enter their own API key (public deployment)
        """
    )

    if mode == "Personal":
        st.markdown("""
        <div class="info-box">
            <strong>Personal Mode</strong><br>
            Using API key from .env file<br>
            All results visible<br>
            Full control
        </div>
        """, unsafe_allow_html=True)

        # Get API key from environment
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')

        # Debug info
        with st.expander("🔍 Debug Info"):
            st.write(f"Project root: {project_root}")
            st.write(f".env path: {env_path}")
            st.write(f".env exists: {env_path.exists()}")
            st.write(f"API key loaded: {'Yes' if api_key else 'No'}")
            if api_key:
                st.write(f"API key (masked): {api_key[:10]}...{api_key[-4:]}")

        if not api_key:
            st.error("⚠️ API key not found in .env file!")
            st.info("Add GOOGLE_MAPS_API_KEY to your .env file")
            st.stop()

    else:  # Shared mode
        st.markdown("""
        <div class="warning-box">
            <strong>Shared Mode</strong><br>
            Enter your own API key<br>
            Only your results visible<br>
            Session-only storage
        </div>
        """, unsafe_allow_html=True)

        # API key input
        api_key = st.text_input(
            "Google Places API Key",
            type="password",
            value=st.session_state.api_key or "",
            help="Your API key is stored only in your browser session",
            placeholder="AIzaSy..."
        )

        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ API key set!")
        else:
            st.warning("⚠️ Please enter your API key to continue")

        # Link to instructions
        with st.expander("📘 How to get API key?"):
            st.markdown("""
            ### Quick Steps:
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project
            3. Enable **Places API** and **Geocoding API**
            4. Create API key in **Credentials**
            5. Enable billing ($200 free credit/month)

            **[Full Instructions →](https://github.com/LeonidSvb/cold-outreach/blob/master/modules/google_maps/ui/API_KEY_SETUP.md)**
            """)

        if not api_key:
            st.stop()

    st.divider()

    # COLLECTION SETTINGS
    st.subheader("📍 Target Locations")

    location_mode = st.radio(
        "Location Input",
        ["Predefined States", "Custom Cities"],
        help="Choose predefined or enter custom locations"
    )

    cities_list = []

    if location_mode == "Predefined States":
        state = st.selectbox(
            "Select State",
            ["Texas", "Florida", "California", "New York"],
            help="All major cities in this state will be scraped"
        )

        # Predefined city lists
        STATE_CITIES = {
            "Texas": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
            "Florida": ["Miami", "Tampa", "Orlando", "Jacksonville", "Fort Lauderdale"],
            "California": ["Los Angeles", "San Francisco", "San Diego", "San Jose", "Sacramento"],
            "New York": ["New York City", "Buffalo", "Rochester", "Yonkers", "Syracuse"]
        }

        cities_list = [f"{city}, {state[:2].upper()}" for city in STATE_CITIES[state]]
        st.info(f"📍 {len(cities_list)} cities selected")

    else:  # Custom cities
        st.markdown("""
        **📝 Enter your cities below. Supported formats:**

        **USA:** `Miami, FL` or `New York City, NY`

        **International:**
        - `Denpasar, Bali, Indonesia`
        - `London, UK`
        - `Paris, France`

        **Multiple ways:**
        - One per line (easiest)
        - Comma-separated bulk paste
        - Copy from Excel/Google Sheets
        """)

        cities_input = st.text_area(
            "Cities List",
            placeholder="""Miami, FL
Houston, TX
Denpasar, Bali, Indonesia
London, UK
Paris, France
Tokyo, Japan
Dubai, UAE""",
            help="Enter city + location. Works worldwide!",
            height=200
        )

        # Parse and validate cities
        if cities_input:
            # Handle different formats
            raw_cities = []

            # Check if comma-separated (single line with multiple commas)
            if '\n' not in cities_input and ',' in cities_input:
                # Split by state abbreviations pattern
                import re
                # Pattern: city name + comma + 2-letter state
                parts = re.split(r',\s*([A-Z]{2})', cities_input)
                for i in range(1, len(parts), 2):
                    if i < len(parts):
                        city_name = parts[i-1].strip().strip(',')
                        state_abbr = parts[i].strip()
                        if city_name and state_abbr:
                            raw_cities.append(f"{city_name}, {state_abbr}")
            else:
                # Newline separated
                raw_cities = [c.strip() for c in cities_input.split('\n') if c.strip()]

            # Validate format (flexible for international cities)
            valid_cities = []
            invalid_cities = []

            for city in raw_cities:
                # Check format: must have at least city + location
                if ',' in city:
                    parts = [p.strip() for p in city.split(',') if p.strip()]

                    if len(parts) >= 2:
                        # Valid formats:
                        # - "Miami, FL" (US state)
                        # - "London, UK" (country code)
                        # - "Denpasar, Bali, Indonesia" (city, region, country)
                        # - "Paris, France" (city, country)

                        # Just capitalize properly and accept
                        formatted_parts = [p.strip().title() for p in parts]

                        # Special handling for US states (keep uppercase)
                        if len(parts) == 2 and len(formatted_parts[-1]) == 2 and formatted_parts[-1].replace('.', '').isalpha():
                            # Likely US state abbreviation - keep uppercase
                            formatted_parts[-1] = formatted_parts[-1].upper()

                        valid_cities.append(', '.join(formatted_parts))
                    else:
                        invalid_cities.append(city)
                else:
                    invalid_cities.append(city)

            cities_list = valid_cities

            # Show validation results
            if valid_cities:
                st.success(f"✅ {len(valid_cities)} valid cities parsed")

                # Show preview
                with st.expander(f"👁️ Preview cities ({len(valid_cities)})"):
                    # Group by last part (state/country)
                    from collections import defaultdict
                    by_location = defaultdict(list)
                    for city in valid_cities:
                        parts = city.split(', ')
                        location_key = parts[-1]  # Last part (FL, UK, Indonesia, etc)
                        city_full = ', '.join(parts[:-1])  # Everything before last
                        by_location[location_key].append(city_full)

                    for location in sorted(by_location.keys()):
                        st.markdown(f"**{location}:** {', '.join(by_location[location])}")

            if invalid_cities:
                st.warning(f"⚠️ {len(invalid_cities)} cities have invalid format")
                with st.expander("❌ Invalid entries (fix these)"):
                    st.markdown("""
                    **Correct formats:**

                    **USA:**
                    - ✅ Miami, FL
                    - ✅ New York City, NY

                    **International:**
                    - ✅ Denpasar, Bali, Indonesia
                    - ✅ London, UK
                    - ✅ Paris, France
                    - ✅ Tokyo, Japan

                    **Invalid:**
                    - ❌ Miami (missing location)
                    - ❌ Miami Florida (missing comma)

                    **Minimum:** City name + comma + location
                    """)
                    for invalid in invalid_cities:
                        st.text(f"❌ {invalid}")
        else:
            st.warning("⚠️ Enter at least one city")

    st.divider()

    # NICHE SELECTION
    st.subheader("🎯 Target Niche")

    niche_mode = st.radio(
        "Niche Input",
        ["Predefined", "Custom"],
        help="Choose from common niches or enter your own"
    )

    if niche_mode == "Predefined":
        niche = st.selectbox(
            "Business Type",
            [
                "HVAC contractors",
                "plumbers",
                "electricians",
                "towing services",
                "garage door repair",
                "locksmiths",
                "roofers",
                "pest control",
                "carpet cleaning",
                "landscaping"
            ],
            help="Common service businesses for voice AI"
        )
    else:
        st.markdown("""
        **💡 Enter your target business type**

        Examples:
        - Service businesses: `dog grooming`, `auto repair`, `pool cleaning`
        - Retail: `coffee shops`, `flower shops`, `pet stores`
        - Healthcare: `dental clinics`, `veterinary clinics`
        - Food: `restaurants`, `bakeries`, `food trucks`
        """)

        niche = st.text_input(
            "Business Type",
            placeholder="e.g., dog grooming services",
            help="Be specific! Google will search for this exact term.",
            max_chars=100
        )

        if niche:
            # Clean and validate
            niche = niche.strip().lower()

            # Show what will be searched
            st.info(f"🔍 Will search for: **\"{niche}\"** in Google Places")

            # Tips
            with st.expander("💡 Tips for better results"):
                st.markdown("""
                **Good examples:**
                - ✅ `hvac contractors` (specific service)
                - ✅ `emergency plumbers` (includes keyword)
                - ✅ `24/7 towing services` (specific niche)

                **Avoid:**
                - ❌ `hvac` (too broad)
                - ❌ `home services` (too general)
                - ❌ `Best HVAC near me` (Google handles this)

                **Pro tip:** Use the exact term your target customers would search for!
                """)
        else:
            st.warning("⚠️ Enter a business type")

    st.divider()

    # QUALITY FILTERS
    st.subheader("🔍 Quality Filters")

    col1, col2 = st.columns(2)
    with col1:
        min_reviews = st.number_input(
            "Min Reviews",
            min_value=0,
            max_value=500,
            value=20,
            step=10
        )

    with col2:
        max_reviews = st.number_input(
            "Max Reviews",
            min_value=50,
            max_value=2000,
            value=800,
            step=50
        )

    min_rating = st.slider(
        "Minimum Rating",
        min_value=0.0,
        max_value=5.0,
        value=4.0,
        step=0.1
    )

    st.divider()

    # ADVANCED SETTINGS
    with st.expander("⚡ Advanced"):
        parallel = st.checkbox("Parallel Processing", value=True)
        save_raw = st.checkbox("Save Raw Data", value=True)

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Start Collection", "📁 View Results", "💰 Cost Calculator"])

with tab1:
    st.header("Start New Collection")

    # Validate inputs
    if not cities_list:
        st.warning("⚠️ Please configure locations in the sidebar")
        st.stop()

    if not niche:
        st.warning("⚠️ Please select or enter a business niche in the sidebar")
        st.stop()

    # Show current configuration
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Cities", len(cities_list))

    with col2:
        st.metric("Niche", niche)

    with col3:
        estimated_cost = len(cities_list) * 1.2 * 0.032 + len(cities_list) * 30 * 0.7 * 0.017
        st.metric("Est. Cost", f"${estimated_cost:.2f}")

    # Show cities preview
    with st.expander("🗺️ Cities to Scrape"):
        st.write(", ".join(cities_list[:20]))
        if len(cities_list) > 20:
            st.write(f"... and {len(cities_list) - 20} more")

    st.divider()

    # Start button
    if st.button("🚀 Start Collection", type="primary", use_container_width=True):

        # Determine output directory based on mode
        if mode == "Personal":
            output_dir = Path("modules/google_maps/results/personal")
        else:
            output_dir = Path(f"modules/google_maps/results/sessions/{st.session_state.session_id}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Create progress containers
        progress_bar = st.progress(0, text="Initializing...")
        status_text = st.empty()

        # Real Google Places API collection
        try:
            start_time = time.time()

            # Phase 1: Initialize
            progress_bar.progress(10, text=f"Preparing to search {len(cities_list)} locations...")

            # Phase 2: API Calls
            progress_bar.progress(30, text=f"Searching Google Places for '{niche}'...")

            # Call real API
            api_result = search_multiple_locations(
                api_key=api_key,
                query=niche,
                locations=cities_list,
                max_results=max_results,
                min_rating=min_rating,
                min_reviews=min_reviews,
                max_reviews=max_reviews
            )

            # Phase 3: Processing results
            progress_bar.progress(70, text="Processing API results...")

            results_data = api_result['results']
            stats = api_result['stats']

            # Convert to DataFrame
            if results_data:
                results_df = pd.DataFrame(results_data)
            else:
                results_df = pd.DataFrame(columns=['Name', 'Phone', 'Rating', 'Reviews', 'Address', 'Website', 'Google Maps'])

            # Phase 4: Saving
            progress_bar.progress(90, text="Saving results...")

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            result_file = output_dir / f"{niche.replace(' ', '_')}_{timestamp}.csv"
            results_df.to_csv(result_file, index=False)

            # Also save JSON with stats
            json_file = output_dir / f"{niche.replace(' ', '_')}_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'niche': niche,
                        'cities': cities_list,
                        'timestamp': timestamp,
                        'filters': {
                            'min_rating': min_rating,
                            'min_reviews': min_reviews,
                            'max_reviews': max_reviews,
                            'max_results': max_results
                        }
                    },
                    'stats': stats,
                    'results': results_data
                }, f, indent=2, ensure_ascii=False)

            # Complete
            progress_bar.progress(100, text="Done!")
            time.sleep(0.5)
            progress_bar.empty()

            # Calculate actual statistics
            end_time = time.time()
            elapsed_time = end_time - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)

            # Estimate cost (Google Places API pricing: $0.017 per Text Search request)
            # Each location = 1 request
            total_requests = len(cities_list)
            estimated_cost = total_requests * 0.017

            # Success message
            st.markdown(f"""
            <div class="success-box">
                <h3>✅ Collection Complete!</h3>
                <p><strong>Results:</strong> {len(results_df)} qualified leads collected</p>
                <p><strong>Time:</strong> {minutes} minutes {seconds} seconds</p>
                <p><strong>Estimated Cost:</strong> ${estimated_cost:.2f} (${total_requests} requests)</p>
                <p><strong>Locations Searched:</strong> {len(cities_list)}</p>
                <p><strong>Saved to:</strong> {result_file.name}</p>
            </div>
            """, unsafe_allow_html=True)

            # Show per-location stats
            if stats:
                st.subheader("Results by Location")
                stats_df = pd.DataFrame([
                    {'Location': loc, 'Results': count}
                    for loc, count in stats.items()
                ])
                st.dataframe(stats_df, use_container_width=True)

            # Display results
            st.subheader(f"Preview of {len(results_df)} Results")
            st.dataframe(results_df, use_container_width=True)

            # Download buttons
            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📥 Download CSV",
                    results_df.to_csv(index=False, encoding='utf-8'),
                    f"{niche.replace(' ', '_')}_{timestamp}.csv",
                    "text/csv",
                    use_container_width=True
                )

            with col2:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json_content = f.read()
                st.download_button(
                    "📄 Download JSON",
                    json_content,
                    f"{niche.replace(' ', '_')}_{timestamp}.json",
                    "application/json",
                    use_container_width=True
                )

        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ Collection failed: {str(e)}")
            st.exception(e)

with tab2:
    st.header("View Past Results")

    # Determine which results to show based on mode
    if mode == "Personal":
        results_dir = Path("modules/google_maps/results/personal")
        st.info("📁 Showing all your personal results")
    else:
        results_dir = Path(f"modules/google_maps/results/sessions/{st.session_state.session_id}")
        st.info("📁 Showing only your session results")

    if results_dir.exists():
        result_files = sorted(list(results_dir.glob("*.csv")), reverse=True)

        if result_files:
            st.success(f"Found {len(result_files)} result files")

            for file in result_files[:20]:
                with st.expander(f"📄 {file.name}"):
                    col1, col2, col3 = st.columns([2, 1, 1])

                    with col1:
                        size_mb = file.stat().st_size / 1024 / 1024
                        modified = datetime.fromtimestamp(file.stat().st_mtime)
                        st.text(f"Size: {size_mb:.2f} MB")
                        st.text(f"Modified: {modified.strftime('%Y-%m-%d %H:%M')}")

                    with col2:
                        if st.button("👁️ Preview", key=f"preview_{file.name}"):
                            df = pd.read_csv(file)
                            st.dataframe(df.head(10))

                    with col3:
                        df = pd.read_csv(file)
                        csv_data = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download",
                            csv_data,
                            file.name,
                            "text/csv",
                            key=f"download_{file.name}"
                        )
        else:
            st.info("No results found yet. Run a collection first!")
    else:
        st.warning("Results directory not found. Run your first collection!")

with tab3:
    st.header("Cost Calculator")

    st.markdown("""
    ### Google Places API Pricing

    - **Nearby Search**: $0.032 per request
    - **Place Details**: $0.017 per request
    - **Geocoding**: $0.005 per request
    - **Free Tier**: $200/month (automatically applied)
    """)

    st.subheader("Estimate Your Costs")

    calc_cities = st.number_input("Number of Cities", min_value=1, max_value=100, value=len(cities_list) if cities_list else 20)
    calc_avg_results = st.slider("Avg Results per City", 15, 50, 20)
    calc_pass_rate = st.slider("Expected Pass Rate", 0.3, 1.0, 0.7, 0.05)

    # Calculations
    total_searches = calc_cities * 1.2
    total_raw = calc_cities * calc_avg_results
    total_filtered = int(total_raw * calc_pass_rate)

    geocoding_cost = calc_cities * 0.005
    search_cost = total_searches * 0.032
    details_cost = total_filtered * 0.017
    total_cost = geocoding_cost + search_cost + details_cost

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

    # Cost breakdown
    st.subheader("Cost Breakdown")

    breakdown_data = pd.DataFrame({
        'Component': ['Geocoding', 'Nearby Search', 'Place Details'],
        'Cost': [geocoding_cost, search_cost, details_cost]
    })

    st.bar_chart(breakdown_data.set_index('Component'))

    # Budget check
    if total_cost <= 200:
        remaining = 200 - total_cost
        st.success(f"✅ Within free tier! ${remaining:.2f} remaining this month")
    else:
        overage = total_cost - 200
        st.error(f"❌ Exceeds free tier by ${overage:.2f}")

# Footer
st.divider()
st.markdown(f"""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Google Places Lead Collector</strong> v2.0.0</p>
    <p>Mode: {mode} | Session: {st.session_state.session_id[:8]}...</p>
    <p>Built with Streamlit | Powered by Google Places API</p>
</div>
""", unsafe_allow_html=True)
