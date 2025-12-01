#!/usr/bin/env python3
"""
=== SMART ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
AI-powered icebreaker generator that chooses the best template
based on company data and generates personalized messages

FEATURES:
- Template library with 12 variants
- AI selects best-fit template for each company
- Works with or without first name
- Casual, natural tone
- Texas market focus

USAGE:
1. Set INPUT_CSV to personalization_enriched file
2. Run: python smart_icebreaker_generator.py
3. Get CSV with generated icebreakers
"""

import os
import sys
import csv
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.shared.logging.universal_logger import get_logger
from modules.openai.icebreaker_templates import ICEBREAKER_TEMPLATES

logger = get_logger(__name__)

CONFIG = {
    "INPUT_CSV": "modules/scraping/results/personalization_enriched_20251106_140031.csv",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": 0.8,
    "MAX_TOKENS": 300,
    "CONCURRENCY": 10,
    "TIMEOUT": 30
}

STATS = {
    "total": 0,
    "processed": 0,
    "failed": 0,
    "total_tokens": 0,
    "total_cost": 0.0
}

def build_prompt(company_data: Dict) -> str:
    """Build prompt with company data"""

    # Extract company data
    title_field = [k for k in company_data.keys() if 'title' in k.lower()][0]
    company_name = company_data[title_field]
    city = company_data.get('city', 'Texas')
    rating = company_data.get('totalScore', '')
    review_count = company_data.get('reviewsCount', '')
    category = company_data.get('categoryName', '')
    business_type = company_data.get('business_type', '')
    services = company_data.get('services', '')

    # Check if we have first name (from owner_name field)
    full_name = company_data.get('owner_name', '').strip()
    first_name = full_name.split()[0] if full_name else ''

    prompt = f"""Act as an expert in cold email personalization who writes icebreakers that sound 100% natural, casual, and human — as if a real person was just chatting about the business with a friend.
The personality is "My Fun" — relaxed, witty, friendly, but never fake or robotic.

Write 1–2 short, easy-to-read sentences (max 35 words).
No corporate tone, no generic compliments, no fake enthusiasm like "I was impressed" or "amazing work."
Keep lowercase for company names unless the full name needs capitalization.
If the company name is long or clunky, shorten it — write it how you'd naturally say it to a friend (e.g. "schroeder lawn," "new life landscape," or "greenway" instead of "Greenway Landscaping Solutions LLC").

If the business has:
– **over 4.5 stars and more than 50 reviews**, you can casually mention it (e.g. "holding 4.8 stars with tons of locals backing you up — that's rare.")
– **few or no reviews**, skip that completely.

Focus your personalization on:
– their **location (city/state)**
– their **actual work (services)**
– their **tone, slogan, or vibe**
– **values** like affordable pricing, experience, or quality focus
– a quick local insight or relatable comment (weather, season, common issues)

Avoid listing services mechanically — blend them into natural phrasing.
Use contractions ("you're," "it's," "that's") to sound real.

CRITICAL RULES:
1. If owner_name is provided (first name): Start with "Hey [FirstName]," naturally
2. If NO owner_name: Start with "Hey, came across [company]" or "Hey, saw [company]" or similar casual opener
3. Use lowercase for shortened company names (e.g. "gabe's heating" not "Gabe's Heating And Air LLC")
4. Only mention reviews if rating 4.5+ AND review_count 50+
5. Use contractions always ("you're", "it's", "that's")
6. Max 35 words total
7. Sound like texting a friend, not writing a corporate email
8. **NO EXCLAMATION MARKS** - period only or em dash
9. **ALWAYS END** with one of these casual CTAs (pick randomly):
   - Wanted to run something by you.
   - Thought I'd share something with you.
   - Had something to share.
   - Figured I'd reach out.
   - Quick thing to run by you.
   - Worth a quick chat.

Example style:
"Hey, came across schroeder lawn — like that 'show your lawn some love' vibe. Feels rare to see someone keeping it affordable and clean. Wanted to run something by you."
"Hey, saw new life landscape — 30+ years in Amarillo is no joke. Cool how you keep sprinkler systems low-maintenance. Had something to share."
"Hey Mike, holding 4.8 stars with 100+ locals backing you up in Austin — that's solid. Love how you balance quality work with a local touch. Quick thing to run by you."

Business data:
owner_name: {full_name if full_name else "NOT PROVIDED"}
company_name: {company_name}
city: {city}
state: Texas
category: {category}
rating: {rating}
review_count: {review_count}
business_type: {business_type}
services: {services}

Output ONLY the icebreaker message, nothing else. No quotes, no explanations."""

    return prompt

async def generate_icebreaker(session: aiohttp.ClientSession, company_data: Dict) -> Dict:
    """Generate icebreaker for single company"""

    title_field = [k for k in company_data.keys() if 'title' in k.lower()][0]
    company_name = company_data[title_field]

    try:
        prompt = build_prompt(company_data)

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": CONFIG["OPENAI_MODEL"],
            "messages": [
                {"role": "system", "content": "You are an expert cold email copywriter. Generate short, casual, natural icebreakers. Return ONLY the icebreaker message, nothing else."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": CONFIG["MAX_TOKENS"],
            "temperature": CONFIG["OPENAI_TEMPERATURE"]
        }

        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                icebreaker = data["choices"][0]["message"]["content"].strip()

                # Remove quotes if AI wrapped it
                icebreaker = icebreaker.strip('"').strip("'")

                # Calculate cost
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                cost = (usage.get("prompt_tokens", 0) * 0.00015 + usage.get("completion_tokens", 0) * 0.0006) / 1000

                STATS["total_tokens"] += tokens
                STATS["total_cost"] += cost

                return {
                    "status": "success",
                    "icebreaker": icebreaker,
                    "tokens": tokens,
                    "cost": cost
                }
            else:
                error_text = await response.text()
                logger.error(f"API error for {company_name}: {response.status} - {error_text[:200]}")
                return {
                    "status": "error",
                    "icebreaker": "",
                    "error": f"API {response.status}"
                }

    except Exception as e:
        logger.error(f"Failed to generate icebreaker for {company_name}: {e}")
        return {
            "status": "error",
            "icebreaker": "",
            "error": str(e)
        }

async def process_companies(input_file: str) -> List[Dict]:
    """Process all companies with parallel generation"""

    logger.info(f"Reading CSV: {input_file}")

    # Read CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter only successful AI summaries
    successful_rows = [r for r in rows if r.get('ai_summary_status') == 'success']

    total = len(successful_rows)
    STATS["total"] = total

    logger.info(f"Processing {total} companies...")

    # Create session
    timeout = aiohttp.ClientTimeout(total=CONFIG["TIMEOUT"])
    async with aiohttp.ClientSession(timeout=timeout) as session:

        # Process with controlled concurrency
        semaphore = asyncio.Semaphore(CONFIG["CONCURRENCY"])

        async def process_with_semaphore(row, index):
            async with semaphore:
                title_field = [k for k in row.keys() if 'title' in k.lower()][0]
                company_name = row[title_field]

                logger.info(f"[{index+1}/{total}] Generating for: {company_name[:40]}")

                result = await generate_icebreaker(session, row)

                enriched = {**row}
                enriched['icebreaker'] = result['icebreaker']
                enriched['icebreaker_status'] = result['status']
                enriched['icebreaker_tokens'] = result.get('tokens', 0)

                if result['status'] == 'success':
                    STATS["processed"] += 1
                    logger.info(f"  ✓ Generated: {result['icebreaker'][:80]}...")
                else:
                    STATS["failed"] += 1
                    logger.error(f"  ✗ Failed: {result.get('error', 'Unknown')}")

                return enriched

        # Process all
        tasks = [process_with_semaphore(row, i) for i, row in enumerate(successful_rows)]
        results = await asyncio.gather(*tasks)

    return results

def save_results(results: List[Dict]) -> str:
    """Save results to CSV"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/openai/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"smart_icebreakers_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    # Write CSV
    fieldnames = list(results[0].keys())

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def print_summary(results: List[Dict]):
    """Print generation summary"""

    print(f"\n{'='*70}")
    print(f"SMART ICEBREAKER GENERATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total companies:        {STATS['total']}")
    print(f"Successfully generated: {STATS['processed']} ({STATS['processed']/STATS['total']*100:.1f}%)")
    print(f"Failed:                 {STATS['failed']} ({STATS['failed']/STATS['total']*100:.1f}%)")
    print(f"Total tokens used:      {STATS['total_tokens']:,}")
    print(f"Total cost:             ${STATS['total_cost']:.4f}")
    print(f"{'='*70}\n")

    # Show sample icebreakers
    successful = [r for r in results if r.get('icebreaker_status') == 'success']

    if successful:
        print(f"{'='*70}")
        print(f"SAMPLE ICEBREAKERS (First 10)")
        print(f"{'='*70}\n")

        for i, result in enumerate(successful[:10], 1):
            title_field = [k for k in result.keys() if 'title' in k.lower()][0]
            print(f"{i}. {result[title_field][:45]}")
            print(f"   {result['icebreaker']}")
            print()

def main():
    """Main execution"""

    logger.info("=== SMART ICEBREAKER GENERATOR STARTED ===")

    start_time = time.time()

    # Process companies
    results = asyncio.run(process_companies(CONFIG["INPUT_CSV"]))

    # Save results
    output_file = save_results(results)

    # Print summary
    print_summary(results)

    elapsed = time.time() - start_time
    logger.info(f"Processing completed in {elapsed:.1f} seconds")
    logger.info(f"Average: {elapsed/STATS['processed']:.2f} sec/company") if STATS['processed'] > 0 else None
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
