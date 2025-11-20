#!/usr/bin/env python3
"""
=== INCREMENTAL HOMEPAGE EMAIL SCRAPER ===
Version: 2.0.0 | Created: 2025-11-20

FEATURES:
- Incremental saving every 100 emails found
- Checkpoint/resume capability
- No data loss if process crashes
- Resume from exact position

IMPROVEMENTS over v1:
- save_incremental() called every 100 emails
- checkpoint.json saves processed URLs
- --resume flag to continue from checkpoint
- Progress saved continuously

USAGE:
New run:
  python scraper_incremental.py --input input.csv --output-dir results/

Resume run:
  python scraper_incremental.py --resume results/checkpoint.json
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import original scraper
from modules.scraping.homepage_email_scraper.scraper import (
    SimpleHomepageScraper, validate_url, logger
)

import pandas as pd
import json
import time
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

class IncrementalScraper(SimpleHomepageScraper):
    """Enhanced scraper with incremental saving"""

    def __init__(self, *args, output_dir: Optional[Path] = None, checkpoint_interval: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = output_dir or Path(f"results/scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_file = self.output_dir / "checkpoint.json"
        self.incremental_csv = self.output_dir / "incremental_results.csv"
        self.processed_urls = set()
        # REMOVED: self.all_results = [] - MEMORY LEAK FIX
        self.emails_found_count = 0

        # Create output dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_checkpoint(self) -> Dict:
        """Load checkpoint if exists"""
        if self.checkpoint_file.exists():
            logger.info(f"Loading checkpoint from {self.checkpoint_file}")
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            self.processed_urls = set(checkpoint.get('processed_urls', []))
            self.emails_found_count = checkpoint.get('emails_found', 0)
            logger.info(f"Checkpoint loaded: {len(self.processed_urls)} URLs already processed, {self.emails_found_count} emails found")
            return checkpoint
        return {}

    def save_checkpoint(self):
        """Save current progress to checkpoint"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'processed_urls': list(self.processed_urls),
            'total_processed': len(self.processed_urls),
            'emails_found': self.emails_found_count,
            'stats': self.stats
        }

        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def save_incremental(self, new_rows: List[Dict]):
        """Save new results incrementally"""
        if not new_rows:
            return

        df_new = pd.DataFrame(new_rows)

        # Append to CSV
        if self.incremental_csv.exists():
            df_new.to_csv(self.incremental_csv, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df_new.to_csv(self.incremental_csv, mode='w', header=True, index=False, encoding='utf-8-sig')

        # Save checkpoint
        self.save_checkpoint()

        logger.info(f"✓ Incremental save: {len(new_rows)} rows saved | Total emails: {self.emails_found_count}")

    def process_batch_incremental(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process batch with incremental saving"""
        logger.info("="*70)
        logger.info("INCREMENTAL HOMEPAGE SCRAPER STARTED")
        logger.info("="*70)
        logger.info(f"Total leads: {len(df)}")
        logger.info(f"Already processed: {len(self.processed_urls)}")
        logger.info(f"Remaining: {len(df) - len(self.processed_urls)}")
        logger.info(f"Workers: {self.workers}")
        logger.info(f"Checkpoint interval: {self.checkpoint_interval} emails")
        logger.info("="*70)

        # Filter out already processed
        df_remaining = df[~df['website'].isin(self.processed_urls)].copy()

        if len(df_remaining) == 0:
            logger.info("All URLs already processed!")
            return pd.read_csv(self.incremental_csv) if self.incremental_csv.exists() else pd.DataFrame()

        logger.info(f"Processing {len(df_remaining)} remaining URLs...")

        start_time = time.time()
        pending_rows = []  # Buffer for incremental save
        last_email_count = self.emails_found_count

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self.scrape_homepage,
                    row.to_dict()
                ): idx for idx, row in df_remaining.iterrows()
            }

            # Collect results
            processed_count = 0
            for future in as_completed(futures):
                try:
                    result_rows = future.result()

                    if result_rows:
                        # Track processed URL
                        website = result_rows[0].get('website', '')
                        self.processed_urls.add(website)

                        # Add to buffer (save to CSV in batches, NOT to memory)
                        # REMOVED: self.all_results.extend(result_rows) - MEMORY LEAK FIX
                        pending_rows.extend(result_rows)

                        # Count emails
                        emails_in_rows = sum(1 for r in result_rows if r.get('email'))
                        self.emails_found_count += emails_in_rows

                    processed_count += 1

                    # Incremental save every N emails
                    if self.emails_found_count - last_email_count >= self.checkpoint_interval:
                        logger.info(f"✓ Checkpoint reached: {self.emails_found_count} emails found")
                        self.save_incremental(pending_rows)
                        pending_rows = []
                        last_email_count = self.emails_found_count

                    # Progress update every 50 leads
                    if processed_count % 50 == 0:
                        logger.info(f"Progress: {processed_count}/{len(df_remaining)} leads | {self.emails_found_count} emails found")

                except Exception as e:
                    logger.error(f"Task failed: {e}")

        # Save any remaining rows
        if pending_rows:
            logger.info(f"Saving final {len(pending_rows)} rows...")
            self.save_incremental(pending_rows)

        # Final summary
        duration = time.time() - start_time
        logger.info("="*70)
        logger.info("SCRAPING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total leads processed: {self.stats['total_processed']}")
        logger.info(f"Total emails found: {self.emails_found_count}")
        logger.info(f"Success: {self.stats['success']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Duration: {duration:.2f}s ({duration/60:.1f} min)")
        logger.info(f"Output: {self.incremental_csv}")
        logger.info("="*70)

        # Return full results from CSV (no longer stored in memory)
        return pd.read_csv(self.incremental_csv) if self.incremental_csv.exists() else pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='Incremental Homepage Scraper with Checkpoint/Resume')
    parser.add_argument('--input', help='Input CSV file path')
    parser.add_argument('--resume', help='Resume from checkpoint file (checkpoint.json)')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--workers', type=int, default=50, help='Number of parallel workers (default: 50)')
    parser.add_argument('--max-pages', type=int, default=10, help='Max pages to search per site (default: 10)')
    parser.add_argument('--checkpoint-interval', type=int, default=100, help='Save every N emails (default: 100)')
    parser.add_argument('--scraping-mode', choices=['homepage_only', 'deep_search'], default='deep_search')
    parser.add_argument('--email-format', choices=['all', 'primary', 'separate'], default='separate')
    parser.add_argument('--website-column', default='website')
    parser.add_argument('--name-column', default='name')

    args = parser.parse_args()

    # Resume mode
    if args.resume:
        checkpoint_path = Path(args.resume)
        if not checkpoint_path.exists():
            logger.error(f"Checkpoint file not found: {checkpoint_path}")
            sys.exit(1)

        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)

        # Get original input from checkpoint parent dir
        output_dir = checkpoint_path.parent
        logger.info(f"Resuming from checkpoint: {checkpoint_path}")
        logger.info(f"Output dir: {output_dir}")

        # Find original input CSV
        # We need to re-read the original input
        if not args.input:
            logger.error("Please provide --input CSV file for resume mode")
            sys.exit(1)

        input_file = args.input
    else:
        # New run
        if not args.input:
            logger.error("Please provide --input CSV file")
            sys.exit(1)

        input_file = args.input
        output_dir = Path(args.output_dir) if args.output_dir else Path(f"modules/scraping/homepage_email_scraper/results/scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    # Load CSV
    logger.info(f"Reading input file: {input_file}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from CSV")

    # Validate website column
    if args.website_column not in df.columns:
        logger.error(f"Website column '{args.website_column}' not found in CSV!")
        sys.exit(1)

    # Create scraper
    scraper = IncrementalScraper(
        workers=args.workers,
        max_pages=args.max_pages,
        scraping_mode=args.scraping_mode,
        extract_emails=True,
        email_format=args.email_format,
        save_content=True,
        output_dir=output_dir,
        checkpoint_interval=args.checkpoint_interval
    )

    # Load checkpoint if resuming
    if args.resume:
        scraper.load_checkpoint()

    # Process
    df_results = scraper.process_batch_incremental(df)

    logger.info(f"\n✓ DONE! Results saved to: {scraper.incremental_csv}")
    logger.info(f"Total emails found: {scraper.emails_found_count}")


if __name__ == "__main__":
    main()
