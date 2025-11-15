#!/usr/bin/env python3
"""
=== MILITARIA STORES EMAIL GENERATOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Generate personalized cold emails for militaria stores about Soviet boots source

FEATURES:
- Business-oriented approach (not museum donation style)
- Native language detection and generation
- No name variables ({{firstName}}, {{contact_name}})
- 3-email sequence
- Casual store names

USAGE:
1. Run: python generate_militaria_emails.py
2. Results: militaria_emails_YYYYMMDD_HHMMSS.csv
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
import glob

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

# Find latest verified militaria stores
VERIFICATION_DIR = Path(__file__).parent.parent.parent / "email_verification" / "results"
verified_files = glob.glob(str(VERIFICATION_DIR / "verified_militaria_stores_*.csv"))
if not verified_files:
    logger.error("No verified_militaria_stores_*.csv found!")
    sys.exit(1)

INPUT_FILE = Path(sorted(verified_files)[-1])

OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1500
TEMPERATURE = 0.7
PARALLEL_WORKERS = 50


def detect_language(text: str, address: str = "") -> str:
    """Detect language from text content"""
    if not text:
        return "en"

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
        elif "poland" in address_lower or "polska" in address_lower:
            return "pl"
        elif "czechia" in address_lower or "czech" in address_lower:
            return "cs"
        elif "italy" in address_lower or "italia" in address_lower:
            return "it"
        elif "spain" in address_lower or "espana" in address_lower:
            return "es"

    # Fallback: check content
    if any(word in text_lower for word in ["der ", "die ", "das ", "und ", "für "]):
        return "de"
    elif any(word in text_lower for word in ["le ", "la ", "les ", "et ", "pour "]):
        return "fr"
    elif any(word in text_lower for word in ["de ", "het ", "een ", "van ", "voor "]):
        return "nl"
    elif any(word in text_lower for word in ["на ", "по ", "из ", "для "]):
        return "ru"

    return "en"


MILITARIA_EMAIL_PROMPT = """You are an expert outreach copywriter helping Leo craft SHORT, casual but professional cold emails for militaria stores about Soviet boots source.

CONTEXT:
Leo's friend sources original Soviet boots directly from veterans. Leo is connecting militaria stores with this authentic Soviet military footwear supplier.

YOUR TASK:
Generate 3 personalized emails for this militaria store. Follow the tone and style EXACTLY as shown in the reference template.

CRITICAL RULES:
1. **Language**: Write ALL emails in {language_name} (detected from store's website)
2. **Tone**: Lowercase greeting (NO name variables - just "hey," or language equivalent)
3. **Store name**: Rewrite into natural, conversational form
4. **Business-oriented**: Focus on "collectors want", "expand inventory", not "exhibits"
5. **NO variables**: Do NOT use {{{{firstName}}}}, {{{{contact_name}}}}, {{{{companyName}}}} - plain text only
6. **Structure**: Generate 3 separate emails (initial, follow-up 1, follow-up 2)

STORE DATA:
Name: {store_name}
Summary: {summary}
Focus Wars: {focus_wars}
Focus Periods: {focus_periods}
Focus Topics: {focus_topics}
Personalization Hooks: {hooks}
Website: {website}
Detected Language: {language_name}

REFERENCE TEMPLATE (English example - business-oriented):
---
Subject: Soviet boots - authentic source

hey,

Saw Belgrade antiques and your vintage militaria collection.

A friend of mine sources original Soviet boots directly from veterans - authentic pieces collectors actually want.

thought it might be worth discussing if you're looking to expand inventory.

best,
Leo
---

FOLLOW-UP 1 TEMPLATE:
Hi,

Still interested in the boots or bad timing?

Best,
Leo

FOLLOW-UP 2 TEMPLATE:
Haven't heard back, so I'll assume it's not a fit right now

Will keep Belgrade antiques in mind if something similar comes up

STORE NAME REWRITING RULES:
- Use only ONE capital letter at start (e.g., "Belgrade antiques" NOT "Belgrade Antiques GmbH")
- Shorten if long/formal (e.g., "Berlin militaria" NOT "Berlin Militaria & Collectibles Store GmbH")
- Sound natural and conversational

FINDING PRODUCT CATEGORY:
Look at Focus Wars, Focus Periods, Focus Topics, Summary.
Find the MOST RELEVANT category to mention:
- Examples: "vintage militaria", "Soviet memorabilia", "WW2 collectibles", "military surplus", "Cold War items"
- Be SPECIFIC - use actual details from their focus areas
- If they focus on "WW2, Cold War" -> mention "Cold War items" or "WW2 collectibles"
- If they have "Soviet Army" in topics -> mention "Soviet memorabilia"

INSTRUCTIONS:
1. Create SHORT_STORE_NAME: Natural, casual version of store name
2. Find PRODUCT_CATEGORY: Most relevant category based on store's focus
3. Generate EMAIL_1 (initial outreach):
   - Mention the PRODUCT_CATEGORY you found
   - Keep it SHORT (4-5 lines like template)
   - Lowercase greeting WITHOUT name variables
   - Natural, conversational
4. Generate SUBJECT_LINE:
   - Business-oriented and short
   - Examples: "Soviet boots - authentic source", "Soviet footwear supplier", "authentic Soviet boots"
   - Lowercase
5. EMAIL_2 and EMAIL_3: Use templates above (translate to target language)

Return ONLY valid JSON in this EXACT format:
{{{{
  "short_store_name": "casual store name here",
  "product_category": "vintage militaria",
  "subject_line": "Soviet boots - authentic source",
  "email_1": "hey,\\n\\nSaw [store], really liked the [category] collection.\\n\\nA friend of mine sources original Soviet boots directly from veterans - authentic pieces collectors actually want.\\n\\nthought it might be worth discussing if you're looking to expand inventory.\\n\\nbest,\\nLeo",
  "email_2": "Hi,\\n\\nStill interested in the boots or bad timing?\\n\\nBest,\\nLeo",
  "email_3": "Haven't heard back, so I'll assume it's not a fit right now\\n\\nWill keep [short store name] in mind if something similar comes up",
  "language": "{language_code}"
}}}}

CRITICAL:
- Write ALL emails in {language_name}
- Use \\n for line breaks
- Be SPECIFIC about the product category you mention
- NO variables like {{{{firstName}}}} - use actual store name instead
- Start email_1 with simple greeting (hey, hallo, hej, etc.) WITHOUT name placeholders
"""


class MilitariaEmailGenerator:
    """OpenAI-powered email generator for militaria stores"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()

    def generate_emails(self, store_data: Dict) -> Optional[Dict]:
        """Generate email sequence for a store using OpenAI"""

        store_name = store_data.get('name', 'Unknown Store')

        # Detect language
        content = store_data.get('scraped_content', '')
        address = store_data.get('address', '')
        language_code = detect_language(content, address)

        language_names = {
            'en': 'English', 'de': 'German', 'fr': 'French', 'nl': 'Dutch',
            'sr': 'Serbian', 'sk': 'Slovak', 'ru': 'Russian', 'pl': 'Polish',
            'cs': 'Czech', 'it': 'Italian', 'es': 'Spanish'
        }
        language_name = language_names.get(language_code, 'English')

        logger.info(f"Processing {store_name} (Language: {language_name})")

        # Build prompt
        prompt = MILITARIA_EMAIL_PROMPT.format(
            store_name=store_name,
            summary=store_data.get('summary', ''),
            focus_wars=store_data.get('focus_wars', ''),
            focus_periods=store_data.get('focus_periods', ''),
            focus_topics=store_data.get('focus_topics', ''),
            hooks=store_data.get('personalization_hooks', ''),
            website=store_data.get('website', ''),
            language_code=language_code,
            language_name=language_name
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert outreach copywriter. Generate casual, professional militaria store emails with SPECIFIC product categories. ALWAYS write in the specified language. NO name variables."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"}
                )

                result = json.loads(response.choices[0].message.content)

                # Calculate cost
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

                with self._lock:
                    self.total_cost += cost
                    self.processed_count += 1

                    if self.processed_count % 10 == 0:
                        logger.info(f"Progress: {self.processed_count} stores | Cost: ${self.total_cost:.4f}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {store_name}: {e}")
                with self._lock:
                    self.failed_count += 1
                return None

            except Exception as e:
                if "rate_limit" in str(e).lower() or attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"API error for {store_name} (attempt {attempt+1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error for {store_name} after {max_retries} attempts: {e}")
                    with self._lock:
                        self.failed_count += 1
                    return None

        return None


def main():
    """Main email generation pipeline"""
    logger.info("=== MILITARIA STORES EMAIL GENERATOR STARTED ===")

    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env")
        return

    # Load verified militaria stores
    logger.info(f"Loading verified stores from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    # Filter: only deliverable
    df_deliverable = df[df['result'] == 'deliverable'].copy()

    logger.info(f"Total stores in CSV: {len(df)}")
    logger.info(f"Deliverable stores: {len(df_deliverable)}")
    logger.info(f"Estimated cost: ${len(df_deliverable) * 0.02:.2f}")

    # Initialize generator
    generator = MilitariaEmailGenerator(api_key)

    # Process stores
    results = []
    start_time = time.time()

    logger.info(f"Starting processing with {PARALLEL_WORKERS} workers...")

    def process_store(row):
        """Process single store"""
        store_data = {
            'name': row['name'],
            'website': row.get('website', ''),
            'email': row['email'],
            'summary': row.get('summary', ''),
            'focus_wars': row.get('focus_wars', ''),
            'focus_periods': row.get('focus_periods', ''),
            'focus_topics': row.get('focus_topics', ''),
            'personalization_hooks': row.get('personalization_hooks', ''),
            'scraped_content': row.get('scraped_content', ''),
            'address': row.get('address', '')
        }

        emails = generator.generate_emails(store_data)

        if emails:
            return {
                'name': row['name'],
                'email': row['email'],
                'website': row.get('website', ''),
                'short_store_name': emails.get('short_store_name', ''),
                'product_category': emails.get('product_category', ''),
                'subject_line': emails.get('subject_line', ''),
                'email_1': emails.get('email_1', ''),
                'email_2': emails.get('email_2', ''),
                'email_3': emails.get('email_3', ''),
                'language': emails.get('language', 'en'),
                'summary': row.get('summary', ''),
                'focus_wars': row.get('focus_wars', ''),
                'focus_periods': row.get('focus_periods', '')
            }
        return None

    # Submit tasks
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        future_to_row = {
            executor.submit(process_store, row): row
            for _, row in df_deliverable.iterrows()
        }

        for future in as_completed(future_to_row):
            result = future.result()
            if result:
                results.append(result)

    # Create results DataFrame
    df_results = pd.DataFrame(results)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV
    output_csv = OUTPUT_DIR / f"militaria_emails_{timestamp}.csv"
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # JSON
    output_json = OUTPUT_DIR / f"militaria_emails_{timestamp}.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'generated_at': timestamp,
                'total_stores': len(results),
                'total_cost': generator.total_cost
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)

    # Stats
    elapsed = time.time() - start_time
    logger.info("=== MILITARIA EMAIL GENERATION COMPLETE ===")
    logger.info(f"Total processed: {generator.processed_count}")
    logger.info(f"Failed: {generator.failed_count}")
    logger.info(f"Total cost: ${generator.total_cost:.4f}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output CSV: {output_csv}")
    logger.info(f"Output JSON: {output_json}")

    # Sample
    if len(df_results) > 0:
        logger.info("\n=== SAMPLE OUTPUT (First Store) ===")
        first = df_results.iloc[0]
        logger.info(f"Store: {first['name']}")
        logger.info(f"Email: {first['email']}")
        logger.info(f"Language: {first['language']}")
        logger.info(f"Short Name: {first['short_store_name']}")
        logger.info(f"Product Category: {first['product_category']}")
        logger.info(f"Subject: {first['subject_line']}")
        logger.info(f"\nEmail 1:\n{first['email_1'][:200]}...")


if __name__ == "__main__":
    main()
