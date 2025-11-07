#!/usr/bin/env python3
"""
=== BATCH ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Process multiple CSV files with LinkedIn-style icebreaker generation

USAGE:
python batch_icebreaker_generator.py
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

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

FILES_TO_PROCESS = [
    {
        "name": "C-level Executives",
        "path": r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - US С - level (1).csv"
    },
    {
        "name": "Founders",
        "path": r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders (3).csv"
    }
]

CONFIG = {
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY"),
        "BASE_URL": "https://api.openai.com/v1",
        "MODEL": "gpt-4o-mini",
        "MAX_TOKENS": 500,
        "TEMPERATURE": 0.7
    },

    "PROCESSING": {
        "CONCURRENCY": 10,
        "RETRY_ATTEMPTS": 3,
        "RETRY_DELAY": 1.0,
        "RATE_LIMIT_DELAY": 0.1
    },

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

Output ONLY the icebreaker message, nothing else."""
}

class BatchIcebreakerGenerator:
    """Generate icebreakers for multiple CSV files"""

    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    async def process_all_files(self):
        """Process all CSV files"""

        print("="*80)
        print("BATCH ICEBREAKER GENERATOR")
        print("="*80)

        total_start = time.time()

        for file_config in FILES_TO_PROCESS:
            print(f"\n{'='*80}")
            print(f"Processing: {file_config['name']}")
            print(f"{'='*80}")

            try:
                await self.process_single_file(
                    file_config['path'],
                    file_config['name']
                )
            except Exception as e:
                logger.error(f"Failed to process {file_config['name']}", error=e)
                print(f"Error: {e}")

        total_time = time.time() - total_start
        print(f"\n{'='*80}")
        print(f"All files processed in {total_time:.1f} seconds")
        print(f"{'='*80}")

    async def process_single_file(self, file_path: str, file_name: str):
        """Process single CSV file"""

        logger.info(f"Loading CSV: {file_path}")
        print(f"\nLoading: {file_path}")

        df = pd.read_csv(file_path, encoding='utf-8-sig')
        total_rows = len(df)

        print(f"Total rows: {total_rows:,}")

        print("\nData preview:")
        preview_cols = ['first_name', 'last_name', 'company_name', 'city']
        available_cols = [col for col in preview_cols if col in df.columns]
        if available_cols:
            print(df[available_cols].head(3).to_string())

        start_time = time.time()
        print(f"\nGenerating icebreakers...")

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session
            icebreakers = await self._process_batch(df)

        df['icebreaker'] = icebreakers

        processing_time = time.time() - start_time
        success_count = sum(1 for ice in icebreakers if not ice.startswith('Error'))

        print(f"\n{'='*60}")
        print(f"Completed: {file_name}")
        print(f"Time: {processing_time:.1f} seconds")
        print(f"Success: {success_count}/{total_rows} rows ({success_count/total_rows*100:.1f}%)")
        print(f"{'='*60}")

        self._save_results(df, file_name)

        self._show_samples(df)

    async def _process_batch(self, df: pd.DataFrame) -> List[str]:
        """Process batch with concurrency control"""

        semaphore = asyncio.Semaphore(self.config['PROCESSING']['CONCURRENCY'])
        total = len(df)

        async def process_with_semaphore(index_row):
            index, row = index_row
            async with semaphore:
                result = await self._process_single_row(row)
                if (index + 1) % 50 == 0 or (index + 1) == total:
                    print(f"Progress: {index + 1}/{total} rows")
                return result

        tasks = [process_with_semaphore((i, row)) for i, (_, row) in enumerate(df.iterrows())]
        results = await asyncio.gather(*tasks)

        return results

    async def _process_single_row(self, row: pd.Series) -> str:
        """Process single row"""

        for attempt in range(self.config['PROCESSING']['RETRY_ATTEMPTS']):
            try:
                prompt = self._prepare_prompt(row)
                response = await self._call_openai_api(prompt)

                if response:
                    return response

                await asyncio.sleep(self.config['PROCESSING']['RETRY_DELAY'])

            except Exception as e:
                if attempt < self.config['PROCESSING']['RETRY_ATTEMPTS'] - 1:
                    await asyncio.sleep(self.config['PROCESSING']['RETRY_DELAY'] * (attempt + 1))
                    continue
                else:
                    return f"Error: {str(e)[:100]}"

        return "Error: Max retries exceeded"

    def _prepare_prompt(self, row: pd.Series) -> str:
        """Prepare prompt with row data"""

        full_name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        company_name = str(row.get('company_name', '')).strip()
        city = str(row.get('city', '')).strip()
        headline = str(row.get('headline', '')).strip()
        title = str(row.get('title', '')).strip()

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
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config['OPENAI_API']['MAX_TOKENS'],
            "temperature": self.config['OPENAI_API']['TEMPERATURE']
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                error_text = await response.text()
                logger.error(f"API error {response.status}", error=error_text[:200])
                return None

        await asyncio.sleep(self.config['PROCESSING']['RATE_LIMIT_DELAY'])

    def _save_results(self, df: pd.DataFrame, file_name: str):
        """Save results to CSV"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = file_name.replace(" ", "_").replace("/", "_")

        csv_filename = f"icebreakers_{safe_name}_{timestamp}.csv"
        csv_path = self.results_dir / csv_filename

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        logger.info(f"Results saved: {csv_filename}")
        print(f"Saved: {csv_filename}")

    def _show_samples(self, df: pd.DataFrame):
        """Show sample results"""

        print("\nSample icebreakers:")
        print("-" * 80)

        success_df = df[~df['icebreaker'].str.startswith('Error', na=False)]

        for i, (idx, row) in enumerate(success_df.head(5).iterrows()):
            first_name = str(row.get('first_name', ''))
            last_name = str(row.get('last_name', ''))
            company = str(row.get('company_name', ''))
            icebreaker = str(row.get('icebreaker', ''))

            print(f"\n{i+1}. {first_name} {last_name}")
            print(f"   Company: {company}")
            print(f"   Icebreaker: {icebreaker}")

async def main():
    """Main execution"""

    generator = BatchIcebreakerGenerator()
    await generator.process_all_files()

if __name__ == "__main__":
    asyncio.run(main())
