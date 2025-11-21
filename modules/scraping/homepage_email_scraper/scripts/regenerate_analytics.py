#!/usr/bin/env python3
"""
=== REGENERATE ANALYTICS FROM CSV FILES ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Regenerate scraping_analytics.json from actual CSV files to fix any discrepancies

FEATURES:
- Scan all result folders
- Read actual CSV files (success.csv or success_emails.csv)
- Count real emails (not just rows)
- Regenerate accurate analytics JSON
- Backup old analytics before overwriting

USAGE:
python regenerate_analytics.py
"""

import sys
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "results"


def count_emails_in_csv(df: pd.DataFrame) -> int:
    """
    Count total emails in success CSV
    Handles both single emails and comma-separated emails per row
    """
    if 'email' not in df.columns:
        return 0

    total = 0
    for emails in df['email'].dropna():
        email_str = str(emails).strip()
        if not email_str or email_str == 'nan':
            continue

        # Check if comma-separated
        email_list = [e.strip() for e in email_str.split(',') if e.strip()]
        total += len(email_list)

    return total


def regenerate_analytics_for_folder(folder: Path) -> dict:
    """
    Regenerate analytics JSON from actual CSV files in folder
    Returns new analytics data
    """
    # Detect format (old vs new)
    old_success = folder / "success_emails.csv"
    new_success = folder / "success.csv"

    if new_success.exists():
        success_file = new_success
        failed_file = folder / "failed.csv"
        format_type = "new"
    elif old_success.exists():
        success_file = old_success
        failed_file = None  # Old format has multiple failed files
        format_type = "old"
    else:
        return None

    # Read success CSV
    df_success = pd.read_csv(success_file, encoding='utf-8-sig')
    success_count = len(df_success)
    total_emails = count_emails_in_csv(df_success)

    # Read failed CSV
    if format_type == "new" and failed_file.exists():
        df_failed = pd.read_csv(failed_file, encoding='utf-8-sig')
        failed_count = len(df_failed)

        # Count failure reasons
        failure_counts = {}
        if 'failure_reason' in df_failed.columns:
            failure_counts = df_failed['failure_reason'].value_counts().to_dict()
    else:
        # Old format - read separate failed files
        failed_static = folder / "failed_static.csv"
        failed_dynamic = folder / "failed_dynamic.csv"
        failed_other = folder / "failed_other.csv"

        failed_count = 0
        failure_counts = {}

        if failed_static.exists():
            df_static = pd.read_csv(failed_static, encoding='utf-8-sig')
            count = len(df_static)
            failed_count += count
            failure_counts['static_no_email'] = count

        if failed_dynamic.exists():
            df_dynamic = pd.read_csv(failed_dynamic, encoding='utf-8-sig')
            count = len(df_dynamic)
            failed_count += count
            failure_counts['dynamic_no_email'] = count

        if failed_other.exists():
            df_other = pd.read_csv(failed_other, encoding='utf-8-sig')
            count = len(df_other)
            failed_count += count
            failure_counts['other_errors'] = count

    total_sites = success_count + failed_count
    success_rate = (success_count / total_sites * 100) if total_sites > 0 else 0

    # Create analytics data
    analytics = {
        "summary": {
            "total_sites": total_sites,
            "success_rate": f"{success_rate:.2f}%",
            "duration_seconds": 0,  # Unknown from CSV
            "duration_minutes": 0,
            "sites_per_second": 0
        },
        "results": {
            "success": {
                "count": success_count,
                "percentage": f"{success_rate:.2f}%",
                "total_emails": total_emails,
                "from_homepage": 0,  # Unknown from CSV
                "from_deep_search": 0
            },
            "failed": {
                "total": failed_count,
                "static_no_email": {
                    "count": failure_counts.get('static_no_email', 0),
                    "percentage": f"{(failure_counts.get('static_no_email', 0) / total_sites * 100) if total_sites > 0 else 0:.2f}%"
                },
                "dynamic_no_email": {
                    "count": failure_counts.get('dynamic_no_email', 0),
                    "percentage": f"{(failure_counts.get('dynamic_no_email', 0) / total_sites * 100) if total_sites > 0 else 0:.2f}%"
                },
                "other_errors": {
                    "count": failure_counts.get('other_errors', 0),
                    "percentage": f"{(failure_counts.get('other_errors', 0) / total_sites * 100) if total_sites > 0 else 0:.2f}%"
                }
            }
        },
        "site_types": {
            "static": 0,  # Unknown from CSV
            "dynamic": 0
        },
        "note": "Regenerated from CSV files on " + datetime.now().isoformat()
    }

    return analytics


def main():
    """Main regeneration function"""

    logger.info("="*70)
    logger.info("REGENERATE ANALYTICS FROM CSV FILES")
    logger.info("="*70)

    if not RESULTS_DIR.exists():
        logger.error(f"Results directory not found: {RESULTS_DIR}")
        return

    # Find all result folders
    result_folders = sorted([d for d in RESULTS_DIR.iterdir() if d.is_dir() and d.name.startswith('scraped_')])

    logger.info(f"\nFound {len(result_folders)} result folders")

    stats = {
        'processed': 0,
        'updated': 0,
        'errors': 0,
        'discrepancies': []
    }

    for folder in result_folders:
        analytics_file = folder / "scraping_analytics.json"

        logger.info(f"\nProcessing: {folder.name}")

        try:
            # Read old analytics if exists
            old_analytics = None
            if analytics_file.exists():
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    old_analytics = json.load(f)

            # Generate new analytics from CSV
            new_analytics = regenerate_analytics_for_folder(folder)

            if new_analytics is None:
                logger.warning("  No CSV files found, skipping")
                continue

            # Compare old vs new
            if old_analytics:
                old_emails = old_analytics.get('results', {}).get('success', {}).get('total_emails', 0)
                new_emails = new_analytics['results']['success']['total_emails']
                old_count = old_analytics.get('results', {}).get('success', {}).get('count', 0)
                new_count = new_analytics['results']['success']['count']

                if old_emails != new_emails or old_count != new_count:
                    logger.warning(f"  DISCREPANCY FOUND:")
                    logger.warning(f"    Old: {old_count} rows, {old_emails} emails")
                    logger.warning(f"    New: {new_count} rows, {new_emails} emails")

                    stats['discrepancies'].append({
                        'folder': folder.name,
                        'old_rows': old_count,
                        'old_emails': old_emails,
                        'new_rows': new_count,
                        'new_emails': new_emails
                    })

                # Backup old analytics
                backup_file = folder / f"scraping_analytics.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(analytics_file, backup_file)
                logger.info(f"  Backed up old analytics to: {backup_file.name}")

            # Write new analytics
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(new_analytics, f, indent=2, ensure_ascii=False)

            logger.info(f"  Updated: {new_analytics['results']['success']['count']} rows, {new_analytics['results']['success']['total_emails']} emails")

            stats['updated'] += 1

        except Exception as e:
            logger.error(f"  Error processing folder: {e}")
            stats['errors'] += 1

        stats['processed'] += 1

    # Summary
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total folders processed: {stats['processed']}")
    logger.info(f"Analytics updated: {stats['updated']}")
    logger.info(f"Errors: {stats['errors']}")

    if stats['discrepancies']:
        logger.info(f"\nDiscrepancies found in {len(stats['discrepancies'])} folders:")
        for disc in stats['discrepancies']:
            logger.info(f"\n  {disc['folder']}:")
            logger.info(f"    Old: {disc['old_rows']} rows, {disc['old_emails']} emails")
            logger.info(f"    New: {disc['new_rows']} rows, {disc['new_emails']} emails")
            logger.info(f"    Difference: {disc['new_emails'] - disc['old_emails']} emails, {disc['new_rows'] - disc['old_rows']} rows")

    logger.info("\n" + "="*70)
    logger.info("DONE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
