#!/usr/bin/env python3
"""
=== APIFY WEBSITE CONTENT CRAWLER - EMAIL EXTRACTOR ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Use Apify Website Content Crawler to extract emails from difficult sites
(dynamic JS, protected, or where simple HTTP failed)

FEATURES:
- Headless browser crawling (bypasses bot protection)
- Deep content extraction from JS-rendered pages
- Email extraction from full page text
- Handles contact forms and dynamic content

USAGE:
1. Configure INPUT_CSV with problem sites
2. Run: python apify_content_crawler_email_extractor.py
3. Results saved with extracted emails

COST:
~$0.5-$5 per 1000 pages (Apify credits)
"""

import os
import sys
import csv
import json
import time
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from logger.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

load_dotenv()

CONFIG = {
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "apify/website-content-crawler",

    "INPUT_CSV": "data/temp/test_5_problem_sites.csv",
    "OUTPUT_DIR": "data/temp",

    # Crawler settings
    "MAX_CRAWL_DEPTH": 2,
    "MAX_PAGES_PER_SITE": 5,
    "CRAWLER_TYPE": "cheerio",
}

STATS = {
    "total_sites": 0,
    "successful_crawls": 0,
    "emails_found": 0,
    "failed_crawls": 0
}

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email or '@' not in email:
        return False

    exclude_patterns = [
        r'@example\.', r'@test\.', r'@domain\.',
        r'@email\.', r'@yoursite\.', r'@sentry\.io',
        r'@2x\.png', r'@3x\.png', r'\.png$', r'\.jpg$'
    ]

    for pattern in exclude_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_emails_from_text(text: str) -> Set[str]:
    """Extract valid emails from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def run_website_content_crawler(url: str) -> Dict:
    """
    Run Apify Website Content Crawler on a single URL

    Args:
        url: Website URL to crawl

    Returns:
        Dict with crawled text and extracted emails
    """
    logger.info(f"Starting Website Content Crawler for: {url}")

    result = {
        "url": url,
        "success": False,
        "emails": [],
        "text_length": 0,
        "pages_crawled": 0,
        "error": None
    }

    # Actor input
    actor_input = {
        "startUrls": [{"url": url}],
        "crawlerType": CONFIG["CRAWLER_TYPE"],
        "maxCrawlDepth": CONFIG["MAX_CRAWL_DEPTH"],
        "maxCrawlPages": CONFIG["MAX_PAGES_PER_SITE"],
        "initialConcurrency": 1,
        "maxConcurrency": 1,
        "htmlTransformer": "readableText",
        "readableTextCharThreshold": 100,
        "removeCookieWarnings": True,
        "clickElementsCssSelector": "button:contains('contact'), a:contains('contact')",
        "saveHtml": False,
        "saveMarkdown": False,
        "saveFiles": False,
        "saveScreenshots": False
    }

    # Start actor (replace / with ~ in actor ID for API)
    actor_id_api = CONFIG['ACTOR_ID'].replace('/', '~')
    api_url = f"https://api.apify.com/v2/acts/{actor_id_api}/runs"
    params = {"token": CONFIG["APIFY_API_KEY"]}

    try:
        response = requests.post(
            api_url,
            json=actor_input,
            headers={"Content-Type": "application/json"},
            params=params,
            timeout=30
        )

        if response.status_code != 201:
            result["error"] = f"Failed to start: {response.status_code}"
            return result

        run_id = response.json()["data"]["id"]
        logger.info(f"Run started: {run_id}")

        # Poll for completion (max 5 minutes)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        max_wait = 300
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(10)
            elapsed += 10

            status_response = requests.get(status_url, params=params)
            status = status_response.json()["data"]["status"]

            if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                break

        if status != "SUCCEEDED":
            result["error"] = f"Run failed: {status}"
            return result

        # Get results
        dataset_id = status_response.json()["data"]["defaultDatasetId"]
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

        results_response = requests.get(dataset_url, params=params)
        crawled_pages = results_response.json()

        result["pages_crawled"] = len(crawled_pages)

        # Extract emails from all crawled pages
        all_emails = set()
        all_text = ""

        for page in crawled_pages:
            text = page.get("text", "")
            all_text += text + " "

            # Extract emails from text
            emails = extract_emails_from_text(text)
            all_emails.update(emails)

        result["text_length"] = len(all_text)
        result["emails"] = list(all_emails)
        result["success"] = True

        logger.info(f"Success! Found {len(all_emails)} emails in {len(crawled_pages)} pages")

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error: {e}")

    return result

def process_csv(input_file: str) -> List[Dict]:
    """Process CSV with problem sites"""
    logger.info(f"Reading: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sites = list(reader)

    STATS["total_sites"] = len(sites)
    logger.info(f"Found {len(sites)} problem sites")

    results = []

    for i, site in enumerate(sites, 1):
        url = site.get('website', '').strip()

        if not url:
            logger.warning(f"[{i}/{len(sites)}] Skipping (no URL)")
            continue

        logger.info(f"\n[{i}/{len(sites)}] Processing: {site['title']}")
        logger.info(f"  URL: {url}")
        logger.info(f"  Reason: {site.get('reason', 'unknown')}")

        # Run crawler
        crawl_result = run_website_content_crawler(url)

        # Update stats
        if crawl_result["success"]:
            STATS["successful_crawls"] += 1
            if crawl_result["emails"]:
                STATS["emails_found"] += len(crawl_result["emails"])
        else:
            STATS["failed_crawls"] += 1

        # Merge with original data
        enriched = {**site}
        enriched["crawler_success"] = "Yes" if crawl_result["success"] else "No"
        enriched["pages_crawled"] = crawl_result["pages_crawled"]
        enriched["text_length"] = crawl_result["text_length"]
        enriched["emails_found"] = len(crawl_result["emails"])
        enriched["emails"] = "; ".join(crawl_result["emails"])
        enriched["error"] = crawl_result["error"] or ""

        results.append(enriched)

        # Log result
        if crawl_result["emails"]:
            logger.info(f"  ✅ Found {len(crawl_result['emails'])} emails: {', '.join(crawl_result['emails'][:3])}")
        else:
            logger.info(f"  ❌ No emails found")

        # Small delay between sites
        time.sleep(2)

    return results

def save_results(results: List[Dict]) -> str:
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(CONFIG["OUTPUT_DIR"]) / f"apify_crawler_results_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    fieldnames = list(results[0].keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def print_summary():
    """Print summary"""
    print(f"\n{'='*70}")
    print(f"WEBSITE CONTENT CRAWLER - EMAIL EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total sites processed:     {STATS['total_sites']}")
    print(f"Successful crawls:         {STATS['successful_crawls']}")
    print(f"Failed crawls:             {STATS['failed_crawls']}")
    print(f"Total emails found:        {STATS['emails_found']}")
    if STATS['successful_crawls'] > 0:
        print(f"Success rate:              {STATS['successful_crawls']/STATS['total_sites']*100:.1f}%")
        print(f"Emails per successful:     {STATS['emails_found']/STATS['successful_crawls']:.1f}")
    print(f"{'='*70}\n")

def main():
    """Main execution"""
    logger.info("=== APIFY WEBSITE CONTENT CRAWLER STARTED ===")

    if not CONFIG["APIFY_API_KEY"]:
        logger.error("APIFY_API_KEY not found in .env")
        return

    start_time = time.time()

    # Process sites
    results = process_csv(CONFIG["INPUT_CSV"])

    # Save results
    output_file = save_results(results)

    # Print summary
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed/60:.1f} minutes")
    logger.info(f"Results: {output_file}")

if __name__ == "__main__":
    main()
