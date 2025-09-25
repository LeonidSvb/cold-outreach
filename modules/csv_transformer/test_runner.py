#!/usr/bin/env python3
"""
Test runner for CSV transformer - direct execution without interactive mode
"""

import os
import sys
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

# Set OpenAI API key from .env
sys.path.append(str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Import OpenAI
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def normalize_company_name(company_name: str) -> str:
    """Apply company name normalization prompt"""

    prompt = f"""You will receive a company name as input.

Your task is to return a shortened, casual version of that name — the way employees or insiders would refer to the company in everyday conversation.

Only output the normalized, informal name — no extra words, no explanations, no capitalization unless absolutely natural.

Strip away any corporate terms like "Inc.", "LLC", "Solutions", "Technologies", "Group", "Enterprises", etc.

Make the name as short and casual as possible, while keeping it recognizable.

Examples:
• "Acme Technologies Inc." → "acme"
• "Northwest Payment Solutions" → "northwest"
• "BrightPixel Group" → "brightpixel"
• "Global Data Systems LLC" →  "globaldata"

Only return the casual name. Nothing else.

Company name: {company_name}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing '{company_name}': {e}")
        return company_name.lower()

def normalize_city_name(city: str) -> str:
    """Apply city name normalization prompt"""

    prompt = f"""You will receive the name of a city or location as input.

Your task is to return a **casual, real-world abbreviation or shorthand** — the way locals or people in tech/startup circles naturally refer to it.

Only return a casual version **if one actually exists and is commonly used**.
If the full city name is already short and used as-is (like "London" or "Berlin"), just return it unchanged.

Guidelines:
• Use natural abbreviations only if they are real and recognized (e.g. "SF" for San Francisco, "NYC" for New York City, "SPB" for Saint Petersburg, "BLR" for Bangalore).
• Do **not** invent abbreviations that no one uses.
• Respect context — only shorten when it's common in tech/startup/business/informal language.
• Keep capitalization natural (e.g. "NYC", not "nyc"; "SPB", not "spb"; "London", not "london").
• Never include country, region, or extra words — just the core location name or its casual abbreviation.

Examples:
• "San Francisco" → "SF"
• "New York" → "NYC"
• "Saint Petersburg" → "SPB"
• "Bangalore" → "BLR"
• "Los Angeles" → "LA"
• "London" → "London"
• "Berlin" → "Berlin"
• "Chicago" → "Chicago"
• "São Paulo" → "Sampa"

Only return the final, normalized city name or abbreviation. No explanation, no punctuation, no extra words.

City name: {city}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error processing '{city}': {e}")
        return city

def main():
    """Run test transformation"""

    print("="*80)
    print("CSV TRANSFORMER TEST RUN")
    print("="*80)

    # Load test data
    csv_file = "test_50_leads.csv"
    if not os.path.exists(csv_file):
        print(f"Test file {csv_file} not found!")
        return

    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} leads from {csv_file}")

    # Show sample data
    print(f"\nSample companies: {list(df['company_name'].head(5))}")
    print(f"Sample cities: {list(df['city'].head(5))}")

    # Process first 5 rows for testing (to avoid encoding issues)
    test_df = df.head(5).copy()

    print(f"\nProcessing {len(test_df)} test leads...")

    # Normalize company names
    normalized_companies = []
    for i, company in enumerate(test_df['company_name']):
        company_str = str(company)[:50]  # Truncate for display
        print(f"Processing company {i+1}/{len(test_df)}: {company_str}")
        normalized = normalize_company_name(str(company))
        normalized_companies.append(normalized)
        print(f"  -> {normalized}")
        time.sleep(0.5)  # Rate limiting

    test_df['normalized_company'] = normalized_companies

    # Normalize city names
    normalized_cities = []
    for i, city in enumerate(test_df['city']):
        print(f"Processing city {i+1}/{len(test_df)}: {city}")
        normalized = normalize_city_name(str(city))
        normalized_cities.append(normalized)
        print(f"  -> {normalized}")
        time.sleep(0.5)  # Rate limiting

    test_df['normalized_city'] = normalized_cities

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/test_results_{timestamp}.csv"

    os.makedirs("results", exist_ok=True)
    test_df.to_csv(output_file, index=False)

    print(f"\nResults saved to: {output_file}")

    # Show comparison
    print(f"\nCOMPARISON RESULTS:")
    print("="*80)

    for i, row in test_df.iterrows():
        print(f"\nLead {i+1}:")
        print(f"  Original company: {row['company_name']}")
        print(f"  Normalized: {row['normalized_company']}")
        print(f"  Original city: {row['city']}")
        print(f"  Normalized: {row['normalized_city']}")

if __name__ == "__main__":
    main()