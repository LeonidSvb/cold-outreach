#!/usr/bin/env python3
"""
Quick test of LLM normalization on 20 companies
"""

import sys
import os
import pandas as pd
import json
from pathlib import Path
from dotenv import load_dotenv
import openai

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

NORMALIZATION_PROMPT = """You are a data normalization expert. Normalize company names and locations for casual cold outreach.

COMPANY NAME RULES:
1. Remove: Inc., LLC, Ltd., Corp., Pty Ltd, Private Ltd
2. Remove taglines after "-", ":", parentheses
3. Long names (4+ words) → keep 1-2 memorable words
4. Think: how would employees call their company casually?

LOCATION RULES:
1. Famous cities → abbreviation: "New York" → "NYC", "San Francisco" → "SF"
2. Less known → "City, ST": "Memphis, Tennessee" → "Memphis, TN"
3. International → famous city alone or "City, COUNTRY"

Return ONLY JSON array:
[{"company": "normalized", "location": "normalized"}, ...]"""

def normalize_batch(batch_data):
    batch_text = []
    for item in batch_data:
        company = item['company_name']
        city = str(item.get('city', ''))
        state = str(item.get('state', ''))

        location = f"{city}, {state}" if city != 'nan' and state != 'nan' else (city if city != 'nan' else state)
        batch_text.append(f'"{company}" / "{location}"')

    user_message = "Normalize:\n\n" + "\n".join(batch_text)

    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": NORMALIZATION_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        result_text = response.choices[0].message.content.strip()
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]

        return json.loads(result_text)

    except Exception as e:
        logger.error("LLM failed", error=str(e))
        return [{"company": item['company_name'], "location": "Unknown"} for item in batch_data]

def main():
    logger.info("Testing LLM normalization on 20 companies")

    df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_processed_20251103_143944.csv')
    perfect = df[df['ICP Match Score'] == 2].head(20)

    batch_data = []
    for idx, row in perfect.iterrows():
        batch_data.append({
            'company_name': row['company_name'],
            'city': row.get('city', ''),
            'state': row.get('state', '')
        })

    logger.info("Calling OpenAI API...")
    results = normalize_batch(batch_data)

    print("\n" + "="*100)
    print("LLM NORMALIZATION RESULTS (Sample 20)")
    print("="*100)

    for i, (original, result) in enumerate(zip(batch_data, results), 1):
        orig_company = original['company_name']
        orig_city = str(original.get('city', ''))
        orig_state = str(original.get('state', ''))
        orig_loc = f"{orig_city}, {orig_state}" if orig_city != 'nan' and orig_state != 'nan' else (orig_city if orig_city != 'nan' else orig_state)

        norm_company = result.get('company', '')
        norm_location = result.get('location', '')

        print(f"\n{i}. ORIGINAL:")
        print(f"   Company: {orig_company}")
        print(f"   Location: {orig_loc}")
        print(f"   NORMALIZED:")
        print(f"   Company: {norm_company}")
        print(f"   Location: {norm_location}")

    logger.info("Test completed successfully!")

if __name__ == "__main__":
    main()
