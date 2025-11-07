#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Icebreaker Generator - Standalone Script"""

import pandas as pd
import anthropic
import os
import time
from datetime import datetime
import sys

# Redirect output to file to avoid encoding issues on Windows
LOG_FILE = r"C:\Users\79818\Desktop\Outreach - new\data\processed\generator.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

class Logger:
    def __init__(self, filepath):
        self.file = open(filepath, 'w', encoding='utf-8')

    def log(self, msg):
        print(msg, file=self.file)
        self.file.flush()

    def close(self):
        self.file.close()

logger = Logger(LOG_FILE)

def log_print(*args, **kwargs):
    msg = ' '.join(str(a) for a in args)
    logger.log(msg)

# Configuration
CSV_PATH = r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv"
OUTPUT_DIR = r"C:\Users\79818\Desktop\Outreach - new\data\processed"
BATCH_SIZE = 200

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load CSV
log_print("Loading CSV...")
df = pd.read_csv(CSV_PATH)
total_rows = len(df)
total_batches = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE

log_print(f"Loaded: {total_rows} rows")
log_print(f"Batches: {total_batches} (size={BATCH_SIZE})")

# Initialize API
api_key = os.environ.get('ANTHROPIC_API_KEY')
client = anthropic.Anthropic(api_key=api_key)

def generate_icebreaker(full_name, company_name, title, headline, city):
    """Generate icebreaker via Claude Haiku."""

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
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()

# Process batches
all_results = []
overall_stats = {'successful': 0, 'companies': 0, 'errors': 0}
start_time = time.time()

for batch_num in range(1, total_batches + 1):
    batch_start_idx = (batch_num - 1) * BATCH_SIZE
    batch_end_idx = min(batch_num * BATCH_SIZE, total_rows)

    batch_df = df.iloc[batch_start_idx:batch_end_idx].copy()

    print(f"\n[BATCH {batch_num}/{total_batches}] Rows {batch_start_idx+1}-{batch_end_idx}...")
    batch_start_time = time.time()

    icebreakers = []
    stats = {'successful': 0, 'companies': 0, 'errors': 0}

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

            result = generate_icebreaker(full_name, company_name, title, headline, city)

            if "its a company" in result.lower():
                stats['companies'] += 1

            icebreakers.append(result)
            stats['successful'] += 1

            # Progress every 20 rows
            local_idx = idx - batch_df.index[0] + 1
            if local_idx % 20 == 0:
                print(f"  -> {local_idx}/{len(batch_df)} rows")

        except Exception as e:
            error_msg = f"ERROR: {str(e)[:40]}"
            icebreakers.append(error_msg)
            stats['errors'] += 1

    batch_df['icebreaker'] = icebreakers
    batch_time = time.time() - batch_start_time

    print(f"  Completed: {batch_time:.1f}s | Success: {stats['successful']}, Companies: {stats['companies']}, Errors: {stats['errors']}")

    # Save batch
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    batch_output = os.path.join(OUTPUT_DIR, f"apollo_batch_{batch_num}_{timestamp}.csv")
    batch_df.to_csv(batch_output, index=False, encoding='utf-8')

    all_results.append(batch_df)
    overall_stats['successful'] += stats['successful']
    overall_stats['companies'] += stats['companies']
    overall_stats['errors'] += stats['errors']

# Merge all batches
final_df = pd.concat(all_results, ignore_index=True)

# Save final result
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
final_output = os.path.join(OUTPUT_DIR, f"apollo_icebreaker_analyzed_{timestamp}.csv")
final_df.to_csv(final_output, index=False, encoding='utf-8')

total_time = time.time() - start_time

# Results
print("\n" + "="*60)
print("PROCESSING COMPLETE")
print("="*60)
print(f"Total rows: {total_rows}")
print(f"Successful: {overall_stats['successful']}")
print(f"Companies: {overall_stats['companies']}")
print(f"Errors: {overall_stats['errors']}")
print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
print(f"Avg per row: {(total_time/total_rows)*1000:.0f}ms")
print(f"\nOutput: {final_output}")

# Show samples
print("\n" + "="*60)
print("SAMPLE ICEBREAKERS (first 10)")
print("="*60 + "\n")

sample_count = 0
for idx, row in final_df.iterrows():
    icebreaker = row['icebreaker']

    if 'ERROR' in str(icebreaker) or 'its a company' in str(icebreaker).lower():
        continue

    sample_count += 1
    print(f"[{sample_count}] {row['full_name']} @ {row['company_name']}")
    print(f"    {icebreaker}\n")

    if sample_count >= 10:
        break

print("="*60)
