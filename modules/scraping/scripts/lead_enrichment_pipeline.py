#!/usr/bin/env python3
"""
=== COMPREHENSIVE LEAD ENRICHMENT PIPELINE ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Complete lead enrichment workflow:
1. Multi-page email discovery (homepage → sitemap → pattern)
2. Content scraping (clean text for AI analysis)
3. AI-powered summarization (business type, wars, activities)
4. Personalization data extraction (icebreaker material)
5. Comprehensive analytics

WORKFLOW:
Input CSV → Scrape Homepage → Extract Emails + Content →
Multi-page Search (if needed) → AI Analysis → Output CSV + Analytics

FEATURES:
- Smart multi-page email search (sitemap-first)
- Multiple emails collection (all found emails)
- Clean text extraction (no HTML)
- AI summarization via OpenAI
- Personalization info for cold outreach
- Detailed analytics (homepage vs deep search)
- Parallel processing

USAGE:
python lead_enrichment_pipeline.py --input enriched.csv --output final.csv

INPUT CSV Required Columns:
- place_id
- name
- website

OUTPUT CSV Columns:
- All input columns
- emails (comma-separated)
- email_count
- email_source (homepage | deep_search | none)
- scraped_content (clean text)
- summary (AI-generated)
- focus_areas (wars, periods, activities)
- personalization_hooks (icebreaker material)
- relevance_score (0-10 for Soviet boots)

COST ESTIMATION:
- Scraping: Free (HTTP only)
- AI Analysis: ~$0.01 per place (OpenAI GPT-4o-mini)
- Total for 100 places: ~$1-2

IMPROVEMENTS:
v1.0.0 - Initial comprehensive pipeline
"""

import os
import sys
import time
import argparse
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import scraping utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from lib.http_utils import HTTPClient
    from lib.text_utils import extract_emails_from_html, clean_html_to_text
    from lib.sitemap_utils import SitemapParser
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html, clean_html_to_text
    from modules.scraping.lib.sitemap_utils import SitemapParser

# OpenAI for AI analysis
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - AI analysis will be skipped")

from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "scraping": {
        "timeout": 15,
        "retries": 3,
        "max_content_length": 20000,
        "workers": 10,
    },
    "email_search": {
        "max_pages_deep_search": 5,
        "stop_on_first_email": False,
    },
    "ai_analysis": {
        "enabled": True,
        "model": "gpt-4o-mini",
        "max_tokens": 500,
        "temperature": 0.3,
    }
}

# ============================================================================
# LEAD ENRICHMENT ENGINE
# ============================================================================

class LeadEnrichmentEngine:
    """
    Comprehensive lead enrichment pipeline

    Combines scraping, email discovery, and AI analysis
    """

    def __init__(self, config: Dict):
        self.config = config
        self.http_client = HTTPClient(
            timeout=config["scraping"]["timeout"],
            retries=config["scraping"]["retries"]
        )
        self.sitemap_parser = SitemapParser(
            timeout=config["scraping"]["timeout"]
        )

        # Initialize OpenAI if available and enabled
        self.openai_client = None
        if config["ai_analysis"]["enabled"] and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OPENAI_API_KEY not found - AI analysis disabled")

        # Stats tracking
        self.stats = {
            "total_processed": 0,
            "homepage_emails": 0,
            "deep_search_emails": 0,
            "no_emails": 0,
            "ai_analysis_success": 0,
            "ai_analysis_failed": 0,
            "scraping_failed": 0,
        }

    def scrape_homepage(self, website: str) -> Dict:
        """
        Scrape homepage and extract emails + content

        Returns:
            {
                'success': bool,
                'emails': [list of emails],
                'content': clean text,
                'html': raw HTML (for fallback)
            }
        """
        result = {
            'success': False,
            'emails': [],
            'content': '',
            'html': ''
        }

        # Normalize URL
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            # Fetch homepage
            response = self.http_client.fetch(website, check_content_length=False)

            if response['status'] == 'success':
                html_content = response['content']
                result['html'] = html_content

                # Extract emails from homepage
                emails = extract_emails_from_html(html_content)
                result['emails'] = [self._clean_email(e) for e in emails if self._clean_email(e)]

                # Extract clean text
                clean_text = clean_html_to_text(
                    html_content,
                    max_length=self.config["scraping"]["max_content_length"]
                )
                result['content'] = clean_text

                result['success'] = True

        except Exception as e:
            logger.error(f"Homepage scraping failed for {website}: {e}")

        return result

    def deep_email_search(self, website: str) -> List[str]:
        """
        Multi-page email search using sitemap + patterns

        Returns:
            List of found emails
        """
        all_emails = []

        try:
            # Get smart pages
            discovery = self.sitemap_parser.get_smart_pages(
                website,
                max_pages=self.config["email_search"]["max_pages_deep_search"]
            )

            # Scrape discovered pages
            for page_url in discovery['pages']:
                try:
                    response = self.http_client.fetch(page_url, check_content_length=False)

                    if response['status'] == 'success':
                        emails = extract_emails_from_html(response['content'])
                        clean_emails = [self._clean_email(e) for e in emails if self._clean_email(e)]
                        all_emails.extend(clean_emails)

                        # Stop if we have emails and config says so
                        if all_emails and self.config["email_search"]["stop_on_first_email"]:
                            break

                except Exception as e:
                    continue

        except Exception as e:
            logger.error(f"Deep search failed for {website}: {e}")

        # Deduplicate
        return list(set(all_emails))

    def analyze_with_ai(self, name: str, content: str) -> Dict:
        """
        AI-powered analysis for summarization + personalization

        Returns:
            {
                'summary': business description,
                'focus_areas': {wars, periods, activities},
                'personalization_hooks': icebreaker material,
                'relevance_score': 0-10
            }
        """
        if not self.openai_client or not content:
            return self._empty_ai_result()

        try:
            # Truncate content if too long
            content_truncated = content[:4000]

            prompt = f"""Analyze this military history organization website.

Organization: {name}
Content: {content_truncated}

Provide analysis in JSON format:
{{
  "summary": "Brief 2-3 sentence description of what they do",
  "type": "museum | reenactment_club | historical_society | research_center | store | other",
  "focus_areas": {{
    "wars": ["WW2", "Cold War", "Afghan War", etc.],
    "periods": ["1939-1945", "Soviet Era", etc.],
    "specific_topics": ["Soviet Army", "Red Army", "Military Equipment", etc.],
    "activities": ["reenactment", "collecting", "education", "preservation", etc.]
  }},
  "personalization_hooks": [
    "List 2-3 specific interesting facts or unique aspects that could be used for personalized cold outreach icebreakers"
  ],
  "relevance_score": {{
    "score": 0-10,
    "reasoning": "Why this score for selling authentic Soviet military boots"
  }}
}}

Focus on Soviet/Russian military history relevance."""

            response = self.openai_client.chat.completions.create(
                model=self.config["ai_analysis"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert analyzer of military history organizations. Provide structured JSON analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config["ai_analysis"]["temperature"],
                max_tokens=self.config["ai_analysis"]["max_tokens"],
                response_format={"type": "json_object"}
            )

            # Parse AI response
            ai_output = json.loads(response.choices[0].message.content)

            return {
                'summary': ai_output.get('summary', ''),
                'type': ai_output.get('type', 'unknown'),
                'focus_wars': ', '.join(ai_output.get('focus_areas', {}).get('wars', [])),
                'focus_periods': ', '.join(ai_output.get('focus_areas', {}).get('periods', [])),
                'focus_topics': ', '.join(ai_output.get('focus_areas', {}).get('specific_topics', [])),
                'activities': ', '.join(ai_output.get('focus_areas', {}).get('activities', [])),
                'personalization_hooks': ' | '.join(ai_output.get('personalization_hooks', [])),
                'relevance_score': ai_output.get('relevance_score', {}).get('score', 0),
                'relevance_reasoning': ai_output.get('relevance_score', {}).get('reasoning', '')
            }

        except Exception as e:
            logger.error(f"AI analysis failed for {name}: {e}")
            return self._empty_ai_result()

    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Complete enrichment pipeline for single lead

        Args:
            lead: Dict with keys: place_id, name, website

        Returns:
            Enriched lead dict
        """
        place_id = lead.get('place_id')
        name = lead.get('name', 'Unknown')
        website = lead.get('website', '')

        result = {
            'place_id': place_id,
            'name': name,
            'website': website,
            'emails': '',
            'email_count': 0,
            'email_source': 'none',
            'scraped_content': '',
            'summary': '',
            'type': '',
            'focus_wars': '',
            'focus_periods': '',
            'focus_topics': '',
            'activities': '',
            'personalization_hooks': '',
            'relevance_score': 0,
            'relevance_reasoning': '',
            'processing_status': 'pending'
        }

        # Handle NaN/None website
        if pd.isna(website) or not website or not isinstance(website, str):
            result['processing_status'] = 'no_website'
            return result

        try:
            # Step 1: Scrape homepage
            homepage_data = self.scrape_homepage(website)

            if not homepage_data['success']:
                result['processing_status'] = 'scraping_failed'
                self.stats['scraping_failed'] += 1
                return result

            result['scraped_content'] = homepage_data['content']

            # Step 2: Email collection
            all_emails = homepage_data['emails']

            if all_emails:
                # Emails found on homepage
                result['email_source'] = 'homepage'
                self.stats['homepage_emails'] += 1
            else:
                # Deep search needed
                deep_emails = self.deep_email_search(website)
                all_emails = deep_emails

                if all_emails:
                    result['email_source'] = 'deep_search'
                    self.stats['deep_search_emails'] += 1
                else:
                    result['email_source'] = 'none'
                    self.stats['no_emails'] += 1

            result['emails'] = ', '.join(all_emails)
            result['email_count'] = len(all_emails)

            # Step 3: AI Analysis
            ai_result = self.analyze_with_ai(name, homepage_data['content'])
            result.update(ai_result)

            if ai_result['summary']:
                self.stats['ai_analysis_success'] += 1
            else:
                self.stats['ai_analysis_failed'] += 1

            result['processing_status'] = 'success'
            self.stats['total_processed'] += 1

        except Exception as e:
            logger.error(f"Lead enrichment failed for {name}: {e}")
            result['processing_status'] = 'error'

        return result

    def process_batch(self, leads_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process batch of leads with parallel workers

        Returns:
            DataFrame with enriched results
        """
        results = []
        total = len(leads_df)

        logger.info(f"Starting enrichment of {total} leads...")
        logger.info(f"Workers: {self.config['scraping']['workers']}")

        with ThreadPoolExecutor(max_workers=self.config['scraping']['workers']) as executor:
            # Submit all tasks
            future_to_lead = {
                executor.submit(self.enrich_lead, row.to_dict()): idx
                for idx, row in leads_df.iterrows()
            }

            # Process completed
            for future in as_completed(future_to_lead):
                idx = future_to_lead[future]

                try:
                    result = future.result()
                    results.append(result)

                    # Progress logging
                    processed = len(results)
                    if processed % 10 == 0 or processed == total:
                        print(f"[{processed}/{total}] {result['name'][:50]:<50} | "
                              f"Emails: {result['email_count']:<2} | "
                              f"Source: {result['email_source']:<12} | "
                              f"Status: {result['processing_status']}")

                    if processed % 20 == 0:
                        self._print_interim_stats(processed, total)

                except Exception as e:
                    logger.error(f"Task failed: {e}")

        return pd.DataFrame(results)

    def _clean_email(self, email: str) -> Optional[str]:
        """Clean and validate email"""
        if not email:
            return None

        email = email.lower().strip()

        # Filter fake emails
        fake_patterns = [
            'example.com', 'test.com', 'placeholder',
            'noreply@', 'no-reply@', 'donotreply@',
            'webmaster@', 'postmaster@',
            'info@example', 'contact@example'
        ]

        if any(pattern in email for pattern in fake_patterns):
            return None

        # Validate format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return None

        return email

    def _empty_ai_result(self) -> Dict:
        """Empty AI result for fallback"""
        return {
            'summary': '',
            'type': '',
            'focus_wars': '',
            'focus_periods': '',
            'focus_topics': '',
            'activities': '',
            'personalization_hooks': '',
            'relevance_score': 0,
            'relevance_reasoning': ''
        }

    def _print_interim_stats(self, processed: int, total: int):
        """Print interim statistics"""
        logger.info(f"\n=== INTERIM STATS ({processed}/{total}) ===")
        logger.info(f"Homepage emails: {self.stats['homepage_emails']}")
        logger.info(f"Deep search emails: {self.stats['deep_search_emails']}")
        logger.info(f"No emails: {self.stats['no_emails']}")
        logger.info(f"AI success: {self.stats['ai_analysis_success']}")
        logger.info(f"Failed: {self.stats['scraping_failed']}")
        logger.info("")

    def get_stats(self) -> Dict:
        """Get final statistics"""
        return self.stats.copy()

# ============================================================================
# ANALYTICS GENERATOR
# ============================================================================

def generate_analytics(results_df: pd.DataFrame, stats: Dict, elapsed_time: float) -> Dict:
    """
    Generate comprehensive analytics report

    Returns:
        Dict with all analytics
    """
    total = len(results_df)

    analytics = {
        "overview": {
            "total_leads": total,
            "processing_time_minutes": round(elapsed_time / 60, 2),
            "avg_time_per_lead": round(elapsed_time / max(total, 1), 2),
        },
        "email_discovery": {
            "total_with_emails": stats['homepage_emails'] + stats['deep_search_emails'],
            "homepage_emails": stats['homepage_emails'],
            "deep_search_emails": stats['deep_search_emails'],
            "no_emails": stats['no_emails'],
            "homepage_success_rate": round(stats['homepage_emails'] / max(total, 1) * 100, 1),
            "deep_search_success_rate": round(stats['deep_search_emails'] / max(total, 1) * 100, 1),
            "total_email_coverage": round((stats['homepage_emails'] + stats['deep_search_emails']) / max(total, 1) * 100, 1),
        },
        "content_analysis": {
            "ai_analysis_success": stats['ai_analysis_success'],
            "ai_analysis_failed": stats['ai_analysis_failed'],
            "ai_success_rate": round(stats['ai_analysis_success'] / max(total, 1) * 100, 1),
        },
        "relevance": {
            "avg_relevance_score": round(results_df['relevance_score'].mean(), 2),
            "high_relevance_7_plus": len(results_df[results_df['relevance_score'] >= 7]),
            "medium_relevance_4_6": len(results_df[(results_df['relevance_score'] >= 4) & (results_df['relevance_score'] < 7)]),
            "low_relevance_0_3": len(results_df[results_df['relevance_score'] < 4]),
        },
        "lead_types": results_df['type'].value_counts().to_dict() if 'type' in results_df.columns else {},
        "failures": {
            "scraping_failed": stats['scraping_failed'],
            "no_website": len(results_df[results_df['processing_status'] == 'no_website']),
        }
    }

    return analytics

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Lead Enrichment Pipeline')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with leads')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers')
    parser.add_argument('--limit', type=int, default=None, help='Limit for testing')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')

    args = parser.parse_args()

    # Update config
    if args.workers:
        CONFIG["scraping"]["workers"] = args.workers
    if args.no_ai:
        CONFIG["ai_analysis"]["enabled"] = False

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE LEAD ENRICHMENT PIPELINE")
    logger.info("=" * 80)

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading leads from: {input_path}")
    df = pd.read_csv(input_path)

    # Validate columns
    required_cols = ['place_id', 'name', 'website']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return

    logger.info(f"Total leads loaded: {len(df)}")

    # Apply limit if testing
    if args.limit:
        df = df.head(args.limit)
        logger.info(f"TESTING MODE: Limited to {args.limit} leads")

    # Initialize engine
    engine = LeadEnrichmentEngine(CONFIG)

    # Process
    logger.info("\nStarting enrichment...\n")
    start_time = time.time()

    results_df = engine.process_batch(df)

    elapsed_time = time.time() - start_time

    # Generate analytics
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING ANALYTICS")
    logger.info("=" * 80)

    stats = engine.get_stats()
    analytics = generate_analytics(results_df, stats, elapsed_time)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False, encoding='utf-8')

    # Save analytics
    analytics_path = output_path.parent / f"analytics_{output_path.stem}.json"
    with open(analytics_path, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)

    # Print final report
    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total leads processed: {analytics['overview']['total_leads']}")
    logger.info(f"Processing time: {analytics['overview']['processing_time_minutes']} minutes")
    logger.info("")
    logger.info("EMAIL DISCOVERY:")
    logger.info(f"  Homepage emails: {analytics['email_discovery']['homepage_emails']} ({analytics['email_discovery']['homepage_success_rate']}%)")
    logger.info(f"  Deep search emails: {analytics['email_discovery']['deep_search_emails']} ({analytics['email_discovery']['deep_search_success_rate']}%)")
    logger.info(f"  Total email coverage: {analytics['email_discovery']['total_email_coverage']}%")
    logger.info(f"  No emails found: {analytics['email_discovery']['no_emails']}")
    logger.info("")
    logger.info("RELEVANCE:")
    logger.info(f"  Avg relevance score: {analytics['relevance']['avg_relevance_score']}/10")
    logger.info(f"  High relevance (7+): {analytics['relevance']['high_relevance_7_plus']}")
    logger.info(f"  Medium relevance (4-6): {analytics['relevance']['medium_relevance_4_6']}")
    logger.info(f"  Low relevance (0-3): {analytics['relevance']['low_relevance_0_3']}")
    logger.info("")
    logger.info(f"Output CSV: {output_path}")
    logger.info(f"Analytics: {analytics_path}")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
