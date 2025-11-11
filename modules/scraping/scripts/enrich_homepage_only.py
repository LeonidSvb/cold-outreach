#!/usr/bin/env python3
"""
=== HOMEPAGE-ONLY LEAD ENRICHMENT ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Fast lead enrichment - homepage scraping only (no deep search)
1. Scrape homepage content
2. Extract emails from homepage
3. AI analysis for Soviet boots personalization

FEATURES:
- Homepage-only scraping (fast)
- Email extraction from homepage
- Clean text extraction for AI
- OpenAI personalization analysis
- Parallel processing
- Comprehensive analytics

USAGE:
python enrich_homepage_only.py --input input.csv --output output.csv --workers 20 --limit 150

INPUT CSV Required Columns:
- place_id
- name
- website

OUTPUT CSV Columns:
- All input columns
- emails (from homepage)
- email_count
- scraped_content
- summary
- type (museum | reenactment_club | store | etc.)
- focus_wars (WW2, Cold War, Afghan War, Chechen War, etc.)
- focus_periods
- focus_topics
- activities
- personalization_hooks
- relevance_score (0-10 for Soviet boots)
- relevance_reasoning

COST ESTIMATION:
- Scraping: Free (HTTP only)
- AI Analysis: ~$0.01 per lead (OpenAI GPT-4o-mini)
- 150 leads: ~$1.50
- 3000 leads: ~$30

IMPROVEMENTS:
v1.0.0 - Initial homepage-only version (fast & simple)
"""

import os
import sys
import time
import argparse
import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html, clean_html_to_text

# OpenAI
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
        "workers": 20,
    },
    "ai_analysis": {
        "enabled": True,
        "model": "gpt-4o-mini",
        "max_tokens": 600,
        "temperature": 0.3,
    }
}

# ============================================================================
# HOMEPAGE ENRICHMENT ENGINE
# ============================================================================

class HomepageEnrichmentEngine:
    """
    Fast homepage-only enrichment engine

    Scrapes homepage, extracts emails + content, runs AI analysis
    """

    def __init__(self, config: Dict):
        self.config = config
        self.http_client = HTTPClient(
            timeout=config["scraping"]["timeout"],
            retries=config["scraping"]["retries"]
        )

        # Initialize OpenAI
        self.openai_client = None
        if config["ai_analysis"]["enabled"] and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OPENAI_API_KEY not found - AI analysis disabled")

        # Stats tracking (thread-safe)
        self._lock = threading.Lock()
        self.stats = {
            "total_processed": 0,
            "scraping_success": 0,
            "scraping_failed": 0,
            "emails_found": 0,
            "no_emails": 0,
            "ai_analysis_success": 0,
            "ai_analysis_failed": 0,
            "no_website": 0,
        }

    def scrape_homepage(self, website: str) -> Dict:
        """
        Scrape homepage and extract emails + content

        Returns:
            {
                'success': bool,
                'emails': [list of emails],
                'content': clean text
            }
        """
        result = {
            'success': False,
            'emails': [],
            'content': ''
        }

        # Normalize URL
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            # Fetch homepage
            response = self.http_client.fetch(website, check_content_length=False)

            if response['status'] == 'success':
                html_content = response['content']

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

    def analyze_with_ai(self, name: str, content: str) -> Dict:
        """
        AI-powered analysis for Soviet boots personalization

        Returns:
            {
                'summary': business description,
                'type': organization type,
                'focus_wars': wars they focus on,
                'focus_periods': historical periods,
                'focus_topics': specific topics,
                'activities': what they do,
                'personalization_hooks': icebreaker material,
                'relevance_score': 0-10,
                'relevance_reasoning': why this score
            }
        """
        if not self.openai_client or not content:
            return self._empty_ai_result()

        try:
            # Truncate content if too long
            content_truncated = content[:4000]

            prompt = f"""Analyze this military history organization website for selling authentic Soviet military boots.

Organization: {name}
Content: {content_truncated}

Context: We are a collector who specializes in Soviet-era military footwear (Afghan War boots, Soviet Army boots, Red Army boots, Cold War era boots, etc.). We can connect organizations with rare authentic Soviet military boots for their collections, reenactments, or exhibitions.

Provide analysis in JSON format:
{{
  "summary": "Brief 2-3 sentence description of what this organization does",

  "type": "museum | reenactment_club | historical_society | research_center | militaria_store | collector | other",

  "focus_areas": {{
    "wars": ["WW2", "Cold War", "Afghan War (1979-1989)", "Chechen War", "Soviet-Afghan War", etc.],
    "periods": ["1939-1945", "Soviet Era (1922-1991)", "Cold War (1947-1991)", "Post-WW2", etc.],
    "specific_topics": ["Soviet Army", "Red Army", "Soviet Military Equipment", "Eastern Front", "Soviet Uniforms", etc.],
    "activities": ["reenactment", "collecting", "education", "preservation", "exhibitions", "restoration", etc.]
  }},

  "personalization_hooks": [
    "List 2-3 specific interesting facts, events, or unique aspects about this organization that could be used for personalized outreach. Focus on Soviet/Russian military connections if any."
  ],

  "relevance_score": {{
    "score": 0-10,
    "reasoning": "Detailed explanation of why this score for selling authentic Soviet military boots. Consider: Do they focus on Soviet history? Do they do reenactments needing authentic gear? Do they have collections? Are they interested in Soviet military equipment? Museums with Soviet exhibits score high."
  }}
}}

Scoring guide:
- 9-10: Heavy Soviet/Russian military focus, active reenactments, or major Soviet exhibits
- 7-8: Some Soviet focus, general WW2 or Cold War with Soviet elements
- 5-6: General military history, might have some Soviet interest
- 3-4: Limited Soviet relevance, mostly other periods/countries
- 0-2: No Soviet connection at all

Return ONLY valid JSON."""

            response = self.openai_client.chat.completions.create(
                model=self.config["ai_analysis"]["model"],
                messages=[
                    {"role": "system", "content": "You are an expert analyzer of military history organizations specializing in Soviet military history and equipment."},
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
            with self._lock:
                self.stats['no_website'] += 1
            return result

        try:
            # Step 1: Scrape homepage
            homepage_data = self.scrape_homepage(website)

            if not homepage_data['success']:
                result['processing_status'] = 'scraping_failed'
                with self._lock:
                    self.stats['scraping_failed'] += 1
                return result

            with self._lock:
                self.stats['scraping_success'] += 1

            result['scraped_content'] = homepage_data['content']

            # Step 2: Emails from homepage
            emails = homepage_data['emails']
            result['emails'] = ', '.join(emails)
            result['email_count'] = len(emails)

            with self._lock:
                if emails:
                    self.stats['emails_found'] += 1
                else:
                    self.stats['no_emails'] += 1

            # Step 3: AI Analysis
            ai_result = self.analyze_with_ai(name, homepage_data['content'])
            result.update(ai_result)

            with self._lock:
                if ai_result['summary']:
                    self.stats['ai_analysis_success'] += 1
                else:
                    self.stats['ai_analysis_failed'] += 1

            result['processing_status'] = 'success'

            with self._lock:
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
        logger.info(f"Mode: HOMEPAGE ONLY (no deep search)")

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

                    # Safe print with encoding handling
                    try:
                        print(f"[{processed}/{total}] {result['name'][:50]:<50} | "
                              f"Emails: {result['email_count']:<2} | "
                              f"Score: {result['relevance_score']:<2} | "
                              f"Status: {result['processing_status']}")
                    except UnicodeEncodeError:
                        print(f"[{processed}/{total}] [Unicode name] | "
                              f"Emails: {result['email_count']:<2} | "
                              f"Score: {result['relevance_score']:<2} | "
                              f"Status: {result['processing_status']}")

                    if processed % 25 == 0:
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
        with self._lock:
            logger.info(f"\n=== INTERIM STATS ({processed}/{total}) ===")
            logger.info(f"Scraping success: {self.stats['scraping_success']}")
            logger.info(f"Emails found: {self.stats['emails_found']}")
            logger.info(f"AI analysis success: {self.stats['ai_analysis_success']}")
            logger.info(f"Failed: {self.stats['scraping_failed']}")
            logger.info("")

    def get_stats(self) -> Dict:
        """Get final statistics"""
        with self._lock:
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
        "scraping": {
            "success": stats['scraping_success'],
            "failed": stats['scraping_failed'],
            "no_website": stats['no_website'],
            "success_rate": round(stats['scraping_success'] / max(total, 1) * 100, 1),
        },
        "email_discovery": {
            "total_with_emails": stats['emails_found'],
            "no_emails": stats['no_emails'],
            "email_coverage": round(stats['emails_found'] / max(stats['scraping_success'], 1) * 100, 1),
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
    }

    return analytics

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Homepage-Only Lead Enrichment')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with leads')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file')
    parser.add_argument('--workers', type=int, default=20, help='Number of parallel workers')
    parser.add_argument('--limit', type=int, default=None, help='Limit for testing')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')

    args = parser.parse_args()

    # Update config
    if args.workers:
        CONFIG["scraping"]["workers"] = args.workers
    if args.no_ai:
        CONFIG["ai_analysis"]["enabled"] = False

    logger.info("=" * 80)
    logger.info("HOMEPAGE-ONLY LEAD ENRICHMENT")
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

    # Filter only leads with websites
    df_with_websites = df[df['website'].notna()].copy()
    logger.info(f"Leads with websites: {len(df_with_websites)}")

    # Apply limit if testing
    if args.limit:
        df_with_websites = df_with_websites.head(args.limit)
        logger.info(f"TESTING MODE: Limited to {args.limit} leads")

    # Initialize engine
    engine = HomepageEnrichmentEngine(CONFIG)

    # Process
    logger.info("\nStarting enrichment...\n")
    start_time = time.time()

    results_df = engine.process_batch(df_with_websites)

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
    logger.info("SCRAPING:")
    logger.info(f"  Success: {analytics['scraping']['success']} ({analytics['scraping']['success_rate']}%)")
    logger.info(f"  Failed: {analytics['scraping']['failed']}")
    logger.info("")
    logger.info("EMAIL DISCOVERY (homepage only):")
    logger.info(f"  Leads with emails: {analytics['email_discovery']['total_with_emails']} ({analytics['email_discovery']['email_coverage']}%)")
    logger.info(f"  No emails: {analytics['email_discovery']['no_emails']}")
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
