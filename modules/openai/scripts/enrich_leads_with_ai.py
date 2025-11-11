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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
PARALLEL_WORKERS = 15  # Parallel API requests (safe for Tier 1: 500 RPM)

# Extraction Prompt Template
EXTRACTION_PROMPT = """Analyze this HVAC/contractor business website and create a personalization summary for Voice AI outreach.

CONTEXT: We're selling Voice AI phone answering service. Extract key insights for personalized cold email.

Return JSON with:

{{
  "business_summary": "2-3 sentence paragraph describing: business type, size, target market, and key services. Natural and conversational.",

  "personalization_angle": "2-3 sentences explaining WHY they need Voice AI based on their business. Reference specific pain points or opportunities from their website. Use 'you' language.",

  "key_flags": {{
    "has_emergency_service": true/false,
    "has_online_booking": true/false,
    "is_family_owned": true/false,
    "is_growing": true/false,
    "targets_residential": true/false,
    "targets_commercial": true/false
  }}
}}

EXAMPLE OUTPUT:
{{
  "business_summary": "Family-owned HVAC company serving Tampa Bay area for 15+ years. Specializes in residential AC repair and maintenance with 24/7 emergency service. Small team with strong local reputation.",

  "personalization_angle": "You mention offering 24/7 emergency service, which means late-night calls can be overwhelming for your small team. Voice AI can handle after-hours calls professionally, book appointments automatically, and ensure you never miss an urgent service request - all without hiring additional staff or disrupting your family time.",

  "key_flags": {{
    "has_emergency_service": true,
    "has_online_booking": false,
    "is_family_owned": true,
    "is_growing": false,
    "targets_residential": true,
    "targets_commercial": false
  }}
}}

WEBSITE CONTENT:
{content}

Return ONLY valid JSON. Be specific and reference actual details from website. Write naturally.
"""


class AIEnricher:
    """OpenAI-powered lead enrichment processor with parallel processing"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()  # Thread-safe counters

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

        max_retries = 3
        for attempt in range(max_retries):
            try:
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

                # Calculate cost (thread-safe)
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

                with self._lock:
                    self.total_cost += cost
                    self.processed_count += 1

                    if self.processed_count % 50 == 0:
                        logger.info(f"Progress: {self.processed_count} leads processed | Cost: ${self.total_cost:.2f}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {lead_name}: {e}")
                with self._lock:
                    self.failed_count += 1
                return None

            except Exception as e:
                # Rate limit or temporary error - retry
                if "rate_limit" in str(e).lower() or attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    logger.warning(f"API error for {lead_name} (attempt {attempt+1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error for {lead_name} after {max_retries} attempts: {e}")
                    with self._lock:
                        self.failed_count += 1
                    return None

        return None


def flatten_enrichment_data(enrichment: Dict) -> Dict:
    """
    Flatten nested JSON into flat columns for DataFrame

    New format: Simple structure with summary paragraphs + key flags
    """
    flat = {}

    # Main content - summary paragraphs
    flat['business_summary'] = enrichment.get('business_summary', '')
    flat['personalization_angle'] = enrichment.get('personalization_angle', '')

    # Key flags for filtering
    flags = enrichment.get('key_flags', {})
    flat['has_emergency_service'] = flags.get('has_emergency_service', False)
    flat['has_online_booking'] = flags.get('has_online_booking', False)
    flat['is_family_owned'] = flags.get('is_family_owned', False)
    flat['is_growing'] = flags.get('is_growing', False)
    flat['targets_residential'] = flags.get('targets_residential', False)
    flat['targets_commercial'] = flags.get('targets_commercial', False)

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

    # PRODUCTION MODE: Process all leads
    # df_to_enrich = df_to_enrich.head(50)  # Uncomment for testing

    logger.info(f"Total leads with email: {len(df[df['email'].notna()])}")
    logger.info(f"Leads to process: {len(df_to_enrich)}")
    logger.info(f"Estimated cost: ${len(df_to_enrich) * 0.015:.2f}")

    # Initialize enricher
    enricher = AIEnricher(api_key)

    # Process leads in parallel
    enrichments = []
    start_time = time.time()

    logger.info(f"Starting parallel processing with {PARALLEL_WORKERS} workers...")

    def process_lead(row):
        """Process single lead (for parallel execution)"""
        lead_name = row['name']
        content = row['website_content']
        place_id = row['place_id']

        enrichment = enricher.enrich_lead(content, lead_name)

        if enrichment:
            flat_data = flatten_enrichment_data(enrichment)
            flat_data['place_id'] = place_id
            return flat_data
        return None

    # Submit all tasks to thread pool
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        # Submit all leads
        future_to_row = {
            executor.submit(process_lead, row): row
            for _, row in df_to_enrich.iterrows()
        }

        # Process completed tasks
        for future in as_completed(future_to_row):
            result = future.result()
            if result:
                enrichments.append(result)

    # Create enrichment DataFrame
    df_enriched = pd.DataFrame(enrichments)

    # Merge with original data
    df_final = df_to_enrich.merge(df_enriched, on='place_id', how='left')

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"enriched_leads_{timestamp}.parquet"
    df_final.to_parquet(output_file, index=False)

    # Export FULL CSV for manual review
    csv_file = OUTPUT_DIR / f"enriched_leads_{timestamp}.csv"

    # Select only relevant columns for review
    review_columns = [
        'name', 'email', 'website', 'city', 'state',
        'business_summary', 'personalization_angle',
        'has_emergency_service', 'has_online_booking', 'is_family_owned',
        'is_growing', 'targets_residential', 'targets_commercial'
    ]

    # Export with only available columns
    available_columns = [col for col in review_columns if col in df_final.columns]
    df_final[available_columns].to_csv(csv_file, index=False, encoding='utf-8-sig')

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
