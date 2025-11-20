#!/usr/bin/env python3
"""
=== ADD CASUAL COMPANY NAMES ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Add Company_Casual column to existing CSV using OpenAI normalization.
Only processes unique company names to save cost.
"""

import sys
import os
from pathlib import Path
import pandas as pd
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

INPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")
MODEL = "gpt-4o-mini"
MAX_TOKENS = 50
TEMPERATURE = 0.3
PARALLEL_WORKERS = 15

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

lock = threading.Lock()
stats = {'processed': 0, 'success': 0, 'failed': 0, 'total_cost': 0.0}

NORMALIZATION_PROMPT = """Convert this company name to a very short, casual format for cold outreach:

INPUT: "{company_name}"

RULES:
1. Remove ALL: Pty Ltd, Limited, Inc, Motel, Motor Inn, Hotel, Resort, Apartments, Lodge, B&B, Accommodation, Guest House, Caravan Park
2. Remove: The, A, An (at start)
3. Keep ONLY: Main brand name (2-3 words maximum)
4. Title case BUT keep small words lowercase: "garden" not "Garden", "vista" not "Vista"
5. First word capitalized, rest lowercase unless proper noun
6. Very short and casual

EXAMPLES:
"Albury Garden Court Motel" -> "Albury garden"
"Bella Vista North Haven Resort" -> "Bella vista"
"Ballina Byron Islander Resort" -> "Ballina islander"
"Blazing Stump Hotel Bar" -> "Blazing stump"
"Adelaide Accommodation Services" -> "Adelaide services"
"188 Apartments" -> "188"

OUTPUT ONLY the normalized name, nothing else. No quotes.

Now normalize: "{company_name}"
"""


def normalize_company_name(company_name: str) -> Optional[str]:
    try:
        prompt = NORMALIZATION_PROMPT.format(company_name=company_name)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a company name normalizer. Output ONLY the normalized name, nothing else."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        normalized = response.choices[0].message.content.strip().strip('"\'')

        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

        with lock:
            stats['success'] += 1
            stats['total_cost'] += cost

        return normalized
    except Exception as e:
        logger.error(f"Failed to normalize '{company_name}': {e}")
        with lock:
            stats['failed'] += 1
        return None


def main():
    logger.info("="*70)
    logger.info("ADD CASUAL COMPANY NAMES")
    logger.info("="*70)

    # Load data
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    logger.info(f"Total rows: {len(df)}")

    # Get unique company names
    unique_companies = df['Company'].unique()
    logger.info(f"Unique companies: {len(unique_companies)}")

    # Normalize unique names
    logger.info(f"\nNormalizing {len(unique_companies)} unique names with {PARALLEL_WORKERS} workers...")

    name_mapping = {}

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        future_to_name = {
            executor.submit(normalize_company_name, name): name
            for name in unique_companies
        }

        for future in as_completed(future_to_name):
            original = future_to_name[future]
            try:
                normalized = future.result()
                name_mapping[original] = normalized if normalized else original

                with lock:
                    stats['processed'] += 1
                    if stats['processed'] % 50 == 0:
                        logger.info(f"Progress: {stats['processed']}/{len(unique_companies)} | Cost: ${stats['total_cost']:.4f}")
            except Exception as e:
                logger.error(f"Error: {e}")
                name_mapping[original] = original

    # Apply mapping
    df['Company_Casual'] = df['Company'].map(name_mapping)

    # Save
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    logger.info("="*70)
    logger.info("COMPLETE")
    logger.info("="*70)
    logger.info(f"Total processed: {stats['processed']}")
    logger.info(f"Success: {stats['success']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total cost: ${stats['total_cost']:.4f}")
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
