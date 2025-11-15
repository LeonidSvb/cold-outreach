#!/usr/bin/env python3
"""
=== VERIFY MILITARIA STORES EMAILS ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Verify militaria store emails using mails.so API

USAGE:
1. Run: python verify_militaria_stores.py
2. Results: verified_militaria_stores_YYYYMMDD_HHMMSS.csv
"""

import sys
import csv
import time
import requests
from pathlib import Path
from datetime import datetime
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Find latest militaria_stores_CLEAN file
RESULTS_DIR = Path(__file__).parent.parent.parent / "scraping" / "results"
militaria_files = glob.glob(str(RESULTS_DIR / "militaria_stores_CLEAN_*.csv"))
if not militaria_files:
    logger.error("No militaria_stores_CLEAN_*.csv file found!")
    sys.exit(1)

INPUT_FILE = Path(sorted(militaria_files)[-1])  # Latest file

# Output
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
CONFIG = {
    "API_KEY": "c6c76660-b774-4dcc-be3f-64cdb999e70f",
    "API_URL": "https://api.mails.so/v1/validate",
    "EMAIL_COLUMN": "email",
    "PARALLEL_WORKERS": 20,  # Number of parallel API requests
    "TIMEOUT": 10,  # seconds
}


def verify_email(email: str) -> dict:
    """Verify single email using mails.so API"""
    try:
        headers = {
            "x-mails-api-key": CONFIG["API_KEY"]
        }

        params = {
            "email": email
        }

        response = requests.get(
            CONFIG["API_URL"],
            headers=headers,
            params=params,
            timeout=CONFIG["TIMEOUT"]
        )

        if response.status_code == 200:
            response_data = response.json()
            # API returns data in "data" object
            data = response_data.get("data", {})
            return {
                "email": email,
                "result": data.get("result", "unknown"),
                "score": data.get("score", 0),
                "is_free_provider": data.get("is_free", False),
                "is_disposable": data.get("is_disposable", False),
                "provider": data.get("provider", ""),
                "status": "success"
            }
        else:
            logger.error(f"API error {response.status_code} for {email}")
            return {
                "email": email,
                "result": "error",
                "score": 0,
                "status": f"api_error_{response.status_code}"
            }

    except Exception as e:
        logger.error(f"Exception verifying {email}: {e}")
        return {
            "email": email,
            "result": "error",
            "score": 0,
            "status": "exception"
        }


def main():
    """Main verification pipeline"""
    logger.info("=== MILITARIA STORES EMAIL VERIFICATION ===")
    logger.info(f"Input file: {INPUT_FILE}")

    # Load CSV
    logger.info("Loading militaria stores CSV...")
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    logger.info(f"Total emails to verify: {len(rows)}")
    logger.info(f"Parallel workers: {CONFIG['PARALLEL_WORKERS']}")

    # Verify emails in parallel
    logger.info("Starting parallel verification...")
    start_time = time.time()

    results = []
    stats = {
        "deliverable": 0,
        "risky": 0,
        "undeliverable": 0,
        "unknown": 0,
        "error": 0
    }

    _lock = threading.Lock()
    processed = 0

    def verify_row(row):
        """Verify single row"""
        nonlocal processed

        email = row.get(CONFIG["EMAIL_COLUMN"], "").strip()

        if not email:
            return None

        # Verify
        verification = verify_email(email)

        # Add original row data
        result_row = row.copy()
        result_row.update(verification)

        # Progress
        with _lock:
            nonlocal processed
            processed += 1
            if processed % 50 == 0:
                logger.info(f"Progress: {processed}/{len(rows)} verified")

        return result_row

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=CONFIG['PARALLEL_WORKERS']) as executor:
        futures = {executor.submit(verify_row, row): row for row in rows}

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

                # Update stats
                result_type = result.get("result", "unknown")
                if result_type in stats:
                    stats[result_type] += 1
                else:
                    stats["unknown"] += 1

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = OUTPUT_DIR / f"verified_militaria_stores_{timestamp}.csv"

    fieldnames = list(results[0].keys()) if results else []
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Statistics
    elapsed = time.time() - start_time

    logger.info("\n=== VERIFICATION COMPLETE ===")
    logger.info(f"Total verified: {len(results)}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output: {output_csv}")

    logger.info("\n=== RESULTS BREAKDOWN ===")
    for result_type, count in stats.items():
        percentage = (count / len(results) * 100) if results else 0
        logger.info(f"{result_type}: {count} ({percentage:.1f}%)")

    # Score distribution
    logger.info("\n=== SCORE DISTRIBUTION ===")
    scores = [r.get("score", 0) for r in results]
    avg_score = sum(scores) / len(scores) if scores else 0
    logger.info(f"Average score: {avg_score:.1f}/100")

    high_score = len([s for s in scores if s >= 80])
    medium_score = len([s for s in scores if 60 <= s < 80])
    low_score = len([s for s in scores if s < 60])

    logger.info(f"High (80-100): {high_score}")
    logger.info(f"Medium (60-79): {medium_score}")
    logger.info(f"Low (0-59): {low_score}")


if __name__ == "__main__":
    main()
