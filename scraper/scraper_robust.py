#!/usr/bin/env python3
"""
=== ROBUST ASYNC WEB SCRAPER WITH AI SUMMARY ===
Version: 3.0.0 | Created: 2025-12-18

IMPROVEMENTS FOR 80%+ SUCCESS RATE:
1. Retry logic: 3 attempts with exponential backoff (10s → 20s → 30s)
2. Fallback URL strategies: https → http, www variants
3. Detailed error tracking and statistics breakdown
4. Smart error handling for different failure types

TARGET: 80%+ success rate (vs 44% baseline)

USAGE:
python scraper/scraper_robust.py
"""

import sys
import os
import time
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
import pandas as pd
import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from bs4 import BeautifulSoup
import html2text
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

load_dotenv()

# ========================
# ERROR TRACKING
# ========================

@dataclass
class ErrorStats:
    """Track detailed error statistics."""
    total_attempts: int = 0
    successful: int = 0
    failed: int = 0

    # Error types
    timeout_errors: int = 0
    http_403_errors: int = 0
    http_404_errors: int = 0
    http_other_errors: int = 0
    ssl_errors: int = 0
    dns_errors: int = 0
    connection_errors: int = 0
    other_errors: int = 0

    # Retry stats
    succeeded_on_retry: int = 0
    succeeded_with_fallback: int = 0

    # Timing
    total_time: float = 0.0
    avg_time_per_site: float = 0.0

    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful / self.total_attempts) * 100

    def print_summary(self):
        """Print detailed error breakdown."""
        logger.info("\n" + "=" * 60)
        logger.info("ERROR STATISTICS BREAKDOWN")
        logger.info("=" * 60)
        logger.info(f"Total attempts: {self.total_attempts}")
        logger.info(f"Successful: {self.successful} ({self.success_rate():.1f}%)")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"\nRetry success:")
        logger.info(f"  - Succeeded on retry: {self.succeeded_on_retry}")
        logger.info(f"  - Succeeded with fallback URL: {self.succeeded_with_fallback}")
        logger.info(f"\nFailure breakdown:")
        logger.info(f"  - Timeout: {self.timeout_errors}")
        logger.info(f"  - HTTP 403 (Forbidden): {self.http_403_errors}")
        logger.info(f"  - HTTP 404 (Not Found): {self.http_404_errors}")
        logger.info(f"  - HTTP Other: {self.http_other_errors}")
        logger.info(f"  - SSL errors: {self.ssl_errors}")
        logger.info(f"  - DNS errors: {self.dns_errors}")
        logger.info(f"  - Connection errors: {self.connection_errors}")
        logger.info(f"  - Other: {self.other_errors}")
        logger.info(f"\nPerformance:")
        logger.info(f"  - Total time: {self.total_time:.1f}s")
        logger.info(f"  - Avg per site: {self.avg_time_per_site:.2f}s")
        logger.info("=" * 60)


# Global stats object
error_stats = ErrorStats()

# ========================
# CONFIG
# ========================

CONFIG = {
    "INPUT_FILE": "scraper/input/recruitment_batch1.csv",
    "WEBSITE_COLUMN": "Company Website",

    "TEST_MODE": True,
    "TEST_ROWS": 50,
    "HOMEPAGE_ONLY": True,
    "CONCURRENT_SCRAPERS": 50,  # Reduced for more stability

    # RETRY SETTINGS
    "MAX_RETRIES": 3,
    "RETRY_TIMEOUTS": [10, 20, 30],  # Progressive timeouts
    "TRY_FALLBACK_URLS": True,  # Try http/https, www variants

    "TEXT_FORMAT": "markdown",
    "MAX_WORDS": 6000,

    "AI_PROCESSING": True,
    "OPENAI_MODEL": "gpt-4o-mini",
    "CONCURRENT_AI_CALLS": 30,
    "AI_PROMPT": """Analyze this website content and provide a detailed summary.

Focus on:
- What does this company/website do?
- What products/services do they offer?
- Who is their target audience?
- Any unique value propositions or key features?

Be thorough but concise. Extract the most important information.""",

    "OUTPUT_DIR": "scraper/results",
    "ADD_SUMMARY_COLUMN": True,
    "ADD_CONTENT_COLUMN": False,
    "ADD_ERROR_DETAILS": True,  # Add error_reason column
}

# ========================
# URL UTILITIES
# ========================

def generate_url_variants(url: str) -> List[str]:
    """
    Generate URL variants to try as fallbacks.

    Returns list: [original, without_www, with_www, http_version, etc]
    """
    url = url.strip()
    if not url:
        return []

    variants = []

    # Normalize base URL
    if not url.startswith(('http://', 'https://')):
        base_url = url
    else:
        base_url = url.replace('https://', '').replace('http://', '')

    # Remove trailing slash
    base_url = base_url.rstrip('/')

    # Generate variants
    # 1. Original with https and www
    if not base_url.startswith('www.'):
        variants.append(f'https://www.{base_url}')
    else:
        variants.append(f'https://{base_url}')

    # 2. https without www
    no_www = base_url.replace('www.', '', 1)
    variants.append(f'https://{no_www}')

    # 3. http with www
    if not base_url.startswith('www.'):
        variants.append(f'http://www.{base_url}')
    else:
        variants.append(f'http://{base_url}')

    # 4. http without www
    variants.append(f'http://{no_www}')

    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)

    return unique_variants


# ========================
# ROBUST SCRAPING WITH RETRY
# ========================

async def scrape_single_attempt(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int,
    attempt: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    Single scrape attempt.

    Returns:
        (content, error_reason) - one will be None
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        async with session.get(url, headers=headers, ssl=False, timeout=timeout) as response:
            if response.status == 403:
                error_stats.http_403_errors += 1
                return (None, f"HTTP 403 Forbidden")

            if response.status == 404:
                error_stats.http_404_errors += 1
                return (None, f"HTTP 404 Not Found")

            if response.status != 200:
                error_stats.http_other_errors += 1
                return (None, f"HTTP {response.status}")

            html = await response.text()

            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')

            # Remove unwanted elements
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
                tag.decompose()

            # Convert to markdown
            if CONFIG['TEXT_FORMAT'] == 'markdown':
                h = html2text.HTML2Text()
                h.ignore_links = False
                h.ignore_images = True
                h.body_width = 0
                text = h.handle(str(soup))
            else:
                text = soup.get_text(separator=' ', strip=True)

            # Clean whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            text = text.strip()

            # Truncate to max words
            words = text.split()
            if len(words) > CONFIG['MAX_WORDS']:
                text = ' '.join(words[:CONFIG['MAX_WORDS']])
                text += '\n\n[Content truncated due to length...]'

            return (text, None)

    except asyncio.TimeoutError:
        error_stats.timeout_errors += 1
        return (None, f"Timeout ({timeout}s)")

    except aiohttp.ClientSSLError as e:
        error_stats.ssl_errors += 1
        return (None, f"SSL Error")

    except aiohttp.ClientConnectorError as e:
        error_stats.dns_errors += 1
        return (None, f"DNS/Connection Error")

    except aiohttp.ClientConnectionError as e:
        error_stats.connection_errors += 1
        return (None, f"Connection Error")

    except Exception as e:
        error_stats.other_errors += 1
        return (None, f"Error: {type(e).__name__}")


async def scrape_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    idx: int
) -> Tuple[int, Optional[str], str, str]:
    """
    Scrape with retry logic and fallback URLs.

    Returns:
        (idx, content, status, error_reason)
    """
    error_stats.total_attempts += 1
    original_url = url

    # Generate URL variants for fallback
    url_variants = generate_url_variants(url)

    if not url_variants:
        error_stats.failed += 1
        return (idx, None, 'no_url', 'Empty URL')

    last_error = "Unknown error"
    attempted_urls = []

    # Try each URL variant
    for variant_idx, url_to_try in enumerate(url_variants):
        attempted_urls.append(url_to_try)

        # Try with progressive timeouts
        for attempt in range(CONFIG['MAX_RETRIES']):
            timeout_seconds = CONFIG['RETRY_TIMEOUTS'][attempt]

            logger.info(f"[{idx}] Attempt {attempt + 1}/{CONFIG['MAX_RETRIES']} - URL variant {variant_idx + 1}/{len(url_variants)}: {url_to_try} (timeout: {timeout_seconds}s)")

            content, error_reason = await scrape_single_attempt(
                session,
                url_to_try,
                timeout_seconds,
                attempt + 1
            )

            if content:
                # SUCCESS!
                words = len(content.split())
                logger.info(f"[{idx}] ✅ Success on attempt {attempt + 1}, variant {variant_idx + 1}: {words} words")

                error_stats.successful += 1

                if attempt > 0:
                    error_stats.succeeded_on_retry += 1

                if variant_idx > 0:
                    error_stats.succeeded_with_fallback += 1

                status_msg = f"success_attempt_{attempt + 1}"
                if variant_idx > 0:
                    status_msg += f"_variant_{variant_idx + 1}"

                return (idx, content, status_msg, "")

            last_error = error_reason or "Unknown error"

            # If 404, don't retry - page doesn't exist
            if "404" in last_error:
                break

            # Small delay between retries
            if attempt < CONFIG['MAX_RETRIES'] - 1:
                await asyncio.sleep(0.5)

        # If we got 403 or timeout, try next URL variant
        # If 404, break - no point trying other variants
        if "404" in last_error:
            break

    # All attempts failed
    error_stats.failed += 1
    logger.warning(f"[{idx}] ❌ Failed after all attempts. Last error: {last_error}")
    logger.warning(f"[{idx}] Tried URLs: {', '.join(attempted_urls)}")

    return (idx, None, 'scrape_failed', last_error)


async def scrape_batch_robust(
    session: aiohttp.ClientSession,
    urls: List[Tuple[int, str]],
    semaphore: asyncio.Semaphore
) -> List[Tuple[int, Optional[str], str, str]]:
    """Scrape batch with retry logic."""
    async def scrape_with_semaphore(idx, url):
        async with semaphore:
            return await scrape_with_retry(session, url, idx)

    tasks = [scrape_with_semaphore(idx, url) for idx, url in urls]
    return await asyncio.gather(*tasks, return_exceptions=False)


# ========================
# AI PROCESSING (unchanged)
# ========================

async def get_ai_summary(
    client: AsyncOpenAI,
    content: str,
    idx: int,
    custom_prompt: Optional[str] = None
) -> Tuple[int, Optional[str]]:
    """Generate AI summary."""
    if not CONFIG['AI_PROCESSING']:
        return (idx, None)

    try:
        prompt = custom_prompt or CONFIG['AI_PROMPT']

        messages = [
            {"role": "system", "content": "You are a helpful assistant that analyzes website content."},
            {"role": "user", "content": f"{prompt}\n\nWebsite content:\n{content}"}
        ]

        response = await client.chat.completions.create(
            model=CONFIG['OPENAI_MODEL'],
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"[{idx}] Generated summary: {len(summary)} chars")
        return (idx, summary)

    except Exception as e:
        logger.error(f"[{idx}] Error generating AI summary: {e}")
        return (idx, None)


async def process_ai_batch(
    client: AsyncOpenAI,
    contents: List[Tuple[int, str]],
    semaphore: asyncio.Semaphore
) -> List[Tuple[int, Optional[str]]]:
    """Process AI summaries in batch."""
    async def ai_with_semaphore(idx, content):
        async with semaphore:
            return await get_ai_summary(client, content, idx)

    tasks = [ai_with_semaphore(idx, content) for idx, content in contents]
    return await asyncio.gather(*tasks, return_exceptions=False)


# ========================
# MAIN ASYNC PROCESSING
# ========================

async def process_csv_async(input_file: str) -> str:
    """Main async processing with robust error handling."""
    logger.info("=" * 60)
    logger.info("ROBUST ASYNC WEB SCRAPER WITH AI SUMMARY")
    logger.info("=" * 60)

    # Read input CSV
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} rows from {input_file}")

    # Check for website column
    if CONFIG['WEBSITE_COLUMN'] not in df.columns:
        raise ValueError(f"Column '{CONFIG['WEBSITE_COLUMN']}' not found in CSV")

    # Test mode
    if CONFIG['TEST_MODE']:
        df = df.head(CONFIG['TEST_ROWS'])
        logger.info(f"TEST MODE: Processing only {len(df)} rows")

    # Add new columns
    df['scraped_content'] = None
    df['ai_summary'] = None
    df['scrape_status'] = 'pending'
    if CONFIG['ADD_ERROR_DETAILS']:
        df['error_reason'] = None

    # Prepare URLs list
    urls_to_scrape = []
    for idx, row in df.iterrows():
        website = row[CONFIG['WEBSITE_COLUMN']]
        if pd.notna(website) and website:
            urls_to_scrape.append((idx, website))
        else:
            df.at[idx, 'scrape_status'] = 'no_url'
            if CONFIG['ADD_ERROR_DETAILS']:
                df.at[idx, 'error_reason'] = 'Empty URL'

    logger.info(f"\n🚀 Starting robust scraping: {len(urls_to_scrape)} URLs")
    logger.info(f"Max retries: {CONFIG['MAX_RETRIES']}")
    logger.info(f"Retry timeouts: {CONFIG['RETRY_TIMEOUTS']}")
    logger.info(f"Fallback URLs: {CONFIG['TRY_FALLBACK_URLS']}")
    logger.info(f"Concurrent scrapers: {CONFIG['CONCURRENT_SCRAPERS']}")

    start_time = time.time()

    # PHASE 1: Scrape all websites with retry logic
    logger.info("\n[PHASE 1/2] Scraping websites with retry + fallback...")

    timeout = ClientTimeout(total=max(CONFIG['RETRY_TIMEOUTS']))
    connector = TCPConnector(limit=CONFIG['CONCURRENT_SCRAPERS'], limit_per_host=5)
    scrape_semaphore = asyncio.Semaphore(CONFIG['CONCURRENT_SCRAPERS'])

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        scrape_results = await scrape_batch_robust(session, urls_to_scrape, scrape_semaphore)

    scrape_time = time.time() - start_time
    error_stats.total_time = scrape_time
    error_stats.avg_time_per_site = scrape_time / len(urls_to_scrape) if urls_to_scrape else 0

    # Process scrape results
    scraped_contents = []

    for idx, content, status, error_reason in scrape_results:
        df.at[idx, 'scrape_status'] = status

        if CONFIG['ADD_ERROR_DETAILS']:
            df.at[idx, 'error_reason'] = error_reason

        if content:
            df.at[idx, 'scraped_content'] = content
            scraped_contents.append((idx, content))

    logger.info(f"\n✅ Scraping complete!")
    logger.info(f"Success rate: {error_stats.success_rate():.1f}%")
    logger.info(f"Total time: {scrape_time:.1f}s")

    # Print detailed error statistics
    error_stats.print_summary()

    # PHASE 2: Generate AI summaries
    if CONFIG['AI_PROCESSING'] and scraped_contents:
        logger.info(f"\n[PHASE 2/2] Generating AI summaries for {len(scraped_contents)} sites...")

        ai_start = time.time()
        client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        ai_semaphore = asyncio.Semaphore(CONFIG['CONCURRENT_AI_CALLS'])

        ai_results = await process_ai_batch(client, scraped_contents, ai_semaphore)

        ai_time = time.time() - ai_start

        # Process AI results
        successful_ai = 0
        for idx, summary in ai_results:
            if summary:
                df.at[idx, 'ai_summary'] = summary
                successful_ai += 1
            else:
                # Keep scrape_status if AI failed
                pass

        logger.info(f"✅ Generated {successful_ai}/{len(scraped_contents)} summaries in {ai_time:.1f}s")

    total_time = time.time() - start_time

    # Prepare output
    output_df = df.copy()

    if not CONFIG['ADD_CONTENT_COLUMN']:
        output_df = output_df.drop(columns=['scraped_content'])

    if not CONFIG['ADD_SUMMARY_COLUMN']:
        output_df = output_df.drop(columns=['ai_summary'])

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{CONFIG['OUTPUT_DIR']}/scraped_robust_{timestamp}.csv"

    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
    output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("FINAL RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(df)}")
    logger.info(f"Successful: {error_stats.successful}")
    logger.info(f"Failed: {error_stats.failed}")
    logger.info(f"Success rate: {error_stats.success_rate():.1f}%")
    logger.info(f"Total time: {total_time:.1f}s")
    logger.info(f"\nOutput saved to: {output_file}")
    logger.info("=" * 60)

    return output_file


def process_csv(input_file: str) -> str:
    """Sync wrapper."""
    return asyncio.run(process_csv_async(input_file))


def main():
    """Main entry point."""
    try:
        output_file = asyncio.run(process_csv_async(CONFIG['INPUT_FILE']))
        logger.info(f"\n✅ Done! Check results: {output_file}")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
