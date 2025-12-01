#!/usr/bin/env python3
"""
=== SOVIET BOOTS DATA EXTRACTOR ===
Version: 1.0.0 | Created: 2025-01-26

PURPOSE:
Extract detailed information from homepage_content to categorize leads
and personalize outreach emails for Soviet Boots campaign.

FEATURES:
- AI-powered content analysis using OpenAI GPT-4
- Automatic category detection (museum/military_shop/historical_society/reenactment)
- Contact name extraction from homepage content
- Personalization detail extraction (exhibits, products, focus areas)
- Short name and location generation
- Parallel processing for speed

USAGE:
1. Set OpenAI API key in .env file
2. Configure input CSV path in CONFIG
3. Run: python soviet_boots_data_extractor.py
4. Results saved with extracted data in new columns

OUTPUT COLUMNS:
- category: museum / military_shop / historical_society / reenactment_group / other
- contact_first_name: Extracted from homepage if available
- specific_detail: For personalization (exhibit name, product type, focus area)
- short_company_name: Shortened version of organization name
- short_location: City, State format
"""

import asyncio
import aiohttp
import json
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.shared.logging.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIG SECTION
# ============================================================================

CONFIG = {
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY"),
        "BASE_URL": "https://api.openai.com/v1/chat/completions",
        "MODEL": "gpt-4o-mini",
        "MAX_TOKENS": 500,
        "TEMPERATURE": 0.2
    },

    "INPUT": {
        "file_path": r"C:\Users\79818\Downloads\Soviet Boots - 950 US  (2).csv",
        "content_column": "homepage_content",
        "name_column": "name",
        "address_column": "address"
    },

    "PROCESSING": {
        "CONCURRENCY": 30,
        "RETRY_ATTEMPTS": 3,
        "TIMEOUT": 30
    },

    "OUTPUT": {
        "dir": "modules/openai/results",
        "filename": "soviet_boots_extracted_data.csv"
    }
}

# Extraction prompt template
EXTRACTION_PROMPT = """
Analyze this organization's homepage content and extract the following information in JSON format.

Organization Name: {name}
Homepage Content: {content}

Extract and return ONLY valid JSON with these fields:

{{
  "category": "<one of: museum | military_shop | historical_society | reenactment_group | community_organization | other>",
  "contact_first_name": "<first name if found on page, otherwise null>",
  "specific_detail": "<specific thing to mention: exhibit name for museums, product type for shops, historical focus for societies, era/conflict for reenactment groups>",
  "short_company_name": "<shortened version of org name, max 40 chars>",
  "category_confidence": "<high | medium | low>"
}}

Category Guidelines:
- museum: Contains exhibits, collections, artifacts, museum in name
- military_shop: Sells military items, surplus, collectibles, memorabilia
- historical_society: Preserves local history, archives, historical society in name
- reenactment_group: Active reenactment, living history, performs historical events
- community_organization: Libraries, parks, chambers of commerce, cultural centers
- other: Doesn't fit above categories

For specific_detail:
- Museums: Mention specific exhibit, collection, or time period (e.g., "Cold War exhibit", "WWII artifacts")
- Shops: Product type (e.g., "military surplus", "collectibles", "authentic gear")
- Historical Societies: Main historical focus (e.g., "Revolutionary War", "local veterans history")
- Reenactment Groups: Era/conflict focus (e.g., "WWII Eastern Front", "Red Army reenactment")
- Others: Main purpose/activity

For contact_first_name:
- Look for "Contact", "Director", "Curator", "Manager", staff names on page
- Extract ONLY first name if found
- Return null if no clear contact name

For short_company_name:
- Remove words like: "Museum & History Center", "Historical Society", "Memorial", "Inc."
- Keep core identifier
- Example: "Keeler Tavern Museum & History Center" → "Keeler Tavern"

Return ONLY the JSON object, no additional text.
"""

# ============================================================================
# PROCESSOR CLASS
# ============================================================================

class SovietBootsExtractor:
    """Extract data from homepage content using OpenAI"""

    def __init__(self):
        self.config = CONFIG
        self.api_key = self.config["OPENAI_API"]["API_KEY"]
        self.session = None
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "cost_usd": 0.0
        }

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def extract_single(self, row: Dict, index: int) -> Dict:
        """
        Extract data from single organization

        Args:
            row: DataFrame row as dict
            index: Row index for logging

        Returns:
            Dict with extracted fields
        """
        name = row.get(self.config["INPUT"]["name_column"], "")
        content = row.get(self.config["INPUT"]["content_column"], "")

        # Truncate content if too long (OpenAI token limits)
        if len(content) > 10000:
            content = content[:10000] + "..."

        prompt = EXTRACTION_PROMPT.format(
            name=name,
            content=content
        )

        payload = {
            "model": self.config["OPENAI_API"]["MODEL"],
            "messages": [
                {"role": "system", "content": "You are a data extraction assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config["OPENAI_API"]["TEMPERATURE"],
            "max_tokens": self.config["OPENAI_API"]["MAX_TOKENS"]
        }

        for attempt in range(self.config["PROCESSING"]["RETRY_ATTEMPTS"]):
            try:
                async with self.session.post(
                    self.config["OPENAI_API"]["BASE_URL"],
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config["PROCESSING"]["TIMEOUT"])
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content_text = data["choices"][0]["message"]["content"].strip()

                        # Clean JSON response (remove markdown code blocks if present)
                        if content_text.startswith("```"):
                            content_text = content_text.split("```")[1]
                            if content_text.startswith("json"):
                                content_text = content_text[4:]

                        extracted = json.loads(content_text)

                        # Calculate cost (rough estimate)
                        usage = data.get("usage", {})
                        cost = (usage.get("prompt_tokens", 0) * 0.00015 +
                               usage.get("completion_tokens", 0) * 0.0006) / 1000
                        self.stats["cost_usd"] += cost

                        logger.info(f"[{index}] Extracted: {name} → {extracted.get('category')}")
                        return extracted

                    else:
                        error_text = await response.text()
                        logger.warning(f"[{index}] API error {response.status}: {error_text}")

            except json.JSONDecodeError as e:
                logger.error(f"[{index}] JSON parse error: {e}")
            except Exception as e:
                logger.error(f"[{index}] Error on attempt {attempt + 1}: {e}")
                if attempt < self.config["PROCESSING"]["RETRY_ATTEMPTS"] - 1:
                    await asyncio.sleep(2 ** attempt)

        # Return default values if all attempts failed
        logger.error(f"[{index}] Failed to extract data for: {name}")
        return {
            "category": "other",
            "contact_first_name": None,
            "specific_detail": "historical items",
            "short_company_name": name[:40],
            "category_confidence": "low"
        }

    async def process_batch(self, df: pd.DataFrame, start_idx: int, end_idx: int) -> List[Dict]:
        """Process batch of rows"""
        tasks = []
        for idx in range(start_idx, min(end_idx, len(df))):
            row = df.iloc[idx].to_dict()
            tasks.append(self.extract_single(row, idx))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions in results
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing error at index {start_idx + idx}: {result}")
                processed_results.append({
                    "category": "other",
                    "contact_first_name": None,
                    "specific_detail": "historical items",
                    "short_company_name": df.iloc[start_idx + idx]["name"][:40],
                    "category_confidence": "low"
                })
            else:
                processed_results.append(result)

        return processed_results

    async def process_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process all rows with concurrency control"""
        await self.create_session()

        try:
            all_results = []
            batch_size = self.config["PROCESSING"]["CONCURRENCY"]
            total_batches = (len(df) + batch_size - 1) // batch_size

            logger.info(f"Processing {len(df)} rows in {total_batches} batches")

            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = start_idx + batch_size

                logger.info(f"Processing batch {batch_num + 1}/{total_batches} (rows {start_idx}-{min(end_idx, len(df))})")

                batch_results = await self.process_batch(df, start_idx, end_idx)
                all_results.extend(batch_results)

                self.stats["total_processed"] += len(batch_results)
                self.stats["successful"] += sum(1 for r in batch_results if r.get("category_confidence") != "low")

                # Small delay between batches to avoid rate limits
                if batch_num < total_batches - 1:
                    await asyncio.sleep(1)

            # Add extracted data to dataframe
            for key in ["category", "contact_first_name", "specific_detail", "short_company_name", "category_confidence"]:
                df[key] = [r.get(key) for r in all_results]

            # Generate short_location from address
            df["short_location"] = df[self.config["INPUT"]["address_column"]].apply(self._extract_short_location)

            logger.info(f"Processing complete! Stats: {self.stats}")

            return df

        finally:
            await self.close_session()

    def _extract_short_location(self, address: str) -> str:
        """Extract city, state from full address"""
        if pd.isna(address) or not address:
            return ""

        # Address format: "Street, City, State ZIP, Country"
        parts = address.split(",")
        if len(parts) >= 3:
            city = parts[-3].strip()
            state_zip = parts[-2].strip()
            state = state_zip.split()[0] if state_zip else ""
            return f"{city}, {state}"

        return address[:30]


def main():
    """Main execution"""
    logger.info("Starting Soviet Boots data extraction")

    try:
        # Load CSV
        input_file = CONFIG["INPUT"]["file_path"]
        logger.info(f"Loading CSV: {input_file}")
        df = pd.read_csv(input_file)

        logger.info(f"Loaded {len(df)} rows")

        # Initialize extractor
        extractor = SovietBootsExtractor()

        # Process data
        logger.info("Starting OpenAI extraction...")
        df_processed = asyncio.run(extractor.process_all(df))

        # Save results
        output_dir = Path(CONFIG["OUTPUT"]["dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"soviet_boots_extracted_{timestamp}.csv"

        df_processed.to_csv(output_file, index=False, encoding='utf-8-sig')

        logger.info(f"Results saved to: {output_file}")
        logger.info(f"Total cost: ${extractor.stats['cost_usd']:.2f}")

        # Show category breakdown
        logger.info("\nCategory breakdown:")
        for category, count in df_processed['category'].value_counts().items():
            logger.info(f"  {category}: {count}")

        return output_file

    except Exception as e:
        logger.error(f"Processing failed", error=e)
        raise


if __name__ == "__main__":
    main()
