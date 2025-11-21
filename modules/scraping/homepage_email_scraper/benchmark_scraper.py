#!/usr/bin/env python3
"""
=== SCRAPER BENCHMARK - OLD VS NEW ===
Version: 1.0.0 | Created: 2025-11-20

COMPARES:
- scraper.py (old, thread-based)
- scraper_ultra_fast.py (new, asyncio)

METRICS:
- Total time
- Sites per second
- Memory usage
- Success rate
- Emails found

USAGE:
python benchmark_scraper.py --input test_100_sites.csv --mode deep_search

OUTPUT:
Detailed comparison table + recommendation
"""

import sys
import time
import argparse
import subprocess
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import psutil
import os

# Paths
SCRIPT_DIR = Path(__file__).parent
OLD_SCRAPER = SCRIPT_DIR / "scraper.py"
NEW_SCRAPER = SCRIPT_DIR / "scraper_ultra_fast.py"
RESULTS_DIR = SCRIPT_DIR / "results"


def get_memory_usage():
    """Get current process memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def run_scraper(scraper_path: Path, input_csv: Path, mode: str, workers: int, max_pages: int) -> dict:
    """
    Run a scraper and measure performance

    Returns:
        dict with metrics: duration, speed, success_rate, emails_found, memory_peak
    """
    print(f"\n{'='*70}")
    print(f"RUNNING: {scraper_path.name}")
    print(f"{'='*70}")

    start_time = time.time()
    start_memory = get_memory_usage()

    # Build command
    cmd = [
        sys.executable,
        str(scraper_path),
        "--input", str(input_csv),
        "--scraping-mode", mode,
        "--workers", str(workers),
        "--max-pages", str(max_pages),
        "--email-format", "separate"
    ]

    print(f"Command: {' '.join(cmd)}")

    # Run scraper
    try:
        result = subprocess.run(
            cmd,
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout
        )

        duration = time.time() - start_time
        end_memory = get_memory_usage()
        memory_peak = end_memory - start_memory

        # Parse output for stats
        stdout = result.stdout
        print(stdout)

        # Find latest result folder
        result_folders = sorted(
            [f for f in RESULTS_DIR.iterdir() if f.is_dir() and 'scraped' in f.name],
            reverse=True
        )

        if result_folders:
            latest_result = result_folders[0]
            analytics_file = latest_result / "scraping_analytics.json"

            if analytics_file.exists():
                with open(analytics_file) as f:
                    analytics = json.load(f)

                return {
                    'scraper': scraper_path.name,
                    'duration_sec': round(duration, 2),
                    'sites_per_sec': analytics['summary']['sites_per_second'],
                    'total_sites': analytics['summary']['total_sites'],
                    'success_rate': analytics['summary']['success_rate'],
                    'emails_found': analytics['results']['success']['total_emails'],
                    'from_homepage': analytics['results']['success']['from_homepage'],
                    'from_deep': analytics['results']['success']['from_deep_search'],
                    'memory_mb': round(memory_peak, 2),
                    'status': 'completed'
                }

        # Fallback if no analytics
        return {
            'scraper': scraper_path.name,
            'duration_sec': round(duration, 2),
            'sites_per_sec': 0,
            'total_sites': 0,
            'success_rate': '0%',
            'emails_found': 0,
            'memory_mb': round(memory_peak, 2),
            'status': 'completed_no_analytics'
        }

    except subprocess.TimeoutExpired:
        return {
            'scraper': scraper_path.name,
            'status': 'timeout',
            'duration_sec': 600,
            'error': 'Scraper timed out after 10 minutes'
        }

    except Exception as e:
        return {
            'scraper': scraper_path.name,
            'status': 'failed',
            'error': str(e)
        }


def print_comparison(old_result: dict, new_result: dict):
    """Print detailed comparison table"""

    print("\n" + "="*70)
    print("BENCHMARK RESULTS - OLD vs NEW")
    print("="*70)

    # Check if both completed
    if old_result['status'] != 'completed' or new_result['status'] != 'completed':
        print("\n⚠️ WARNING: One or both scrapers did not complete successfully")
        print(f"Old scraper: {old_result['status']}")
        print(f"New scraper: {new_result['status']}")
        return

    # Calculate speedup
    speedup = old_result['duration_sec'] / new_result['duration_sec']

    # Print comparison table
    print("\n[PERFORMANCE METRICS]")
    print("-" * 70)
    print(f"{'Metric':<30} {'Old Scraper':<20} {'New Scraper':<20}")
    print("-" * 70)

    print(f"{'Duration (seconds)':<30} {old_result['duration_sec']:<20} {new_result['duration_sec']:<20}")
    print(f"{'Sites per second':<30} {old_result['sites_per_sec']:<20} {new_result['sites_per_sec']:<20}")
    print(f"{'Total sites':<30} {old_result['total_sites']:<20} {new_result['total_sites']:<20}")
    print(f"{'Success rate':<30} {old_result['success_rate']:<20} {new_result['success_rate']:<20}")
    print(f"{'Emails found':<30} {old_result['emails_found']:<20} {new_result['emails_found']:<20}")
    print(f"{'Memory usage (MB)':<30} {old_result['memory_mb']:<20} {new_result['memory_mb']:<20}")

    print("-" * 70)
    print(f"\n[SPEEDUP] {speedup:.2f}x faster")

    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    if speedup >= 5:
        print(f"\n[RESULT] NEW SCRAPER IS {speedup:.1f}x FASTER!")
        print("   -> Highly recommended to replace old scraper")
        print(f"   -> Time saved: {old_result['duration_sec'] - new_result['duration_sec']:.1f} seconds")
    elif speedup >= 2:
        print(f"\n[RESULT] NEW SCRAPER IS {speedup:.1f}x FASTER")
        print("   -> Recommended to replace old scraper")
    elif speedup >= 1.2:
        print(f"\n[RESULT] NEW SCRAPER IS {speedup:.1f}x FASTER")
        print("   -> Moderate improvement, consider replacing")
    else:
        print(f"\n[RESULT] NEW SCRAPER IS ONLY {speedup:.1f}x FASTER")
        print("   -> Small improvement, may not be worth replacing")

    # Quality check
    print("\n[EMAIL EXTRACTION QUALITY]")
    old_emails = old_result['emails_found']
    new_emails = new_result['emails_found']

    if new_emails >= old_emails:
        print(f"   [OK] New scraper found {new_emails} emails (>= old: {old_emails})")
    else:
        print(f"   [WARNING] New scraper found {new_emails} emails (< old: {old_emails})")
        print(f"   -> Email extraction quality decreased by {old_emails - new_emails} emails")


def main():
    parser = argparse.ArgumentParser(description='Benchmark old vs new scraper')
    parser.add_argument('--input', required=True, help='Input CSV (recommend 100-500 sites)')
    parser.add_argument('--mode', choices=['homepage_only', 'deep_search'], default='deep_search')
    parser.add_argument('--workers-old', type=int, default=50, help='Workers for old scraper')
    parser.add_argument('--workers-new', type=int, default=500, help='Workers for new scraper')
    parser.add_argument('--max-pages', type=int, default=5)
    parser.add_argument('--skip-old', action='store_true', help='Skip old scraper (only test new)')

    args = parser.parse_args()

    input_csv = Path(args.input)

    if not input_csv.exists():
        print(f"[ERROR] Input file not found: {input_csv}")
        sys.exit(1)

    # Load CSV to check size
    df = pd.read_csv(input_csv)
    print(f"\nLoaded {len(df)} sites from {input_csv.name}")

    if len(df) > 1000:
        print(f"WARNING: {len(df)} sites may take a long time!")
        print("   Recommend using --limit 100 for quick testing")

    # Run benchmarks
    results = {}

    if not args.skip_old:
        print("\n" + "[OLD] RUNNING OLD SCRAPER (thread-based)")
        results['old'] = run_scraper(OLD_SCRAPER, input_csv, args.mode, args.workers_old, args.max_pages)

    print("\n" + "[NEW] RUNNING NEW SCRAPER (asyncio)")
    results['new'] = run_scraper(NEW_SCRAPER, input_csv, args.mode, args.workers_new, args.max_pages)

    # Compare results
    if not args.skip_old and 'old' in results and 'new' in results:
        print_comparison(results['old'], results['new'])

    # Save benchmark results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    benchmark_file = RESULTS_DIR / f"benchmark_{timestamp}.json"

    with open(benchmark_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n[SAVED] Benchmark results saved to: {benchmark_file}")


if __name__ == "__main__":
    main()
