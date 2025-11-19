#!/usr/bin/env python3
"""
STEP 3: Generate icebreakers for deliverable emails (PARALLEL VERSION)
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import glob
import os
from openai import OpenAI
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

print("="*70)
print("STEP 3: GENERATE ICEBREAKERS (PARALLEL)")
print("="*70)

# Load environment
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
MAX_WORKERS = 50  # Parallel threads

# Find latest verified file
RESULTS_DIR = Path(__file__).parent.parent / "results"
verified_files = sorted(glob.glob(str(RESULTS_DIR / "us_1900_VERIFIED_*.csv")))
if not verified_files:
    print("ERROR: No verified file found! Run step2 first.")
    sys.exit(1)

INPUT_FILE = Path(verified_files[-1])

print(f"\nInput file: {INPUT_FILE.name}")
print(f"Parallel workers: {MAX_WORKERS}")


def generate_icebreaker(business_data: dict) -> str:
    """Generate personalized icebreaker using OpenAI"""
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Extract data with fallbacks
    company_name = business_data.get('name', 'your business')
    city = business_data.get('city', '')
    state = business_data.get('state', '')
    category = business_data.get('niche', '')
    rating = business_data.get('rating', '')
    review_count = business_data.get('reviews', 0)
    business_type = business_data.get('business_summary', '')
    owner_name = ''  # Not in dataset

    # User's prompt
    prompt = f"""Act as an expert in cold email personalization who writes icebreakers that sound 100% natural, casual, and human - as if a real person was just chatting about the business with a friend.
The personality is "My Fun" - relaxed, witty, friendly, but never fake or robotic.

Write 1-2 short, easy-to-read sentences (max 35 words).
No corporate tone, no generic compliments, no fake enthusiasm like "I was impressed" or "amazing work."
Keep lowercase for company names unless the full name needs capitalization.
If the company name is long or clunky, shorten it - write it how you'd naturally say it to a friend.

If the business has:
- over 4.5 stars and more than 50 reviews, you can casually mention it (e.g. "holding 4.8 stars with tons of locals backing you up - that's rare.")
- few or no reviews, skip that completely.

Focus your personalization on:
- their location (city/state)
- their actual work (services)
- their tone, slogan, or vibe
- values like affordable pricing, experience, or quality focus
- a quick local insight or relatable comment

Avoid listing services mechanically - blend them into natural phrasing.
Use contractions ("you're," "it's," "that's") to sound real.

CRITICAL RULES:
1. If owner_name is provided (first name): Start with "Hey [FirstName]," naturally
2. If NO owner_name: Start with "Hey, came across [company]" or "Hey, saw [company]" or similar casual opener
3. Use lowercase for shortened company names
4. Only mention reviews if rating 4.5+ AND review_count 50+
5. Use contractions always ("you're", "it's", "that's")
6. Max 35 words total
7. Sound like texting a friend, not writing a corporate email
8. NO EXCLAMATION MARKS - period only or em dash
9. ALWAYS END with one of these casual CTAs (pick randomly):
   - Wanted to run something by you.
   - Thought I'd share something with you.
   - Had something to share.
   - Figured I'd reach out.
   - Quick thing to run by you.
   - Worth a quick chat.

Business data:
owner_name: {owner_name or "NOT PROVIDED"}
company_name: {company_name}
city: {city}
state: {state}
category: {category}
rating: {rating}
review_count: {review_count}
business_type: {business_type}

Output ONLY the icebreaker message, nothing else. No quotes, no explanations."""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )

        icebreaker = response.choices[0].message.content.strip()
        icebreaker = icebreaker.strip('"').strip("'")

        return icebreaker

    except Exception as e:
        return f"ERROR: {str(e)}"


def process_row(idx, row_data):
    """Process single row - wrapper for parallel execution"""
    business_data = {
        'name': row_data['name'],
        'city': row_data['city'],
        'state': row_data['state'],
        'niche': row_data['niche'],
        'rating': row_data['rating'],
        'reviews': row_data['reviews'],
        'business_summary': row_data['business_summary'],
    }

    icebreaker = generate_icebreaker(business_data)

    return {
        'idx': idx,
        'icebreaker': icebreaker,
        'status': 'success' if icebreaker and not icebreaker.startswith('ERROR') else 'failed'
    }


# Read verified file
df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
print(f"Total rows: {len(df)}")

# Filter only deliverable emails
deliverable = df[df['verification_result'] == 'deliverable'].copy()
print(f"Deliverable emails: {len(deliverable)}")

print("\n" + "="*70)
print("GENERATING ICEBREAKERS (PARALLEL)")
print(f"Estimated time: ~{len(deliverable) / MAX_WORKERS / 2:.1f} minutes (with {MAX_WORKERS} threads)")
print("="*70 + "\n")

# Add icebreaker columns to df
df['icebreaker'] = ""
df['icebreaker_status'] = "not_generated"

# Parallel processing
start_time = datetime.now()
completed_count = 0
lock = threading.Lock()

# Prepare tasks
tasks = []
for idx in deliverable.index:
    row_data = df.loc[idx].to_dict()
    tasks.append((idx, row_data))

print(f"Processing {len(tasks)} emails with {MAX_WORKERS} parallel workers...\n")

# Execute in parallel
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(process_row, idx, row_data): idx for idx, row_data in tasks}

    for future in as_completed(futures):
        result = future.result()

        # Update dataframe
        df.at[result['idx'], 'icebreaker'] = result['icebreaker']
        df.at[result['idx'], 'icebreaker_status'] = result['status']

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
output_file = RESULTS_DIR / f"us_1900_WITH_ICEBREAKERS_{timestamp}.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')

duration = (datetime.now() - start_time).total_seconds()
success_count = len(df[df['icebreaker_status'] == 'success'])
failed_count = len(df[df['icebreaker_status'] == 'failed'])

print("\n" + "="*70)
print("ICEBREAKER GENERATION COMPLETE")
print("="*70)
print(f"Total processed: {completed_count}")
print(f"Success: {success_count}")
print(f"Failed: {failed_count}")
print(f"\nDuration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
print(f"Average rate: {completed_count/duration:.2f} icebreakers/sec")
print(f"Speedup: ~{(len(tasks) * 2 / duration):.1f}x faster than sequential")
print(f"\nSaved to: {output_file.name}")
print("="*70)
print("\nNext step: Run step4_create_final_outputs.py")
print("="*70)
