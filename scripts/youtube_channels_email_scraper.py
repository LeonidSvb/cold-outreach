#!/usr/bin/env python3
"""
=== YOUTUBE CHANNELS EMAIL SCRAPER ===
Version: 1.0.0 | Created: 2025-12-02

PURPOSE:
Extract emails from YouTube channels' websites using ultra-fast scraper

FEATURES:
- Reads YouTube channel JSON (from Apify/manual scraping)
- Extracts website URLs from channel bio links
- Scrapes emails using async ultra-fast scraper
- Filters out link aggregators (linktr.ee, patreon, etc.)

USAGE:
python youtube_channels_email_scraper.py --input dataset.json --limit 50
"""

import sys
import json
import asyncio
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.shared.logging.universal_logger import get_logger
from modules.scraping.homepage_email_scraper.scraper_ultra_fast import UltraFastScraper

logger = get_logger(__name__)

# Link aggregators to skip (won't have email)
SKIP_DOMAINS = [
    'linktr.ee',
    'linkin.bio',
    'beacons.ai',
    'patreon.com',
    'ko-fi.com',
    'buymeacoffee.com',
    'gofundme.com',
    'twitter.com',
    'instagram.com',
    'facebook.com',
    'linkedin.com',
    'youtube.com',
    'tiktok.com'
]

def extract_channel_data(json_path: str) -> List[Dict]:
    """
    Extract channel data from YouTube JSON
    Returns list of dicts with channel_name, channel_url, website
    """
    logger.info(f"Reading JSON: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} YouTube channels")

    channels = []

    for record in data:
        channel_info = record.get('channelInfo', {})
        link_info = channel_info.get('link', {})

        # Extract website (try both 'website' and 'Web' keys)
        website = link_info.get('website', '') or link_info.get('Web', '')

        if not website or not website.strip():
            continue

        # Skip link aggregators
        website_lower = website.lower()
        if any(domain in website_lower for domain in SKIP_DOMAINS):
            logger.debug(f"Skipping link aggregator: {website}")
            continue

        # Get channel name from author or title
        channel_name = record.get('author', '') or record.get('title', '') or 'Unknown'

        # Get channel URL (YouTube channel)
        youtube_url = link_info.get('YOUTUBE', '')
        if youtube_url and not youtube_url.startswith('http'):
            youtube_url = f'https://{youtube_url}'

        # Extract other useful info
        subscriber_count = record.get('subscriberCount', 0)

        channels.append({
            'channel_name': channel_name,
            'channel_url': youtube_url,
            'website': website,
            'subscriber_count': subscriber_count,
            'twitter': link_info.get('Twitter', ''),
            'instagram': link_info.get('Instagram', ''),
            'facebook': link_info.get('Facebook', '')
        })

    logger.info(f"Extracted {len(channels)} channels with valid websites")
    return channels

async def scrape_channels_async(channels: List[Dict], limit: Optional[int] = None) -> pd.DataFrame:
    """
    Scrape emails from channel websites using ultra-fast async scraper
    """
    if limit:
        channels = channels[:limit]
        logger.info(f"Limited to first {limit} channels")

    # Convert to DataFrame format expected by scraper
    df = pd.DataFrame(channels)
    df = df.rename(columns={'channel_name': 'name'})

    # Create ultra-fast scraper
    scraper = UltraFastScraper(
        workers=100,  # Parallel connections
        max_pages=5,  # Check homepage + 4 deep pages
        scraping_mode='deep_search',  # Try /contact, /about pages
        extract_emails=True,
        email_format='all',  # Get all emails found
        save_content=False  # Don't need full content
    )

    logger.info("Starting email scraping...")
    logger.info(f"Workers: 100")
    logger.info(f"Mode: deep_search (homepage + /contact + /about)")
    logger.info("="*70)

    # Scrape all channels
    df_results = await scraper.process_batch_async(df)

    # Print analytics
    analytics = scraper.get_analytics()

    logger.info("\n" + "="*70)
    logger.info("SCRAPING RESULTS:")
    logger.info("="*70)
    logger.info(f"Total channels: {analytics['summary']['total_sites']}")
    logger.info(f"Success rate: {analytics['summary']['success_rate']}")
    logger.info(f"Total emails found: {analytics['results']['success']['total_emails']}")
    logger.info(f"  - From homepage: {analytics['results']['success']['from_homepage']}")
    logger.info(f"  - From deep search: {analytics['results']['success']['from_deep_search']}")
    logger.info(f"Duration: {analytics['summary']['duration_seconds']}s")
    logger.info(f"Speed: {analytics['summary']['sites_per_second']} sites/sec")
    logger.info("="*70)

    return df_results

def save_results(df: pd.DataFrame, input_file: str) -> str:
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create results directory
    results_dir = Path(__file__).parent.parent / "modules" / "scraping" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Generate output filename
    input_name = Path(input_file).stem
    output_file = results_dir / f"youtube_emails_{input_name}_{timestamp}.csv"

    # Save full results
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"Full results saved: {output_file}")

    # Save success only (with emails)
    success_df = df[df['scrape_status'] == 'success'].copy()
    if len(success_df) > 0:
        success_file = results_dir / f"youtube_emails_{input_name}_{timestamp}_SUCCESS.csv"
        success_df.to_csv(success_file, index=False, encoding='utf-8-sig')
        logger.info(f"Success results saved: {success_file}")

    # Print sample results
    logger.info("\n" + "="*70)
    logger.info("SAMPLE RESULTS (First 10 with emails):")
    logger.info("="*70)

    with_emails = df[df['email'].notna() & (df['email'] != '')].head(10)
    for idx, row in with_emails.iterrows():
        logger.info(f"\n{row['name']}")
        logger.info(f"  Website: {row['website']}")
        logger.info(f"  Email(s): {row['email']}")
        logger.info(f"  Subscribers: {row.get('subscriber_count', 0):,}")

    return str(output_file)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Scrape emails from YouTube channels websites')
    parser.add_argument('--input', required=True, help='Input JSON file path')
    parser.add_argument('--limit', type=int, help='Limit number of channels (default: all)')
    parser.add_argument('--test', action='store_true', help='Test mode: limit to 50 channels')

    args = parser.parse_args()

    logger.info("="*70)
    logger.info("YOUTUBE CHANNELS EMAIL SCRAPER")
    logger.info("="*70)

    # Extract channel data from JSON
    channels = extract_channel_data(args.input)

    if not channels:
        logger.error("No valid channels found with websites!")
        return

    # Apply limit
    limit = 50 if args.test else args.limit

    # Scrape emails (async)
    df_results = asyncio.run(scrape_channels_async(channels, limit))

    # Save results
    output_file = save_results(df_results, args.input)

    logger.info(f"\n✅ Done! Results saved to: {output_file}")

if __name__ == "__main__":
    main()
