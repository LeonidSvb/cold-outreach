#!/usr/bin/env python3
"""
=== WEBSITE CONTENT PARSER (OpenAI) ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Parse website homepage content and extract 15 universal business variables using OpenAI

FEATURES:
- Parallel processing: 50 concurrent OpenAI requests
- Auto-detect content column (homepage_content, website_content, etc.)
- Extract 15 universal variables from website text
- Creative insights column for unique opportunities
- Real-time progress tracking and cost estimation

USAGE:
1. Configure INPUT_FILE path below
2. Run: python website_content_parser.py
3. Results saved to results/

EXTRACTED VARIABLES (15):
1. owner_first_name
2. tagline
3. value_proposition
4. guarantees
5. certifications
6. awards_badges
7. special_offers
8. is_hiring
9. hiring_roles
10. is_family_owned
11. emergency_24_7
12. free_estimate
13. license_number
14. testimonial_snippet
15. corporate_clients

PLUS:
16. creative_insights - AI-generated unique opportunities
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
from dotenv import load_dotenv

print("="*70)
print("WEBSITE CONTENT PARSER (OpenAI)")
print("="*70)

# Load environment
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
MAX_WORKERS = 50
RESULTS_DIR = Path(__file__).parent.parent / "results"

# Input file (change to full file when ready)
INPUT_FILE = r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\test_sample_10.csv"
# INPUT_FILE = r"C:\Users\79818\Downloads\success_emails (1).csv"  # Full file (982 rows)

print(f"\nInput file: {Path(INPUT_FILE).name}")
print(f"Model: {OPENAI_MODEL}")
print(f"Parallel workers: {MAX_WORKERS}")


def detect_content_column(df: pd.DataFrame) -> str:
    """Auto-detect column with most text content"""
    candidates = ['homepage_content', 'website_content', 'content', 'page_content', 'text']

    # Check for exact matches
    for col in candidates:
        if col in df.columns:
            return col

    # Find column with longest average text
    text_cols = df.select_dtypes(include=['object']).columns
    max_len = 0
    max_col = None

    for col in text_cols:
        avg_len = df[col].astype(str).str.len().mean()
        if avg_len > max_len:
            max_len = avg_len
            max_col = col

    return max_col


def parse_website_content(content: str, company_name: str) -> dict:
    """Parse website content and extract 15 variables using OpenAI"""
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are an expert data extractor. Analyze this website content and extract business information.

COMPANY: {company_name}

WEBSITE CONTENT:
{content[:8000]}

Extract the following 15 variables (return "N/A" if not found):

1. owner_first_name - First name of owner/founder (e.g., "Ryan", "Joe")
2. tagline - Main tagline or slogan (e.g., "Your Neighbors, Your Electricians")
3. value_proposition - Core value prop (e.g., "Fast, reliable service")
4. guarantees - Any guarantees (e.g., "100% Satisfaction Guarantee")
5. certifications - Certifications/credentials (e.g., "Tesla Certified, Generac Dealer")
6. awards_badges - Awards or badges (e.g., "Best of Florida 2025")
7. special_offers - Special offers/promotions (e.g., "Free Quote", "$50 off")
8. is_hiring - Are they hiring? (yes/no)
9. hiring_roles - What roles? (e.g., "Lead Electrician, Helper")
10. is_family_owned - Family-owned? (yes/no)
11. emergency_24_7 - 24/7 emergency service? (yes/no)
12. free_estimate - Free estimate offered? (yes/no)
13. license_number - License number if mentioned (e.g., "EC13008327")
14. testimonial_snippet - One short customer quote (max 100 chars)
15. corporate_clients - Any big clients mentioned (e.g., "Amazon, Lyft")

PLUS CREATIVE INSIGHTS:
16. creative_insights - What unique angles, growth signals, or interesting details could be used for personalization that DON'T fit into the above categories? (2-3 bullet points, max 200 chars total)

Return ONLY valid JSON format:
{{
  "owner_first_name": "...",
  "tagline": "...",
  "value_proposition": "...",
  "guarantees": "...",
  "certifications": "...",
  "awards_badges": "...",
  "special_offers": "...",
  "is_hiring": "...",
  "hiring_roles": "...",
  "is_family_owned": "...",
  "emergency_24_7": "...",
  "free_estimate": "...",
  "license_number": "...",
  "testimonial_snippet": "...",
  "corporate_clients": "...",
  "creative_insights": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        result = response.choices[0].message.content.strip()

        # Parse JSON
        import json
        parsed = json.loads(result)

        return parsed

    except Exception as e:
        print(f"  Error parsing content: {e}")
        return {
            "owner_first_name": "ERROR",
            "tagline": "ERROR",
            "value_proposition": "ERROR",
            "guarantees": "ERROR",
            "certifications": "ERROR",
            "awards_badges": "ERROR",
            "special_offers": "ERROR",
            "is_hiring": "ERROR",
            "hiring_roles": "ERROR",
            "is_family_owned": "ERROR",
            "emergency_24_7": "ERROR",
            "free_estimate": "ERROR",
            "license_number": "ERROR",
            "testimonial_snippet": "ERROR",
            "corporate_clients": "ERROR",
            "creative_insights": f"ERROR: {str(e)}"
        }


def process_row(idx, row_data, content_col):
    """Process single row - wrapper for parallel execution"""
    content = row_data[content_col]
    company_name = row_data.get('name', row_data.get('company_name', 'Unknown'))

    # Skip if no content
    if pd.isna(content) or str(content).strip() == '':
        return {
            'idx': idx,
            'data': {k: "N/A" for k in [
                "owner_first_name", "tagline", "value_proposition", "guarantees",
                "certifications", "awards_badges", "special_offers", "is_hiring",
                "hiring_roles", "is_family_owned", "emergency_24_7", "free_estimate",
                "license_number", "testimonial_snippet", "corporate_clients", "creative_insights"
            ]},
            'status': 'skipped'
        }

    parsed_data = parse_website_content(str(content), company_name)

    return {
        'idx': idx,
        'data': parsed_data,
        'status': 'success'
    }


# Read CSV
df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
print(f"\nTotal rows: {len(df)}")

# Auto-detect content column
content_col = detect_content_column(df)
print(f"Content column detected: {content_col}")

# Check if content exists
if content_col not in df.columns:
    print("ERROR: No content column found!")
    sys.exit(1)

# Count rows with content
rows_with_content = df[df[content_col].notna() & (df[content_col] != '')].shape[0]
print(f"Rows with content: {rows_with_content}")

print("\n" + "="*70)
print("STARTING CONTENT PARSING")
print(f"Estimated time: ~{rows_with_content / MAX_WORKERS / 2:.1f} minutes")
print(f"Estimated cost: ~${rows_with_content * 0.002:.2f} USD")
print("="*70 + "\n")

# Initialize result columns
for col in ["owner_first_name", "tagline", "value_proposition", "guarantees",
            "certifications", "awards_badges", "special_offers", "is_hiring",
            "hiring_roles", "is_family_owned", "emergency_24_7", "free_estimate",
            "license_number", "testimonial_snippet", "corporate_clients", "creative_insights"]:
    df[col] = ""

# Parallel processing
start_time = datetime.now()
completed_count = 0
lock = threading.Lock()

# Prepare tasks
tasks = []
for idx in df.index:
    row_data = df.loc[idx].to_dict()
    tasks.append((idx, row_data, content_col))

print(f"Processing {len(tasks)} rows with {MAX_WORKERS} parallel workers...\n")

# Execute in parallel
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(process_row, idx, row_data, content_col): idx
               for idx, row_data, content_col in tasks}

    for future in as_completed(futures):
        result = future.result()

        # Update dataframe
        for key, value in result['data'].items():
            df.at[result['idx'], key] = value

        # Progress tracking
        with lock:
            completed_count += 1

            if completed_count % 50 == 0 or completed_count == len(tasks):
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = completed_count / elapsed if elapsed > 0 else 0
                remaining = (len(tasks) - completed_count) / rate if rate > 0 else 0
                progress_pct = (completed_count / len(tasks)) * 100

                print(f"[{completed_count}/{len(tasks)}] {progress_pct:.1f}% | "
                      f"Rate: {rate:.1f}/s | ETA: {remaining/60:.1f} min")

# Save results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = RESULTS_DIR / f"parsed_website_content_{timestamp}.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')

duration = (datetime.now() - start_time).total_seconds()
success_count = len(df[df['owner_first_name'] != 'ERROR'])
error_count = len(df[df['owner_first_name'] == 'ERROR'])

print("\n" + "="*70)
print("PARSING COMPLETE")
print("="*70)
print(f"Total processed: {completed_count}")
print(f"Success: {success_count}")
print(f"Errors: {error_count}")
print(f"\nDuration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
print(f"Average rate: {completed_count/duration:.2f} rows/sec")
print(f"Estimated cost: ${completed_count * 0.002:.2f} USD")
print(f"\nSaved to: {output_file.name}")
print("="*70)
