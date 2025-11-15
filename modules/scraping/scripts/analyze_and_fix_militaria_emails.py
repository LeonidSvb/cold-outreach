#!/usr/bin/env python3
"""
=== ANALYZE AND FIX MILITARIA STORE EMAILS ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
1. Extract militaria_store emails from Soviet Boots CSV
2. Analyze for suspicious/broken patterns
3. Re-scrape if needed
4. Output clean CSV ready for verification

USAGE:
1. Run: python analyze_and_fix_militaria_emails.py
2. Output: militaria_stores_CLEAN_YYYYMMDD_HHMMSS.csv
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
SOVIET_BOOTS_CSV = Path(r"C:\Users\79818\Downloads\Soviet Boots - Sheet3.csv")
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config
MAX_WORKERS = 100
TIMEOUT = 10


def is_suspicious_email(email: str) -> tuple[bool, List[str]]:
    """Check if email is suspicious/broken"""
    if not email or '@' not in email:
        return True, ['invalid_format']

    issues = []

    # Pattern 1: Has phone number (6+ consecutive digits)
    if re.search(r'\d{6,}', email):
        issues.append('has_phone')

    # Pattern 2: Starts with digit sequence
    if re.match(r'^[\d\-]+[a-z]', email):
        issues.append('starts_with_digits')

    # Pattern 3: Check for concatenation
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

    return len(issues) > 0, issues


class EmailFixer:
    """Re-scrape and fix emails"""

    def __init__(self):
        self.processed_count = 0
        self.fixed_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()

    def scrape_emails(self, website: str) -> List[str]:
        """Scrape emails from website using fixed extraction"""
        if not website or pd.isna(website):
            return []

        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(website, headers=headers, timeout=TIMEOUT)

            if response.status_code != 200:
                return []

            html = response.text
            emails = extract_emails_from_html(html)
            return emails

        except Exception as e:
            return []


def main():
    """Main pipeline"""
    logger.info("=== ANALYZE AND FIX MILITARIA STORE EMAILS ===")

    # Step 1: Load and filter militaria_store
    logger.info(f"Loading Soviet Boots CSV: {SOVIET_BOOTS_CSV}")
    df = pd.read_csv(SOVIET_BOOTS_CSV)

    df_militaria = df[df['type'] == 'militaria_store'].copy()
    logger.info(f"Found {len(df_militaria)} militaria_store records")

    # Step 2: Expand multiple emails to separate rows
    logger.info("Expanding multiple emails to separate rows...")
    rows_list = []

    for _, row in df_militaria.iterrows():
        emails_str = str(row['emails'])

        if pd.isna(row['emails']) or not emails_str.strip():
            continue

        emails = [e.strip() for e in emails_str.split(',') if e.strip()]

        for email in emails:
            new_row = row.copy()
            new_row['email'] = email
            rows_list.append(new_row)

    df_expanded = pd.DataFrame(rows_list)
    logger.info(f"Expanded to {len(df_expanded)} email contacts")

    # Step 3: Analyze for suspicious patterns
    logger.info("Analyzing emails for suspicious patterns...")

    suspicious_rows = []
    clean_rows = []

    for idx, row in df_expanded.iterrows():
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

    if len(suspicious_rows) > 0:
        # Show issue breakdown
        from collections import Counter
        all_issues = []
        for item in suspicious_rows:
            all_issues.extend(item['issues'])

        issue_counts = Counter(all_issues)

        logger.info("\n=== ISSUES BREAKDOWN ===")
        for issue, count in issue_counts.most_common():
            logger.info(f"{issue}: {count}")

        # Step 4: Re-scrape suspicious websites
        logger.info(f"\nRe-scraping {len(suspicious_rows)} suspicious emails with {MAX_WORKERS} workers...")

        fixer = EmailFixer()
        start_time = time.time()

        # Group by website
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

        # Step 5: Update emails
        logger.info("\nUpdating emails in rows...")

        fixed_rows = []

        for website, items in website_to_rows.items():
            new_emails = website_to_emails.get(website, [])

            for item in items:
                old_email = item['email']
                row_data = item['row_data'].copy()

                if new_emails:
                    # Match domain or take first
                    best_email = None

                    if '@' in old_email:
                        old_domain = old_email.split('@')[1].split('.')[0]
                        for new_email in new_emails:
                            if '@' in new_email and old_domain in new_email:
                                best_email = new_email
                                break

                    if not best_email:
                        best_email = new_emails[0]

                    row_data['email'] = best_email
                    row_data['_old_email'] = old_email
                    row_data['_fixed'] = 'YES'
                    fixer.fixed_count += 1
                else:
                    row_data['_fixed'] = 'NO'
                    fixer.failed_count += 1

                fixed_rows.append(row_data)

        elapsed = time.time() - start_time
        logger.info(f"Re-scraping complete in {elapsed:.1f} seconds")

    else:
        logger.info("No suspicious emails found!")
        fixed_rows = []

    # Step 6: Merge clean + fixed
    logger.info("\nMerging clean and fixed emails...")

    df_clean = pd.DataFrame(clean_rows)
    df_clean['_fixed'] = 'CLEAN'
    df_clean['_old_email'] = ''

    if len(fixed_rows) > 0:
        df_fixed = pd.DataFrame(fixed_rows)
        df_final = pd.concat([df_clean, df_fixed], ignore_index=True)
    else:
        df_final = df_clean

    # Reorder columns
    cols = [c for c in df_final.columns if not c.startswith('_')]
    meta_cols = [c for c in df_final.columns if c.startswith('_')]
    df_final = df_final[cols + meta_cols]

    # Step 7: Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = OUTPUT_DIR / f"militaria_stores_CLEAN_{timestamp}.csv"
    df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Step 8: Statistics
    logger.info("\n=== ANALYSIS COMPLETE ===")
    logger.info(f"Total emails: {len(df_final)}")
    logger.info(f"Clean: {len(clean_rows)}")
    if len(suspicious_rows) > 0:
        logger.info(f"Fixed: {fixer.fixed_count}")
        logger.info(f"Failed to fix: {fixer.failed_count}")
    logger.info(f"Output: {output_csv}")

    # Show samples
    if len(suspicious_rows) > 0 and fixer.fixed_count > 0:
        logger.info("\n=== SAMPLE FIXED EMAILS (First 10) ===")
        fixed_samples = df_final[df_final['_fixed'] == 'YES'].head(10)
        for _, row in fixed_samples.iterrows():
            logger.info(f"OLD: {row['_old_email']}")
            logger.info(f"NEW: {row['email']}")
            logger.info(f"Store: {row['name']}")
            logger.info("---")


if __name__ == "__main__":
    main()
