#!/usr/bin/env python3
"""
=== BUSINESS EMAIL FINDER & VERIFIER ===
Version: 1.0.0 | Created: 2025-11-10

PURPOSE:
Find and verify business emails for local businesses using pattern generation + SMTP verification

FEATURES:
- Generate common business email patterns (info@, contact@, service@, etc.)
- SMTP verification (100% FREE - no API costs)
- DNS MX record checking
- Catch-all domain detection
- Rate limiting to avoid blocks
- Industry-specific patterns (HVAC, electricians, plumbers)

HOW IT WORKS:
1. Load parquet/CSV with business websites
2. Extract domain from website URL
3. Generate common email patterns (info@domain.com, contact@domain.com, etc.)
4. Verify each pattern via SMTP (does email exist?)
5. Return valid emails + verification status

SMTP VERIFICATION (FREE):
- DNS MX lookup → find mail server
- SMTP connection → connect to server
- RCPT TO command → check if email exists
- Close without sending → 100% free

USAGE:
    # Test mode (10 businesses)
    python business_email_finder.py --input all_leads.parquet --output emails.csv --test

    # Full mode (all businesses)
    python business_email_finder.py --input all_leads.parquet --output emails.csv

    # Custom patterns only
    python business_email_finder.py --input all_leads.parquet --output emails.csv --patterns info contact

BENCHMARKS:
    - DNS MX lookup: ~50ms
    - SMTP verification: ~200-400ms per email
    - Rate limiting: 2 sec delay between checks (safety)
    - 1000 businesses x 8 patterns = ~4 hours (with delays)

IMPROVEMENTS:
v1.0.0 - Initial version with SMTP verification
"""

import sys
import argparse
import pandas as pd
import time
import smtplib
import dns.resolver
import socket
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # Common business email patterns (order by popularity)
    "COMMON_PATTERNS": [
        "info",
        "contact",
        "hello",
        "sales",
        "support",
        "service",
        "office",
        "admin"
    ],

    # Industry-specific patterns
    "INDUSTRY_PATTERNS": {
        "hvac": ["service", "schedule", "appointments"],
        "electricians": ["service", "emergency", "schedule"],
        "plumbers": ["service", "emergency", "dispatch"],
        "restaurants": ["reservations", "catering", "events"],
        "contractors": ["estimates", "projects", "quotes"]
    },

    # SMTP settings
    "SMTP_TIMEOUT": 10,
    "SMTP_FROM_EMAIL": "verify@mydomain.com",
    "SMTP_HELO_DOMAIN": "mydomain.com",

    # Rate limiting (to avoid blocks)
    "RATE_LIMIT_DELAY": 2.0,  # seconds between checks
    "MAX_RETRIES": 2,

    # Verification settings
    "CHECK_CATCH_ALL": True,  # Detect domains that accept all emails
    "RANDOM_EMAIL_TEST": "randomstring12345xyz",

    # Processing
    "MAX_WORKERS": 5,  # Parallel workers (conservative to avoid blocks)
    "TEST_MODE_LIMIT": 10  # Number of businesses to test in test mode
}


# ============================================================================
# EMAIL VERIFICATION FUNCTIONS
# ============================================================================

def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from website URL

    Args:
        url: Website URL (e.g., https://www.acehvac.com/contact)

    Returns:
        Domain (e.g., acehvac.com) or None if invalid
    """
    try:
        if not url or pd.isna(url):
            return None

        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain if domain else None

    except Exception as e:
        logger.error(f"Failed to extract domain from {url}: {e}")
        return None


def verify_email_smtp(email: str) -> Dict:
    """
    Verify email existence via SMTP (FREE!)

    Process:
    1. Extract domain from email
    2. DNS MX lookup - find mail server
    3. SMTP connection - connect to server
    4. RCPT TO - check if email exists
    5. Close without sending

    Args:
        email: Email to verify (e.g., info@acehvac.com)

    Returns:
        {
            'email': email,
            'status': 'valid' | 'invalid' | 'unknown' | 'error',
            'code': SMTP code,
            'mx_host': mail server,
            'error': error message (if failed)
        }
    """
    try:
        # Extract domain
        domain = email.split('@')[1]

        # DNS MX lookup
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange).rstrip('.')
        except dns.resolver.NXDOMAIN:
            return {
                'email': email,
                'status': 'no_mx_record',
                'error': 'Domain has no mail server'
            }
        except dns.resolver.NoAnswer:
            return {
                'email': email,
                'status': 'no_mx_record',
                'error': 'No MX records found'
            }
        except Exception as e:
            return {
                'email': email,
                'status': 'dns_error',
                'error': f'DNS lookup failed: {str(e)}'
            }

        # SMTP verification
        try:
            server = smtplib.SMTP(timeout=CONFIG['SMTP_TIMEOUT'])
            server.set_debuglevel(0)  # Disable debug output

            # Connect
            server.connect(mx_host)
            server.helo(CONFIG['SMTP_HELO_DOMAIN'])
            server.mail(CONFIG['SMTP_FROM_EMAIL'])

            # Check if email exists
            code, message = server.rcpt(email)
            server.quit()

            # Interpret SMTP code
            if code == 250:
                status = 'valid'
            elif code in [550, 551, 553]:
                status = 'invalid'
            elif code in [450, 451, 452]:
                status = 'temporary_error'
            else:
                status = 'unknown'

            return {
                'email': email,
                'status': status,
                'code': code,
                'mx_host': mx_host,
                'message': message.decode() if isinstance(message, bytes) else str(message)
            }

        except smtplib.SMTPServerDisconnected:
            return {
                'email': email,
                'status': 'smtp_error',
                'error': 'Server disconnected'
            }
        except smtplib.SMTPConnectError:
            return {
                'email': email,
                'status': 'smtp_error',
                'error': 'Connection failed'
            }
        except socket.timeout:
            return {
                'email': email,
                'status': 'timeout',
                'error': 'Mail server not responding'
            }
        except Exception as e:
            return {
                'email': email,
                'status': 'smtp_error',
                'error': str(e)
            }

    except Exception as e:
        return {
            'email': email,
            'status': 'error',
            'error': str(e)
        }


def check_catch_all(domain: str) -> bool:
    """
    Check if domain accepts all emails (catch-all)

    Tests a random non-existent email to see if domain accepts it

    Args:
        domain: Domain to check (e.g., acehvac.com)

    Returns:
        True if catch-all detected
    """
    random_email = f"{CONFIG['RANDOM_EMAIL_TEST']}@{domain}"
    result = verify_email_smtp(random_email)

    return result['status'] == 'valid'


def generate_email_patterns(domain: str, niche: Optional[str] = None) -> List[str]:
    """
    Generate common business email patterns for domain

    Args:
        domain: Business domain (e.g., acehvac.com)
        niche: Business niche/industry (e.g., 'hvac', 'electricians')

    Returns:
        List of email addresses to verify
    """
    patterns = CONFIG['COMMON_PATTERNS'].copy()

    # Add industry-specific patterns
    if niche and niche.lower() in CONFIG['INDUSTRY_PATTERNS']:
        industry_patterns = CONFIG['INDUSTRY_PATTERNS'][niche.lower()]
        patterns.extend(industry_patterns)

    # Remove duplicates while preserving order
    seen = set()
    unique_patterns = []
    for pattern in patterns:
        if pattern not in seen:
            seen.add(pattern)
            unique_patterns.append(pattern)

    # Generate emails
    emails = [f"{pattern}@{domain}" for pattern in unique_patterns]

    return emails


# ============================================================================
# BUSINESS PROCESSING
# ============================================================================

def process_business(row: Dict) -> Dict:
    """
    Process single business - generate and verify emails

    Args:
        row: Business data (from dataframe row)

    Returns:
        Result dict with verified emails
    """
    start_time = time.time()

    result = {
        'name': row.get('name', ''),
        'website': row.get('website', ''),
        'niche': row.get('niche', ''),
        'city': row.get('city', ''),
        'state': row.get('state', ''),
        'domain': None,
        'patterns_tested': 0,
        'valid_emails': '',
        'invalid_emails': '',
        'catch_all': False,
        'status': 'pending',
        'processing_time': 0
    }

    # Extract domain
    domain = extract_domain(row.get('website'))
    if not domain:
        result['status'] = 'no_domain'
        result['processing_time'] = time.time() - start_time
        return result

    result['domain'] = domain

    # Check catch-all (optional)
    if CONFIG['CHECK_CATCH_ALL']:
        result['catch_all'] = check_catch_all(domain)
        if result['catch_all']:
            logger.warning(f"{domain} - Catch-all detected (accepts all emails)")

    # Generate email patterns
    emails_to_test = generate_email_patterns(domain, row.get('niche'))
    result['patterns_tested'] = len(emails_to_test)

    valid_emails = []
    invalid_emails = []

    # Verify each pattern
    for email in emails_to_test:
        verification = verify_email_smtp(email)

        if verification['status'] == 'valid':
            valid_emails.append(email)
            logger.info(f"[VALID] {email}")
        elif verification['status'] == 'invalid':
            invalid_emails.append(email)
            logger.debug(f"[INVALID] {email}")
        else:
            logger.debug(f"[{verification['status'].upper()}] {email}")

        # Rate limiting
        time.sleep(CONFIG['RATE_LIMIT_DELAY'])

    # Store results
    result['valid_emails'] = ', '.join(valid_emails)
    result['invalid_emails'] = ', '.join(invalid_emails)
    result['status'] = 'success'
    result['processing_time'] = time.time() - start_time

    return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    """
    Main function with argument parsing
    """
    parser = argparse.ArgumentParser(
        description='Business Email Finder & Verifier',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (10 businesses)
  python business_email_finder.py --input all_leads.parquet --output emails.csv --test

  # Full mode
  python business_email_finder.py --input all_leads.parquet --output emails.csv

  # Custom patterns
  python business_email_finder.py --input all_leads.parquet --output emails.csv --patterns info contact
        """
    )

    # Required arguments
    parser.add_argument('--input', required=True, help='Input parquet/CSV file with business data')
    parser.add_argument('--output', required=True, help='Output CSV file for verified emails')

    # Optional arguments
    parser.add_argument('--test', action='store_true', help='Test mode (process only 10 businesses)')
    parser.add_argument('--patterns', nargs='+', help='Custom email patterns to test (default: all common)')
    parser.add_argument('--workers', type=int, default=CONFIG['MAX_WORKERS'], help='Number of parallel workers')
    parser.add_argument('--delay', type=float, default=CONFIG['RATE_LIMIT_DELAY'], help='Delay between checks (seconds)')
    parser.add_argument('--no-catch-all', action='store_true', help='Skip catch-all detection')

    args = parser.parse_args()

    # Update config
    if args.patterns:
        CONFIG['COMMON_PATTERNS'] = args.patterns
    if args.no_catch_all:
        CONFIG['CHECK_CATCH_ALL'] = False
    CONFIG['RATE_LIMIT_DELAY'] = args.delay

    # Load input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {args.input}")
        return

    logger.info(f"Loading input file: {args.input}")

    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)

    # Filter only businesses with websites
    df_with_websites = df[df['website'].notna()].copy()

    # Test mode
    if args.test:
        df_with_websites = df_with_websites.head(CONFIG['TEST_MODE_LIMIT'])

    total = len(df_with_websites)

    print(f"\n{'='*80}")
    print(f"BUSINESS EMAIL FINDER & VERIFIER")
    print(f"{'='*80}")
    print(f"Input file:            {args.input}")
    print(f"Output file:           {args.output}")
    print(f"Total businesses:      {len(df)}")
    print(f"With websites:         {total}")
    print(f"Mode:                  {'TEST (10 businesses)' if args.test else 'FULL'}")
    print(f"")
    print(f"Configuration:")
    print(f"  Email patterns:      {', '.join(CONFIG['COMMON_PATTERNS'])}")
    print(f"  Check catch-all:     {CONFIG['CHECK_CATCH_ALL']}")
    print(f"  Rate limit delay:    {CONFIG['RATE_LIMIT_DELAY']} sec")
    print(f"  Workers:             {args.workers}")
    print(f"")
    print(f"Estimated time:        ~{total * len(CONFIG['COMMON_PATTERNS']) * CONFIG['RATE_LIMIT_DELAY'] / 60:.1f} min")
    print(f"{'='*80}\n")

    # Process businesses
    results = []
    processed = 0

    logger.info(f"Starting processing {total} businesses...")

    for idx, row in df_with_websites.iterrows():
        processed += 1

        print(f"\n[{processed}/{total}] Processing: {row['name']}")
        print(f"  Website: {row['website']}")

        result = process_business(row.to_dict())
        results.append(result)

        # Print summary
        if result['valid_emails']:
            print(f"  [+] Found {len(result['valid_emails'].split(','))} valid email(s): {result['valid_emails']}")
        else:
            print(f"  [-] No valid emails found")

        if result['catch_all']:
            print(f"  [!] Catch-all domain (accepts all emails)")

    # Save results
    logger.info(f"Saving results to: {args.output}")

    df_results = pd.DataFrame(results)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)

    # Statistics
    total_valid = sum(1 for r in results if r['valid_emails'])
    total_catch_all = sum(1 for r in results if r['catch_all'])

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Processed:             {len(results)}")
    print(f"Valid emails found:    {total_valid}")
    print(f"Catch-all domains:     {total_catch_all}")
    print(f"Success rate:          {total_valid/len(results)*100:.1f}%")
    print(f"")
    print(f"Results saved to:      {args.output}")
    print(f"{'='*80}\n")

    logger.info("Processing completed successfully")


if __name__ == "__main__":
    main()
