#!/usr/bin/env python3
"""
=== WEB SCRAPER + AI ENRICHMENT ===
Version: 1.0.0 | Created: 2025-12-12

PURPOSE:
Scrape websites and analyze with AI in single pipeline.
Combines SimpleHomepageScraper + OpenAI processing for personalized outreach.

FEATURES:
- Homepage or multi-page scraping (sitemap-first strategy)
- Flexible AI analysis with customizable prompt
- Parallel processing (scraping + AI)
- Cost tracking and analytics
- Multiple output formats (CSV, JSON)

USAGE:
python scraper_with_ai.py --input leads.csv --prompt-file prompt.txt --scraping-mode multi_page

OUTPUT:
results/scraped_ai_YYYYMMDD_HHMMSS/
├── success.csv           # Successfully processed
├── success.json
├── failed.csv            # Failed scraping or AI
├── failed.json
└── analytics.json        # Performance metrics
"""

import sys
import os
from pathlib import Path
import argparse
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import scraping utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from lib.http_utils import HTTPClient
    from lib.text_utils import clean_html_to_text
    from lib.sitemap_utils import SitemapParser
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import clean_html_to_text
    from modules.scraping.lib.sitemap_utils import SitemapParser

# Import logger
try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')


class WebScraperAI:
    """Unified web scraper with AI enrichment"""

    def __init__(
        self,
        openai_api_key: str,
        ai_prompt_template: str,
        workers: int = 20,
        ai_workers: int = 5,
        max_pages: int = 5,
        scraping_mode: str = 'multi_page',
        ai_model: str = 'gpt-4o-mini'
    ):
        self.http_client = HTTPClient(timeout=15, retries=3)
        self.sitemap_parser = SitemapParser(timeout=15)
        self.openai_client = OpenAI(api_key=openai_api_key)

        self.ai_prompt_template = ai_prompt_template
        self.workers = workers
        self.ai_workers = ai_workers
        self.max_pages = max_pages
        self.scraping_mode = scraping_mode
        self.ai_model = ai_model

        # Thread-safe stats
        self._lock = threading.Lock()
        self.stats = {
            'total_processed': 0,
            'scraping_success': 0,
            'scraping_failed': 0,
            'ai_success': 0,
            'ai_failed': 0,
            'total_cost': 0.0
        }

    def scrape_website(self, url: str) -> Dict:
        """
        Scrape website content (homepage or multi-page)

        Args:
            url: Website URL to scrape

        Returns:
            {
                'status': 'success' | 'failed',
                'content': str,  # Combined text from all pages
                'error': str
            }
        """
        if not url:
            return {'status': 'failed', 'error': 'Empty URL'}

        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if self.scraping_mode == 'homepage_only':
            # Scrape only homepage
            response = self.http_client.fetch(url, check_content_length=False)

            if response['status'] == 'success':
                content = clean_html_to_text(response['content'], max_length=50000)
                return {'status': 'success', 'content': content}
            else:
                return {'status': 'failed', 'error': response.get('error', 'Unknown error')}

        else:  # multi_page
            # Scrape multiple pages
            all_content = []

            # Homepage first
            response = self.http_client.fetch(url, check_content_length=False)
            if response['status'] == 'success':
                homepage_text = clean_html_to_text(response['content'], max_length=20000)
                all_content.append(homepage_text)

            # Get additional pages from sitemap
            try:
                discovery = self.sitemap_parser.get_smart_pages(url, max_pages=self.max_pages)

                for page_url in discovery['pages'][:self.max_pages]:
                    try:
                        page_response = self.http_client.fetch(page_url, check_content_length=False)
                        if page_response['status'] == 'success':
                            page_text = clean_html_to_text(page_response['content'], max_length=10000)
                            all_content.append(page_text)
                    except Exception as e:
                        logger.debug(f"Failed to scrape additional page {page_url}: {e}")
                        continue
            except Exception as e:
                logger.debug(f"Failed to get smart pages for {url}: {e}")

            if all_content:
                combined = '\n\n'.join(all_content)
                return {'status': 'success', 'content': combined[:50000]}  # Limit to 50k chars
            else:
                return {'status': 'failed', 'error': 'No content extracted'}

    def analyze_with_ai(self, content: str, company_name: str = '') -> Optional[Dict]:
        """
        Analyze content with OpenAI

        Args:
            content: Website text content
            company_name: Company name for logging

        Returns:
            Parsed JSON response or None if failed
        """
        if not content or len(content) < 100:
            logger.warning(f"Skipping {company_name}: content too short ({len(content)} chars)")
            return None

        # Truncate for cost optimization
        content_truncated = content[:8000] if len(content) > 8000 else content

        # Replace {content} placeholder in prompt
        prompt = self.ai_prompt_template.replace('{content}', content_truncated)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.ai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a business intelligence analyst. Extract structured data accurately and concisely."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )

                # Parse JSON response
                result = json.loads(response.choices[0].message.content)

                # Calculate cost
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                if self.ai_model == 'gpt-4o-mini':
                    cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)
                else:  # gpt-4o
                    cost = (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.00 / 1_000_000)

                with self._lock:
                    self.stats['total_cost'] += cost
                    self.stats['ai_success'] += 1

                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {company_name}: {e}")
                with self._lock:
                    self.stats['ai_failed'] += 1
                return None

            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"Rate limit hit for {company_name}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif attempt < max_retries - 1:
                    logger.warning(f"AI error for {company_name}, retrying: {e}")
                    time.sleep(1)
                    continue
                else:
                    logger.error(f"AI analysis failed for {company_name} after {max_retries} attempts: {e}")
                    with self._lock:
                        self.stats['ai_failed'] += 1
                    return None

        return None

    def process_lead(self, row_data: Dict) -> Dict:
        """
        Process single lead: scrape + AI analysis

        Args:
            row_data: Row from CSV as dict

        Returns:
            Row dict with original columns + AI fields
        """
        name = row_data.get('name', row_data.get('company_name', 'Unknown'))
        website = row_data.get('website', '')

        # Base result with original columns
        result = row_data.copy()
        result.update({
            'scrape_status': 'failed',
            'scrape_error': '',
            'ai_status': 'failed',
            'website_content': '',
            # AI fields (will be populated if successful)
            'icp': '',
            'business_summary': '',
            'recent_achievements': '',
            'personalization_angle': ''
        })

        # Step 1: Scrape website
        scrape_result = self.scrape_website(website)

        if scrape_result['status'] == 'success':
            result['scrape_status'] = 'success'
            result['website_content'] = scrape_result['content']

            with self._lock:
                self.stats['scraping_success'] += 1

            # Step 2: AI analysis
            ai_result = self.analyze_with_ai(scrape_result['content'], name)

            if ai_result:
                result['ai_status'] = 'success'

                # Flatten AI results into columns
                result['icp'] = ai_result.get('icp', '')
                result['business_summary'] = ai_result.get('business_summary', '')
                result['recent_achievements'] = ai_result.get('recent_achievements', '')
                result['personalization_angle'] = ai_result.get('personalization_angle', '')

                logger.info(f"Success: {name}")
            else:
                logger.warning(f"AI failed: {name}")
        else:
            result['scrape_error'] = scrape_result.get('error', 'Unknown error')
            with self._lock:
                self.stats['scraping_failed'] += 1
            logger.warning(f"Scrape failed: {name} - {scrape_result.get('error', 'Unknown')}")

        with self._lock:
            self.stats['total_processed'] += 1

            # Log progress every 10 items
            if self.stats['total_processed'] % 10 == 0:
                logger.info(f"Progress: {self.stats['total_processed']} processed | "
                          f"{self.stats['ai_success']} AI success | "
                          f"Cost: ${self.stats['total_cost']:.2f}")

        return result

    def process_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process batch of leads with parallel processing

        Args:
            df: DataFrame with website column

        Returns:
            DataFrame with original columns + AI analysis
        """
        logger.info("="*70)
        logger.info("WEB SCRAPER + AI STARTED")
        logger.info("="*70)
        logger.info(f"Total leads: {len(df)}")
        logger.info(f"Workers: {self.workers}")
        logger.info(f"AI model: {self.ai_model}")
        logger.info(f"Scraping mode: {self.scraping_mode}")
        logger.info(f"Max pages: {self.max_pages}")
        logger.info("="*70)

        start_time = time.time()
        all_results = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(self.process_lead, row.to_dict()): idx
                for idx, row in df.iterrows()
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Task failed: {e}")

        df_results = pd.DataFrame(all_results)

        # Print summary
        duration = time.time() - start_time
        logger.info("="*70)
        logger.info("PROCESSING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Scraping success: {self.stats['scraping_success']}")
        logger.info(f"AI success: {self.stats['ai_success']}")
        logger.info(f"Total cost: ${self.stats['total_cost']:.2f}")
        logger.info(f"Duration: {duration:.2f}s ({duration/60:.1f} min)")
        logger.info("="*70)

        return df_results


def main():
    """Main CLI handler"""
    parser = argparse.ArgumentParser(description='Web Scraper + AI Enrichment')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--prompt-file', required=True, help='AI prompt template file')
    parser.add_argument('--website-column', default='website', help='Website column name')
    parser.add_argument('--name-column', default='name', help='Company name column')
    parser.add_argument('--workers', type=int, default=20, help='Scraping workers (default: 20)')
    parser.add_argument('--ai-workers', type=int, default=5, help='AI workers (default: 5)')
    parser.add_argument('--max-pages', type=int, default=5, help='Max pages per site (default: 5)')
    parser.add_argument('--scraping-mode',
                       choices=['homepage_only', 'multi_page'],
                       default='multi_page',
                       help='Scraping mode (default: multi_page)')
    parser.add_argument('--ai-model',
                       default='gpt-4o-mini',
                       help='OpenAI model (default: gpt-4o-mini)')
    parser.add_argument('--limit', type=int, help='Limit rows for testing')

    args = parser.parse_args()

    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        logger.error("Please set OPENAI_API_KEY in .env file")
        sys.exit(1)

    # Load prompt template
    try:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        logger.info(f"Loaded AI prompt from: {args.prompt_file}")
    except Exception as e:
        logger.error(f"Failed to load prompt file: {e}")
        sys.exit(1)

    # Load CSV
    try:
        logger.info(f"Loading CSV from: {args.input}")
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    # Rename columns
    rename_map = {}
    if args.website_column in df.columns:
        rename_map[args.website_column] = 'website'
    if args.name_column in df.columns:
        rename_map[args.name_column] = 'name'

    if rename_map:
        df = df.rename(columns=rename_map)

    # Validate required columns
    if 'website' not in df.columns:
        logger.error(f"Website column not found. Available columns: {df.columns.tolist()}")
        sys.exit(1)

    # Add name column if missing
    if 'name' not in df.columns:
        df['name'] = df['website'].apply(lambda x: x.split('//')[-1].split('/')[0] if x else 'Unknown')

    # Limit rows for testing
    if args.limit:
        df = df.head(args.limit)
        logger.info(f"Limited to {len(df)} rows")

    # Process
    scraper = WebScraperAI(
        openai_api_key=api_key,
        ai_prompt_template=prompt_template,
        workers=args.workers,
        ai_workers=args.ai_workers,
        max_pages=args.max_pages,
        scraping_mode=args.scraping_mode,
        ai_model=args.ai_model
    )

    df_results = scraper.process_batch(df)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent / "results" / f"scraped_ai_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Success/failed split
    success_df = df_results[
        (df_results['scrape_status'] == 'success') &
        (df_results['ai_status'] == 'success')
    ].copy()

    failed_df = df_results[
        (df_results['scrape_status'] == 'failed') |
        (df_results['ai_status'] == 'failed')
    ].copy()

    # Save files
    success_df.to_csv(output_dir / "success.csv", index=False, encoding='utf-8-sig')
    success_df.to_json(output_dir / "success.json", orient='records', indent=2, force_ascii=False)

    failed_df.to_csv(output_dir / "failed.csv", index=False, encoding='utf-8-sig')
    failed_df.to_json(output_dir / "failed.json", orient='records', indent=2, force_ascii=False)

    # Analytics
    analytics = {
        'summary': {
            'total': len(df_results),
            'success': len(success_df),
            'failed': len(failed_df),
            'total_cost': round(scraper.stats['total_cost'], 2)
        },
        'stats': scraper.stats
    }

    with open(output_dir / "analytics.json", 'w') as f:
        json.dump(analytics, f, indent=2)

    logger.info("")
    logger.info(f"Results saved to: {output_dir}")
    logger.info(f"Success: {len(success_df)} | Failed: {len(failed_df)}")
    logger.info(f"Total cost: ${scraper.stats['total_cost']:.2f}")


if __name__ == "__main__":
    main()
