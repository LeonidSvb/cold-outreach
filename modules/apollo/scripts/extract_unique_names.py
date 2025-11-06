#!/usr/bin/env python3
"""
Extract unique company names and locations for LLM analysis
"""

import pandas as pd
import json

df = pd.read_csv(r'C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv')

# Get unique company names (only from ICP score 2 - our target companies)
df_processed = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_processed_20251103_143944.csv')
perfect_matches = df_processed[df_processed['ICP Match Score'] == 2]

# Extract unique company names from perfect matches
unique_companies = perfect_matches['company_name'].dropna().unique()[:100]

# Extract locations (city + state combinations)
locations_data = []
for idx, row in perfect_matches.head(100).iterrows():
    city = str(row.get('city', ''))
    state = str(row.get('state', ''))
    country = str(row.get('country', ''))

    if city != 'nan' and state != 'nan':
        locations_data.append(f"{city}, {state}")
    elif city != 'nan':
        locations_data.append(city)
    elif state != 'nan':
        locations_data.append(state)
    elif country != 'nan':
        locations_data.append(country)

unique_locations = list(set(locations_data))[:100]

# Save to JSON for analysis
output = {
    "company_names": list(unique_companies),
    "locations": unique_locations,
    "total_companies": len(unique_companies),
    "total_locations": len(unique_locations)
}

with open(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\unique_names_locations.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"Extracted {len(unique_companies)} unique company names")
print(f"Extracted {len(unique_locations)} unique locations")
print("\nSample company names:")
for i, name in enumerate(list(unique_companies)[:10], 1):
    print(f"  {i}. {name}")

print("\nSample locations:")
for i, loc in enumerate(unique_locations[:10], 1):
    print(f"  {i}. {loc}")
