#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=== Icebreaker Generator via Claude Haiku ===
Version: 1.0.0 | Created: 2025-11-03

PURPOSE:
Generate personalized icebreaker messages for cold outreach using Claude Haiku API.

FEATURES:
- Batch processing (200 rows per batch)
- Detects companies vs. individuals
- Generates contextual, casual messages
- Progress tracking and error handling

USAGE:
1. Set ANTHROPIC_API_KEY environment variable
2. Run: python 2025-11-03-icebreaker-generator.py
3. Results saved to data/processed/

IMPROVEMENTS:
v1.0.0 - Initial version with batch processing
"""

import sys
import os
from pathlib import Path
import pandas as pd
import anthropic
import json
import time
from datetime import datetime
import io

# Fix encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

CSV_PATH = r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv"
OUTPUT_DIR = r"C:\Users\79818\Desktop\Outreach - new\data\processed"
BATCH_SIZE = 200

def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

def generate_icebreaker(client, full_name, company_name, title, headline, city):
    """Generate single icebreaker via Claude Haiku API."""

    prompt = f"""You are an outreach message generator.
Your role: create short, casual, human-sounding icebreaker messages for LinkedIn-style outreach.
Goal: make the recipient feel recognized for their work without sounding pushy or overly formal.

Your task:
- If "full_name" looks like a company (contains words such as Company, Inc, LLC, Ltd, Group, Realty, Properties, Brokers, UAE, Dubai, Abu Dhabi):
    -> Output ONLY: its a company

- Else (if "full_name" is a person):
    1. Extract firstName = first word of full_name.
    2. Normalize company_name into shortCompany:
        - If ALL CAPS -> convert to Title Case (only first letter uppercase).
        - Remove corporate suffixes: Properties, Realty, Group, Brokers, LLC, Ltd, Inc, UAE, Dubai, Abu Dhabi.
        - Remove apostrophes or special symbols.
    3. Normalize region into shortRegion:
        - Dubai, Abu Dhabi -> Dubai
        - San Francisco -> SF
        - New York City -> NYC
        - Else keep original.
    4. Generate opening = pick randomly, in casual tone:
        - love how you
        - really like how you
        - awesome to see you
        - impressed by how you
        - great track with how you
        - cool to see you
    5. specializationPhrase:
        - Look at headline or title.
        - If clear keyword (luxury, sales, marketing, engineering, talent acquisition, product, design, etc.) -> rewrite naturally as an action (2-3 words).
            * Example: "Luxury Consultant" -> "drive luxury sales"
            * "Marketing Manager" -> "lead marketing"
            * "Talent Acquisition" -> "grow teams"
            * "Software Engineer" -> "build products"
        - If generic title -> simplify to meaningful action:
            * "Consultant" -> "work with clients"
            * "Broker" -> "push sales"
            * "Analyst" -> "dig into insights"
        - If nothing useful -> fallback: "bring industry experience".
    6. regionPhrase = pick randomly:
        - I'm also in the {{shortRegion}} market
        - I work across {{shortRegion}} as well
        - I'm active in {{shortRegion}} too
        - I also focus on {{shortRegion}}
    7. closingPhrase = pick randomly:
        - Wanted to run something by you.
        - Thought I'd share an idea with you.
        - Had something you might find interesting.
        - Figured I'd reach out quickly.

Final Output (always one line, no labels, no JSON):
Hey {{firstName}}, {{opening}} {{specializationPhrase}} at {{shortCompany}} - {{regionPhrase}}. {{closingPhrase}}

Context for this row:
full_name: {full_name}
company_name: {company_name}
title: {title}
headline: {headline}
city: {city}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.content[0].text.strip()

def process_batch(client, batch_df, batch_num, total_batches):
    """Process single batch of rows."""

    print(f"\n[BATCH {batch_num}/{total_batches}] Processing {len(batch_df)} rows...")
    batch_start = time.time()

    icebreakers = []
    stats = {
        'successful': 0,
        'companies': 0,
        'errors': 0
    }

    for idx, row in batch_df.iterrows():
        try:
            full_name = str(row.get('full_name', '')).strip()
            company_name = str(row.get('company_name', '')).strip()
            title = str(row.get('title', '')).strip()
            headline = str(row.get('headline', '')).strip()
            city = str(row.get('city', '')).strip()

            if not full_name or full_name == 'nan':
                icebreakers.append("ERROR: Missing full_name")
                stats['errors'] += 1
                continue

            result = generate_icebreaker(client, full_name, company_name, title, headline, city)

            if "its a company" in result.lower():
                stats['companies'] += 1

            icebreakers.append(result)
            stats['successful'] += 1

            # Progress every 20 rows
            local_idx = idx - batch_df.index[0] + 1
            if local_idx % 20 == 0:
                print(f"  -> {local_idx}/{len(batch_df)} rows processed")

        except Exception as e:
            error_msg = f"ERROR: {str(e)[:40]}"
            icebreakers.append(error_msg)
            stats['errors'] += 1
            print(f"  ⚠ Error at row {idx}: {error_msg}")

    batch_df = batch_df.copy()
    batch_df['icebreaker'] = icebreakers

    batch_time = time.time() - batch_start
    print(f"  ✓ Batch completed in {batch_time:.1f}s")
    print(f"  -> Success: {stats['successful']}, Companies: {stats['companies']}, Errors: {stats['errors']}")

    return batch_df, stats, batch_time

def main():
    """Main process."""

    print("=" * 60)
    print("ICEBREAKER GENERATOR - Claude Haiku API")
    print("=" * 60)

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Load CSV
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"\nLoaded CSV: {CSV_PATH}")
        print(f"Total rows: {len(df)}")
    except Exception as e:
        print(f"ERROR: Failed to load CSV: {e}")
        sys.exit(1)

    # Ensure output directory
    ensure_output_dir()

    # Initialize client
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✓ Anthropic client initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize Anthropic client: {e}")
        sys.exit(1)

    # Calculate batches
    total_batches = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\nBatch configuration:")
    print(f"  Batch size: {BATCH_SIZE} rows")
    print(f"  Total batches: {total_batches}")

    # Process batches
    all_results = []
    total_stats = {
        'total_processed': 0,
        'total_successful': 0,
        'total_companies': 0,
        'total_errors': 0,
        'batch_times': []
    }

    start_time = time.time()

    for batch_num in range(1, total_batches + 1):
        batch_start_idx = (batch_num - 1) * BATCH_SIZE
        batch_end_idx = min(batch_num * BATCH_SIZE, len(df))

        batch_df = df.iloc[batch_start_idx:batch_end_idx].copy()

        result_df, stats, batch_time = process_batch(client, batch_df, batch_num, total_batches)

        # Save batch
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_output = os.path.join(OUTPUT_DIR, f"apollo_batch_{batch_num}_{timestamp}.csv")
        result_df.to_csv(batch_output, index=False, encoding='utf-8')
        print(f"  -> Saved: {batch_output}")

        # Update totals
        all_results.append(result_df)
        total_stats['total_processed'] += stats['successful'] + stats['errors']
        total_stats['total_successful'] += stats['successful']
        total_stats['total_companies'] += stats['companies']
        total_stats['total_errors'] += stats['errors']
        total_stats['batch_times'].append(batch_time)

    # Merge all batches
    print("\nMerging all batches...")
    final_df = pd.concat(all_results, ignore_index=True)

    # Save final result
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_output = os.path.join(OUTPUT_DIR, f"apollo_icebreaker_analyzed_{timestamp}.csv")
    final_df.to_csv(final_output, index=False, encoding='utf-8')

    # Generate report
    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nFinal Results:")
    print(f"  Total rows processed: {total_stats['total_processed']}")
    print(f"  Successful: {total_stats['total_successful']}")
    print(f"  Companies detected: {total_stats['total_companies']}")
    print(f"  Errors: {total_stats['total_errors']}")
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"  Avg time per row: {(total_time/total_stats['total_processed'])*1000:.0f}ms")

    print(f"\nOutput file: {final_output}")

    # Show sample icebreakers
    print("\n" + "=" * 60)
    print("SAMPLE ICEBREAKERS (first 10)")
    print("=" * 60)

    sample_count = 0
    for idx, row in final_df.iterrows():
        if "ERROR" not in str(row['icebreaker']) and "its a company" not in str(row['icebreaker']).lower():
            print(f"\n[{sample_count+1}] {row['full_name']} @ {row['company_name']}")
            print(f"    {row['icebreaker']}")
            sample_count += 1
            if sample_count >= 10:
                break

    print("\n" + "=" * 60)

if __name__ == "__main__":
    # Log to file as well as stdout
    log_file = os.path.join(OUTPUT_DIR, "generator_log.txt")

    # Create a simple logging wrapper
    class Logger:
        def __init__(self, filepath):
            self.filepath = filepath
            self.file = open(filepath, 'w', encoding='utf-8')

        def log(self, msg):
            print(msg)
            self.file.write(msg + '\n')
            self.file.flush()

        def close(self):
            self.file.close()

    logger = Logger(log_file)

    try:
        logger.log("ICEBREAKER GENERATOR STARTING...")
        main()
        logger.log("ICEBREAKER GENERATOR COMPLETED!")
    except Exception as e:
        logger.log(f"FATAL ERROR: {e}")
        import traceback
        logger.log(traceback.format_exc())
    finally:
        logger.close()
