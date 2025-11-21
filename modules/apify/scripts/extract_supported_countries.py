#!/usr/bin/env python3
"""
Extract supported countries from Apify actor
"""

import json
import re
from pathlib import Path

# Countries extracted from API error response
countries_raw = 'Field input.country must be equal to one of the allowed values: "ALL", "US", "GB", "AE", "AR", "AU", "BE", "BR", "CA", "DK", "ES", "FI", "FR", "IE", "IN", "IT", "JP", "KR", "MX", "NL", "NO", "PL", "PT", "SA", "SE", "TH", "TR"'

# Extract country codes
country_codes = re.findall(r'"([A-Z]+)"', countries_raw)

# Country code to name mapping (ISO 3166-1)
COUNTRY_NAMES = {
    'ALL': 'All Countries',
    'US': 'United States',
    'GB': 'United Kingdom',
    'AE': 'United Arab Emirates',
    'AR': 'Argentina',
    'AU': 'Australia',
    'BE': 'Belgium',
    'BR': 'Brazil',
    'CA': 'Canada',
    'DK': 'Denmark',
    'ES': 'Spain',
    'FI': 'Finland',
    'FR': 'France',
    'IE': 'Ireland',
    'IN': 'India',
    'IT': 'Italy',
    'JP': 'Japan',
    'KR': 'South Korea',
    'MX': 'Mexico',
    'NL': 'Netherlands',
    'NO': 'Norway',
    'NZ': 'New Zealand',
    'PL': 'Poland',
    'PT': 'Portugal',
    'SA': 'Saudi Arabia',
    'SE': 'Sweden',
    'TH': 'Thailand',
    'TR': 'Turkey',
}

countries_data = []
for code in country_codes:
    countries_data.append({
        'code': code,
        'name': COUNTRY_NAMES.get(code, code)
    })

print(f"Total supported countries: {len(countries_data)}")

# Save to JSON
data_dir = Path(__file__).parent.parent / 'data'
data_dir.mkdir(exist_ok=True)

output_file = data_dir / 'supported_countries.json'
with open(output_file, 'w') as f:
    json.dump({
        "countries": countries_data,
        "total": len(countries_data),
        "source": "Apify API error response",
        "actor": "xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps",
        "date": "2025-11-21",
        "note": "Use 'ALL' to search across all countries"
    }, f, indent=2)

# Save human-readable list
txt_file = data_dir / 'SUPPORTED_COUNTRIES.txt'
with open(txt_file, 'w') as f:
    f.write("APIFY ACTOR - SUPPORTED COUNTRIES (28 total)\n")
    f.write("=" * 60 + "\n\n")
    f.write("Use 'ALL' to search globally, or specify country code:\n\n")

    for item in countries_data:
        code = item['code']
        name = item['name']
        f.write(f"{code:3s} - {name}\n")

print(f"\nFiles saved:")
print(f"  - {output_file}")
print(f"  - {txt_file}")

print(f"\nTop markets for cold outreach:")
english_speaking = ['US', 'GB', 'AU', 'CA', 'IE', 'NZ']
high_gdp = ['US', 'JP', 'GB', 'FR', 'IT', 'CA', 'KR', 'AU', 'ES', 'NL']

print(f"\nEnglish-speaking: {', '.join(english_speaking)}")
print(f"High GDP markets: {', '.join(high_gdp[:10])}")

print(f"\nRegional groupings:")
print(f"  North America: US, CA, MX")
print(f"  Europe: GB, FR, IT, ES, NL, BE, IE, DK, FI, NO, SE, PL, PT")
print(f"  Asia-Pacific: AU, JP, KR, IN, TH, SG")
print(f"  Middle East: AE, SA, TR")
print(f"  South America: AR, BR")
