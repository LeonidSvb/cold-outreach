#!/usr/bin/env python3
"""
=== TEXAS EMERGENCY SERVICES COMBINED HEAT MAP ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Generate interactive heat map showing ALL emergency service niches across Texas

FEATURES:
- Multiple niches on one map with color coding
- Interactive HTML map with zoom/pan
- Heat map layer showing overall density
- Clickable markers with company details
- Niche-based color coding

USAGE:
python modules/google_maps/scripts/create_combined_heatmap.py

OUTPUT:
modules/google_maps/results/texas_emergency_services_heatmap.html
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict

import folium
from folium import plugins

def extract_city_from_address(address: str) -> str:
    """Extract city name from full address"""
    parts = address.split(',')
    if len(parts) >= 3:
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

def get_niche_color(niche: str) -> str:
    """Get color for each niche"""
    niche_colors = {
        "hvac": "red",
        "plumbers": "blue",
        "electricians": "orange",
        "locksmiths": "purple",
        "towing": "green",
        "garage": "darkred"
    }

    niche_lower = niche.lower()
    for key, color in niche_colors.items():
        if key in niche_lower:
            return color

    return "gray"

def get_niche_icon(niche: str) -> str:
    """Get icon for each niche"""
    niche_lower = niche.lower()

    if "hvac" in niche_lower:
        return "fire"
    elif "plumber" in niche_lower:
        return "tint"
    elif "electric" in niche_lower:
        return "flash"
    elif "locksmith" in niche_lower:
        return "lock"
    elif "towing" in niche_lower:
        return "truck"
    elif "garage" in niche_lower or "door" in niche_lower:
        return "home"

    return "info-sign"

def create_combined_heatmap(niche_files: Dict[str, Path], output_file: Path):
    """
    Create combined heat map from multiple Google Places results

    Args:
        niche_files: Dict mapping niche name to JSON file path
        output_file: Path to output HTML file
    """
    print("="*70)
    print("TEXAS EMERGENCY SERVICES COMBINED HEAT MAP")
    print("="*70)
    print()

    # Get city coordinates
    city_coords = get_texas_city_coordinates()

    # Create base map centered on Texas
    texas_center = [31.0, -99.0]
    m = folium.Map(
        location=texas_center,
        zoom_start=6,
        tiles='OpenStreetMap'
    )

    # Prepare heat map data
    heat_data = []

    # Statistics
    total_companies = 0
    niche_stats = {}

    # Process each niche
    for niche_name, json_file in niche_files.items():
        print(f"Loading {niche_name}...")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        all_places = data.get('all_places', [])
        niche_stats[niche_name] = len(all_places)
        total_companies += len(all_places)

        # Group companies by city
        companies_by_city = defaultdict(list)

        for place in all_places:
            address = place.get('address', place.get('vicinity', ''))
            city = extract_city_from_address(address)
            city_normalized = city.strip()
            companies_by_city[city_normalized].append(place)

        # Get color for this niche
        color = get_niche_color(niche_name)
        icon = get_niche_icon(niche_name)

        # Add markers for this niche
        for city, companies in companies_by_city.items():
            if city in city_coords:
                lat, lng = city_coords[city]

                # Add to heat map data
                heat_data.append([lat, lng, len(companies)])

                # Create markers
                for company in companies:
                    popup_html = f"""
                    <div style="width:300px">
                        <h4>{company.get('name', 'N/A')}</h4>
                        <p><b>Niche:</b> {niche_name}</p>
                        <p><b>Address:</b> {company.get('address', company.get('vicinity', 'N/A'))}</p>
                        <p><b>Phone:</b> {company.get('phone', 'N/A')}</p>
                        <p><b>Rating:</b> {company.get('rating', 0)} ({company.get('user_ratings_total', 0)} reviews)</p>
                        <p><b>Website:</b> <a href="{company.get('website', '#')}" target="_blank">Visit</a></p>
                    </div>
                    """

                    folium.Marker(
                        location=[lat, lng],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"{company.get('name', 'Company')} ({niche_name})",
                        icon=folium.Icon(color=color, icon=icon)
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

    # Create legend HTML
    legend_items = ""
    for niche_name, count in sorted(niche_stats.items(), key=lambda x: x[1], reverse=True):
        color = get_niche_color(niche_name)
        legend_items += f"""
        <p style="margin: 3px 0">
            <span style="color: {color}">●</span> {niche_name}: {count} companies
        </p>
        """

    legend_html = f'''
    <div style="position: fixed;
                top: 10px; right: 10px; width: 250px; height: auto;
                background-color: white; border:2px solid grey; z-index:9999;
                font-size:14px; padding: 10px">
        <h4 style="margin-top:0">Texas Emergency Services</h4>
        <p style="margin: 5px 0"><b>Total: {total_companies} companies</b></p>
        <hr style="margin: 5px 0">
        {legend_items}
        <hr style="margin: 5px 0">
        <p style="margin-top: 5px; font-size: 12px"><b>Heat Map:</b><br>
        Density of all companies</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    output_file.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_file))

    print("="*70)
    print("COMBINED HEAT MAP GENERATED")
    print("="*70)
    print(f"Output file: {output_file}")
    print(f"Total companies: {total_companies}")
    print()
    print("Statistics by niche:")
    for niche_name, count in sorted(niche_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {niche_name:<20} {count:>3} companies")
    print()
    print("Open the HTML file in browser to view interactive map!")
    print("="*70)

def main():
    """Main execution"""
    # Define niche files
    niche_files = {
        "HVAC Contractors": Path("data/processed/google_statewide_20251109_174421.json"),
        "Plumbers": Path("data/processed/google_statewide_20251109_175704.json"),
        "Electricians": Path("data/processed/google_statewide_20251109_175621.json"),
        "Locksmiths": Path("data/processed/google_statewide_20251109_175642.json"),
        "Towing Services": Path("data/processed/google_statewide_20251109_175650.json"),
        "Garage Door Repair": Path("data/processed/google_statewide_20251109_175659.json"),
    }

    output_file = Path("modules/google_maps/results/texas_emergency_services_heatmap.html")

    create_combined_heatmap(niche_files, output_file)

if __name__ == "__main__":
    main()
