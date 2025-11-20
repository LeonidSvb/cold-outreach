#!/usr/bin/env python3
"""
=== COMPANY NAME NORMALIZATION WITH OPENAI ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Normalize company names to casual outreach-friendly format using OpenAI.
Remove legal entities, INN, ABN, fix truncations, apply proper title case.

FEATURES:
- GPT-4o-mini for cost-effective normalization
- Batch processing with rate limiting
- Remove: Pty Ltd, Limited, INN, ABN, ACN, articles
- Fix truncated names and typos
- Title case (first letter capital, rest lowercase for common words)
- Parallel processing (15 workers)

USAGE:
1. Configure OPENAI_API_KEY in .env
2. Run: python normalize_company_names.py
3. Results: Original CSV updated with 'Company_Casual' column

COST ESTIMATE:
- 543 companies x $0.0001 = ~$0.05 (very cheap)
- Processing time: ~2-3 minutes
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
from typing import Optional
import time
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Configuration
INPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")
MODEL = "gpt-4o-mini"
MAX_TOKENS = 50
TEMPERATURE = 0.3
PARALLEL_WORKERS = 15

# OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Thread-safe counters
lock = threading.Lock()
stats = {
    'processed': 0,
    'success': 0,
    'failed': 0,
    'total_cost': 0.0
}

NORMALIZATION_PROMPT = """Convert this company name to a casual, outreach-friendly format:

INPUT: "{company_name}"

RULES:
1. Remove: Pty Ltd, Limited, Inc, Corp, LLC, INN, ABN, ACN, & Assoc, & Co
2. Remove articles: The, A, An (if at start)
3. Fix truncations (e.g., "B &" -> "B&B", "urt" -> "Court")
4. Fix obvious typos
5. Title case: First letter of each word capital, rest lowercase
6. Keep numbers as-is (e.g., "188 Apartments")
7. Maximum 4-5 words, drop unnecessary parts
8. Natural and readable for cold outreach

OUTPUT ONLY the normalized name, nothing else. No quotes, no explanation.

EXAMPLES:
"Aarons CENTRAL TOURIST PARK Pty Ltd" -> "Aarons Central Tourist Park"
"Aarn House B &" -> "Aarn House B&B"
"Adelaide Accommodation - The" -> "Adelaide Accommodation"
"Albury Garden urt Motel" -> "Albury Garden Court Motel"
"188 Apartments" -> "188 Apartments"
"ACCOMMODATION CHOICES INN 123456789" -> "Accommodation Choices"

Now normalize: "{company_name}"
"""


def normalize_company_name(company_name: str) -> Optional[str]:
    """
    Normalize company name using OpenAI

    Args:
        company_name: Original company name

    Returns:
        Normalized casual name or None if failed
    """
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

        normalized = response.choices[0].message.content.strip()

        # Remove quotes if OpenAI added them
        normalized = normalized.strip('"\'')

        # Calculate cost (GPT-4o-mini: $0.150 / 1M input, $0.600 / 1M output)
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


def process_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process all companies in parallel

    Args:
        df: DataFrame with 'Company' column

    Returns:
        DataFrame with 'Company_Casual' column added
    """
    logger.info(f"Processing {len(df)} companies with {PARALLEL_WORKERS} workers...")

    results = {}

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(normalize_company_name, row['Company']): idx
            for idx, row in df.iterrows()
        }

        # Collect results
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            original_name = df.loc[idx, 'Company']

            try:
                normalized = future.result()
                results[idx] = normalized if normalized else original_name

                with lock:
                    stats['processed'] += 1
                    if stats['processed'] % 50 == 0:
                        logger.info(f"Progress: {stats['processed']}/{len(df)} | "
                                  f"Success: {stats['success']} | "
                                  f"Failed: {stats['failed']} | "
                                  f"Cost: ${stats['total_cost']:.4f}")

            except Exception as e:
                logger.error(f"Error processing {original_name}: {e}")
                results[idx] = original_name

    # Add normalized names to DataFrame
    df['Company_Casual'] = df.index.map(results)

    return df


def main():
    """Main execution"""

    logger.info("="*70)
    logger.info("COMPANY NAME NORMALIZATION WITH OPENAI")
    logger.info("="*70)

    # Load data
    logger.info(f"Loading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')

    logger.info(f"Total companies: {len(df)}")

    # Check if already has Company_Casual column
    if 'Company_Casual' in df.columns:
        logger.warning("'Company_Casual' column already exists. Overwriting...")
        df = df.drop(columns=['Company_Casual'])

    # Process
    start_time = time.time()
    df = process_batch(df)
    elapsed = time.time() - start_time

    # Save
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # Final stats
    logger.info("="*70)
    logger.info("NORMALIZATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Total processed: {stats['processed']}")
    logger.info(f"Success: {stats['success']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total cost: ${stats['total_cost']:.4f}")
    logger.info(f"Processing time: {elapsed/60:.1f} minutes")
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info("="*70)

    # Show sample
    logger.info("\nSAMPLE RESULTS:")
    logger.info("-"*70)
    sample = df[['Company', 'Company_Casual']].head(10)
    for _, row in sample.iterrows():
        logger.info(f"  {row['Company']:<40} -> {row['Company_Casual']}")
    logger.info("-"*70)


if __name__ == "__main__":
    main()
