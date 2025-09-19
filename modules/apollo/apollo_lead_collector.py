#!/usr/bin/env python3
"""
=== APOLLO LEAD COLLECTOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Массовый сбор лидов через Apollo API с параллельной обработкой и интеграцией Google Sheets

FEATURES:
- Parallel processing: 50+ concurrent API requests
- Smart batch processing for large datasets
- Google Sheets auto-update integration
- Real-time progress tracking with statistics
- Intelligent rate limiting and retry logic
- Timestamped JSON results export
- Advanced filtering and data validation

USAGE:
1. Set Apollo API key in CONFIG section below
2. Configure search parameters and Google Sheets settings
3. Run: python apollo_lead_collector_20250119.py
4. Results automatically saved to results/ and Google Sheets

IMPROVEMENTS:
v1.0.0 - Initial version with mass parallel processing
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log
from shared.google_sheets import GoogleSheetsManager

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # APOLLO API SETTINGS
    "APOLLO_API": {
        "API_KEY": os.getenv("APOLLO_API_KEY", "your_apollo_api_key_here"),
        "BASE_URL": "https://api.apollo.io/v1",
        "RATE_LIMIT_PER_MINUTE": 1000,
        "TIMEOUT_SECONDS": 30
    },

    # PROCESSING SETTINGS
    "PROCESSING": {
        "CONCURRENCY": 50,              # Parallel requests
        "BATCH_SIZE": 100,              # Items per batch
        "MAX_TOTAL_LEADS": 10000,       # Total leads to collect
        "RETRY_ATTEMPTS": 3,            # API retry count
        "RETRY_DELAY": 1.0              # Initial retry delay
    },

    # SEARCH CRITERIA
    "SEARCH_PARAMS": {
        "person_titles": [
            "CEO", "Chief Executive Officer",
            "CTO", "Chief Technology Officer",
            "Founder", "Co-Founder",
            "VP Engineering", "Head of Engineering",
            "VP Marketing", "Head of Marketing"
        ],
        "company_headcount_min": 10,
        "company_headcount_max": 1000,
        "company_locations": ["United States", "Canada", "United Kingdom"],
        "company_industries": [
            "Computer Software",
            "Information Technology",
            "Marketing and Advertising",
            "E-commerce"
        ]
    },

    # GOOGLE SHEETS INTEGRATION
    "GOOGLE_SHEETS": {
        "ENABLED": True,
        "SHEET_ID": "your_google_sheet_id_here",
        "WORKSHEET_NAME": "Apollo Leads",
        "COLUMN_MAPPING": {
            "first_name": "A",
            "last_name": "B",
            "email": "C",
            "title": "D",
            "company_name": "E",
            "company_website": "F",
            "company_industry": "G",
            "company_size": "H",
            "company_location": "I",
            "linkedin_url": "J",
            "phone": "K"
        }
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "UPDATE_GOOGLE_SHEETS": True,
        "EXPORT_CSV": True,
        "INCLUDE_RAW_DATA": False,       # Include full API response
        "RESULTS_DIR": "results"
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "total_leads_collected": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "avg_cost_per_lead": 0.0,
    "total_api_calls": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class ApolloLeadCollector:
    """High-performance Apollo lead collection with parallel processing"""

    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.leads_collected = 0
        self.api_calls_made = 0

        # Validate config
        self._validate_config()

    def _validate_config(self):
        """Validate configuration settings"""
        if self.config["APOLLO_API"]["API_KEY"] == "your_apollo_api_key_here":
            print("⚠️ Please set your Apollo API key in CONFIG section")

        if (self.config["GOOGLE_SHEETS"]["ENABLED"] and
            self.config["GOOGLE_SHEETS"]["SHEET_ID"] == "your_google_sheet_id_here"):
            print("⚠️ Please set your Google Sheet ID in CONFIG section")

    @auto_log("apollo_lead_collector")
    async def collect_leads(self, target_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Main function to collect leads massively"""

        if target_count is None:
            target_count = self.config["PROCESSING"]["MAX_TOTAL_LEADS"]

        print(f"🚀 Starting Apollo Lead Collection")
        print(f"📊 Target: {target_count:,} leads")
        print(f"🔧 Concurrency: {self.config['PROCESSING']['CONCURRENCY']} threads")
        print(f"⚡ Batch size: {self.config['PROCESSING']['BATCH_SIZE']}")

        start_time = time.time()

        # Initialize session
        timeout = aiohttp.ClientTimeout(total=self.config["APOLLO_API"]["TIMEOUT_SECONDS"])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session

            # Create search batches
            batches = self._create_search_batches(target_count)
            print(f"📦 Created {len(batches)} search batches")

            # Process all batches in parallel
            all_leads = []
            batch_results = await self._process_batches_parallel(batches)

            # Combine results
            for result in batch_results:
                if isinstance(result, list):
                    all_leads.extend(result)

            # Remove duplicates
            unique_leads = self._deduplicate_leads(all_leads)

        # Save results
        await self._save_results(unique_leads, start_time)

        # Update Google Sheets if enabled
        if self.config["GOOGLE_SHEETS"]["ENABLED"] and unique_leads:
            await self._update_google_sheets(unique_leads)

        self._update_script_stats(len(unique_leads), time.time() - start_time)

        print(f"✅ Collection completed!")
        print(f"📈 Total unique leads: {len(unique_leads):,}")
        print(f"⏱️ Processing time: {time.time() - start_time:.2f}s")
        print(f"🔥 Rate: {len(unique_leads)/(time.time() - start_time)*60:.1f} leads/min")

        return unique_leads

    def _create_search_batches(self, target_count: int) -> List[Dict[str, Any]]:
        """Create search parameter batches for parallel processing"""
        batch_size = self.config["PROCESSING"]["BATCH_SIZE"]
        num_batches = (target_count + batch_size - 1) // batch_size

        # Create variations of search parameters for better coverage
        titles_groups = [
            ["CEO", "Chief Executive Officer", "Founder", "Co-Founder"],
            ["CTO", "Chief Technology Officer", "VP Engineering", "Head of Engineering"],
            ["VP Marketing", "Head of Marketing", "CMO", "Chief Marketing Officer"]
        ]

        batches = []
        for i in range(num_batches):
            # Rotate through title groups for variety
            title_group = titles_groups[i % len(titles_groups)]

            batch = {
                "offset": 0,  # Apollo handles pagination differently
                "limit": min(batch_size, target_count - i * batch_size),
                "person_titles": title_group,
                "company_headcount_min": self.config["SEARCH_PARAMS"]["company_headcount_min"],
                "company_headcount_max": self.config["SEARCH_PARAMS"]["company_headcount_max"],
                "company_locations": self.config["SEARCH_PARAMS"]["company_locations"],
                "page": i + 1  # Apollo pagination
            }
            batches.append(batch)

        return batches

    async def _process_batches_parallel(self, batches: List[Dict[str, Any]]) -> List[List[Dict]]:
        """Process all batches in parallel with controlled concurrency"""

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config["PROCESSING"]["CONCURRENCY"])

        async def process_with_semaphore(batch):
            async with semaphore:
                return await self._process_single_batch(batch)

        # Process all batches
        print(f"🔄 Processing {len(batches)} batches in parallel...")
        tasks = [process_with_semaphore(batch) for batch in batches]

        # Track progress
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Progress update
            if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                progress = (i + 1) / len(tasks) * 100
                print(f"📊 Progress: {progress:.1f}% ({i + 1}/{len(tasks)} batches)")

        return results

    async def _process_single_batch(self, batch_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process a single batch of search results with retry logic"""

        for attempt in range(self.config["PROCESSING"]["RETRY_ATTEMPTS"]):
            try:
                # Prepare API request
                url = f"{self.config['APOLLO_API']['BASE_URL']}/mixed_people/search"
                headers = {
                    "Cache-Control": "no-cache",
                    "Content-Type": "application/json",
                    "Api-Key": self.config["APOLLO_API"]["API_KEY"]
                }

                # Make API call
                async with self.session.post(url, json=batch_params, headers=headers) as response:
                    self.api_calls_made += 1

                    if response.status == 200:
                        data = await response.json()
                        people = data.get('people', [])

                        # Process and clean the data
                        processed_leads = self._process_people_data(people)
                        self.leads_collected += len(processed_leads)

                        return processed_leads

                    elif response.status == 429:  # Rate limited
                        wait_time = 2 ** attempt
                        print(f"⏳ Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    else:
                        print(f"❌ API error {response.status} for batch")
                        await asyncio.sleep(self.config["PROCESSING"]["RETRY_DELAY"])
                        continue

            except Exception as e:
                print(f"❌ Batch processing error (attempt {attempt + 1}): {str(e)}")
                if attempt < self.config["PROCESSING"]["RETRY_ATTEMPTS"] - 1:
                    await asyncio.sleep(self.config["PROCESSING"]["RETRY_DELAY"] * (attempt + 1))

        print(f"❌ Failed to process batch after {self.config['PROCESSING']['RETRY_ATTEMPTS']} attempts")
        return []

    def _process_people_data(self, people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and clean people data from Apollo API"""

        processed_leads = []

        for person in people:
            try:
                # Extract key information
                lead = {
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "email": person.get("email", ""),
                    "title": person.get("title", ""),
                    "linkedin_url": person.get("linkedin_url", ""),
                    "phone": person.get("phone_numbers", [{}])[0].get("raw_number", "") if person.get("phone_numbers") else "",
                }

                # Extract company information
                company = person.get("organization", {})
                if company:
                    lead.update({
                        "company_name": company.get("name", ""),
                        "company_website": company.get("website_url", ""),
                        "company_industry": company.get("industry", ""),
                        "company_size": company.get("estimated_num_employees", ""),
                        "company_location": f"{company.get('city', '')}, {company.get('state', '')}, {company.get('country', '')}".strip(", ")
                    })

                # Only include leads with email addresses
                if lead["email"] and self._is_valid_email(lead["email"]):
                    processed_leads.append(lead)

            except Exception as e:
                print(f"⚠️ Error processing person data: {e}")
                continue

        return processed_leads

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _deduplicate_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate leads based on email"""
        seen_emails = set()
        unique_leads = []

        for lead in leads:
            email = lead.get("email", "").lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_leads.append(lead)

        print(f"🔍 Deduplication: {len(leads)} → {len(unique_leads)} unique leads")
        return unique_leads

    async def _save_results(self, leads: List[Dict[str, Any]], start_time: float):
        """Save results to JSON and optionally CSV"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processing_time = time.time() - start_time

        # Prepare results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_leads": len(leads),
                "processing_time_seconds": round(processing_time, 2),
                "total_api_calls": self.api_calls_made,
                "config_used": self.config,
                "script_version": SCRIPT_STATS["version"]
            },
            "leads": leads
        }

        # Save JSON
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"apollo_leads_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"💾 JSON saved: {json_filename}")

        # Save CSV
        if self.config["OUTPUT"]["EXPORT_CSV"] and leads:
            import pandas as pd

            csv_filename = f"apollo_leads_{timestamp}.csv"
            csv_filepath = self.results_dir / csv_filename

            df = pd.DataFrame(leads)
            df.to_csv(csv_filepath, index=False, encoding='utf-8')

            print(f"📊 CSV saved: {csv_filename}")

    async def _update_google_sheets(self, leads: List[Dict[str, Any]]):
        """Update Google Sheets with collected leads"""

        try:
            print(f"📊 Updating Google Sheets...")

            gs_manager = GoogleSheetsManager(
                self.config["GOOGLE_SHEETS"]["SHEET_ID"],
                self.config["GOOGLE_SHEETS"]["WORKSHEET_NAME"]
            )

            success = await gs_manager.batch_write_leads(
                leads,
                self.config["GOOGLE_SHEETS"]["COLUMN_MAPPING"]
            )

            if success:
                print(f"✅ Google Sheets updated with {len(leads):,} leads")
            else:
                print(f"❌ Failed to update Google Sheets")

        except Exception as e:
            print(f"❌ Google Sheets update error: {e}")

    def _update_script_stats(self, leads_count: int, processing_time: float):
        """Update script statistics"""
        global SCRIPT_STATS

        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["total_leads_collected"] += leads_count
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["total_api_calls"] += self.api_calls_made

        # Calculate success rate (simplified)
        if self.api_calls_made > 0:
            SCRIPT_STATS["success_rate"] = (leads_count / self.api_calls_made) * 100

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""

    print("=" * 60)
    print("🚀 APOLLO LEAD COLLECTOR v1.0.0")
    print("=" * 60)

    collector = ApolloLeadCollector()

    # Collect leads (default from CONFIG)
    leads = await collector.collect_leads()

    print("=" * 60)
    print(f"🎯 Mission accomplished: {len(leads):,} leads collected")
    print(f"📈 Success rate: {SCRIPT_STATS['success_rate']:.1f}%")
    print(f"⚡ Total API calls: {SCRIPT_STATS['total_api_calls']:,}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())