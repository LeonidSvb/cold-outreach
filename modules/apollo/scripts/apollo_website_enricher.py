#!/usr/bin/env python3
"""
=== APOLLO WEBSITE ENRICHER ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Enrich Apollo CSV data with website personalization for cold outreach

FEATURES:
- Check website accessibility (HTTP-only)
- Scrape accessible sites (extract clean text)
- Generate AI personalization summaries (OpenAI)
- Parallel processing (25 concurrent workers)
- CSV output ready for icebreaker generation

WORKFLOW:
1. Read Apollo CSV (must have 'company_url' column)
2. Check each website accessibility
3. Scrape accessible sites (remove HTML, extract text)
4. Send to OpenAI for personalization analysis
5. Output: enriched CSV with personalization data

USAGE:
1. Set OPENAI_API_KEY in .env
2. Set INPUT_CSV path below
3. Run: python apollo_website_enricher.py
4. Results in modules/apollo/results/
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
    "scraped": 0,
    "personalized": 0,
    "failed": 0
}

def check_website_accessible(url: str) -> Dict:
    """
    Check if website is accessible via HTTP (not dynamic/JS)
    Returns: dict with accessible status and basic info
    """
    result = {
        "url": url,
        "accessible": False,
        "status": "pending",
        "title": ""
    }

    if not url or url.strip() == '':
        result["status"] = "no_url"
        return result

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result["url"] = url

    try:
        time.sleep(random.uniform(0.3, 0.8))

        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        content_type = response.headers.get('Content-Type', '')

        if response.status_code == 200 and 'text/html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text().strip()

            if len(text_content) > 200:
                result["accessible"] = True
                result["status"] = "success"

                if soup.title:
                    result["title"] = soup.title.string.strip() if soup.title.string else ""
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

def extract_clean_text(html_content: str) -> str:
    """Extract clean text from HTML (no tags, no scripts)"""
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
        logger.error(f"Text extraction failed: {e}")
        return ""

def scrape_website_content(url: str) -> Dict:
    """Scrape website and extract clean text"""
    result = {
        "url": url,
        "content": "",
        "status": "pending"
    }

    try:
        time.sleep(random.uniform(0.5, 1.2))

        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        if response.status_code == 200:
            content = extract_clean_text(response.text)

            if len(content) > 200:
                result["content"] = content
                result["status"] = "success"
            else:
                result["status"] = "empty_content"
        else:
            result["status"] = f"http_{response.status_code}"

    except Exception as e:
        result["status"] = f"error: {str(e)[:50]}"

    return result

def generate_personalization(company_name: str, website: str, content: str) -> Dict:
    """
    Generate personalization summary using OpenAI

    Returns:
    - owner_name: founder/CEO name
    - business_summary: 1-line description
    - personalization_hook: icebreaker phrase
    """
    try:
        client = OpenAI()

        prompt = f"""Analyze this company website and extract personalization data for cold outreach.

Company: {company_name}
Website: {website}
Content: {content[:8000]}

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
- business_summary: casual tone, specific details about services/industry/experience
- personalization_hook: natural phrase that fits "love how you [HOOK]" or "saw you're [HOOK]"

Return ONLY the JSON object."""

        response = client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are a B2B research analyst. Extract personalization data from websites for cold outreach. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=CONFIG["OPENAI_MAX_TOKENS"],
            temperature=CONFIG["OPENAI_TEMPERATURE"]
        )

        ai_response = response.choices[0].message.content.strip()

        ai_response = re.sub(r'^```json\s*', '', ai_response)
        ai_response = re.sub(r'^```\s*', '', ai_response)
        ai_response = re.sub(r'\s*```$', '', ai_response)
        ai_response = ai_response.strip()

        analysis = json.loads(ai_response)

        return {
            "status": "success",
            "analysis": analysis,
            "tokens": response.usage.total_tokens
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        return {"status": "json_error", "error": str(e)}
    except Exception as e:
        logger.error(f"OpenAI failed: {e}")
        return {"status": "error", "error": str(e)}

def process_single_row(row: Dict, index: int, total: int) -> Dict:
    """Process single company: check → scrape → personalize"""

    company_name = row.get('company_name', 'Unknown')
    company_url = row.get('company_url', '').strip()

    logger.info(f"[{index}/{total}] {company_name[:40]}")

    enriched = {**row}
    enriched["website_accessible"] = "No"
    enriched["website_status"] = ""
    enriched["personalization_status"] = "pending"
    enriched["owner_name"] = ""
    enriched["business_summary"] = ""
    enriched["personalization_hook"] = ""

    if not company_url:
        enriched["personalization_status"] = "no_url"
        logger.warning("  No URL")
        STATS["not_accessible"] += 1
        return enriched

    logger.info(f"  Checking accessibility...")
    access_check = check_website_accessible(company_url)

    enriched["website_status"] = access_check["status"]

    if not access_check["accessible"]:
        enriched["personalization_status"] = f"not_accessible_{access_check['status']}"
        logger.warning(f"  Not accessible: {access_check['status']}")
        STATS["not_accessible"] += 1
        return enriched

    STATS["accessible"] += 1
    enriched["website_accessible"] = "Yes"
    logger.info(f"  Accessible! Scraping...")

    scrape_result = scrape_website_content(company_url)

    if scrape_result["status"] != "success":
        enriched["personalization_status"] = f"scrape_failed_{scrape_result['status']}"
        logger.warning(f"  Scraping failed: {scrape_result['status']}")
        STATS["failed"] += 1
        return enriched

    STATS["scraped"] += 1
    logger.info(f"  Scraped {len(scrape_result['content'])} chars")

    logger.info(f"  Generating AI personalization...")
    ai_result = generate_personalization(
        company_name,
        company_url,
        scrape_result["content"]
    )

    if ai_result["status"] == "success":
        analysis = ai_result["analysis"]

        enriched["personalization_status"] = "success"
        enriched["owner_name"] = analysis.get("owner_name") or ""
        enriched["business_summary"] = analysis.get("business_summary", "")
        enriched["personalization_hook"] = analysis.get("personalization_hook", "")

        STATS["personalized"] += 1
        logger.info(f"  Success!")
    else:
        enriched["personalization_status"] = f"ai_failed_{ai_result['status']}"
        logger.error(f"  AI failed: {ai_result['status']}")
        STATS["failed"] += 1

    return enriched

def process_csv_parallel(input_file: str) -> List[Dict]:
    """Process CSV with parallel enrichment"""

    logger.info(f"Reading: {input_file}")

    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    STATS["total"] = total

    logger.info(f"Processing {total} companies with {CONFIG['MAX_WORKERS']} workers...")

    results = []

    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        future_to_row = {
            executor.submit(process_single_row, row, i+1, total): row
            for i, row in enumerate(rows)
        }

        for future in as_completed(future_to_row):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    return results

def save_results(results: List[Dict], input_file: str) -> str:
    """Save enriched results to CSV"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/apollo/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    input_name = Path(input_file).stem
    output_file = results_dir / f"{input_name}_enriched_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    fieldnames = list(results[0].keys())

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved: {output_file}")
    return str(output_file)

def print_summary():
    """Print processing summary"""

    print(f"\n{'='*70}")
    print(f"APOLLO WEBSITE ENRICHMENT SUMMARY")
    print(f"{'='*70}")
    print(f"Total companies:           {STATS['total']}")
    print(f"Accessible websites:       {STATS['accessible']} ({STATS['accessible']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Not accessible:            {STATS['not_accessible']} ({STATS['not_accessible']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Successfully scraped:      {STATS['scraped']}")
    print(f"Personalized:              {STATS['personalized']} ({STATS['personalized']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Failed:                    {STATS['failed']}")
    print(f"{'='*70}\n")

def main():
    """Main execution"""

    logger.info("=== APOLLO WEBSITE ENRICHER STARTED ===")

    start_time = time.time()

    results = process_csv_parallel(CONFIG["INPUT_CSV"])
    output_file = save_results(results, CONFIG["INPUT_CSV"])
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.1f}s")

    if STATS['personalized'] > 0:
        logger.info(f"Average: {elapsed/STATS['personalized']:.1f}s per company")

    successful = [r for r in results if r.get('personalization_status') == 'success']
    if successful:
        print(f"\nSAMPLE PERSONALIZATION (first 5):")
        print(f"{'='*70}")
        for i, r in enumerate(successful[:5], 1):
            print(f"\n{i}. {r.get('company_name', 'N/A')}")
            print(f"   Owner: {r.get('owner_name') or 'Not found'}")
            print(f"   Summary: {r.get('business_summary', 'N/A')}")
            print(f"   Hook: {r.get('personalization_hook', 'N/A')}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
