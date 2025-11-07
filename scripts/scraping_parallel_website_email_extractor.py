#!/usr/bin/env python3
"""
=== PARALLEL WEBSITE EMAIL EXTRACTOR ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Fast parallel checking of websites for accessibility and email extraction
Checks if site is static (accessible via HTTP) and extracts emails

FEATURES:
- Parallel processing (10 concurrent threads)
- HTTP-only checking (skips dynamic/JS sites)
- Email extraction from accessible pages
- CSV input/output with enrichment

USAGE:
1. Configure INPUT_CSV path
2. Run: python parallel_website_email_extractor.py
3. Results saved with emails to results/
"""

import sys
import csv
import json
import re
import time
import random
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Try to import logger, fall back to print if not available
try:
    from logger.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

CONFIG = {
    "INPUT_CSV": r"C:\Users\79818\Downloads\dataset_crawler-google-places_2025-11-06_03-24-15-870.csv",
    "MAX_WORKERS": 25,
    "TIMEOUT": 10,
    "DELAY_MIN": 0.5,
    "DELAY_MAX": 1.5,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

STATS = {
    "total": 0,
    "accessible": 0,
    "dynamic": 0,
    "failed": 0,
    "with_emails": 0
}

def is_valid_email(email: str) -> bool:
    """Validate email format and exclude common false positives"""
    if not email or '@' not in email:
        return False

    # Exclude common false positives
    exclude_patterns = [
        r'@example\.',
        r'@test\.',
        r'@domain\.',
        r'@email\.',
        r'@yoursite\.',
        r'@sentry\.io',
        r'@2x\.png',
        r'@3x\.png',
    ]

    for pattern in exclude_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            return False

    # Valid email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def extract_emails_from_text(text: str) -> Set[str]:
    """Extract all valid email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def check_website_accessibility(url: str) -> Dict:
    """
    Check if website is accessible via HTTP and extract emails
    Returns dict with status and emails
    """
    result = {
        "website": url,
        "accessible": False,
        "is_dynamic": False,
        "emails": [],
        "status": "pending"
    }

    if not url or url.strip() == '':
        result["status"] = "no_url"
        return result

    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result["website"] = url

    # Pages to check for emails
    pages_to_check = [
        url,
        urljoin(url, '/contact'),
        urljoin(url, '/contact-us'),
        urljoin(url, '/about'),
    ]

    all_emails = set()
    main_page_accessible = False

    try:
        # Add small random delay to avoid rate limiting
        time.sleep(random.uniform(CONFIG["DELAY_MIN"], CONFIG["DELAY_MAX"]))

        # Try to fetch main page
        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        # Check if we got actual HTML content
        content_type = response.headers.get('Content-Type', '')

        if response.status_code == 200 and 'text/html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Check if page is mostly empty (sign of dynamic content)
            text_content = soup.get_text().strip()

            # If page has substantial content, it's accessible
            if len(text_content) > 200:
                main_page_accessible = True
                result["accessible"] = True

                # Extract emails from main page
                emails = extract_emails_from_text(text_content)
                all_emails.update(emails)

                # Extract from mailto links
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                for link in mailto_links:
                    email = link.get('href', '').replace('mailto:', '').split('?')[0].strip()
                    if is_valid_email(email):
                        all_emails.add(email.lower())

                # Try contact/about pages if we haven't found emails yet
                if len(all_emails) == 0:
                    for page_url in pages_to_check[1:]:
                        try:
                            time.sleep(random.uniform(0.3, 0.7))
                            page_response = requests.get(
                                page_url,
                                headers={'User-Agent': CONFIG["USER_AGENT"]},
                                timeout=CONFIG["TIMEOUT"]
                            )

                            if page_response.status_code == 200:
                                page_soup = BeautifulSoup(page_response.content, 'html.parser')
                                page_text = page_soup.get_text()
                                page_emails = extract_emails_from_text(page_text)
                                all_emails.update(page_emails)

                                # Check mailto links
                                mailto_links = page_soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                                for link in mailto_links:
                                    email = link.get('href', '').replace('mailto:', '').split('?')[0].strip()
                                    if is_valid_email(email):
                                        all_emails.add(email.lower())

                                if all_emails:
                                    break

                        except Exception as e:
                            continue

                result["status"] = "success"
            else:
                # Page returned but mostly empty - likely dynamic
                result["is_dynamic"] = True
                result["status"] = "dynamic"
        else:
            result["status"] = f"error_{response.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
    except Exception as e:
        result["status"] = f"error: {str(e)[:50]}"

    result["emails"] = list(all_emails)

    return result

def process_csv_row(row: Dict, index: int, total: int) -> Dict:
    """Process a single CSV row"""
    website = row.get('website', '').strip()

    logger.info(f"[{index}/{total}] Checking: {website[:50]}...")

    result = check_website_accessibility(website)

    # Update stats
    if result["accessible"]:
        STATS["accessible"] += 1
    if result["is_dynamic"]:
        STATS["dynamic"] += 1
    if result["emails"]:
        STATS["with_emails"] += 1
    if result["status"] not in ["success", "dynamic"]:
        STATS["failed"] += 1

    # Merge with original row
    enriched_row = {**row}
    enriched_row["accessible"] = "Yes" if result["accessible"] else "No"
    enriched_row["is_dynamic"] = "Yes" if result["is_dynamic"] else "No"
    enriched_row["emails_found"] = len(result["emails"])
    enriched_row["emails"] = "; ".join(result["emails"]) if result["emails"] else ""
    enriched_row["check_status"] = result["status"]

    # Log result
    if result["emails"]:
        logger.info(f"  Found {len(result['emails'])} emails: {', '.join(result['emails'][:2])}")
    elif result["is_dynamic"]:
        logger.warning(f"  Dynamic site (skipped)")
    elif not result["accessible"]:
        logger.warning(f"  Not accessible ({result['status']})")
    else:
        logger.info(f"  No emails found")

    return enriched_row

def process_csv_parallel(input_file: str) -> List[Dict]:
    """Process CSV with parallel website checking"""
    logger.info(f"Reading CSV: {input_file}")

    # Read CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    STATS["total"] = total

    logger.info(f"Found {total} rows. Starting parallel processing with {CONFIG['MAX_WORKERS']} workers...")

    results = []

    # Process in parallel
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        # Submit all tasks
        future_to_row = {
            executor.submit(process_csv_row, row, i+1, total): row
            for i, row in enumerate(rows)
        }

        # Collect results as they complete
        for future in as_completed(future_to_row):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    return results

def save_results(results: List[Dict]) -> str:
    """Save enriched results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"email_extraction_{timestamp}.csv"

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

def save_results_to_path(results: List[Dict], output_path: str) -> str:
    """Save enriched results to specified CSV path (for in-place updates)"""
    if not results:
        logger.warning("No results to save")
        return ""

    # Ensure parent directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save using pandas for better CSV handling
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False, encoding='utf-8')

    logger.info(f"Results saved to: {output_path}")
    print(f"CSV saved: {output_path}")

    return str(output_path)

def print_summary():
    """Print processing summary"""
    print(f"\n{'='*70}")
    print(f"WEBSITE EMAIL EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total websites checked:    {STATS['total']}")
    print(f"Accessible (static):       {STATS['accessible']} ({STATS['accessible']/STATS['total']*100:.1f}%)")
    print(f"Dynamic (JS-only):         {STATS['dynamic']} ({STATS['dynamic']/STATS['total']*100:.1f}%)")
    print(f"Failed/Timeout:            {STATS['failed']} ({STATS['failed']/STATS['total']*100:.1f}%)")
    print(f"With emails found:         {STATS['with_emails']} ({STATS['with_emails']/STATS['total']*100:.1f}%)")
    print(f"{'='*70}\n")

def parse_cli_arguments():
    """Parse command line arguments for frontend integration"""
    parser = argparse.ArgumentParser(description="Website Scraper - Extract text and emails from websites")

    parser.add_argument('--input', type=str, help='Path to input CSV file (must have "website" column)')
    parser.add_argument('--output', type=str, help='Output file path (optional, auto-generated if not provided)')
    parser.add_argument('--workers', type=int, default=25, help='Number of parallel workers (10-50)')
    parser.add_argument('--mode', type=str, default='quick', choices=['quick', 'full'],
                        help='Processing mode: quick (text only) or full (text + emails)')

    return parser.parse_args()

def main():
    """Main execution with CLI argument support"""
    logger.info("=== PARALLEL WEBSITE EMAIL EXTRACTOR STARTED ===")

    # Parse CLI arguments
    args = parse_cli_arguments()

    # Apply CLI overrides to config
    if args.workers:
        CONFIG["MAX_WORKERS"] = args.workers

    start_time = time.time()

    # Determine input file
    input_file = args.input if args.input else CONFIG["INPUT_CSV"]

    if not input_file or not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}")
        print(f"❌ Error: Input file not found: {input_file}")
        return

    # Process CSV
    results = process_csv_parallel(input_file)

    # Save results
    if args.output:
        output_file = save_results_to_path(results, args.output)
    else:
        output_file = save_results(results)

    # Print summary
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Processing completed in {elapsed:.1f} seconds")
    if results:
        logger.info(f"Average: {elapsed/len(results):.2f} sec/website")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
