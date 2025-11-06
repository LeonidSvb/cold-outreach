#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Icebreaker Generator - Simple Standalone Version"""

import pandas as pd
import anthropic
import os
import time
from datetime import datetime

# Paths
CSV_PATH = r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv"
OUTPUT_DIR = r"C:\Users\79818\Desktop\Outreach - new\data\processed"
LOG_FILE = os.path.join(OUTPUT_DIR, "icebreaker_generator.log")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Simple file logging
log_file = open(LOG_FILE, 'w', encoding='utf-8')

def log_msg(msg):
    log_file.write(msg + '\n')
    log_file.flush()

# Load CSV
log_msg("="*60)
log_msg("ICEBREAKER GENERATOR STARTED")
log_msg("="*60)

try:
    log_msg("[1/5] Loading CSV...")
    df = pd.read_csv(CSV_PATH)
    log_msg(f"SUCCESS: {len(df)} rows loaded")
except Exception as e:
    log_msg(f"FAILED: {e}")
    log_file.close()
    exit(1)

# Initialize API
try:
    log_msg("[2/5] Initializing API...")
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")
    client = anthropic.Anthropic(api_key=api_key)
    log_msg("SUCCESS: API initialized")
except Exception as e:
    log_msg(f"FAILED: {e}")
    log_file.close()
    exit(1)

# Generate icebreaker function
def generate_icebreaker(full_name, company_name, title, headline, city):
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

# Process data
log_msg("[3/5] Processing rows...")
total_rows = len(df)
batch_size = 200
total_batches = (total_rows + batch_size - 1) // batch_size

all_icebreakers = []
stats_successful = 0
stats_companies = 0
stats_errors = 0

start_time = time.time()

for batch_num in range(1, total_batches + 1):
    batch_start_idx = (batch_num - 1) * batch_size
    batch_end_idx = min(batch_num * batch_size, total_rows)

    log_msg(f"\n[BATCH {batch_num}/{total_batches}] Processing rows {batch_start_idx+1}-{batch_end_idx}...")
    batch_start_time = time.time()

    batch_icebreakers = []

    for idx in range(batch_start_idx, batch_end_idx):
        try:
            row = df.iloc[idx]
            full_name = str(row.get('full_name', '')).strip()
            company_name = str(row.get('company_name', '')).strip()
            title = str(row.get('title', '')).strip()
            headline = str(row.get('headline', '')).strip()
            city = str(row.get('city', '')).strip()

            if not full_name or full_name == 'nan':
                batch_icebreakers.append("ERROR: Missing full_name")
                stats_errors += 1
                continue

            result = generate_icebreaker(full_name, company_name, title, headline, city)

            if "its a company" in result.lower():
                stats_companies += 1
            else:
                stats_successful += 1

            batch_icebreakers.append(result)

            if (idx - batch_start_idx + 1) % 20 == 0:
                log_msg(f"  -> {idx - batch_start_idx + 1}/{batch_end_idx - batch_start_idx} rows")

        except Exception as e:
            batch_icebreakers.append(f"ERROR: {str(e)[:40]}")
            stats_errors += 1

    all_icebreakers.extend(batch_icebreakers)
    batch_time = time.time() - batch_start_time
    log_msg(f"  BATCH DONE in {batch_time:.1f}s")

# Add icebreakers to dataframe
df['icebreaker'] = all_icebreakers

# Save results
log_msg("\n[4/5] Saving results...")
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = os.path.join(OUTPUT_DIR, f"apollo_icebreaker_analyzed_{timestamp}.csv")

try:
    df.to_csv(output_file, index=False, encoding='utf-8')
    log_msg(f"SUCCESS: Saved to {output_file}")
except Exception as e:
    log_msg(f"FAILED: {e}")
    log_file.close()
    exit(1)

# Final statistics
total_time = time.time() - start_time

log_msg("\n[5/5] Final statistics")
log_msg("="*60)
log_msg(f"Total rows: {total_rows}")
log_msg(f"Successful: {stats_successful}")
log_msg(f"Companies detected: {stats_companies}")
log_msg(f"Errors: {stats_errors}")
log_msg(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
log_msg(f"Output: {output_file}")
log_msg("="*60)

# Sample icebreakers
log_msg("\nSAMPLE ICEBREAKERS (first 10):")
log_msg("="*60)
sample_count = 0
for idx, row in df.iterrows():
    icebreaker = row['icebreaker']
    if 'ERROR' not in str(icebreaker) and 'its a company' not in str(icebreaker).lower():
        sample_count += 1
        log_msg(f"\n[{sample_count}] {row['full_name']} @ {row['company_name']}")
        log_msg(f"    {icebreaker}")
        if sample_count >= 10:
            break

log_msg("\n" + "="*60)
log_msg("GENERATION COMPLETE")
log_msg("="*60)

log_file.close()

# Print to console
print(f"Log saved to: {LOG_FILE}")
print("Check the log file for results")
