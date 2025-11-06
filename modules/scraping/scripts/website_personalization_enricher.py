#!/usr/bin/env python3
"""
=== WEBSITE PERSONALIZATION ENRICHER ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Scrape accessible websites and create AI-powered personalization summaries
for cold email outreach

FEATURES:
- HTTP-only scraping (static sites)
- OpenAI summarization for personalization
- Extract: services, owner name, company info
- Parallel processing (25 concurrent)
- CSV output ready for email campaigns

USAGE:
1. Set OPENAI_API_KEY env variable
2. Configure INPUT_CSV (result from email extractor)
3. Run: python website_personalization_enricher.py
4. Get enriched CSV with personalization data
"""

import sys
import csv
import json
import re
import time
import random
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_CSV": "modules/scraping/results/email_extraction_20251106_135242.csv",
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
    "scraped": 0,
    "analyzed": 0,
    "failed": 0
}

def extract_clean_text(html_content: str) -> str:
    """Extract clean text from HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = ' '.join(text.split())

        # Truncate if too long
        if len(text) > CONFIG["MAX_CONTENT_LENGTH"]:
            text = text[:CONFIG["MAX_CONTENT_LENGTH"]]

        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""

def scrape_website_content(url: str) -> Dict:
    """Scrape website and extract clean text content"""
    result = {
        "url": url,
        "content": "",
        "title": "",
        "status": "pending"
    }

    if not url or url.strip() == '':
        result["status"] = "no_url"
        return result

    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result["url"] = url

    try:
        # Add delay to be polite
        time.sleep(random.uniform(0.5, 1.2))

        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            if soup.title:
                result["title"] = soup.title.string.strip() if soup.title.string else ""

            # Extract clean text
            content = extract_clean_text(response.text)

            if len(content) > 200:
                result["content"] = content
                result["status"] = "success"
            else:
                result["status"] = "empty_content"
        else:
            result["status"] = f"http_{response.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
    except Exception as e:
        result["status"] = f"error: {str(e)[:50]}"

    return result

def generate_personalization_summary(company_name: str, website: str, content: str) -> Dict:
    """
    Generate personalization summary using OpenAI

    Extracts:
    - Type of service/business
    - Owner/founder name (if mentioned)
    - Key differentiators
    - Personalization hooks
    """

    try:
        client = OpenAI()

        prompt = f"""Analyze this company website and provide personalization data for cold email outreach.

Company: {company_name}
Website: {website}
Content: {content[:8000]}

Extract and return ONLY valid JSON (no markdown, no code blocks):
{{
    "business_type": "brief description of what they do (max 20 words)",
    "services": ["service 1", "service 2", "service 3"],
    "owner_name": "owner/founder name if found, otherwise null",
    "key_differentiators": ["unique aspect 1", "unique aspect 2"],
    "personalization_hooks": ["hook for outreach 1", "hook 2"],
    "company_size_estimate": "solo/small/medium",
    "target_market": "who they serve",
    "pain_points": ["possible pain point 1", "pain point 2"]
}}

IMPORTANT: Return ONLY the JSON object, no other text."""

        response = client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are a B2B research analyst. Extract personalization data from company websites for cold outreach. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=CONFIG["OPENAI_MAX_TOKENS"],
            temperature=CONFIG["OPENAI_TEMPERATURE"]
        )

        ai_response = response.choices[0].message.content.strip()

        # Clean response - remove markdown code blocks if present
        ai_response = re.sub(r'^```json\s*', '', ai_response)
        ai_response = re.sub(r'^```\s*', '', ai_response)
        ai_response = re.sub(r'\s*```$', '', ai_response)
        ai_response = ai_response.strip()

        # Parse JSON
        analysis = json.loads(ai_response)

        return {
            "status": "success",
            "analysis": analysis,
            "tokens_used": response.usage.total_tokens
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}\nResponse: {ai_response[:200]}")
        return {
            "status": "json_error",
            "error": str(e),
            "raw_response": ai_response[:500]
        }
    except Exception as e:
        logger.error(f"OpenAI analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def process_single_company(row: Dict, index: int, total: int) -> Dict:
    """Process a single company: scrape + analyze"""

    company_name = row.get('\ufeff"title"', row.get('title', 'Unknown'))
    website = row.get('website', '').strip()
    accessible = row.get('accessible', 'No')

    logger.info(f"[{index}/{total}] Processing: {company_name[:40]}")

    # Initialize enriched row
    enriched = {**row}
    enriched["scraped_content_length"] = 0
    enriched["ai_summary_status"] = "pending"
    enriched["business_type"] = ""
    enriched["services"] = ""
    enriched["owner_name"] = ""
    enriched["personalization_hooks"] = ""
    enriched["target_market"] = ""
    enriched["pain_points"] = ""

    # Only process accessible sites
    if accessible != "Yes" or not website:
        enriched["ai_summary_status"] = "skipped_not_accessible"
        logger.warning(f"  Skipped (not accessible)")
        return enriched

    # Step 1: Scrape website
    logger.info(f"  Scraping website...")
    scrape_result = scrape_website_content(website)

    if scrape_result["status"] != "success":
        enriched["ai_summary_status"] = f"scrape_failed_{scrape_result['status']}"
        logger.warning(f"  Scraping failed: {scrape_result['status']}")
        STATS["failed"] += 1
        return enriched

    STATS["scraped"] += 1
    enriched["scraped_content_length"] = len(scrape_result["content"])
    logger.info(f"  Scraped {len(scrape_result['content'])} chars")

    # Step 2: Generate AI summary
    logger.info(f"  Generating AI summary...")
    ai_result = generate_personalization_summary(
        company_name,
        website,
        scrape_result["content"]
    )

    if ai_result["status"] == "success":
        analysis = ai_result["analysis"]

        enriched["ai_summary_status"] = "success"
        enriched["business_type"] = analysis.get("business_type", "")
        enriched["services"] = "; ".join(analysis.get("services", []))
        enriched["owner_name"] = analysis.get("owner_name") or ""
        enriched["personalization_hooks"] = "; ".join(analysis.get("personalization_hooks", []))
        enriched["target_market"] = analysis.get("target_market", "")
        enriched["pain_points"] = "; ".join(analysis.get("pain_points", []))
        enriched["company_size_estimate"] = analysis.get("company_size_estimate", "")
        enriched["key_differentiators"] = "; ".join(analysis.get("key_differentiators", []))

        STATS["analyzed"] += 1
        logger.info(f"  ✓ AI summary generated successfully")
    else:
        enriched["ai_summary_status"] = f"ai_failed_{ai_result['status']}"
        enriched["ai_error"] = ai_result.get("error", "")
        logger.error(f"  AI analysis failed: {ai_result['status']}")
        STATS["failed"] += 1

    return enriched

def process_csv_parallel(input_file: str) -> List[Dict]:
    """Process CSV with parallel scraping and AI analysis"""

    logger.info(f"Reading CSV: {input_file}")

    # Read CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter only accessible sites
    accessible_rows = [r for r in rows if r.get('accessible') == 'Yes']

    total = len(accessible_rows)
    STATS["total"] = total

    logger.info(f"Found {total} accessible websites to process")
    logger.info(f"Starting parallel processing with {CONFIG['MAX_WORKERS']} workers...")

    results = []

    # Process in parallel
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        future_to_row = {
            executor.submit(process_single_company, row, i+1, total): row
            for i, row in enumerate(accessible_rows)
        }

        for future in as_completed(future_to_row):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    # Add back non-accessible rows without processing
    non_accessible = [r for r in rows if r.get('accessible') != 'Yes']
    for row in non_accessible:
        enriched = {**row}
        enriched["ai_summary_status"] = "skipped_not_accessible"
        results.append(enriched)

    return results

def save_results(results: List[Dict]) -> str:
    """Save enriched results to CSV"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"personalization_enriched_{timestamp}.csv"

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

def print_summary():
    """Print processing summary"""

    print(f"\n{'='*70}")
    print(f"WEBSITE PERSONALIZATION ENRICHMENT SUMMARY")
    print(f"{'='*70}")
    print(f"Total accessible sites:    {STATS['total']}")
    print(f"Successfully scraped:      {STATS['scraped']} ({STATS['scraped']/max(1,STATS['total'])*100:.1f}%)")
    print(f"AI summaries generated:    {STATS['analyzed']} ({STATS['analyzed']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Failed:                    {STATS['failed']} ({STATS['failed']/max(1,STATS['total'])*100:.1f}%)")
    print(f"{'='*70}\n")

def main():
    """Main execution"""

    logger.info("=== WEBSITE PERSONALIZATION ENRICHER STARTED ===")

    start_time = time.time()

    # Process CSV
    results = process_csv_parallel(CONFIG["INPUT_CSV"])

    # Save results
    output_file = save_results(results)

    # Print summary
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Processing completed in {elapsed:.1f} seconds")

    if STATS['analyzed'] > 0:
        logger.info(f"Average: {elapsed/STATS['analyzed']:.1f} sec/company")

    logger.info(f"Results saved to: {output_file}")

    # Show sample results
    successful = [r for r in results if r.get('ai_summary_status') == 'success']
    if successful:
        print(f"\n{'='*70}")
        print(f"SAMPLE PERSONALIZATION DATA (first 3)")
        print(f"{'='*70}")
        for i, result in enumerate(successful[:3], 1):
            title_field = [k for k in result.keys() if 'title' in k.lower()][0]
            print(f"\n{i}. {result[title_field]}")
            print(f"   Business: {result.get('business_type', 'N/A')}")
            print(f"   Services: {result.get('services', 'N/A')[:70]}")
            print(f"   Owner: {result.get('owner_name', 'N/A')}")
            print(f"   Hooks: {result.get('personalization_hooks', 'N/A')[:80]}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
