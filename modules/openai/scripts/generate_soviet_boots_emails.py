#!/usr/bin/env python3
"""
=== SOVIET BOOTS EMAIL GENERATOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Generate personalized cold email sequences for Soviet boots outreach.
Creates 3-email sequence in original language with casual, professional tone.

FEATURES:
- Handles multiple emails per organization (duplicates rows)
- Auto-detects language from scraped content
- Generates 3-email sequence (initial, follow-up 1, follow-up 2)
- Casual company name normalization
- JSON output for Instantly

USAGE:
1. Configure INPUT_CSV path
2. Run: python generate_soviet_boots_emails.py
3. Results: modules/openai/results/soviet_boots_emails_YYYYMMDD_HHMMSS.json

COST ESTIMATE:
- ~$0.01-0.02 per organization
- Test mode: 2 organizations = ~$0.04
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
from typing import Dict, Optional, List
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
INPUT_FILE = Path(r"C:\Users\79818\Downloads\Soviet Boots - Sheet3.csv")
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1500
TEMPERATURE = 0.7
PARALLEL_WORKERS = 5

# TEST MODE: Set to True to process only 2 organizations
TEST_MODE = True
TEST_LIMIT = 2


def detect_language(text: str, address: str = "") -> str:
    """
    Detect language from text content

    Returns: language code (en, de, fr, nl, ru, sk, etc.)
    """
    if not text:
        return "en"

    # Simple keyword-based detection
    text_lower = text.lower()

    # Check by country in address first
    if address:
        address_lower = address.lower()
        if "germany" in address_lower or "deutschland" in address_lower:
            return "de"
        elif "france" in address_lower:
            return "fr"
        elif "netherlands" in address_lower or "nederland" in address_lower:
            return "nl"
        elif "serbia" in address_lower or "srbija" in address_lower:
            return "sr"
        elif "slovakia" in address_lower:
            return "sk"
        elif "russia" in address_lower:
            return "ru"

    # Fallback: check content for language patterns
    if any(word in text_lower for word in ["der ", "die ", "das ", "und ", "für "]):
        return "de"
    elif any(word in text_lower for word in ["le ", "la ", "les ", "et ", "pour "]):
        return "fr"
    elif any(word in text_lower for word in ["de ", "het ", "een ", "van ", "voor "]):
        return "nl"
    elif any(word in text_lower for word in ["на ", "по ", "из ", "для "]):
        return "ru"
    elif any(word in text_lower for word in ["na ", "po ", "od ", "za "]):
        return "sr"

    return "en"  # Default to English


def split_emails(df: pd.DataFrame) -> pd.DataFrame:
    """
    Split rows with multiple emails into separate rows

    Example:
    - Input: 1 row with "email1@test.com, email2@test.com"
    - Output: 2 rows with separate emails
    """
    logger.info("Splitting multiple emails into separate rows...")

    rows_list = []

    for _, row in df.iterrows():
        emails_str = str(row['emails'])

        # Skip if no emails
        if pd.isna(row['emails']) or not emails_str.strip():
            continue

        # Split by comma and clean
        emails = [e.strip() for e in emails_str.split(',') if e.strip()]

        # Create a row for each email
        for email in emails:
            new_row = row.copy()
            new_row['email'] = email  # Single email column
            new_row['emails'] = email  # Keep for reference
            rows_list.append(new_row)

    result_df = pd.DataFrame(rows_list)

    logger.info(f"Split complete: {len(df)} organizations -> {len(result_df)} email contacts")

    return result_df


EMAIL_GENERATION_PROMPT = """You are an expert outreach copywriter helping Leo craft short, casual but professional cold emails for stores/museums about Soviet military boots.

CONTEXT:
Leo's friend gets original Soviet boots from veterans. Leo is connecting organizations with this source of authentic artifacts.

YOUR TASK:
Generate 3 personalized emails based on the organization data provided. Follow the tone and style EXACTLY as shown in the reference template.

CRITICAL RULES:
1. **Language**: Write emails in {language_name} (detected from organization's website)
2. **Tone**: Lowercase greeting ("hey {{{{contact_name}}}}"), casual but professional
3. **Company name**: Rewrite into natural, conversational form (see instructions below)
4. **Structure**: Generate 3 separate emails (initial, follow-up 1, follow-up 2)

ORGANIZATION DATA:
Name: {org_name}
Summary: {summary}
Personalization Hooks: {hooks}
Website: {website}
Detected Language: {language_name}

REFERENCE TEMPLATE (English example):
---
Subject: quick intro question

hey {{{{contact_name | default("there")}}}},

Checked out the {{{{museum_name}}}}, really liked the {{{{exhibit_or_section}}}} section.

A friend of mine gets original Soviet boots from veterans, thought it might fit your exhibits, people usually love authentic stuff like that.

figured it might be worth connecting you two.

best,
Leo
---

FOLLOW-UP 1 TEMPLATE:
Hi {{{{firstName | default("")}}}}

Still worth making the connection or bad timing?

Best,
Leo

FOLLOW-UP 2 TEMPLATE:
Haven't heard back, so I'll assume it's not a fit right now

Will keep {{{{companyName}}}} in mind if something similar comes up

COMPANY NAME REWRITING RULES:
- Use only ONE capital letter at start (e.g., "German historica" NOT "German-Historica An- Verkauf Orden & Ehrenzeichen")
- If name is long/formal, shorten to casual version (e.g., "Belgrade antiques" NOT "Belgrade Antiques & Collectibles Store")
- Sound natural and conversational

INSTRUCTIONS:
1. Create SHORT_COMPANY_NAME: Natural, casual version of organization name
2. Generate EMAIL_1 (initial outreach):
   - Use summary and hooks to personalize
   - Reference specific section/focus area
   - Keep SHORT (4-5 lines like template)
   - Lowercase greeting
3. Generate SUBJECT_LINE:
   - Very casual and short
   - Examples: "quick intro question", "thought of you"
   - Lowercase
4. EMAIL_2 and EMAIL_3: Use templates above (translate to target language)

Return ONLY valid JSON in this EXACT format:
{{{{
  "short_company_name": "casual organization name here",
  "subject_line": "quick intro question",
  "email_1": "hey {{{{{{{{firstName | default(\\"there\\")}}}}}}}},\\n\\nChecked out [organization], really liked [specific section].\\n\\nA friend of mine gets original Soviet boots from veterans, thought it might fit your collection, people usually love authentic stuff like that.\\n\\nfigured it might be worth connecting you two.\\n\\nbest,\\nLeo",
  "email_2": "Hi {{{{{{{{firstName}}}}}}}}\\n\\nStill worth making the connection or bad timing?\\n\\nBest,\\nLeo",
  "email_3": "Haven't heard back, so I'll assume it's not a fit right now\\n\\nWill keep {{{{{{{{companyName}}}}}}}} in mind if something similar comes up",
  "language": "{language_code}"
}}}}

CRITICAL: Write all emails in {language_name}. Use \\n for line breaks in JSON strings.
"""


class SovietBootsEmailGenerator:
    """OpenAI-powered email generator for Soviet boots outreach"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()

    def generate_emails(self, org_data: Dict) -> Optional[Dict]:
        """
        Generate email sequence for an organization using OpenAI

        Args:
            org_data: Organization information

        Returns:
            Generated emails dict or None if failed
        """
        org_name = org_data.get('name', 'Unknown Organization')

        # Detect language
        content = org_data.get('scraped_content', '')
        address = org_data.get('address', '')
        language_code = detect_language(content, address)

        language_names = {
            'en': 'English',
            'de': 'German',
            'fr': 'French',
            'nl': 'Dutch',
            'sr': 'Serbian',
            'sk': 'Slovak',
            'ru': 'Russian'
        }
        language_name = language_names.get(language_code, 'English')

        logger.info(f"Processing {org_name} (Language: {language_name})")

        # Build prompt
        prompt = EMAIL_GENERATION_PROMPT.format(
            org_name=org_name,
            summary=org_data.get('summary', ''),
            hooks=org_data.get('personalization_hooks', ''),
            website=org_data.get('website', ''),
            language_code=language_code,
            language_name=language_name
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert outreach copywriter. Generate casual, professional cold emails following the exact tone and style provided. ALWAYS write in the specified language."},
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

                with self._lock:
                    self.total_cost += cost
                    self.processed_count += 1

                    if self.processed_count % 5 == 0:
                        logger.info(f"Progress: {self.processed_count} organizations | Cost: ${self.total_cost:.4f}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {org_name}: {e}")
                with self._lock:
                    self.failed_count += 1
                return None

            except Exception as e:
                if "rate_limit" in str(e).lower() or attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"API error for {org_name} (attempt {attempt+1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error for {org_name} after {max_retries} attempts: {e}")
                    with self._lock:
                        self.failed_count += 1
                    return None

        return None


def main():
    """Main email generation pipeline"""
    logger.info("=== Soviet Boots Email Generator Started ===")
    logger.info(f"TEST MODE: {'ENABLED' if TEST_MODE else 'DISABLED'}")

    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env")
        return

    # Load input data
    logger.info(f"Loading data from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    logger.info(f"Total organizations in CSV: {len(df)}")

    # Split multiple emails into separate rows
    df_split = split_emails(df)

    # Filter: only successful scraping with emails
    df_to_process = df_split[
        (df_split['processing_status'] == 'success') &
        (df_split['email'].notna())
    ].copy()

    # TEST MODE: Process only first N
    if TEST_MODE:
        df_to_process = df_to_process.head(TEST_LIMIT)
        logger.info(f"TEST MODE: Processing only {len(df_to_process)} organizations")

    logger.info(f"Organizations to process: {len(df_to_process)}")
    logger.info(f"Estimated cost: ${len(df_to_process) * 0.015:.2f}")

    # Initialize generator
    generator = SovietBootsEmailGenerator(api_key)

    # Process organizations
    results = []
    start_time = time.time()

    logger.info(f"Starting processing with {PARALLEL_WORKERS} workers...")

    def process_organization(row):
        """Process single organization"""
        org_data = {
            'name': row['name'],
            'website': row.get('website', ''),
            'email': row['email'],
            'summary': row.get('summary', ''),
            'personalization_hooks': row.get('personalization_hooks', ''),
            'scraped_content': row.get('scraped_content', ''),
            'address': row.get('address', '')
        }

        emails = generator.generate_emails(org_data)

        if emails:
            return {
                'name': row['name'],
                'email': row['email'],
                'website': row.get('website', ''),
                'short_company_name': emails.get('short_company_name', ''),
                'subject_line': emails.get('subject_line', ''),
                'email_1': emails.get('email_1', ''),
                'email_2': emails.get('email_2', ''),
                'email_3': emails.get('email_3', ''),
                'language': emails.get('language', 'en'),
                'summary': row.get('summary', ''),
                'personalization_hooks': row.get('personalization_hooks', '')
            }
        return None

    # Submit tasks
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        future_to_row = {
            executor.submit(process_organization, row): row
            for _, row in df_to_process.iterrows()
        }

        for future in as_completed(future_to_row):
            result = future.result()
            if result:
                results.append(result)

    # Create results DataFrame
    df_results = pd.DataFrame(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as JSON
    output_json = OUTPUT_DIR / f"soviet_boots_emails_{timestamp}.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'generated_at': timestamp,
                'total_organizations': len(results),
                'test_mode': TEST_MODE,
                'total_cost': generator.total_cost
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)

    # Save as CSV for review
    output_csv = OUTPUT_DIR / f"soviet_boots_emails_{timestamp}.csv"
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Final stats
    elapsed = time.time() - start_time
    logger.info("=== Email Generation Complete ===")
    logger.info(f"Total processed: {generator.processed_count}")
    logger.info(f"Failed: {generator.failed_count}")
    logger.info(f"Total cost: ${generator.total_cost:.4f}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output JSON: {output_json}")
    logger.info(f"Output CSV: {output_csv}")

    # Display sample
    if len(df_results) > 0:
        logger.info("\n=== SAMPLE OUTPUT (First Organization) ===")
        first = df_results.iloc[0]
        logger.info(f"Organization: {first['name']}")
        logger.info(f"Email: {first['email']}")
        logger.info(f"Language: {first['language']}")
        logger.info(f"Short Name: {first['short_company_name']}")
        logger.info(f"Subject: {first['subject_line']}")
        logger.info(f"\nEmail 1:\n{first['email_1']}")
        logger.info(f"\nEmail 2:\n{first['email_2']}")
        logger.info(f"\nEmail 3:\n{first['email_3']}")


if __name__ == "__main__":
    main()
