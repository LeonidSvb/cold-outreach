#!/usr/bin/env python3
"""
=== LOCAL BUSINESSES EMAIL PROCESSOR ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Process US local businesses CSV: clean emails, verify, split multi-emails, merge with landscaping

FEATURES:
- Email cleanup (URL encoding, concatenation, remove-this patterns)
- Multi-email splitting (one row per email)
- mails.so API verification with rate limiting
- Merge with existing landscaping file
- Icebreaker generation using gpt-4o-mini
- Output: deliverable CSV + phone-only CSV

USAGE:
1. Run: python process_local_businesses.py
2. Results in results/
"""

import sys
import re
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
from openai import OpenAI

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

# Load environment
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Configuration
CONFIG = {
    "MAILS_SO_API_KEY": "c6c76660-b774-4dcc-be3f-64cdb999e70f",
    "MAILS_SO_API_URL": "https://api.mails.so/v1/validate",
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "OPENAI_MODEL": "gpt-4o-mini",

    "FILE_LANDSCAPING": r"C:\Users\79818\Downloads\Master Sheet - 100 landscaping texas.csv",
    "FILE_US_1900": r"C:\Users\79818\Downloads\Master Sheet - US 1900 local biz+.csv",

    "RATE_LIMIT_DELAY": 0.5,  # seconds between API calls
    "TIMEOUT": 10,
    "BATCH_SIZE": 50,  # Process N emails at a time
}

# Email cleanup patterns
CLEANUP_PATTERNS = [
    # URL encoding
    (r'^%20+', ''),
    (r'%20', ''),

    # Concatenated text after email
    (r'@([a-zA-Z0-9\-\.]+\.[a-z]{2,})([a-z]{2,}.*?)$', r'@\1'),  # example: .comhoursavailable -> .com

    # Concatenated domains
    (r'@(.+?)\.(huhorizon)$', r'@\1.hu'),
    (r'@(.+?)\.(chder)$', r'@\1.ch'),
    (r'@(.+?)\.(ukregistered)$', r'@\1.uk'),
    (r'@(.+?)\.(nliban)$', r'@\1.nl'),
    (r'@(.+?)\.(chhorizon)$', r'@\1.ch'),
    (r'@(.+?)\.(dehorizon)$', r'@\1.de'),

    # Remove-this pattern
    (r'@remove-this\.', r'@'),
    (r'@remove\.', r'@'),

    # Phone numbers mixed with emails (remove phone part)
    (r'\(\d{3}\)\s*\d{3}-\d{4}', ''),
    (r'\d{3}-\d{3}-\d{4}', ''),
]


def clean_email(email: str) -> str:
    """
    Clean email address by applying cleanup patterns

    Args:
        email: Raw email string

    Returns:
        Cleaned email
    """
    if not email or pd.isna(email):
        return ""

    cleaned = email.strip()

    for pattern, replacement in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    # Additional cleanup
    cleaned = cleaned.strip().lower()

    # Validate basic email format
    if '@' not in cleaned or '.' not in cleaned.split('@')[-1]:
        return ""

    return cleaned


def split_multi_emails(email_str: str) -> List[str]:
    """
    Split comma/semicolon-separated emails into list

    Args:
        email_str: String potentially containing multiple emails

    Returns:
        List of individual emails
    """
    if not email_str or pd.isna(email_str):
        return []

    # Split by comma or semicolon
    emails = re.split(r'[,;]\s*', email_str)

    # Clean each email
    cleaned_emails = []
    for email in emails:
        cleaned = clean_email(email)
        if cleaned and '@' in cleaned:
            cleaned_emails.append(cleaned)

    return cleaned_emails


def verify_email(email: str) -> dict:
    """
    Verify email using mails.so API

    Args:
        email: Email to verify

    Returns:
        Verification result dict
    """
    try:
        headers = {"x-mails-api-key": CONFIG["MAILS_SO_API_KEY"]}
        params = {"email": email}

        response = requests.get(
            CONFIG["MAILS_SO_API_URL"],
            headers=headers,
            params=params,
            timeout=CONFIG["TIMEOUT"]
        )

        if response.status_code == 200:
            api_data = response.json().get("data", {})
            return {
                "status": "success",
                "result": api_data.get("result", "unknown"),
                "score": api_data.get("score", 0),
                "format_valid": api_data.get("isv_format", "unknown"),
                "domain_valid": api_data.get("isv_domain", "unknown"),
                "mx_valid": api_data.get("isv_mx", "unknown"),
                "is_disposable": api_data.get("is_disposable", "unknown"),
                "is_free": api_data.get("is_free", "unknown"),
                "provider": api_data.get("provider", ""),
            }
        else:
            logger.error(f"API error for {email}: {response.status_code}")
            return {"status": "error", "result": "error", "error": f"HTTP {response.status_code}"}

    except Exception as e:
        logger.error(f"Exception verifying {email}: {e}")
        return {"status": "error", "result": "error", "error": str(e)}


def generate_icebreaker(business_data: dict) -> str:
    """
    Generate personalized icebreaker using OpenAI gpt-4o-mini

    Args:
        business_data: Dict with business info

    Returns:
        Generated icebreaker text
    """
    client = OpenAI(api_key=CONFIG["OPENAI_API_KEY"])

    # Extract data with fallbacks
    company_name = business_data.get('name', 'your business')
    city = business_data.get('city', '')
    state = business_data.get('state', '')
    category = business_data.get('niche', '')
    rating = business_data.get('rating', '')
    review_count = business_data.get('reviews', 0)
    business_type = business_data.get('business_summary', '')
    owner_name = business_data.get('owner_name', '')

    # Build prompt based on user's template
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
            model=CONFIG["OPENAI_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )

        icebreaker = response.choices[0].message.content.strip()

        # Remove quotes if AI added them
        icebreaker = icebreaker.strip('"').strip("'")

        return icebreaker

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return ""


def process_us_1900_file(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process US 1900 file: clean emails, split multi-emails, verify

    Args:
        df: Input DataFrame

    Returns:
        Processed DataFrame with verified emails
    """
    logger.info("Processing US 1900 file...")

    # Step 1: Split multi-email rows
    logger.info("Step 1: Splitting multi-email rows...")
    expanded_rows = []

    for idx, row in df.iterrows():
        email_str = row['email']
        emails = split_multi_emails(email_str)

        if not emails:
            # No valid email - keep row for phone-only file
            row_copy = row.copy()
            row_copy['email'] = ""
            row_copy['email_status'] = "no_valid_email"
            expanded_rows.append(row_copy)
        else:
            # Create one row per email
            for email in emails:
                row_copy = row.copy()
                row_copy['email'] = email
                row_copy['email_status'] = "pending_verification"
                expanded_rows.append(row_copy)

    df_expanded = pd.DataFrame(expanded_rows)
    logger.info(f"Expanded {len(df)} rows into {len(df_expanded)} rows")

    # Step 2: Verify emails
    logger.info("Step 2: Verifying emails via mails.so API...")
    verified_count = 0

    for idx, row in df_expanded.iterrows():
        email = row['email']

        if not email or row['email_status'] == "no_valid_email":
            continue

        if verified_count % 50 == 0:
            logger.info(f"Verified {verified_count}/{len(df_expanded[df_expanded['email'] != ''])} emails...")

        verification = verify_email(email)

        # Add verification columns
        df_expanded.at[idx, 'verification_result'] = verification.get('result', 'unknown')
        df_expanded.at[idx, 'verification_score'] = verification.get('score', 0)
        df_expanded.at[idx, 'format_valid'] = verification.get('format_valid', 'unknown')
        df_expanded.at[idx, 'domain_valid'] = verification.get('domain_valid', 'unknown')
        df_expanded.at[idx, 'mx_valid'] = verification.get('mx_valid', 'unknown')
        df_expanded.at[idx, 'is_disposable'] = verification.get('is_disposable', 'unknown')
        df_expanded.at[idx, 'provider'] = verification.get('provider', '')

        verified_count += 1

        # Rate limiting
        time.sleep(CONFIG["RATE_LIMIT_DELAY"])

    logger.info(f"Verification complete. Total verified: {verified_count}")

    return df_expanded


def generate_icebreakers_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate icebreakers for all deliverable emails

    Args:
        df: DataFrame with verified emails

    Returns:
        DataFrame with icebreaker column added
    """
    logger.info("Generating icebreakers for deliverable emails...")

    deliverable = df[df['verification_result'] == 'deliverable'].copy()
    logger.info(f"Found {len(deliverable)} deliverable emails")

    df['icebreaker'] = ""
    df['icebreaker_status'] = "not_generated"

    for idx, row in deliverable.iterrows():
        logger.info(f"Generating icebreaker {idx+1}/{len(deliverable)}: {row['email']}")

        business_data = {
            'name': row.get('name', ''),
            'city': row.get('city', ''),
            'state': row.get('state', ''),
            'niche': row.get('niche', ''),
            'rating': row.get('rating', ''),
            'reviews': row.get('reviews', 0),
            'business_summary': row.get('business_summary', ''),
            'owner_name': ''  # Not provided in US 1900 file
        }

        icebreaker = generate_icebreaker(business_data)

        if icebreaker:
            df.at[idx, 'icebreaker'] = icebreaker
            df.at[idx, 'icebreaker_status'] = "success"
        else:
            df.at[idx, 'icebreaker_status'] = "failed"

        # Rate limiting for OpenAI
        time.sleep(0.3)

    return df


def main():
    """Main execution function"""
    logger.info("="*70)
    logger.info("LOCAL BUSINESSES EMAIL PROCESSOR STARTED")
    logger.info("="*70)

    start_time = datetime.now()

    try:
        # Read files
        logger.info("Reading input files...")
        df_landscaping = pd.read_csv(CONFIG["FILE_LANDSCAPING"], encoding='utf-8-sig')
        df_us_1900 = pd.read_csv(CONFIG["FILE_US_1900"], encoding='utf-8')

        logger.info(f"Landscaping file: {len(df_landscaping)} rows")
        logger.info(f"US 1900 file: {len(df_us_1900)} rows")

        # Process US 1900 file
        df_us_processed = process_us_1900_file(df_us_1900)

        # Generate icebreakers for US 1900
        df_us_processed = generate_icebreakers_batch(df_us_processed)

        # Create output directory
        output_dir = Path(__file__).parent.parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # File 1: Deliverable emails with icebreakers (US 1900 only)
        deliverable = df_us_processed[df_us_processed['verification_result'] == 'deliverable'].copy()
        output_deliverable = output_dir / f"us_1900_DELIVERABLE_with_icebreakers_{timestamp}.csv"
        deliverable.to_csv(output_deliverable, index=False, encoding='utf-8-sig')
        logger.info(f"Saved deliverable file: {output_deliverable}")
        logger.info(f"  Rows: {len(deliverable)}")

        # File 2: Merged file (Landscaping + US 1900 deliverable)
        # Align columns before merge
        common_cols = ['name', 'email', 'phone', 'website', 'city', 'state', 'rating', 'icebreaker']

        # Prepare landscaping file
        df_landscaping_aligned = pd.DataFrame()
        df_landscaping_aligned['name'] = df_landscaping.get('\ufeff"title"', df_landscaping.get('title', ''))
        df_landscaping_aligned['email'] = df_landscaping['emails']
        df_landscaping_aligned['phone'] = df_landscaping['phone']
        df_landscaping_aligned['website'] = df_landscaping['website']
        df_landscaping_aligned['city'] = df_landscaping['city']
        df_landscaping_aligned['state'] = df_landscaping['state']
        df_landscaping_aligned['rating'] = df_landscaping['totalScore']
        df_landscaping_aligned['icebreaker'] = df_landscaping['icebreaker']
        df_landscaping_aligned['source'] = 'landscaping_texas'

        # Prepare US 1900 file
        df_us_aligned = deliverable[['name', 'email', 'phone', 'website', 'city', 'state', 'rating', 'icebreaker']].copy()
        df_us_aligned['source'] = 'us_1900_local_biz'

        # Merge
        df_merged = pd.concat([df_landscaping_aligned, df_us_aligned], ignore_index=True)
        output_merged = output_dir / f"MERGED_deliverable_all_{timestamp}.csv"
        df_merged.to_csv(output_merged, index=False, encoding='utf-8-sig')
        logger.info(f"Saved merged file: {output_merged}")
        logger.info(f"  Rows: {len(df_merged)} ({len(df_landscaping_aligned)} landscaping + {len(df_us_aligned)} US 1900)")

        # File 3: Phone-only (no valid email OR verification failed)
        phone_only = df_us_processed[
            (df_us_processed['email'] == '') |
            (df_us_processed['verification_result'].isin(['undeliverable', 'unknown', 'error']))
        ].copy()

        # Keep only rows with phone numbers
        phone_only = phone_only[phone_only['phone'].notna() & (phone_only['phone'] != '')].copy()

        output_phone = output_dir / f"us_1900_PHONE_ONLY_{timestamp}.csv"
        phone_only[['name', 'phone', 'website', 'city', 'state', 'address', 'rating', 'reviews', 'niche', 'business_summary']].to_csv(
            output_phone, index=False, encoding='utf-8-sig'
        )
        logger.info(f"Saved phone-only file: {output_phone}")
        logger.info(f"  Rows: {len(phone_only)}")

        # Summary
        duration = (datetime.now() - start_time).total_seconds()

        logger.info("="*70)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total US 1900 rows processed: {len(df_us_processed)}")
        logger.info(f"Deliverable emails: {len(deliverable)}")
        logger.info(f"Phone-only contacts: {len(phone_only)}")
        logger.info(f"Merged total: {len(df_merged)}")
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
