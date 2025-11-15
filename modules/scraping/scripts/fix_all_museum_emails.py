#!/usr/bin/env python3
"""
=== FIX ALL MUSEUM EMAILS ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Analyze museum_emails CSV, find all suspicious/broken emails, re-scrape, update CSV

FEATURES:
- Detect suspicious emails (concatenation, numeric prefixes, etc.)
- Re-scrape websites using fixed text_utils.py
- Maximum parallelism (50-100 workers)
- Update museum_emails CSV with clean emails
- Keep email generation data (subject, email_1, etc.)

USAGE:
1. Run: python fix_all_museum_emails.py
2. Output: museum_emails_CLEAN_YYYYMMDD_HHMMSS.csv
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
import re
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import fixed email extraction
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.text_utils import extract_emails_from_html, is_valid_email, VALID_TLDS

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
MUSEUM_EMAILS_CSV = Path(__file__).parent.parent.parent / "openai" / "results" / "museum_emails_20251115_155304.csv"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "openai" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config
MAX_WORKERS = 100  # Maximum parallelism
TIMEOUT = 10  # seconds


def is_suspicious_email(email: str) -> tuple[bool, List[str]]:
    """
    Check if email is suspicious/broken

    Returns:
        (is_suspicious, issues_list)
    """
    if not email or '@' not in email:
        return True, ['invalid_format']

    issues = []

    # Pattern 1: Has phone number (6+ consecutive digits)
    if re.search(r'\d{6,}', email):
        issues.append('has_phone')

    # Pattern 2: Starts with digit sequence
    if re.match(r'^[\d\-]+[a-z]', email):
        issues.append('starts_with_digits')

    # Pattern 3: TLD longer than 3 chars or concatenated
    # Check if domain ends with text after valid TLD
    if '@' in email:
        try:
            domain = email.split('@')[1]

            # Check for concatenation: .tld + extra letters
            for tld in sorted(VALID_TLDS, key=len, reverse=True):
                pattern = rf'\.{re.escape(tld)}[a-z]+'
                if re.search(pattern, domain):
                    issues.append('concatenated_domain')
                    break

            # Check if TLD is valid
            tld = domain.split('.')[-1]
            if tld not in VALID_TLDS:
                issues.append('invalid_tld')
        except:
            issues.append('parse_error')

    # Pattern 4: Contains common concatenation patterns
    concat_patterns = [
        r'\.com[a-z]+$',
        r'\.de[a-z]+$',
        r'\.uk[a-z]+$',
        r'\.nl[a-z]+$',
        r'\.ch[a-z]+$',
        r'\.fr[a-z]+$',
        r'\.pl[a-z]+$',
        r'\.cz[a-z]+$',
        r'\.hu[a-z]+$',
    ]

    for pattern in concat_patterns:
        if re.search(pattern, email):
            if 'concatenated_domain' not in issues:
                issues.append('concatenated_domain')
            break

    # Pattern 5: Has appended text patterns
    appended_patterns = [
        r'@.*\.se[a-z]+$',
        r'@.*\.info[a-z]+$',
        r'@gmail\.com[a-z]+$',
        r'@hotmail\.co\.uk[a-z]+$',
    ]

    for pattern in appended_patterns:
        if re.search(pattern, email):
            if 'concatenated_domain' not in issues:
                issues.append('appended_text')
            break

    return len(issues) > 0, issues


class MuseumEmailFixer:
    """Re-scrape and fix museum emails"""

    def __init__(self):
        self.processed_count = 0
        self.fixed_count = 0
        self.failed_count = 0
        self.already_clean_count = 0
        self._lock = threading.Lock()

    def scrape_emails(self, website: str) -> List[str]:
        """Scrape emails from website using fixed extraction"""

        if not website or pd.isna(website):
            return []

        # Normalize URL
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            # Fetch homepage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(website, headers=headers, timeout=TIMEOUT)

            if response.status_code != 200:
                return []

            # Extract emails using FIXED text_utils
            html = response.text
            emails = extract_emails_from_html(html)

            return emails

        except Exception as e:
            logger.debug(f"Failed to scrape {website}: {e}")
            return []


def main():
    """Main fixing pipeline"""
    logger.info("=== FIX ALL MUSEUM EMAILS STARTED ===")

    # Step 1: Load museum emails CSV
    logger.info(f"Loading museum emails: {MUSEUM_EMAILS_CSV}")
    df = pd.read_csv(MUSEUM_EMAILS_CSV)

    logger.info(f"Total emails in CSV: {len(df)}")

    # Step 2: Analyze emails for issues
    logger.info("Analyzing emails for suspicious patterns...")

    suspicious_rows = []
    clean_rows = []

    for idx, row in df.iterrows():
        email = row['email']
        is_susp, issues = is_suspicious_email(email)

        if is_susp:
            suspicious_rows.append({
                'index': idx,
                'email': email,
                'website': row['website'],
                'issues': issues,
                'row_data': row
            })
        else:
            clean_rows.append(row)

    logger.info(f"Clean emails: {len(clean_rows)}")
    logger.info(f"Suspicious emails: {len(suspicious_rows)}")

    if len(suspicious_rows) == 0:
        logger.info("No suspicious emails found! CSV is already clean.")
        return

    # Show issue breakdown
    all_issues = []
    for item in suspicious_rows:
        all_issues.extend(item['issues'])

    from collections import Counter
    issue_counts = Counter(all_issues)

    logger.info("\n=== ISSUES BREAKDOWN ===")
    for issue, count in issue_counts.most_common():
        logger.info(f"{issue}: {count}")

    # Step 3: Re-scrape suspicious websites
    logger.info(f"\nRe-scraping {len(suspicious_rows)} websites with {MAX_WORKERS} workers...")

    fixer = MuseumEmailFixer()
    start_time = time.time()

    # Group by website to avoid duplicate scraping
    website_to_rows = {}
    for item in suspicious_rows:
        website = item['website']
        if website not in website_to_rows:
            website_to_rows[website] = []
        website_to_rows[website].append(item)

    logger.info(f"Unique websites to scrape: {len(website_to_rows)}")

    # Scrape in parallel
    website_to_emails = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_website = {
            executor.submit(fixer.scrape_emails, website): website
            for website in website_to_rows.keys()
        }

        completed = 0
        for future in as_completed(future_to_website):
            website = future_to_website[future]
            emails = future.result()
            website_to_emails[website] = emails

            completed += 1
            if completed % 50 == 0:
                logger.info(f"Progress: {completed}/{len(website_to_rows)} websites scraped")

    # Step 4: Update emails in rows
    logger.info("\nUpdating emails in rows...")

    fixed_rows = []

    for website, items in website_to_rows.items():
        new_emails = website_to_emails.get(website, [])

        for item in items:
            old_email = item['email']
            row_data = item['row_data'].copy()

            if new_emails:
                # Strategy: Pick best matching email or first valid one
                # Try to find email that matches old one (e.g., same domain)
                best_email = None

                # Try to match domain
                if '@' in old_email:
                    old_domain = old_email.split('@')[1].split('.')[0]  # Get base domain
                    for new_email in new_emails:
                        if '@' in new_email and old_domain in new_email:
                            best_email = new_email
                            break

                # If no match, take first email
                if not best_email:
                    best_email = new_emails[0]

                row_data['email'] = best_email
                row_data['_old_email'] = old_email
                row_data['_fixed'] = 'YES'

                fixer.fixed_count += 1
                logger.debug(f"FIXED: {old_email} -> {best_email}")
            else:
                # Keep old email if scraping failed
                row_data['_fixed'] = 'NO'
                fixer.failed_count += 1
                logger.debug(f"FAILED: {old_email} (no new emails found)")

            fixed_rows.append(row_data)

    # Step 5: Merge clean + fixed rows
    logger.info("\nMerging clean and fixed emails...")

    df_clean = pd.DataFrame(clean_rows)
    df_clean['_fixed'] = 'ALREADY_CLEAN'
    df_clean['_old_email'] = ''

    df_fixed = pd.DataFrame(fixed_rows)

    df_final = pd.concat([df_clean, df_fixed], ignore_index=True)

    # Reorder columns (put _fixed and _old_email at end)
    cols = [c for c in df_final.columns if not c.startswith('_')]
    meta_cols = [c for c in df_final.columns if c.startswith('_')]
    df_final = df_final[cols + meta_cols]

    # Step 6: Save updated CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = OUTPUT_DIR / f"museum_emails_CLEAN_{timestamp}.csv"
    df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Step 7: Statistics
    elapsed = time.time() - start_time

    logger.info("\n=== FIX COMPLETE ===")
    logger.info(f"Total emails: {len(df_final)}")
    logger.info(f"Already clean: {len(clean_rows)}")
    logger.info(f"Fixed: {fixer.fixed_count}")
    logger.info(f"Failed to fix: {fixer.failed_count}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output: {output_csv}")

    # Show samples
    logger.info("\n=== SAMPLE FIXED EMAILS (First 10) ===")
    fixed_samples = df_final[df_final['_fixed'] == 'YES'].head(10)
    for _, row in fixed_samples.iterrows():
        logger.info(f"OLD: {row['_old_email']}")
        logger.info(f"NEW: {row['email']}")
        logger.info(f"Museum: {row['name']}")
        logger.info("---")


if __name__ == "__main__":
    main()
