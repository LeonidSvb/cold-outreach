#!/usr/bin/env python3
"""
=== EMAIL VERIFICATION SCRIPT ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE:
Verify email addresses using mails.so API to check deliverability

FEATURES:
- CSV input with automatic email column detection
- API verification with rate limiting
- Detailed verification results (deliverable, syntax, domain checks)
- Progress tracking and error handling
- Timestamped output files

USAGE:
1. Configure CONFIG section with API key and input file
2. Run: python verify_emails.py
3. Results saved to results/verified_emails_YYYYMMDD_HHMMSS.csv

IMPROVEMENTS:
v1.0.0 - Initial version with mails.so API integration
"""

import sys
import csv
import time
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

# Configuration
CONFIG = {
    "API_KEY": "c6c76660-b774-4dcc-be3f-64cdb999e70f",
    "API_URL": "https://api.mails.so/v1/validate",
    "INPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\modules\openai\results\museum_emails_CLEAN_20251115_163418.csv",
    "EMAIL_COLUMN": "email",  # Column name containing emails
    "OFFSET": 500,  # Skip first N emails (already verified)
    "LIMIT": 300,  # Maximum number of emails to verify (None for all)
    "RATE_LIMIT_DELAY": 0.5,  # Delay between API requests in seconds
    "TIMEOUT": 10,  # API request timeout in seconds
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_verified": 0,
    "valid_emails": 0,
    "invalid_emails": 0,
    "api_errors": 0,
    "start_time": None,
    "end_time": None
}


def verify_email(email: str) -> dict:
    """
    Verify single email using mails.so API

    Args:
        email: Email address to verify

    Returns:
        dict with verification results
    """
    try:
        headers = {
            "x-mails-api-key": CONFIG["API_KEY"]
        }

        params = {
            "email": email
        }

        logger.debug(f"Verifying email: {email}")

        response = requests.get(
            CONFIG["API_URL"],
            headers=headers,
            params=params,
            timeout=CONFIG["TIMEOUT"]
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Verification result for {email}: {data}")
            return {
                "status": "success",
                "data": data
            }
        else:
            logger.error(f"API error for {email}: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "error": f"API returned {response.status_code}",
                "data": None
            }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout verifying {email}")
        return {
            "status": "error",
            "error": "Request timeout",
            "data": None
        }
    except Exception as e:
        logger.error(f"Exception verifying {email}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }


def process_csv(input_file: str) -> list:
    """
    Read CSV and verify all emails

    Args:
        input_file: Path to input CSV file

    Returns:
        List of dicts with original data + verification results
    """
    results = []

    try:
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Apply offset and limit if specified
        total_rows = len(rows)
        offset = CONFIG.get("OFFSET", 0)
        limit = CONFIG.get("LIMIT")

        if offset > 0:
            rows = rows[offset:]
            logger.info(f"Found {total_rows} rows, skipped first {offset}")

        if limit and limit < len(rows):
            rows = rows[:limit]
            logger.info(f"Processing {len(rows)} rows (emails {offset+1} to {offset+len(rows)})")
        else:
            logger.info(f"Processing {len(rows)} rows from offset {offset}")

        for idx, row in enumerate(rows, 1):
            email = row.get(CONFIG["EMAIL_COLUMN"], "").strip()

            if not email:
                logger.warning(f"Row {idx}: No email found")
                row["verification_status"] = "missing"
                row["is_valid"] = "N/A"
                row["verification_error"] = "No email provided"
                results.append(row)
                continue

            logger.info(f"Processing {idx}/{len(rows)}: {email}")

            # Verify email
            verification = verify_email(email)

            if verification["status"] == "success":
                api_response = verification["data"]

                # API returns data inside 'data' key
                data = api_response.get("data", {})

                # Extract key fields from API response
                row["verification_status"] = "verified"
                row["result"] = data.get("result", "unknown")  # deliverable/undeliverable/risky/unknown
                row["score"] = data.get("score", 0)
                row["format_valid"] = data.get("isv_format", "unknown")
                row["domain_valid"] = data.get("isv_domain", "unknown")
                row["mx_valid"] = data.get("isv_mx", "unknown")
                row["is_disposable"] = data.get("is_disposable", "unknown")
                row["is_free_provider"] = data.get("is_free", "unknown")
                row["provider"] = data.get("provider", "")
                row["mx_record"] = data.get("mx_record", "")
                row["verification_error"] = ""

                if data.get("result") == "deliverable":
                    SCRIPT_STATS["valid_emails"] += 1
                else:
                    SCRIPT_STATS["invalid_emails"] += 1

            else:
                row["verification_status"] = "error"
                row["result"] = "error"
                row["verification_error"] = verification.get("error", "Unknown error")
                SCRIPT_STATS["api_errors"] += 1

            SCRIPT_STATS["total_verified"] += 1
            results.append(row)

            # Rate limiting
            if idx < len(rows):
                time.sleep(CONFIG["RATE_LIMIT_DELAY"])

        return results

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        raise
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise


def save_results(results: list, output_dir: Path) -> str:
    """
    Save verified results to CSV

    Args:
        results: List of dicts with verification results
        output_dir: Directory to save results

    Returns:
        Path to output file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"verified_emails_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return None

    # Get all fieldnames (original + verification columns)
    fieldnames = list(results[0].keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("EMAIL VERIFICATION SCRIPT STARTED")
    logger.info("="*60)

    SCRIPT_STATS["start_time"] = datetime.now()

    try:
        # Validate config
        if not CONFIG["API_KEY"]:
            raise ValueError("API_KEY not configured")

        if not Path(CONFIG["INPUT_FILE"]).exists():
            raise FileNotFoundError(f"Input file not found: {CONFIG['INPUT_FILE']}")

        # Create results directory
        results_dir = Path(__file__).parent.parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Process CSV
        logger.info(f"Processing file: {CONFIG['INPUT_FILE']}")
        results = process_csv(CONFIG["INPUT_FILE"])

        # Save results
        output_file = save_results(results, results_dir)

        # Print summary
        SCRIPT_STATS["end_time"] = datetime.now()
        duration = (SCRIPT_STATS["end_time"] - SCRIPT_STATS["start_time"]).total_seconds()

        logger.info("="*60)
        logger.info("VERIFICATION COMPLETE")
        logger.info("="*60)
        logger.info(f"Total processed: {SCRIPT_STATS['total_verified']}")
        logger.info(f"Valid emails: {SCRIPT_STATS['valid_emails']}")
        logger.info(f"Invalid emails: {SCRIPT_STATS['invalid_emails']}")
        logger.info(f"API errors: {SCRIPT_STATS['api_errors']}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Output file: {output_file}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
