#!/usr/bin/env python3
"""
=== SIMPLE WEB SCRAPER WITH AI SUMMARY ===
Version: 1.0.0 | Created: 2025-12-18

PURPOSE:
Scrape homepage content and generate AI summaries with maximum flexibility.

FEATURES:
- Homepage-only scraping (fast and focused)
- Markdown text extraction (clean and structured)
- OpenAI AI summaries with customizable prompt
- Test mode (10 rows) by default
- CSV output with summary column

USAGE:
1. Place your CSV in scraper/input/ folder (must have 'website' column)
2. Edit CONFIG section below if needed
3. Run: python scraper/scraper.py
4. Results saved to scraper/results/

DEFAULT SETTINGS:
- Test mode: 10 rows
- Homepage only: Yes
- AI Processing: Yes
- Model: gpt-4o-mini (cheap and fast)

IMPROVEMENTS:
v1.0.0 - Initial version with flexible AI summaries
"""

import sys
import os
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
import requests
from bs4 import BeautifulSoup
import html2text
from openai import OpenAI
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

# Load environment variables
load_dotenv()

# ========================
# CONFIG
# ========================

CONFIG = {
    # INPUT/OUTPUT
    "INPUT_FILE": "scraper/input/input.csv",  # CSV with 'website' column
    "WEBSITE_COLUMN": "website",  # Column name with URLs

    # SCRAPING SETTINGS
    "TEST_MODE": True,  # Only process first 10 rows
    "TEST_ROWS": 10,
    "HOMEPAGE_ONLY": True,  # Only scrape homepage (no deep search)
    "TIMEOUT": 10,  # Request timeout in seconds

    # TEXT EXTRACTION
    "TEXT_FORMAT": "markdown",  # markdown or plain_text
    "MAX_WORDS": 6000,  # Truncate to fit in GPT context (~8K tokens)

    # AI PROCESSING
    "AI_PROCESSING": True,  # Enable AI summaries
    "OPENAI_MODEL": "gpt-4o-mini",  # Cheap and fast model
    "AI_PROMPT": """Analyze this website content and provide a detailed summary.

Focus on:
- What does this company/website do?
- What products/services do they offer?
- Who is their target audience?
- Any unique value propositions or key features?

Be thorough but concise. Extract the most important information.""",

    # RATE LIMITING
    "DELAY_BETWEEN_REQUESTS": 0.5,  # Seconds between scrape requests
    "DELAY_BETWEEN_AI_CALLS": 0.2,  # Seconds between OpenAI API calls

    # OUTPUT
    "OUTPUT_DIR": "scraper/results",
    "ADD_SUMMARY_COLUMN": True,  # Add 'ai_summary' column to output
    "ADD_CONTENT_COLUMN": False,  # Add 'scraped_content' column (large!)
}

# ========================
# SCRAPING FUNCTIONS
# ========================

def normalize_url(url: str) -> str:
    """Normalize URL to ensure it has http/https prefix."""
    url = url.strip()
    if not url:
        return ""

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    return url


def scrape_homepage(url: str) -> Optional[str]:
    """
    Scrape homepage and extract text content.

    Returns:
        Markdown text or None if failed
    """
    try:
        url = normalize_url(url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=CONFIG['TIMEOUT'],
            allow_redirects=True
        )

        if response.status_code != 200:
            logger.warning(f"Failed to fetch {url}: Status {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
            tag.decompose()

        # Convert to markdown or plain text
        if CONFIG['TEXT_FORMAT'] == 'markdown':
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # No line wrapping
            text = h.handle(str(soup))
        else:
            text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = re.sub(r' {2,}', ' ', text)  # Remove multiple spaces
        text = text.strip()

        # Truncate to max words
        words = text.split()
        if len(words) > CONFIG['MAX_WORDS']:
            text = ' '.join(words[:CONFIG['MAX_WORDS']])
            text += '\n\n[Content truncated due to length...]'

        logger.info(f"Scraped {url}: {len(words)} words, {len(text)} chars")
        return text

    except requests.Timeout:
        logger.warning(f"Timeout scraping {url}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None


def get_ai_summary(content: str, custom_prompt: Optional[str] = None) -> Optional[str]:
    """
    Generate AI summary using OpenAI API.

    Args:
        content: Scraped website content
        custom_prompt: Override default prompt

    Returns:
        AI-generated summary or None if failed
    """
    if not CONFIG['AI_PROCESSING']:
        return None

    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        prompt = custom_prompt or CONFIG['AI_PROMPT']

        messages = [
            {"role": "system", "content": "You are a helpful assistant that analyzes website content."},
            {"role": "user", "content": f"{prompt}\n\nWebsite content:\n{content}"}
        ]

        response = client.chat.completions.create(
            model=CONFIG['OPENAI_MODEL'],
            messages=messages,
            temperature=0.3,
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated summary: {len(summary)} chars")
        return summary

    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return None


# ========================
# MAIN PROCESSING
# ========================

def process_csv(input_file: str) -> str:
    """
    Process CSV file: scrape websites and generate AI summaries.

    Returns:
        Path to output file
    """
    logger.info("=" * 60)
    logger.info("SIMPLE WEB SCRAPER WITH AI SUMMARY")
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

    # Process each row
    successful = 0
    failed = 0

    for idx, row in df.iterrows():
        website = row[CONFIG['WEBSITE_COLUMN']]

        if pd.isna(website) or not website:
            df.at[idx, 'scrape_status'] = 'no_url'
            failed += 1
            continue

        logger.info(f"\n[{idx + 1}/{len(df)}] Processing: {website}")

        # Scrape homepage
        content = scrape_homepage(website)
        time.sleep(CONFIG['DELAY_BETWEEN_REQUESTS'])

        if not content:
            df.at[idx, 'scrape_status'] = 'scrape_failed'
            failed += 1
            continue

        df.at[idx, 'scraped_content'] = content

        # Generate AI summary
        if CONFIG['AI_PROCESSING']:
            summary = get_ai_summary(content)
            time.sleep(CONFIG['DELAY_BETWEEN_AI_CALLS'])

            if summary:
                df.at[idx, 'ai_summary'] = summary
                df.at[idx, 'scrape_status'] = 'success'
                successful += 1
            else:
                df.at[idx, 'scrape_status'] = 'ai_failed'
                failed += 1
        else:
            df.at[idx, 'scrape_status'] = 'success'
            successful += 1

    # Prepare output
    output_df = df.copy()

    # Remove scraped_content column if not needed
    if not CONFIG['ADD_CONTENT_COLUMN']:
        output_df = output_df.drop(columns=['scraped_content'])

    # Remove ai_summary column if not needed
    if not CONFIG['ADD_SUMMARY_COLUMN']:
        output_df = output_df.drop(columns=['ai_summary'])

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{CONFIG['OUTPUT_DIR']}/scraped_{timestamp}.csv"

    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)
    output_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SCRAPING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total processed: {len(df)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success rate: {successful / len(df) * 100:.1f}%")
    logger.info(f"\nOutput saved to: {output_file}")
    logger.info("=" * 60)

    return output_file


# ========================
# MAIN
# ========================

def main():
    """Main entry point."""
    try:
        output_file = process_csv(CONFIG['INPUT_FILE'])
        logger.info(f"\nDone! Check results: {output_file}")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
