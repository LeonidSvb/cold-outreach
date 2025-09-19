#!/usr/bin/env python3
"""
=== SHEETS DATA PROCESSOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Advanced Google Sheets data processing and transformation

FEATURES:
- Data cleaning and validation
- Lead scoring and prioritization
- Duplicate detection and merging
- Data enrichment workflows
- Cross-sheet data synchronization

USAGE:
1. Configure sheet IDs in CONFIG
2. Run: python sheets_data_processor.py

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import asyncio
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log
from shared.google_sheets import GoogleSheetsManager

CONFIG = {
    "SHEETS": {
        "INPUT_SHEET_ID": "your_input_sheet_id",
        "OUTPUT_SHEET_ID": "your_output_sheet_id",
        "PROCESSING_SHEET_ID": "your_processing_sheet_id"
    },
    "PROCESSING": {
        "CLEAN_DATA": True,
        "REMOVE_DUPLICATES": True,
        "VALIDATE_EMAILS": True,
        "SCORE_LEADS": True
    },
    "OUTPUT": {
        "SAVE_JSON": True,
        "RESULTS_DIR": "results"
    }
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "rows_processed": 0,
    "duplicates_removed": 0
}

class SheetsDataProcessor:
    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    @auto_log("sheets_data_processor")
    async def process_sheet_data(self, sheet_id: str) -> Dict[str, Any]:
        print(f"Processing data from sheet: {sheet_id}")

        # Read data from sheet
        gs_manager = GoogleSheetsManager(sheet_id)
        data = gs_manager.batch_read_data()

        if not data:
            print("No data found in sheet")
            return {"error": "No data found"}

        print(f"Processing {len(data)} rows")

        # Process data
        processed_data = self._process_data(data)

        # Save results
        await self._save_results(processed_data)

        return {
            "original_rows": len(data),
            "processed_rows": len(processed_data),
            "duplicates_removed": len(data) - len(processed_data)
        }

    def _process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        df = pd.DataFrame(data)

        # Clean data
        if self.config["PROCESSING"]["CLEAN_DATA"]:
            df = self._clean_data(df)

        # Remove duplicates
        if self.config["PROCESSING"]["REMOVE_DUPLICATES"]:
            df = self._remove_duplicates(df)

        # Validate emails
        if self.config["PROCESSING"]["VALIDATE_EMAILS"]:
            df = self._validate_emails(df)

        # Score leads
        if self.config["PROCESSING"]["SCORE_LEADS"]:
            df = self._score_leads(df)

        return df.to_dict('records')

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Remove empty rows
        df = df.dropna(how='all')

        # Clean email addresses
        if 'email' in df.columns:
            df['email'] = df['email'].str.strip().str.lower()

        # Clean company names
        if 'company' in df.columns:
            df['company'] = df['company'].str.strip()

        return df

    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'email' in df.columns:
            return df.drop_duplicates(subset=['email'])
        return df

    def _validate_emails(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'email' in df.columns:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            df = df[df['email'].str.match(email_pattern, na=False)]
        return df

    def _score_leads(self, df: pd.DataFrame) -> pd.DataFrame:
        df['lead_score'] = 0

        # Score based on company size
        if 'company_size' in df.columns:
            df.loc[df['company_size'] == 'large', 'lead_score'] += 3
            df.loc[df['company_size'] == 'medium', 'lead_score'] += 2
            df.loc[df['company_size'] == 'small', 'lead_score'] += 1

        # Score based on title
        if 'title' in df.columns:
            exec_titles = ['ceo', 'cto', 'vp', 'director', 'founder']
            for title in exec_titles:
                df.loc[df['title'].str.contains(title, case=False, na=False), 'lead_score'] += 2

        return df

    async def _save_results(self, data: List[Dict[str, Any]]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"processed_data_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Processed data saved: {filename}")

async def main():
    processor = SheetsDataProcessor()
    result = await processor.process_sheet_data(CONFIG["SHEETS"]["INPUT_SHEET_ID"])
    print(f"Processing complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())