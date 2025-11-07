#!/usr/bin/env python3
"""
=== OPENAI MASS PROCESSOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Массовая обработка данных через OpenAI API с параллельными запросами и интеграцией Google Sheets

FEATURES:
- Parallel processing: 50+ concurrent OpenAI requests
- Smart prompt management and batch processing
- Multiple OpenAI models support (GPT-4, GPT-3.5)
- Google Sheets integration for input/output
- Real-time cost tracking and optimization
- Advanced retry logic and rate limiting
- Content analysis and data enrichment

USAGE:
1. Set OpenAI API key in CONFIG section below
2. Configure prompts and processing parameters
3. Run: python openai_mass_processor.py
4. Results automatically saved to results/ and Google Sheets

IMPROVEMENTS:
v1.0.0 - Initial version with mass parallel processing
"""

import asyncio
import aiohttp
import json
import re
import time
import os
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import logger, fall back to print if not available
try:
    from logger.universal_logger import get_logger
    logger = get_logger(__name__)
    def auto_log(name):
        def decorator(func):
            return func
        return decorator
except ImportError:
    logger = None
    def auto_log(name):
        def decorator(func):
            return func
        return decorator

# Google Sheets is optional
try:
    from shared.google_sheets import GoogleSheetsManager
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    GoogleSheetsManager = None

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # OPENAI API SETTINGS
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY", "your_openai_api_key_here"),
        "BASE_URL": "https://api.openai.com/v1",
        "DEFAULT_MODEL": "gpt-4o-mini",
        "BACKUP_MODEL": "gpt-3.5-turbo",
        "MAX_TOKENS": 4000,
        "TEMPERATURE": 0.3
    },

    # PROCESSING SETTINGS
    "PROCESSING": {
        "CONCURRENCY": 50,              # Parallel requests
        "BATCH_SIZE": 100,              # Items per batch
        "RETRY_ATTEMPTS": 3,            # API retry count
        "RETRY_DELAY": 1.0,             # Initial retry delay
        "RATE_LIMIT_RPM": 3000,         # Requests per minute
        "COST_LIMIT_USD": 50.0          # Max cost per run
    },

    # PROMPTS CONFIGURATION
    "PROMPTS": {
        "COMPANY_ANALYZER": """
Analyze this company information and extract key insights:
Company: {{company_name}}
Website: {{website}}
Industry: {{industry}}

Provide analysis in JSON format:
{{
  "pain_points": ["list of potential business pain points"],
  "tech_stack": ["likely technologies used"],
  "decision_makers": ["typical decision maker titles"],
  "personalization_hooks": ["specific hooks for outreach"],
  "company_size_estimate": "small/medium/large",
  "priority_score": 1-10
}}""",

        "EMAIL_PERSONALIZER": """
Create a personalized email opener for this lead:
Name: {{first_name}} {{last_name}}
Title: {{title}}
Company: {{company_name}}
Industry: {{industry}}
Website: {{website}}

Create a highly personalized 2-3 sentence opener that:
1. References something specific about their company/industry
2. Shows genuine research and interest
3. Creates curiosity about our solution

Return only the opener text, no additional formatting.""",

        "CONTENT_ENRICHER": """
Enrich this lead data with additional insights:
{{lead_data}}

Add the following fields in JSON format:
{{
  "enriched_title": "cleaned and standardized job title",
  "seniority_level": "junior/mid/senior/executive",
  "department": "sales/marketing/engineering/etc",
  "buying_power": "low/medium/high",
  "outreach_priority": 1-10,
  "best_contact_time": "morning/afternoon/evening",
  "communication_style": "formal/casual/technical"
}}"""
    },

    # GOOGLE SHEETS INTEGRATION
    "GOOGLE_SHEETS": {
        "ENABLED": True,
        "INPUT_SHEET_ID": "your_input_sheet_id_here",
        "OUTPUT_SHEET_ID": "your_output_sheet_id_here",
        "INPUT_WORKSHEET": "Raw Leads",
        "OUTPUT_WORKSHEET": "Processed Leads",
        "COLUMN_MAPPING": {
            "company_name": "A",
            "website": "B",
            "first_name": "C",
            "last_name": "D",
            "email": "E",
            "title": "F",
            "analysis": "G",
            "personalization": "H",
            "priority_score": "I"
        }
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "UPDATE_GOOGLE_SHEETS": True,
        "EXPORT_CSV": True,
        "INCLUDE_COSTS": True,
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
    "total_items_processed": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "total_cost_usd": 0.0,
    "total_api_calls": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class OpenAIMassProcessor:
    """High-performance OpenAI processing with parallel requests"""

    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.items_processed = 0
        self.api_calls_made = 0
        self.total_cost = 0.0

        # Validate config
        self._validate_config()

    def _validate_config(self):
        """Validate configuration settings"""
        if self.config["OPENAI_API"]["API_KEY"] == "your_openai_api_key_here":
            print("WARNING: Please set your OpenAI API key in CONFIG section")

    @auto_log("openai_mass_processor")
    async def process_data(self, data: List[Dict[str, Any]], prompt_type: str = "COMPANY_ANALYZER") -> List[Dict[str, Any]]:
        """Main function to process data through OpenAI"""

        print(f"Starting OpenAI Mass Processing")
        print(f"Total items: {len(data):,}")
        print(f"Concurrency: {self.config['PROCESSING']['CONCURRENCY']} threads")
        print(f"Model: {self.config['OPENAI_API']['DEFAULT_MODEL']}")
        print(f"Prompt: {prompt_type}")

        start_time = time.time()

        # Initialize session
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session

            # Create processing batches
            batches = self._create_processing_batches(data)
            print(f"Created {len(batches)} processing batches")

            # Process all batches in parallel
            processed_results = await self._process_batches_parallel(batches, prompt_type)

        # Save results
        await self._save_results(processed_results, start_time)

        # Update Google Sheets if enabled and available
        if GOOGLE_SHEETS_AVAILABLE and self.config["GOOGLE_SHEETS"]["ENABLED"] and processed_results:
            await self._update_google_sheets(processed_results)

        self._update_script_stats(len(processed_results), time.time() - start_time)

        print(f"Processing completed!")
        print(f"Total processed: {len(processed_results):,}")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"Processing time: {time.time() - start_time:.2f}s")

        return processed_results

    def _create_processing_batches(self, data: List[Dict[str, Any]]) -> List[List[Dict]]:
        """Create processing batches for parallel execution"""
        batch_size = self.config["PROCESSING"]["BATCH_SIZE"]
        batches = []
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batches.append(batch)
            
        return batches

    async def _process_batches_parallel(self, batches: List[List[Dict]], prompt_type: str) -> List[Dict[str, Any]]:
        """Process all batches in parallel"""
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config["PROCESSING"]["CONCURRENCY"])

        async def process_with_semaphore(batch):
            async with semaphore:
                return await self._process_single_batch(batch, prompt_type)

        # Process all batches
        print(f"Processing {len(batches)} batches in parallel...")
        tasks = [process_with_semaphore(batch) for batch in batches]

        # Track progress
        all_results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            batch_results = await task
            all_results.extend(batch_results)

            # Progress update
            if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                progress = (i + 1) / len(tasks) * 100
                print(f"Progress: {progress:.1f}% ({i + 1}/{len(tasks)} batches)")

        return all_results

    async def _process_single_batch(self, batch: List[Dict[str, Any]], prompt_type: str) -> List[Dict[str, Any]]:
        """Process a single batch through OpenAI API"""
        
        batch_results = []
        
        for item in batch:
            try:
                # Check cost limit
                if self.total_cost >= self.config["PROCESSING"]["COST_LIMIT_USD"]:
                    print(f"WARNING: Cost limit reached: ${self.total_cost:.4f}")
                    break
                    
                # Process single item
                result = await self._process_single_item(item, prompt_type)
                if result:
                    batch_results.append(result)
                    
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"ERROR: Error processing item: {e}")
                continue
                
        return batch_results

    async def _process_single_item(self, item: Dict[str, Any], prompt_type: str) -> Optional[Dict[str, Any]]:
        """Process a single item through OpenAI API with retry logic"""
        
        for attempt in range(self.config["PROCESSING"]["RETRY_ATTEMPTS"]):
            try:
                # Prepare prompt
                prompt = self._prepare_prompt(item, prompt_type)
                
                # Make API call
                response_data = await self._make_openai_request(prompt)
                
                if response_data:
                    # Calculate cost
                    cost = self._calculate_cost(response_data)
                    self.total_cost += cost

                    # Prepare result
                    result = item.copy()

                    # Parse OpenAI response (universal: JSON dict or plain text)
                    openai_content = response_data["choices"][0]["message"]["content"]
                    parsed_fields = self._parse_openai_response(openai_content)
                    result.update(parsed_fields)

                    result["processing_cost"] = cost
                    result["model_used"] = response_data["model"]
                    result["processed_at"] = datetime.now().isoformat()

                    self.items_processed += 1
                    return result
                    
            except Exception as e:
                if attempt < self.config["PROCESSING"]["RETRY_ATTEMPTS"] - 1:
                    await asyncio.sleep(self.config["PROCESSING"]["RETRY_DELAY"] * (attempt + 1))
                    continue
                else:
                    print(f"ERROR: Failed to process item after {self.config['PROCESSING']['RETRY_ATTEMPTS']} attempts: {e}")
                    
        return None

    def _parse_openai_response(self, content: str) -> Dict[str, Any]:
        """
        Universal parser for OpenAI responses.
        Tries to extract JSON from markdown blocks or plain text.
        Creates multiple columns from dict, or single 'ai_result' column.
        """
        # Try to extract JSON from markdown code blocks first
        json_block_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_block_pattern, content, re.DOTALL)

        if match:
            json_str = match.group(1).strip()
        else:
            # No markdown block, try the whole content
            json_str = content.strip()

        try:
            # Try to parse as JSON
            parsed = json.loads(json_str)

            # If it's a dict, return it (each key becomes a column)
            if isinstance(parsed, dict):
                return parsed

            # If it's a list or other type, stringify and return as single column
            return {"ai_result": json.dumps(parsed)}

        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, return as plain text
            return {"ai_result": content.strip()}

    def _prepare_prompt(self, item: Dict[str, Any], prompt_type: str) -> str:
        """Prepare prompt with item data"""
        prompt_template = self.config["PROMPTS"].get(prompt_type, self.config["PROMPTS"]["COMPANY_ANALYZER"])
        
        # Replace placeholders
        prompt = prompt_template
        for key, value in item.items():
            placeholder = "{{" + key + "}}"
            prompt = prompt.replace(placeholder, str(value))
            
        return prompt

    async def _make_openai_request(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Make request to OpenAI API"""
        
        url = f"{self.config['OPENAI_API']['BASE_URL']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config['OPENAI_API']['API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config["OPENAI_API"]["DEFAULT_MODEL"],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.config["OPENAI_API"]["MAX_TOKENS"],
            "temperature": self.config["OPENAI_API"]["TEMPERATURE"]
        }
        
        async with self.session.post(url, json=payload, headers=headers) as response:
            self.api_calls_made += 1
            
            if response.status == 200:
                return await response.json()
            else:
                print(f"ERROR: OpenAI API error {response.status}")
                return None

    def _calculate_cost(self, response_data: Dict[str, Any]) -> float:
        """Calculate cost based on token usage"""
        # Simplified cost calculation for GPT-4o-mini
        usage = response_data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        # GPT-4o-mini pricing (approximate)
        input_cost = input_tokens * 0.00015 / 1000
        output_cost = output_tokens * 0.0006 / 1000
        
        return input_cost + output_cost

    async def _save_results(self, results: List[Dict[str, Any]], start_time: float):
        """Save results to JSON and optionally CSV"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processing_time = time.time() - start_time
        
        # Prepare results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_items": len(results),
                "processing_time_seconds": round(processing_time, 2),
                "total_cost_usd": round(self.total_cost, 4),
                "total_api_calls": self.api_calls_made,
                "config_used": self.config,
                "script_version": SCRIPT_STATS["version"]
            },
            "results": results
        }
        
        # Save JSON
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"openai_processed_{timestamp}.json"
            json_filepath = self.results_dir / json_filename
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"JSON saved: {json_filename}")

    async def _update_google_sheets(self, results: List[Dict[str, Any]]):
        """Update Google Sheets with processed results"""
        
        try:
            print(f"Updating Google Sheets...")

            gs_manager = GoogleSheetsManager(
                self.config["GOOGLE_SHEETS"]["OUTPUT_SHEET_ID"],
                self.config["GOOGLE_SHEETS"]["OUTPUT_WORKSHEET"]
            )
            
            success = await gs_manager.batch_write_leads(
                results,
                self.config["GOOGLE_SHEETS"]["COLUMN_MAPPING"]
            )
            
            if success:
                print(f"Google Sheets updated with {len(results):,} items")
            else:
                print(f"ERROR: Failed to update Google Sheets")

        except Exception as e:
            print(f"ERROR: Google Sheets update error: {e}")

    def _update_script_stats(self, items_count: int, processing_time: float):
        """Update script statistics"""
        global SCRIPT_STATS
        
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["total_items_processed"] += items_count
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["total_cost_usd"] += self.total_cost
        SCRIPT_STATS["total_api_calls"] += self.api_calls_made
        
        # Calculate success rate
        if self.api_calls_made > 0:
            SCRIPT_STATS["success_rate"] = (items_count / self.api_calls_made) * 100

# ============================================================================
# CLI ARGUMENTS PARSING
# ============================================================================

def parse_cli_arguments():
    """Parse command line arguments for frontend integration"""
    parser = argparse.ArgumentParser(description="OpenAI Mass Processor - Universal CSV AI processing")

    parser.add_argument('--input', type=str, help='Path to input CSV file')
    parser.add_argument('--prompt', type=str, help='Custom OpenAI prompt (use {{column_name}} placeholders)')
    parser.add_argument('--model', type=str, default='gpt-4o-mini',
                        choices=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
                        help='OpenAI model to use')
    parser.add_argument('--concurrency', type=int, default=25,
                        help='Number of parallel requests (1-50)')
    parser.add_argument('--temperature', type=float, default=0.3,
                        help='Temperature for OpenAI (0.0-1.0)')
    parser.add_argument('--output', type=str, help='Output file path (optional, auto-generated if not provided)')

    return parser.parse_args()

def load_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """Load CSV file and convert to list of dicts"""
    try:
        df = pd.read_csv(file_path)
        data = df.to_dict(orient='records')
        print(f"Loaded {len(data):,} rows from {file_path}")
        return data
    except Exception as e:
        print(f"ERROR: Error loading CSV: {e}")
        return []

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function with CLI argument support"""

    # Parse CLI arguments
    args = parse_cli_arguments()

    print("=" * 60)
    print("OPENAI MASS PROCESSOR v1.0.0")
    print("=" * 60)

    processor = OpenAIMassProcessor()

    # Apply CLI overrides to config
    if args.model:
        processor.config["OPENAI_API"]["DEFAULT_MODEL"] = args.model
    if args.concurrency:
        processor.config["PROCESSING"]["CONCURRENCY"] = args.concurrency
    if args.temperature is not None:
        processor.config["OPENAI_API"]["TEMPERATURE"] = args.temperature

    # Add custom prompt to config if provided
    if args.prompt:
        processor.config["PROMPTS"]["CUSTOM"] = args.prompt
        prompt_type = "CUSTOM"
    else:
        prompt_type = "COMPANY_ANALYZER"

    # Load data
    if args.input:
        # Load from CSV file
        data = load_csv_data(args.input)
        if not data:
            print("ERROR: No data loaded, exiting.")
            return
    else:
        # Sample data for testing
        print("WARNING: No --input provided, using sample data for testing")
        data = [
            {
                "company_name": "Tech Startup Inc",
                "website": "https://techstartup.com",
                "industry": "Software"
            }
        ]

    # Process data
    results = await processor.process_data(data, prompt_type)

    # Save results to CSV
    if results and args.input:
        output_path = args.output or f"results/openai_processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False, encoding='utf-8')
        print(f"CSV saved: {output_path}")

    print("=" * 60)
    print(f"Processing completed: {len(results):,} items")
    print(f"Total cost: ${SCRIPT_STATS['total_cost_usd']:.4f}")
    print(f"Total API calls: {SCRIPT_STATS['total_api_calls']:,}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())