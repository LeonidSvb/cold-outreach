#!/usr/bin/env python3
"""
=== APOLLO FULL ENRICHER (All-in-One) ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Complete enrichment pipeline for Apollo CSV files:
- Check website accessibility
- Scrape accessible websites
- Generate AI personalization
All in ONE script

INPUT: Apollo CSV with company_url column
OUTPUT: Enriched CSV ready for icebreaker generation

USAGE:
1. Set OPENAI_API_KEY in .env
2. Set INPUT_CSV below
3. Run: python apollo_full_enricher.py
"""

import sys
import csv
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_CSV": r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - US С - level (1).csv",
    "MAX_WORKERS": 25,
    "TIMEOUT": 12,
    "MAX_CONTENT_LENGTH": 15000,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_MAX_TOKENS": 500,
    "OPENAI_TEMPERATURE": 0.3
}

STATS = {
    "total": 0,
    "accessible": 0,
    "not_accessible": 0,
    "personalized": 0,
    "failed": 0
}

def extract_clean_text(html_content: str) -> str:
    """Extract clean text from HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()

        text = soup.get_text(separator=' ', strip=True)
        text = ' '.join(text.split())

        if len(text) > CONFIG["MAX_CONTENT_LENGTH"]:
            text = text[:CONFIG["MAX_CONTENT_LENGTH"]]

        return text
    except Exception as e:
        return ""

def scrape_and_personalize(url: str, company_name: str) -> Dict:
    """
    Combined function: scrape website AND generate personalization
    Returns dict with personalization data or error
    """
    result = {
        "accessible": "No",
        "status": "pending",
        "owner_name": "",
        "business_summary": "",
        "personalization_hook": ""
    }

    if not url or url.strip() == '':
        result["status"] = "no_url"
        return result

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        time.sleep(random.uniform(0.5, 1.2))

        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        if response.status_code != 200:
            result["status"] = f"http_{response.status_code}"
            return result

        content_type = response.headers.get('Content-Type', '')
        if 'text/html' not in content_type:
            result["status"] = "not_html"
            return result

        text_content = extract_clean_text(response.text)

        if len(text_content) < 200:
            result["status"] = "empty_content"
            return result

        result["accessible"] = "Yes"
        result["status"] = "scraped"

        client = OpenAI()

        prompt = f"""Analyze this company website and extract personalization data for cold outreach.

Company: {company_name}
Website: {url}
Content: {text_content[:8000]}

Extract and return ONLY valid JSON (no markdown):
{{
    "owner_name": "first and last name of owner/founder/CEO if found, otherwise null",
    "business_summary": "1-line casual description of what they do (max 25 words)",
    "personalization_hook": "1 casual phrase for icebreaker - their specialty or unique value (max 15 words)"
}}

Examples:
{{
    "owner_name": "Sarah Mitchell",
    "business_summary": "Marketing agency specializing in B2B SaaS - 10+ years, focus on demand generation",
    "personalization_hook": "helping B2B SaaS companies scale through data-driven demand gen"
}}

{{
    "owner_name": null,
    "business_summary": "Full-service digital agency - web design, SEO, PPC for small businesses",
    "personalization_hook": "building beautiful websites that actually convert for small businesses"
}}

Rules:
- owner_name: extract ONLY if clearly stated (CEO, Founder, Owner). Return null if unsure.
- business_summary: casual tone, specific details
- personalization_hook: natural phrase for "love how you [HOOK]"

Return ONLY JSON."""

        ai_response = client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "Extract personalization data. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=CONFIG["OPENAI_MAX_TOKENS"],
            temperature=CONFIG["OPENAI_TEMPERATURE"]
        )

        ai_text = ai_response.choices[0].message.content.strip()
        ai_text = re.sub(r'^```json\s*', '', ai_text)
        ai_text = re.sub(r'^```\s*', '', ai_text)
        ai_text = re.sub(r'\s*```$', '', ai_text)
        ai_text = ai_text.strip()

        analysis = json.loads(ai_text)

        result["status"] = "success"
        result["owner_name"] = analysis.get("owner_name") or ""
        result["business_summary"] = analysis.get("business_summary", "")
        result["personalization_hook"] = analysis.get("personalization_hook", "")

        return result

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
    except json.JSONDecodeError as e:
        result["status"] = "json_error"
        result["accessible"] = "Yes"
    except Exception as e:
        result["status"] = f"error: {str(e)[:50]}"

    return result

def process_row(row: Dict, index: int, total: int) -> Dict:
    """Process single company"""

    company_name = row.get('company_name', 'Unknown')
    company_url = row.get('company_url', '').strip()

    logger.info(f"[{index}/{total}] {company_name[:40]}")

    enriched = {**row}

    if not company_url:
        enriched["website_accessible"] = "No"
        enriched["personalization_status"] = "no_url"
        enriched["owner_name"] = ""
        enriched["business_summary"] = ""
        enriched["personalization_hook"] = ""
        STATS["not_accessible"] += 1
        return enriched

    logger.info(f"  Processing URL: {company_url[:50]}")

    result = scrape_and_personalize(company_url, company_name)

    enriched["website_accessible"] = result["accessible"]
    enriched["personalization_status"] = result["status"]
    enriched["owner_name"] = result["owner_name"]
    enriched["business_summary"] = result["business_summary"]
    enriched["personalization_hook"] = result["personalization_hook"]

    if result["accessible"] == "Yes":
        STATS["accessible"] += 1
    else:
        STATS["not_accessible"] += 1

    if result["status"] == "success":
        STATS["personalized"] += 1
        logger.info(f"  ✓ Personalized!")
    elif result["status"] in ["json_error"]:
        STATS["failed"] += 1
        logger.warning(f"  Failed: {result['status']}")
    else:
        logger.warning(f"  {result['status']}")

    return enriched

def main():
    """Main execution"""

    logger.info("=== APOLLO FULL ENRICHER STARTED ===")

    start = time.time()

    logger.info(f"Reading: {CONFIG['INPUT_CSV']}")

    with open(CONFIG['INPUT_CSV'], 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    STATS["total"] = total

    logger.info(f"Processing {total} companies with {CONFIG['MAX_WORKERS']} workers...")

    results = []

    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        future_to_row = {
            executor.submit(process_row, row, i+1, total): row
            for i, row in enumerate(rows)
        }

        for future in as_completed(future_to_row):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/apollo/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    input_name = Path(CONFIG['INPUT_CSV']).stem
    output_file = results_dir / f"{input_name}_enriched_{timestamp}.csv"

    if results:
        fieldnames = list(results[0].keys())

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Saved: {output_file}")

    elapsed = time.time() - start

    print(f"\n{'='*70}")
    print(f"APOLLO ENRICHMENT SUMMARY")
    print(f"{'='*70}")
    print(f"Total:                     {STATS['total']}")
    print(f"Accessible:                {STATS['accessible']} ({STATS['accessible']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Not accessible:            {STATS['not_accessible']} ({STATS['not_accessible']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Personalized:              {STATS['personalized']} ({STATS['personalized']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Failed:                    {STATS['failed']}")
    print(f"Time:                      {elapsed:.1f}s")
    if STATS['personalized'] > 0:
        print(f"Average:                   {elapsed/STATS['personalized']:.1f}s per company")
    print(f"{'='*70}\n")

    successful = [r for r in results if r.get('personalization_status') == 'success']
    if successful:
        print(f"SAMPLE RESULTS (first 5):")
        print(f"{'='*70}")
        for i, r in enumerate(successful[:5], 1):
            print(f"\n{i}. {r.get('company_name', 'N/A')}")
            print(f"   Owner: {r.get('owner_name') or 'Not found'}")
            print(f"   Summary: {r.get('business_summary', 'N/A')[:80]}")
            print(f"   Hook: {r.get('personalization_hook', 'N/A')[:80]}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
