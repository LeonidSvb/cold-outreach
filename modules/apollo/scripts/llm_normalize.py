#!/usr/bin/env python3
"""
=== LLM-Based Company Name & Location Normalization ===
Version: 1.0.0 | Created: 2025-11-03

PURPOSE:
Use OpenAI API to normalize company names and locations
for casual, icebreaker-friendly format.

FEATURES:
- Batch processing (10 companies at a time for efficiency)
- Context-aware normalization (understands "NYC" vs "New York")
- Handles edge cases better than regex
- Progress tracking and error recovery

USAGE:
python llm_normalize.py
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import openai
from time import sleep

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# Load environment
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_processed_20251103_143944.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "BATCH_SIZE": 10,
    "MODEL": "gpt-4o-mini",
    "TEMPERATURE": 0.3,
}

NORMALIZATION_PROMPT = """You are a data normalization expert. Your task is to normalize company names and locations for use in casual, personalized cold outreach icebreakers.

COMPANY NAME RULES:
1. Remove legal suffixes: Inc., LLC, Ltd., Corporation, Corp., Co., Pty Ltd, Private Ltd
2. Remove taglines/descriptors after "-", ":", or in parentheses
3. For long names (4+ words), keep the most memorable 1-2 words
4. Keep unique brand identity (don't over-simplify)
5. Think: how would employees casually call their company?

LOCATION RULES:
1. Famous cities → abbreviation: "New York" → "NYC", "San Francisco" → "SF"
2. Less known cities → "City, STATE" where STATE is 2-letter code: "Memphis, Tennessee" → "Memphis, TN"
3. International → Keep city name if famous (London, Sydney) or add country: "Melbourne, AU"
4. State/Country only → abbreviate: "United States" → "US"

EXAMPLES:
- "TeleVoIPs - Business Phone Solutions" / "Lithia, Florida" → "TeleVoIPs" / "Lithia, FL"
- "Integrated Management Resources Group, Inc." / "Lanham, Maryland" → "Integrated" / "Lanham, MD"
- "Call Team Six: Special Ops for Car Dealers" / "Dallas, Texas" → "Call Team Six" / "Dallas"
- "U.S. Employee Benefits Services Group" / "United States" → "U.S. Employee Benefits" / "US"
- "CHIKOL - Professional Turnaround..." / "San Francisco, California" → "CHIKOL" / "SF"

Return ONLY a JSON array with this exact format:
[
  {"company": "normalized name", "location": "normalized location"},
  ...
]

No explanations, no markdown, just the JSON array."""

def normalize_batch_with_llm(batch_data):
    """
    Normalize a batch of companies using OpenAI API.

    Args:
        batch_data: List of dicts with 'company_name', 'city', 'state', 'country'

    Returns:
        List of dicts with 'company' and 'location' normalized
    """
    # Prepare batch for prompt
    batch_text = []
    for item in batch_data:
        company = item.get('company_name', '')
        city = item.get('city', '')
        state = item.get('state', '')
        country = item.get('country', '')

        # Build location string
        location_parts = []
        if pd.notna(city) and str(city) != 'nan':
            location_parts.append(str(city))
        if pd.notna(state) and str(state) != 'nan':
            location_parts.append(str(state))
        elif pd.notna(country) and str(country) != 'nan':
            location_parts.append(str(country))

        location = ', '.join(location_parts) if location_parts else 'Unknown'

        batch_text.append(f'"{company}" / "{location}"')

    user_message = "Normalize these company names and locations:\n\n" + "\n".join(batch_text)

    try:
        response = openai.chat.completions.create(
            model=CONFIG["MODEL"],
            messages=[
                {"role": "system", "content": NORMALIZATION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=CONFIG["TEMPERATURE"],
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON response
        # Remove markdown code blocks if present
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        result = json.loads(result_text)

        if len(result) != len(batch_data):
            logger.warning("Batch size mismatch", expected=len(batch_data), got=len(result))

        return result

    except Exception as e:
        logger.error("LLM normalization failed", error=str(e))
        # Fallback to original data
        return [
            {"company": item.get('company_name', ''), "location": "Unknown"}
            for item in batch_data
        ]

def main():
    logger.info("Starting LLM-based normalization")

    try:
        # Read CSV
        logger.info("Reading input CSV", file=CONFIG["INPUT_FILE"])
        df = pd.read_csv(CONFIG["INPUT_FILE"])
        logger.info("CSV loaded", rows=len(df), columns=len(df.columns))

        # Process only ICP Score = 2 (perfect matches)
        perfect_matches = df[df['ICP Match Score'] == 2].copy()
        logger.info("Filtering perfect matches", count=len(perfect_matches))

        # Prepare batches
        total_batches = (len(perfect_matches) + CONFIG["BATCH_SIZE"] - 1) // CONFIG["BATCH_SIZE"]
        logger.info("Processing in batches",
                   total_companies=len(perfect_matches),
                   batch_size=CONFIG["BATCH_SIZE"],
                   total_batches=total_batches)

        # Store results
        normalized_companies = []
        normalized_locations = []

        # Process in batches
        for batch_num in range(total_batches):
            start_idx = batch_num * CONFIG["BATCH_SIZE"]
            end_idx = min(start_idx + CONFIG["BATCH_SIZE"], len(perfect_matches))

            batch_df = perfect_matches.iloc[start_idx:end_idx]

            # Prepare batch data
            batch_data = []
            for idx, row in batch_df.iterrows():
                batch_data.append({
                    'company_name': row.get('company_name', ''),
                    'city': row.get('city', ''),
                    'state': row.get('state', ''),
                    'country': row.get('country', '')
                })

            logger.info("Processing batch",
                       batch=f"{batch_num + 1}/{total_batches}",
                       companies=f"{start_idx + 1}-{end_idx}")

            # Call LLM
            results = normalize_batch_with_llm(batch_data)

            # Extract results
            for result in results:
                normalized_companies.append(result.get('company', ''))
                normalized_locations.append(result.get('location', ''))

            # Rate limiting (avoid hitting API limits)
            if batch_num < total_batches - 1:
                sleep(1)

        # Add normalized columns
        perfect_matches['Normalized Company Name (LLM)'] = normalized_companies
        perfect_matches['Normalized Location (LLM)'] = normalized_locations

        # Merge back with full dataset
        df_full = df.copy()
        df_full['Normalized Company Name (LLM)'] = ''
        df_full['Normalized Location (LLM)'] = ''

        # Update perfect matches
        for col in ['Normalized Company Name (LLM)', 'Normalized Location (LLM)']:
            df_full.loc[perfect_matches.index, col] = perfect_matches[col].values

        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = CONFIG["OUTPUT_DIR"] / f"call_centers_llm_normalized_{timestamp}.csv"

        df_full.to_csv(output_file, index=False)
        logger.info("LLM normalized CSV saved", file=str(output_file))

        # Show sample results
        logger.info("Sample normalization results (first 5):")
        for i in range(min(5, len(perfect_matches))):
            row = perfect_matches.iloc[i]
            logger.info("Normalization sample",
                       original=row.get('company_name', ''),
                       normalized=row.get('Normalized Company Name (LLM)', ''),
                       location_original=f"{row.get('city', '')}, {row.get('state', '')}",
                       location_normalized=row.get('Normalized Location (LLM)', ''))

        return output_file

    except Exception as e:
        logger.error("LLM normalization failed", error=str(e))
        raise

if __name__ == "__main__":
    output = main()
    print(f"\nLLM normalized file saved to: {output}")
