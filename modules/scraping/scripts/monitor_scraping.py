#!/usr/bin/env python3
"""
=== SCRAPING MONITOR - REAL-TIME STATS ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Monitor incremental scraping progress in real-time

FEATURES:
- Shows emails found, processing rate, ETA
- Auto-refreshes every 10 seconds
- Works with incremental_results.csv + checkpoint.json

USAGE:
python modules/scraping/scripts/monitor_scraping.py --dir results/aus_client_deep_search
"""

import pandas as pd
import json
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse

def format_duration(seconds):
    """Format seconds to human readable"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def monitor_progress(results_dir: Path, refresh_interval: int = 10):
    """Monitor scraping progress"""
    csv_file = results_dir / "incremental_results.csv"
    checkpoint_file = results_dir / "checkpoint.json"

    print("=" * 80)
    print("SCRAPING MONITOR - REAL-TIME STATS")
    print("=" * 80)
    print(f"Results dir: {results_dir}")
    print(f"Refresh: every {refresh_interval}s (Ctrl+C to stop)")
    print("=" * 80)

    iteration = 0
    start_monitor_time = time.time()
    prev_emails = 0
    prev_processed = 0
    prev_time = time.time()

    try:
        while True:
            iteration += 1
            current_time = time.time()

            # Clear screen (Windows)
            if iteration > 1:
                print("\n" + "=" * 80)

            print(f"\nUPDATE #{iteration} | {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 80)

            # Check if files exist
            if not csv_file.exists() and not checkpoint_file.exists():
                print("Waiting for scraper to start...")
                print("   No results yet. Scraper may still be initializing...")
                time.sleep(refresh_interval)
                continue

            # Read checkpoint
            checkpoint_data = {}
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)

            # Read CSV
            emails_found = 0
            unique_companies = 0
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file)
                    emails_found = len(df)
                    unique_companies = df['name'].nunique() if 'name' in df.columns else 0
                except Exception as e:
                    print(f"Error reading CSV: {e}")

            # Get stats from checkpoint
            processed_urls = checkpoint_data.get('total_processed', 0)
            stats = checkpoint_data.get('stats', {})
            checkpoint_time = checkpoint_data.get('timestamp', '')

            # Calculate rates
            time_elapsed = current_time - prev_time if prev_time else refresh_interval
            emails_rate = (emails_found - prev_emails) / time_elapsed if time_elapsed > 0 else 0
            processing_rate = (processed_urls - prev_processed) / time_elapsed if time_elapsed > 0 else 0

            # Print stats
            print(f"\nEMAILS FOUND")
            print(f"   Total: {emails_found:,}")
            print(f"   Companies: {unique_companies:,}")
            print(f"   Rate: {emails_rate:.1f} emails/sec")

            print(f"\nPROCESSING STATUS")
            print(f"   URLs processed: {processed_urls:,} / 10,408")
            print(f"   Progress: {(processed_urls/10408*100):.1f}%")
            print(f"   Rate: {processing_rate:.1f} URLs/sec")

            if stats:
                success = stats.get('success', 0)
                failed = stats.get('failed', 0)
                success_rate = (success / processed_urls * 100) if processed_urls > 0 else 0

                print(f"\nSUCCESS METRICS")
                print(f"   Success: {success:,} ({success_rate:.1f}%)")
                print(f"   Failed: {failed:,}")
                print(f"   Emails from homepage: {stats.get('emails_from_homepage', 0):,}")
                print(f"   Emails from deep search: {stats.get('emails_from_deep', 0):,}")

            # ETA calculation
            if processing_rate > 0:
                remaining = 10408 - processed_urls
                eta_seconds = remaining / processing_rate
                eta_time = datetime.now() + timedelta(seconds=eta_seconds)

                print(f"\nTIME ESTIMATES")
                print(f"   Remaining: {format_duration(eta_seconds)}")
                print(f"   ETA: {eta_time.strftime('%H:%M:%S')}")

            if checkpoint_time:
                print(f"\nLAST CHECKPOINT")
                print(f"   {checkpoint_time}")

            # Update previous values
            prev_emails = emails_found
            prev_processed = processed_urls
            prev_time = current_time

            # Summary bar
            print("\n" + "=" * 80)
            progress_bar_width = 50
            progress_filled = int((processed_urls / 10408) * progress_bar_width)
            progress_bar = "█" * progress_filled + "░" * (progress_bar_width - progress_filled)
            print(f"[{progress_bar}] {processed_urls:,}/10,408 URLs")

            # Wait
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("Monitoring stopped")
        print("=" * 80)
        print(f"Final stats:")
        print(f"  - Emails found: {emails_found:,}")
        print(f"  - URLs processed: {processed_urls:,}")
        print(f"  - Monitoring duration: {format_duration(time.time() - start_monitor_time)}")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Monitor scraping progress in real-time')
    parser.add_argument('--dir', default='modules/scraping/homepage_email_scraper/results/aus_client_deep_search',
                       help='Results directory to monitor')
    parser.add_argument('--interval', type=int, default=10,
                       help='Refresh interval in seconds (default: 10)')

    args = parser.parse_args()
    results_dir = Path(args.dir)

    if not results_dir.exists():
        print(f"ERROR: Directory not found: {results_dir}")
        sys.exit(1)

    monitor_progress(results_dir, args.interval)


if __name__ == "__main__":
    main()
