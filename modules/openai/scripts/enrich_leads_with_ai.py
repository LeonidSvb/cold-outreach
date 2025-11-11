#!/usr/bin/env python3
"""
=== AI LEAD ENRICHMENT PIPELINE ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Extract structured business intelligence from website content using OpenAI.
Designed for Voice AI personalization (identify pain points, tech readiness, unique hooks).

FEATURES:
- Structured JSON extraction (business profile, pain points, ICP, tech stack)
- Batch processing with rate limiting
- Cost tracking ($0.01-0.02 per lead)
- Incremental processing (resume on failure)
- Export enriched data to Parquet

USAGE:
1. Configure API key in .env (OPENAI_API_KEY)
2. Run: python enrich_leads_with_ai.py
3. Results: modules/openai/results/enriched_YYYYMMDD_HHMMSS.parquet

COST ESTIMATE:
- 1,894 leads × $0.015 = ~$28.41
- Processing time: ~30-45 minutes (50 req/min rate limit)
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
from typing import Dict, Optional
import time
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

# Paths
INPUT_FILE = Path(__file__).parent.parent.parent / "google_maps" / "data" / "enriched" / "enriched_final_latest.parquet"
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
MODEL = "gpt-4o-mini"  # Cost-effective for extraction ($0.150 / 1M input tokens)
MAX_TOKENS = 1000
TEMPERATURE = 0.1  # Low temperature for consistent extraction
RATE_LIMIT_DELAY = 1.2  # 50 requests per minute = 1.2s delay

# Extraction Prompt Template
EXTRACTION_PROMPT = """Analyze this HVAC/contractor business website content and extract structured information for Voice AI personalization.

CONTEXT: We're selling Voice AI phone answering service. Extract signals that help personalize outreach.

Extract the following in JSON format:

{
  "business_profile": {
    "business_type": "family-owned | franchise | corporate | independent | unknown",
    "years_mentioned": "10+ years | established YYYY | new | unknown",
    "service_area": "local | regional | statewide | multi-state | unknown",
    "company_size_signals": "small team | growing | large operation | unknown"
  },

  "pain_points": {
    "emergency_service": true/false,
    "call_handling_mentions": ["24/7 calls", "busy season", "overwhelmed", "missed calls"] or [],
    "staffing_challenges": ["hiring", "small team", "family business"] or [],
    "peak_season_mentions": ["summer rush", "winter heating", "busy season"] or []
  },

  "ideal_customer_profile": {
    "target_markets": ["residential", "commercial", "industrial", "new construction"] or [],
    "service_specializations": ["installation", "repair", "maintenance", "emergency"] or [],
    "pricing_positioning": "premium | competitive | budget-friendly | unknown"
  },

  "technology_readiness": {
    "online_booking": true/false,
    "live_chat": true/false,
    "automation_mentioned": ["CRM", "dispatch software", "online scheduling"] or [],
    "growth_signals": ["hiring", "expanding", "new locations", "investing"] or []
  },

  "unique_differentiators": {
    "certifications": ["licensed", "insured", "certified", "bonded"] or [],
    "special_attributes": ["veteran-owned", "family-owned", "eco-friendly", "women-owned"] or [],
    "guarantees": ["satisfaction guarantee", "warranty", "money-back"] or [],
    "response_time": "same day | 2-hour | 24-hour | emergency | unknown"
  },

  "personalization_hooks": [
    "1-2 key sentences that could be used for personalized outreach"
  ]
}

WEBSITE CONTENT:
{content}

Return ONLY valid JSON. Be concise. Use "unknown" if unclear. Extract maximum 3 items per array.
"""


class AIEnricher:
    """OpenAI-powered lead enrichment processor"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0

    def enrich_lead(self, content: str, lead_name: str) -> Optional[Dict]:
        """
        Extract structured data from website content using OpenAI

        Args:
            content: Website text content
            lead_name: Business name (for logging)

        Returns:
            Extracted structured data or None if failed
        """
        if not content or len(content) < 100:
            logger.warning(f"Skipping {lead_name}: content too short ({len(content)} chars)")
            return None

        # Truncate content to 8000 chars (cost optimization)
        content_truncated = content[:8000] if len(content) > 8000 else content

        prompt = EXTRACTION_PROMPT.format(content=content_truncated)

        try:
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a business intelligence extraction specialist. Extract structured data accurately and concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                response_format={"type": "json_object"}
            )

            # Parse response
            result = json.loads(response.choices[0].message.content)

            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)
            self.total_cost += cost

            self.processed_count += 1

            if self.processed_count % 10 == 0:
                logger.info(f"Processed {self.processed_count} leads | Cost: ${self.total_cost:.2f}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error for {lead_name}: {e}")
            self.failed_count += 1
            return None
        except Exception as e:
            logger.error(f"API error for {lead_name}: {e}")
            self.failed_count += 1
            return None


def flatten_enrichment_data(enrichment: Dict) -> Dict:
    """
    Flatten nested JSON into flat columns for DataFrame

    Returns:
        Dict with flattened keys (e.g., business_profile_type, pain_points_emergency)
    """
    flat = {}

    # Business Profile
    bp = enrichment.get('business_profile', {})
    flat['business_type'] = bp.get('business_type', 'unknown')
    flat['years_mentioned'] = bp.get('years_mentioned', 'unknown')
    flat['service_area'] = bp.get('service_area', 'unknown')
    flat['company_size_signals'] = bp.get('company_size_signals', 'unknown')

    # Pain Points
    pp = enrichment.get('pain_points', {})
    flat['has_emergency_service'] = pp.get('emergency_service', False)
    flat['call_handling_issues'] = ', '.join(pp.get('call_handling_mentions', []))
    flat['staffing_challenges'] = ', '.join(pp.get('staffing_challenges', []))
    flat['peak_season_mentions'] = ', '.join(pp.get('peak_season_mentions', []))

    # ICP
    icp = enrichment.get('ideal_customer_profile', {})
    flat['target_markets'] = ', '.join(icp.get('target_markets', []))
    flat['service_specializations'] = ', '.join(icp.get('service_specializations', []))
    flat['pricing_positioning'] = icp.get('pricing_positioning', 'unknown')

    # Tech Readiness
    tech = enrichment.get('technology_readiness', {})
    flat['has_online_booking'] = tech.get('online_booking', False)
    flat['has_live_chat'] = tech.get('live_chat', False)
    flat['automation_tools'] = ', '.join(tech.get('automation_mentioned', []))
    flat['growth_signals'] = ', '.join(tech.get('growth_signals', []))

    # Differentiators
    diff = enrichment.get('unique_differentiators', {})
    flat['certifications'] = ', '.join(diff.get('certifications', []))
    flat['special_attributes'] = ', '.join(diff.get('special_attributes', []))
    flat['guarantees'] = ', '.join(diff.get('guarantees', []))
    flat['response_time'] = diff.get('response_time', 'unknown')

    # Hooks
    flat['personalization_hooks'] = ' | '.join(enrichment.get('personalization_hooks', []))

    return flat


def main():
    """Main enrichment pipeline"""
    logger.info("=== AI Lead Enrichment Pipeline Started ===")

    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env")
        return

    # Load input data
    logger.info(f"Loading leads from: {INPUT_FILE}")
    df = pd.read_parquet(INPUT_FILE)

    # Filter: only leads with email AND website_content
    df_to_enrich = df[
        (df['email'].notna()) &
        (df['website_content'].notna()) &
        (df['content_length'] > 500)
    ].copy()

    logger.info(f"Total leads with email: {len(df[df['email'].notna()])}")
    logger.info(f"Leads with sufficient content: {len(df_to_enrich)}")
    logger.info(f"Estimated cost: ${len(df_to_enrich) * 0.015:.2f}")

    # Initialize enricher
    enricher = AIEnricher(api_key)

    # Process leads
    enrichments = []
    start_time = time.time()

    for idx, row in df_to_enrich.iterrows():
        lead_name = row['name']
        content = row['website_content']

        logger.info(f"Processing [{idx+1}/{len(df_to_enrich)}]: {lead_name}")

        enrichment = enricher.enrich_lead(content, lead_name)

        if enrichment:
            flat_data = flatten_enrichment_data(enrichment)
            flat_data['place_id'] = row['place_id']
            enrichments.append(flat_data)

    # Create enrichment DataFrame
    df_enriched = pd.DataFrame(enrichments)

    # Merge with original data
    df_final = df_to_enrich.merge(df_enriched, on='place_id', how='left')

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"enriched_leads_{timestamp}.parquet"
    df_final.to_parquet(output_file, index=False)

    # Export CSV sample
    csv_file = OUTPUT_DIR / f"enriched_leads_{timestamp}_sample.csv"
    df_final.head(100).to_csv(csv_file, index=False)

    # Final stats
    elapsed = time.time() - start_time
    logger.info("=== Enrichment Complete ===")
    logger.info(f"Total processed: {enricher.processed_count}")
    logger.info(f"Failed: {enricher.failed_count}")
    logger.info(f"Total cost: ${enricher.total_cost:.2f}")
    logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
    logger.info(f"Output: {output_file}")
    logger.info(f"CSV Sample: {csv_file}")


if __name__ == "__main__":
    main()
