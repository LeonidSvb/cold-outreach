#!/usr/bin/env python3
"""
=== MUSEUM EMAIL GENERATOR (SOVIET BOOTS) ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Generate highly personalized cold emails for museums mentioning specific exhibits/sections.
Creates emails in museum's native language with casual, professional tone.

FEATURES:
- Finds specific exhibit/section to mention (e.g., "Cold War section")
- Handles multiple emails per museum (duplicates rows)
- Auto-detects language from content
- 3-email sequence (initial, follow-up 1, follow-up 2)
- Casual museum name normalization

USAGE:
1. Ensure museums CSV exists in modules/openai/data/
2. Run: python generate_museum_emails.py
3. Results: modules/openai/results/museum_emails_YYYYMMDD_HHMMSS.json

COST ESTIMATE:
- ~$0.015-0.025 per museum
- 891 museums = ~$13-22
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

# Paths - find latest museums CSV
DATA_DIR = Path(__file__).parent.parent / "data"
museum_files = glob.glob(str(DATA_DIR / "soviet_boots_museums_only_*.csv"))
if not museum_files:
    logger.error(f"No museum CSV files found in {DATA_DIR}")
    logger.error("Please run filter_museums.py first!")
    sys.exit(1)

INPUT_FILE = Path(sorted(museum_files)[-1])  # Latest file

OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI Configuration
MODEL = "gpt-4o-mini"
MAX_TOKENS = 1500
TEMPERATURE = 0.7
PARALLEL_WORKERS = 50

# TEST MODE: Set to True to process only N museums
TEST_MODE = False
TEST_LIMIT = 10


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


def split_emails(df: pd.DataFrame) -> pd.DataFrame:
    """Split rows with multiple emails into separate rows"""
    logger.info("Splitting multiple emails into separate rows...")

    rows_list = []

    for _, row in df.iterrows():
        emails_str = str(row['emails'])

        if pd.isna(row['emails']) or not emails_str.strip():
            continue

        emails = [e.strip() for e in emails_str.split(',') if e.strip()]

        for email in emails:
            new_row = row.copy()
            new_row['email'] = email
            new_row['emails'] = email
            rows_list.append(new_row)

    result_df = pd.DataFrame(rows_list)
    logger.info(f"Split complete: {len(df)} museums -> {len(result_df)} email contacts")

    return result_df


MUSEUM_EMAIL_PROMPT = """You are an expert outreach copywriter helping Leo craft SHORT, casual but professional cold emails for museums about Soviet military boots.

CONTEXT:
Leo's friend gets original Soviet boots from veterans. Leo is connecting museums with this source of authentic artifacts.

YOUR TASK:
Generate 3 personalized emails for this museum. Follow the tone and style EXACTLY as shown in the reference template.

CRITICAL RULES:
1. **Language**: Write ALL emails in {language_name} (detected from museum's website)
2. **Tone**: Lowercase greeting ("hey {{{{contact_name}}}}"), casual but professional
3. **Museum name**: Rewrite into natural, conversational form (see instructions below)
4. **IMPORTANT**: Identify and mention a SPECIFIC exhibit/section/period from their collection
5. **Structure**: Generate 3 separate emails (initial, follow-up 1, follow-up 2)

MUSEUM DATA:
Name: {museum_name}
Summary: {summary}
Focus Wars: {focus_wars}
Focus Periods: {focus_periods}
Focus Topics: {focus_topics}
Personalization Hooks: {hooks}
Website: {website}
Detected Language: {language_name}

REFERENCE TEMPLATE (English example):
---
Subject: quick intro question

hey,

Checked out the Polish army museum, really liked the Cold War section.

A friend of mine gets original Soviet boots from veterans, thought it might fit your exhibits, people usually love authentic stuff like that.

figured it might be worth connecting you two.

best,
Leo
---

FOLLOW-UP 1 TEMPLATE:
Hi,

Still worth making the connection or bad timing?

Best,
Leo

FOLLOW-UP 2 TEMPLATE:
Haven't heard back, so I'll assume it's not a fit right now

Will keep [museum short name] in mind if something similar comes up

MUSEUM NAME REWRITING RULES:
- Use only ONE capital letter at start (e.g., "Polish army museum" NOT "Polish Army Museum Foundation")
- Shorten if long/formal (e.g., "German war museum" NOT "German War History Museum and Memorial Center")
- Sound natural and conversational

FINDING SPECIFIC EXHIBIT/SECTION:
Look at Focus Wars, Focus Periods, Focus Topics, Summary, and Personalization Hooks.
Find the MOST RELEVANT section to mention:
- Examples: "Cold War section", "WW2 Eastern Front exhibit", "Soviet military equipment collection", "1945-1991 period room"
- Be SPECIFIC - use actual details from their focus areas
- If they focus on "WW2, Cold War" -> mention "Cold War section" or "WW2 section"
- If they have "Soviet Army" in topics -> mention "Soviet military collection"

INSTRUCTIONS:
1. Create SHORT_MUSEUM_NAME: Natural, casual version of museum name
2. Find SPECIFIC_SECTION: Most relevant exhibit/section based on museum's focus
3. Generate EMAIL_1 (initial outreach):
   - Mention the SPECIFIC_SECTION you found
   - Keep it SHORT (4-5 lines like template)
   - Lowercase greeting
   - Natural, conversational
4. Generate SUBJECT_LINE:
   - Very casual and short
   - Examples: "quick intro question", "thought of you", "quick question"
   - Lowercase
5. EMAIL_2 and EMAIL_3: Use templates above (translate to target language)

Return ONLY valid JSON in this EXACT format:
{{{{
  "short_museum_name": "casual museum name here",
  "specific_section": "Cold War section",
  "subject_line": "quick intro question",
  "email_1": "hey,\\n\\nChecked out [museum], really liked the [specific section].\\n\\nA friend of mine gets original Soviet boots from veterans, thought it might fit your exhibits, people usually love authentic stuff like that.\\n\\nfigured it might be worth connecting you two.\\n\\nbest,\\nLeo",
  "email_2": "Hi,\\n\\nStill worth making the connection or bad timing?\\n\\nBest,\\nLeo",
  "email_3": "Haven't heard back, so I'll assume it's not a fit right now\\n\\nWill keep [short museum name] in mind if something similar comes up",
  "language": "{language_code}"
}}}}

CRITICAL:
- Write ALL emails in {language_name}
- Use \\n for line breaks
- Be SPECIFIC about the section/exhibit you mention
- NO variables like {{{{firstName}}}} or {{{{companyName}}}} - use actual museum name instead
- Start email_1 with simple greeting (hey, hola, hallo, etc.) without name placeholders
"""


class MuseumEmailGenerator:
    """OpenAI-powered email generator for museum outreach"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()

    def generate_emails(self, museum_data: Dict) -> Optional[Dict]:
        """Generate email sequence for a museum using OpenAI"""

        museum_name = museum_data.get('name', 'Unknown Museum')

        # Detect language
        content = museum_data.get('scraped_content', '')
        address = museum_data.get('address', '')
        language_code = detect_language(content, address)

        language_names = {
            'en': 'English', 'de': 'German', 'fr': 'French', 'nl': 'Dutch',
            'sr': 'Serbian', 'sk': 'Slovak', 'ru': 'Russian', 'pl': 'Polish',
            'cs': 'Czech', 'it': 'Italian', 'es': 'Spanish'
        }
        language_name = language_names.get(language_code, 'English')

        logger.info(f"Processing {museum_name} (Language: {language_name})")

        # Build prompt
        prompt = MUSEUM_EMAIL_PROMPT.format(
            museum_name=museum_name,
            summary=museum_data.get('summary', ''),
            focus_wars=museum_data.get('focus_wars', ''),
            focus_periods=museum_data.get('focus_periods', ''),
            focus_topics=museum_data.get('focus_topics', ''),
            hooks=museum_data.get('personalization_hooks', ''),
            website=museum_data.get('website', ''),
            language_code=language_code,
            language_name=language_name
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert outreach copywriter. Generate casual, professional museum emails with SPECIFIC exhibit mentions. ALWAYS write in the specified language."},
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
                        logger.info(f"Progress: {self.processed_count} museums | Cost: ${self.total_cost:.4f}")

                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for {museum_name}: {e}")
                with self._lock:
                    self.failed_count += 1
                return None

            except Exception as e:
                if "rate_limit" in str(e).lower() or attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"API error for {museum_name} (attempt {attempt+1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error for {museum_name} after {max_retries} attempts: {e}")
                    with self._lock:
                        self.failed_count += 1
                    return None

        return None


def main():
    """Main email generation pipeline for museums"""
    logger.info("=== MUSEUM EMAIL GENERATOR STARTED ===")
    logger.info(f"TEST MODE: {'ENABLED' if TEST_MODE else 'DISABLED'}")

    # Load API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env")
        return

    # Load museum data
    logger.info(f"Loading museums from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)

    logger.info(f"Total museums in CSV: {len(df)}")

    # Split multiple emails
    df_split = split_emails(df)

    # Filter: only successful scraping with emails
    df_to_process = df_split[
        (df_split['processing_status'] == 'success') &
        (df_split['email'].notna())
    ].copy()

    # TEST MODE
    if TEST_MODE:
        df_to_process = df_to_process.head(TEST_LIMIT)
        logger.info(f"TEST MODE: Processing only {len(df_to_process)} museums")

    logger.info(f"Museums to process: {len(df_to_process)}")
    logger.info(f"Estimated cost: ${len(df_to_process) * 0.02:.2f}")

    # Initialize generator
    generator = MuseumEmailGenerator(api_key)

    # Process museums
    results = []
    start_time = time.time()

    logger.info(f"Starting processing with {PARALLEL_WORKERS} workers...")

    def process_museum(row):
        """Process single museum"""
        museum_data = {
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

        emails = generator.generate_emails(museum_data)

        if emails:
            return {
                'name': row['name'],
                'email': row['email'],
                'website': row.get('website', ''),
                'short_museum_name': emails.get('short_museum_name', ''),
                'specific_section': emails.get('specific_section', ''),
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
            executor.submit(process_museum, row): row
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

    # JSON
    output_json = OUTPUT_DIR / f"museum_emails_{timestamp}.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'generated_at': timestamp,
                'total_museums': len(results),
                'test_mode': TEST_MODE,
                'total_cost': generator.total_cost
            },
            'results': results
        }, f, indent=2, ensure_ascii=False)

    # CSV
    output_csv = OUTPUT_DIR / f"museum_emails_{timestamp}.csv"
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Stats
    elapsed = time.time() - start_time
    logger.info("=== MUSEUM EMAIL GENERATION COMPLETE ===")
    logger.info(f"Total processed: {generator.processed_count}")
    logger.info(f"Failed: {generator.failed_count}")
    logger.info(f"Total cost: ${generator.total_cost:.4f}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output JSON: {output_json}")
    logger.info(f"Output CSV: {output_csv}")

    # Sample
    if len(df_results) > 0:
        logger.info("\n=== SAMPLE OUTPUT (First Museum) ===")
        first = df_results.iloc[0]
        logger.info(f"Museum: {first['name']}")
        logger.info(f"Email: {first['email']}")
        logger.info(f"Language: {first['language']}")
        logger.info(f"Short Name: {first['short_museum_name']}")
        logger.info(f"Specific Section: {first['specific_section']}")
        logger.info(f"Subject: {first['subject_line']}")
        logger.info(f"\nEmail 1:\n{first['email_1'][:200]}...")


if __name__ == "__main__":
    main()
