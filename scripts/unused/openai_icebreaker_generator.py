#!/usr/bin/env python3
"""
=== ICEBREAKER MESSAGE GENERATOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Generate personalized icebreaker messages for LinkedIn outreach using OpenAI

FEATURES:
- Custom prompt-based message generation
- Batch processing with OpenAI API
- CSV input/output
- Cost tracking and rate limiting

USAGE:
1. Configure CONFIG section with your settings
2. Run: python icebreaker_generator.py
3. Results saved to results/
"""

import os
import sys
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from modules.shared.logging.universal_logger import get_logger
    logger = get_logger(__name__)
    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False
    logger = None

# Simple decorator if logger not available
def auto_log(name):
    def decorator(func):
        return func
    return decorator if not HAS_LOGGER else lambda f: f

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # INPUT FILE
    "INPUT": {
        "FILE_PATH": r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders (3).csv",
        "TEST_ROWS": None,  # None = process all rows
        "SKIP_ROWS": 0  # Skip first N rows
    },

    # OPENAI API SETTINGS
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY"),
        "BASE_URL": "https://api.openai.com/v1",
        "MODEL": "gpt-4o-mini",
        "MAX_TOKENS": 500,
        "TEMPERATURE": 0.7
    },

    # PROCESSING SETTINGS
    "PROCESSING": {
        "CONCURRENCY": 30,  # Parallel requests
        "RETRY_ATTEMPTS": 3,
        "RETRY_DELAY": 1.0,
        "RATE_LIMIT_DELAY": 0.1
    },

    # PROMPT
    "PROMPT": """You are an outreach message generator.
Your role: create short, casual, human-sounding icebreaker messages for LinkedIn-style outreach.
Goal: make the recipient feel recognized for their work without sounding pushy or overly formal.

Your task:
- If "full_name" looks like a company (contains words such as Company, Inc, LLC, Ltd, Group, Realty, Properties, Brokers, UAE, Dubai, Abu Dhabi):
    → Output ONLY:
    its a company

- Else (if "full_name" is a person):
    1. Extract firstName = first word of full_name.
    2. Normalize company_name into shortCompany:
        - If ALL CAPS → convert to Title Case (only first letter uppercase).
        - Remove corporate suffixes: Properties, Realty, Group, Brokers, LLC, Ltd, Inc, UAE, Dubai, Abu Dhabi.
        - Remove apostrophes or special symbols.
    3. Normalize region into shortRegion:
        - Dubai, Abu Dhabi → Dubai
        - San Francisco → SF
        - New York City → NYC
        - Else keep original.
    4. Generate opening = pick randomly, in casual tone:
        - love how you
        - really like how you
        - awesome to see you
        - impressed by how you
        - great track with how you
        - cool to see you
    5. specializationPhrase:
        - Look at headline or title.
        - If clear keyword (luxury, sales, marketing, engineering, talent acquisition, product, design, etc.) → rewrite naturally as an action (2–3 words).
            • Example: "Luxury Consultant" → "drive luxury sales"
            • "Marketing Manager" → "lead marketing"
            • "Talent Acquisition" → "grow teams"
            • "Software Engineer" → "build products"
        - If generic title → simplify to meaningful action:
            • "Consultant" → "work with clients"
            • "Broker" → "push sales"
            • "Analyst" → "dig into insights"
        - If nothing useful → fallback: "bring industry experience".
    6. regionPhrase = pick randomly:
        - I'm also in the {{shortRegion}} market
        - I work across {{shortRegion}} as well
        - I'm active in {{shortRegion}} too
        - I also focus on {{shortRegion}}
    7. closingPhrase = pick randomly:
        - Wanted to run something by you.
        - Thought I'd share an idea with you.
        - Had something you might find interesting.
        - Figured I'd reach out quickly.

Final Output (always one line, no labels, no JSON):
Hey {{firstName}}, {{opening}} {{specializationPhrase}} at {{shortCompany}} – {{regionPhrase}}. {{closingPhrase}}

Input data:
full_name: {full_name}
company_name: {company_name}
region: {region}
headline: {headline}
title: {title}

Output ONLY the icebreaker message, nothing else.""",

    # OUTPUT SETTINGS
    "OUTPUT": {
        "RESULTS_DIR": "results",
        "SAVE_JSON": True,
        "SAVE_CSV": True
    }
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class IcebreakerGenerator:
    """Generate icebreaker messages using OpenAI API"""

    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.total_cost = 0.0
        self.processed_count = 0

    @auto_log("icebreaker_generator")
    async def process_csv(self, test_mode: bool = False) -> pd.DataFrame:
        """Process CSV file and generate icebreakers"""

        print("="*80)
        print("ICEBREAKER GENERATOR v1.0.0")
        print("="*80)

        # Load CSV
        print(f"\nLoading CSV: {self.config['INPUT']['FILE_PATH']}")
        df = pd.read_csv(self.config['INPUT']['FILE_PATH'])
        print(f"Loaded {len(df):,} rows")

        # Process only test rows if in test mode
        if test_mode and self.config['INPUT']['TEST_ROWS']:
            rows_to_process = self.config['INPUT']['TEST_ROWS']
            skip_rows = self.config['INPUT']['SKIP_ROWS']
            df = df.iloc[skip_rows:skip_rows + rows_to_process]
            print(f"\nTest mode: Processing {len(df)} rows")

        # Display preview
        print("\nData preview:")
        print(df[['first_name', 'last_name', 'company_name', 'city', 'title']].head(3).to_string())

        # Generate icebreakers
        print(f"\nGenerating icebreakers with OpenAI...")
        start_time = time.time()

        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session
            icebreakers = await self._process_batch(df)

        # Add icebreakers to dataframe
        df['icebreaker'] = icebreakers

        processing_time = time.time() - start_time

        print(f"\n{'='*80}")
        print(f"Processing completed!")
        print(f"Time: {processing_time:.1f} seconds")
        print(f"Processed: {self.processed_count}/{len(df)} rows")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"{'='*80}")

        # Save results
        self._save_results(df)

        return df

    async def _process_batch(self, df: pd.DataFrame) -> List[str]:
        """Process batch of rows with OpenAI"""

        semaphore = asyncio.Semaphore(self.config['PROCESSING']['CONCURRENCY'])

        async def process_with_semaphore(index_row):
            index, row = index_row
            async with semaphore:
                result = await self._process_single_row(row)
                if (index + 1) % 5 == 0 or (index + 1) == len(df):
                    print(f"Progress: {index + 1}/{len(df)} rows processed")
                return result

        # Use gather to preserve order
        tasks = [process_with_semaphore((i, row)) for i, (_, row) in enumerate(df.iterrows())]
        results = await asyncio.gather(*tasks)

        return results

    async def _process_single_row(self, row: pd.Series) -> str:
        """Process single row and generate icebreaker"""

        for attempt in range(self.config['PROCESSING']['RETRY_ATTEMPTS']):
            try:
                # Prepare prompt with row data
                prompt = self._prepare_prompt(row)

                # Call OpenAI API
                response = await self._call_openai_api(prompt)

                if response:
                    self.processed_count += 1
                    return response

                await asyncio.sleep(self.config['PROCESSING']['RETRY_DELAY'])

            except Exception as e:
                if attempt < self.config['PROCESSING']['RETRY_ATTEMPTS'] - 1:
                    await asyncio.sleep(self.config['PROCESSING']['RETRY_DELAY'] * (attempt + 1))
                    continue
                else:
                    print(f"Error processing row: {e}")
                    return f"Error: {str(e)}"

        return "Error: Max retries exceeded"

    def _prepare_prompt(self, row: pd.Series) -> str:
        """Prepare prompt with row data"""

        # Combine first_name and last_name for full_name
        full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()

        # Get other fields
        company_name = str(row.get('company_name', '')).strip()
        city = str(row.get('city', '')).strip()
        headline = str(row.get('headline', '')).strip()
        title = str(row.get('title', '')).strip()

        # Format prompt
        prompt = self.config['PROMPT'].format(
            full_name=full_name or "Not provided",
            company_name=company_name or "Not provided",
            region=city or "Not provided",
            headline=headline or "Not provided",
            title=title or "Not provided"
        )

        return prompt

    async def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API"""

        url = f"{self.config['OPENAI_API']['BASE_URL']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['OPENAI_API']['API_KEY']}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.config['OPENAI_API']['MODEL'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config['OPENAI_API']['MAX_TOKENS'],
            "temperature": self.config['OPENAI_API']['TEMPERATURE']
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()

                # Calculate cost
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                # GPT-4o-mini pricing
                cost = (input_tokens * 0.00015 + output_tokens * 0.0006) / 1000
                self.total_cost += cost

                return data["choices"][0]["message"]["content"].strip()
            else:
                error_text = await response.text()
                print(f"API error {response.status}: {error_text}")
                return None

        await asyncio.sleep(self.config['PROCESSING']['RATE_LIMIT_DELAY'])

    def _save_results(self, df: pd.DataFrame):
        """Save results to CSV and JSON"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save CSV
        if self.config['OUTPUT']['SAVE_CSV']:
            csv_filename = f"icebreakers_{timestamp}.csv"
            csv_path = self.results_dir / csv_filename
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"\nCSV saved: {csv_filename}")

        # Save JSON
        if self.config['OUTPUT']['SAVE_JSON']:
            json_filename = f"icebreakers_{timestamp}.json"
            json_path = self.results_dir / json_filename

            results_data = {
                "metadata": {
                    "timestamp": timestamp,
                    "total_rows": len(df),
                    "processed_rows": self.processed_count,
                    "total_cost_usd": round(self.total_cost, 4),
                    "model_used": self.config['OPENAI_API']['MODEL']
                },
                "results": df.to_dict(orient='records')
            }

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"JSON saved: {json_filename}")

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""

    generator = IcebreakerGenerator()

    # Process CSV (full file)
    df_results = await generator.process_csv(test_mode=False)

    # Display sample results
    print("\nSample icebreakers:")
    print("-" * 80)
    for i, row in df_results.head(10).iterrows():
        first_name = str(row.get('first_name', '')).encode('ascii', errors='ignore').decode('ascii')
        last_name = str(row.get('last_name', '')).encode('ascii', errors='ignore').decode('ascii')
        company = str(row.get('company_name', '')).encode('ascii', errors='ignore').decode('ascii')
        icebreaker = str(row.get('icebreaker', '')).encode('ascii', errors='ignore').decode('ascii')

        print(f"\n{i+1}. {first_name} {last_name}")
        print(f"   Company: {company}")
        print(f"   Icebreaker: {icebreaker}")

if __name__ == "__main__":
    asyncio.run(main())
