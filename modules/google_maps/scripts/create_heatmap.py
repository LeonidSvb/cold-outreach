#!/usr/bin/env python3
"""
=== TEXAS HVAC HEAT MAP GENERATOR ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Generate interactive heat map of HVAC companies across Texas

FEATURES:
- Interactive HTML map with zoom/pan
- Heat map layer showing HVAC density
- Clickable markers with company details
- City-based clustering
- Review count weighting

USAGE:
python modules/google_maps/scripts/create_heatmap.py

OUTPUT:
modules/google_maps/results/texas_hvac_heatmap.html
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

import folium
from folium import plugins

def extract_city_from_address(address: str) -> str:
    """Extract city name from full address"""
    # Format: "123 Main St, Houston, TX 77001, USA"
    parts = address.split(',')
    if len(parts) >= 3:
        # City is usually second-to-last before state
        city = parts[-3].strip()
        return city
    return "Unknown"

def get_texas_city_coordinates() -> Dict[str, Tuple[float, float]]:
    """
    Approximate coordinates for major Texas cities
    For accurate visualization
    """
    return {
        "Houston": (29.7604, -95.3698),
        "Dallas": (32.7767, -96.7970),
        "San Antonio": (29.4241, -98.4936),
        "Austin": (30.2672, -97.7431),
        "Fort Worth": (32.7555, -97.3308),
        "El Paso": (31.7619, -106.4850),
        "Arlington": (32.7357, -97.1081),
        "Corpus Christi": (27.8006, -97.3964),
        "Plano": (33.0198, -96.6989),
        "Laredo": (27.5306, -99.4803),
        "Lubbock": (33.5779, -101.8552),
        "Irving": (32.8140, -96.9489),
        "Garland": (32.9126, -96.6389),
        "Frisco": (33.1507, -96.8236),
        "McKinney": (33.1972, -96.6397),
        "Amarillo": (35.2220, -101.8313),
        "Grand Prairie": (32.7460, -96.9978),
        "Brownsville": (25.9017, -97.4975),
        "Pasadena": (29.6911, -95.2091),
        "Mesquite": (32.7668, -96.5992),
        "Killeen": (31.1171, -97.7278),
        "McAllen": (26.2034, -98.2300),
        "Waco": (31.5493, -97.1467),
        "Carrollton": (32.9537, -96.8903),
        "Beaumont": (30.0860, -94.1018),
        "Abilene": (32.4487, -99.7331),
        "Round Rock": (30.5083, -97.6789),
        "Richardson": (32.9483, -96.7299),
        "Midland": (31.9973, -102.0779),
        "Odessa": (31.8457, -102.3676),
        "Lewisville": (33.0462, -96.9942),
        "College Station": (30.6280, -96.3344),
        "Pearland": (29.5636, -95.2861),
        "Sugar Land": (29.6196, -95.6349),
        "Tyler": (32.3513, -95.3011),
        "Denton": (33.2148, -97.1331),
        "Wichita Falls": (33.9137, -98.4934),
    }

def create_heatmap(json_file: Path, output_file: Path):
    """
    Create interactive heat map from Google Places results

    Args:
        json_file: Path to results JSON file
        output_file: Path to output HTML file
    """
    print("="*70)
    print("TEXAS HVAC HEAT MAP GENERATOR")
    print("="*70)
    print()

    # Load data
    print(f"Loading data from: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_places = data.get('all_places', [])
    print(f"Total places: {len(all_places)}")
    print()

    # Get city coordinates
    city_coords = get_texas_city_coordinates()

    # Group companies by city
    companies_by_city = defaultdict(list)

    for place in all_places:
        address = place.get('address', place.get('vicinity', ''))
        city = extract_city_from_address(address)

        # Normalize city name
        city_normalized = city.strip()

        companies_by_city[city_normalized].append(place)

    print("Companies by city:")
    for city, companies in sorted(companies_by_city.items(),
                                   key=lambda x: len(x[1]),
                                   reverse=True)[:10]:
        print(f"  {city:<20} {len(companies):>3} companies")
    print()

    # Create base map centered on Texas
    texas_center = [31.0, -99.0]  # Geographic center of Texas
    m = folium.Map(
        location=texas_center,
        zoom_start=6,
        tiles='OpenStreetMap'
    )

    # Prepare heat map data
    heat_data = []

    # Add markers and collect heat map points
    for city, companies in companies_by_city.items():
        if city in city_coords:
            lat, lng = city_coords[city]

            # Heat map point with weight based on number of companies
            heat_data.append([lat, lng, len(companies)])

            # Create marker cluster for this city
            for company in companies:
                # Create popup with company info
                popup_html = f"""
                <div style="width:300px">
                    <h4>{company.get('name', 'N/A')}</h4>
                    <p><b>Address:</b> {company.get('address', company.get('vicinity', 'N/A'))}</p>
                    <p><b>Phone:</b> {company.get('phone', 'N/A')}</p>
                    <p><b>Rating:</b> {company.get('rating', 0)} ({company.get('user_ratings_total', 0)} reviews)</p>
                    <p><b>Website:</b> <a href="{company.get('website', '#')}" target="_blank">Visit</a></p>
                </div>
                """

                # Determine marker color based on review count
                reviews = company.get('user_ratings_total', 0)
                if reviews >= 300:
                    color = 'red'  # High activity
                elif reviews >= 100:
                    color = 'orange'  # Medium activity
                else:
                    color = 'green'  # Lower activity

                folium.Marker(
                    location=[lat, lng],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=company.get('name', 'HVAC Company'),
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)

    # Add heat map layer
    if heat_data:
        plugins.HeatMap(
            heat_data,
            min_opacity=0.3,
            max_opacity=0.8,
            radius=30,
            blur=25,
            gradient={
                0.0: 'blue',
                0.4: 'lime',
                0.6: 'yellow',
                0.8: 'orange',
                1.0: 'red'
            }
        ).add_to(m)

    # Add legend
    legend_html = '''
    <div style="position: fixed;
                top: 10px; right: 10px; width: 220px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
        <h4 style="margin-top:0">Texas HVAC Heat Map</h4>
        <p style="margin: 5px 0"><b>Marker Colors:</b></p>
        <p style="margin: 3px 0">
            <span style="color: red">●</span> 300+ reviews (High activity)
        </p>
        <p style="margin: 3px 0">
            <span style="color: orange">●</span> 100-299 reviews (Medium)
        </p>
        <p style="margin: 3px 0">
            <span style="color: green">●</span> 30-99 reviews (Lower)
        </p>
        <p style="margin-top: 10px"><b>Heat Map:</b><br>
        Density of HVAC companies</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    output_file.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_file))

    print("="*70)
    print("HEAT MAP GENERATED")
    print("="*70)
    print(f"Output file: {output_file}")
    print(f"Total companies mapped: {len(all_places)}")
    print(f"Cities covered: {len(companies_by_city)}")
    print()
    print("Open the HTML file in browser to view interactive map!")
    print("="*70)

def main():
    """Main execution"""
    # Find latest results file
    results_dir = Path("data/processed")

    # Get all Google statewide results
    result_files = sorted(results_dir.glob("google_statewide_*.json"), reverse=True)

    if not result_files:
        print("No results found! Run texas_hvac_scraper.py first.")
        return

    latest_file = result_files[0]
    output_file = Path("modules/google_maps/results/texas_hvac_heatmap.html")

    create_heatmap(latest_file, output_file)

if __name__ == "__main__":
    main()
