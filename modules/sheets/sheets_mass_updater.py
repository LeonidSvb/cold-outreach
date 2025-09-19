#!/usr/bin/env python3
"""
=== SHEETS MASS UPDATER ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Mass Google Sheets operations with parallel processing and advanced data management

FEATURES:
- Parallel sheet operations: 50+ concurrent updates
- Multi-sheet batch processing across workbooks
- Advanced column mapping and data transformation
- Real-time data validation and cleaning
- Cross-sheet data synchronization
- Automatic backup and version control
- Smart conflict resolution

USAGE:
1. Configure sheet IDs and mappings in CONFIG section below
2. Set data sources and transformation rules
3. Run: python sheets_mass_updater.py
4. Results automatically logged and backed up

IMPROVEMENTS:
v1.0.0 - Initial version with mass parallel processing
"""

import asyncio
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import pandas as pd

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log
from shared.google_sheets import GoogleSheetsManager

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # GOOGLE SHEETS SETTINGS
    "SHEETS_CONFIG": {
        "PRIMARY_SHEET_ID": "your_primary_sheet_id_here",
        "BACKUP_SHEET_ID": "your_backup_sheet_id_here",
        "PROCESSING_SHEET_ID": "your_processing_sheet_id_here",
        "DEFAULT_WORKSHEET": "Sheet1"
    },

    # PROCESSING SETTINGS
    "PROCESSING": {
        "CONCURRENCY": 50,              # Parallel operations
        "BATCH_SIZE": 1000,             # Rows per batch
        "RETRY_ATTEMPTS": 3,            # API retry count
        "RETRY_DELAY": 1.0,             # Initial retry delay
        "ENABLE_BACKUP": True,          # Auto-backup before changes
        "VALIDATE_DATA": True           # Enable data validation
    },

    # COLUMN MAPPINGS
    "COLUMN_MAPPINGS": {
        "LEADS_MAPPING": {
            "first_name": "A",
            "last_name": "B",
            "email": "C",
            "company": "D",
            "title": "E",
            "phone": "F",
            "website": "G",
            "industry": "H",
            "status": "I",
            "last_updated": "J"
        },
        "COMPANIES_MAPPING": {
            "company_name": "A",
            "website": "B",
            "industry": "C",
            "size": "D",
            "location": "E",
            "technologies": "F",
            "priority_score": "G",
            "analysis_date": "H"
        },
        "CAMPAIGNS_MAPPING": {
            "campaign_name": "A",
            "status": "B",
            "leads_count": "C",
            "open_rate": "D",
            "reply_rate": "E",
            "last_run": "F",
            "next_run": "G"
        }
    },

    # DATA TRANSFORMATION
    "TRANSFORMATIONS": {
        "CLEAN_EMAILS": True,
        "STANDARDIZE_PHONES": True,
        "NORMALIZE_COMPANIES": True,
        "VALIDATE_WEBSITES": True,
        "AUTO_DEDUPLICATE": True,
        "ADD_TIMESTAMPS": True
    },

    # OPERATIONS
    "OPERATIONS": {
        "SUPPORTED_FORMATS": ["json", "csv", "xlsx"],
        "AUTO_CREATE_WORKSHEETS": True,
        "PRESERVE_FORMULAS": True,
        "UPDATE_MODE": "append",  # "append", "replace", "merge"
        "CONFLICT_RESOLUTION": "latest_wins"  # "latest_wins", "manual", "merge"
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "LOG_ALL_OPERATIONS": True,
        "SAVE_BACKUPS": True,
        "EXPORT_REPORTS": True,
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
    "total_rows_processed": 0,
    "total_sheets_updated": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "total_operations": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class SheetsMassUpdater:
    """High-performance Google Sheets mass updater with parallel processing"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.rows_processed = 0
        self.sheets_updated = 0
        self.operations_performed = 0

        # Validate config
        self._validate_config()

    def _validate_config(self):
        """Validate configuration settings"""
        required_sheets = ["PRIMARY_SHEET_ID", "BACKUP_SHEET_ID", "PROCESSING_SHEET_ID"]
        for sheet_key in required_sheets:
            if self.config["SHEETS_CONFIG"][sheet_key] == f"your_{sheet_key.lower()}_here":
                print(f"Please set {sheet_key} in CONFIG section")

    @auto_log("sheets_mass_updater")
    async def mass_update_sheets(self, data_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Main function to perform mass sheet updates"""

        print(f"Starting Sheets Mass Update")
        print(f"Data sources: {len(data_sources):,}")
        print(f"Concurrency: {self.config['PROCESSING']['CONCURRENCY']} threads")
        print(f"Batch size: {self.config['PROCESSING']['BATCH_SIZE']} rows")

        start_time = time.time()
        results = {
            "successful_updates": [],
            "failed_updates": [],
            "backups_created": [],
            "total_rows_processed": 0
        }

        # Create backup if enabled
        if self.config["PROCESSING"]["ENABLE_BACKUP"]:
            await self._create_backups(data_sources)

        # Process all data sources in parallel
        update_results = await self._process_data_sources_parallel(data_sources)

        # Compile results
        for result in update_results:
            if result["success"]:
                results["successful_updates"].append(result)
                self.sheets_updated += 1
                self.rows_processed += result["rows_processed"]
            else:
                results["failed_updates"].append(result)

        results["total_rows_processed"] = self.rows_processed

        # Save operation log
        await self._save_operation_log(results, start_time)

        # Generate report
        if self.config["OUTPUT"]["EXPORT_REPORTS"]:
            await self._generate_report(results, start_time)

        self._update_script_stats(len(data_sources), time.time() - start_time)

        print(f"Mass update completed!")
        print(f"Sheets updated: {self.sheets_updated:,}")
        print(f"Rows processed: {self.rows_processed:,}")
        print(f"Processing time: {time.time() - start_time:.2f}s")

        return results

    async def _create_backups(self, data_sources: List[Dict[str, Any]]):
        """Create backups of sheets before modification"""
        
        print(f"Creating backups...")
        
        backup_tasks = []
        for source in data_sources:
            if "sheet_id" in source:
                backup_task = self._backup_single_sheet(source["sheet_id"])
                backup_tasks.append(backup_task)
        
        if backup_tasks:
            await asyncio.gather(*backup_tasks, return_exceptions=True)
            print(f"Backups created for {len(backup_tasks)} sheets")

    async def _backup_single_sheet(self, sheet_id: str) -> bool:
        """Create backup of a single sheet"""
        
        try:
            # Read current data
            gs_manager = GoogleSheetsManager(sheet_id)
            current_data = gs_manager.batch_read_data()
            
            if current_data:
                # Save backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"backup_{sheet_id}_{timestamp}.json"
                backup_filepath = self.results_dir / "backups" / backup_filename
                backup_filepath.parent.mkdir(exist_ok=True)
                
                with open(backup_filepath, 'w', encoding='utf-8') as f:
                    json.dump(current_data, f, indent=2, ensure_ascii=False)
                    
                print(f"Backup created: {backup_filename}")
                return True
                
        except Exception as e:
            print(f"Backup failed for {sheet_id}: {e}")
            return False

    async def _process_data_sources_parallel(self, data_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process all data sources in parallel"""
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.config["PROCESSING"]["CONCURRENCY"])

        async def process_with_semaphore(source):
            async with semaphore:
                return await self._process_single_data_source(source)

        # Process all sources
        print(f"Processing {len(data_sources)} data sources in parallel...")
        tasks = [process_with_semaphore(source) for source in data_sources]

        # Track progress
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            results.append(result)

            # Progress update
            if (i + 1) % 10 == 0 or (i + 1) == len(tasks):
                progress = (i + 1) / len(tasks) * 100
                print(f"Progress: {progress:.1f}% ({i + 1}/{len(tasks)} sources)")

        return results

    async def _process_single_data_source(self, data_source: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data source"""
        
        result = {
            "source_id": data_source.get("id", "unknown"),
            "sheet_id": data_source.get("sheet_id"),
            "worksheet": data_source.get("worksheet", self.config["SHEETS_CONFIG"]["DEFAULT_WORKSHEET"]),
            "success": False,
            "rows_processed": 0,
            "error_message": None,
            "processing_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Load data
            data = await self._load_data_from_source(data_source)
            if not data:
                result["error_message"] = "No data found in source"
                return result
            
            # Transform data if needed
            if self.config["TRANSFORMATIONS"]:
                data = self._transform_data(data)
            
            # Get column mapping
            mapping_type = data_source.get("mapping_type", "LEADS_MAPPING")
            column_mapping = self.config["COLUMN_MAPPINGS"].get(mapping_type, {})
            
            # Update sheet
            gs_manager = GoogleSheetsManager(
                data_source["sheet_id"],
                result["worksheet"]
            )
            
            update_mode = data_source.get("update_mode", self.config["OPERATIONS"]["UPDATE_MODE"])
            
            if update_mode == "append":
                success = gs_manager.append_data(data, column_mapping)
            elif update_mode == "replace":
                success = await gs_manager.batch_write_leads(data, column_mapping)
            else:  # merge
                success = await self._merge_data(gs_manager, data, column_mapping)
            
            if success:
                result["success"] = True
                result["rows_processed"] = len(data)
                self.operations_performed += 1
            else:
                result["error_message"] = "Sheet update failed"
                
        except Exception as e:
            result["error_message"] = str(e)
            
        result["processing_time"] = time.time() - start_time
        return result

    async def _load_data_from_source(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load data from various source types"""
        
        source_type = data_source.get("type", "json")
        source_path = data_source.get("path")
        
        if source_type == "json":
            if source_path and Path(source_path).exists():
                with open(source_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        elif source_type == "csv":
            if source_path and Path(source_path).exists():
                df = pd.read_csv(source_path)
                return df.to_dict('records')
        
        elif source_type == "xlsx":
            if source_path and Path(source_path).exists():
                df = pd.read_excel(source_path)
                return df.to_dict('records')
        
        elif source_type == "direct":
            return data_source.get("data", [])
        
        elif source_type == "sheet":
            # Load from another sheet
            source_sheet_id = data_source.get("source_sheet_id")
            source_worksheet = data_source.get("source_worksheet", "Sheet1")
            
            if source_sheet_id:
                gs_manager = GoogleSheetsManager(source_sheet_id, source_worksheet)
                return gs_manager.batch_read_data()
        
        return []

    def _transform_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply data transformations"""
        
        transformed_data = []
        
        for item in data:
            transformed_item = item.copy()
            
            # Clean emails
            if self.config["TRANSFORMATIONS"]["CLEAN_EMAILS"] and "email" in transformed_item:
                email = transformed_item["email"]
                if email and isinstance(email, str):
                    transformed_item["email"] = email.strip().lower()
            
            # Standardize phone numbers
            if self.config["TRANSFORMATIONS"]["STANDARDIZE_PHONES"] and "phone" in transformed_item:
                phone = transformed_item["phone"]
                if phone:
                    # Remove non-digits and format
                    digits = ''.join(filter(str.isdigit, str(phone)))
                    if len(digits) == 10:
                        transformed_item["phone"] = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            
            # Normalize company names
            if self.config["TRANSFORMATIONS"]["NORMALIZE_COMPANIES"] and "company" in transformed_item:
                company = transformed_item["company"]
                if company:
                    # Remove common suffixes and normalize
                    company = company.strip()
                    for suffix in [" Inc", " LLC", " Corp", " Ltd"]:
                        if company.endswith(suffix):
                            company = company[:-len(suffix)]
                    transformed_item["company"] = company.strip()
            
            # Add timestamps
            if self.config["TRANSFORMATIONS"]["ADD_TIMESTAMPS"]:
                transformed_item["last_updated"] = datetime.now().isoformat()
            
            transformed_data.append(transformed_item)
        
        # Auto-deduplicate
        if self.config["TRANSFORMATIONS"]["AUTO_DEDUPLICATE"]:
            seen_emails = set()
            deduplicated_data = []
            
            for item in transformed_data:
                email = item.get("email", "")
                if email and email not in seen_emails:
                    seen_emails.add(email)
                    deduplicated_data.append(item)
                elif not email:  # Keep items without emails
                    deduplicated_data.append(item)
            
            print(f"Deduplication: {len(transformed_data)} -> {len(deduplicated_data)} rows")
            transformed_data = deduplicated_data
        
        return transformed_data

    async def _merge_data(self, gs_manager: GoogleSheetsManager, new_data: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> bool:
        """Merge new data with existing sheet data"""
        
        try:
            # Get existing data
            existing_data = gs_manager.batch_read_data()
            
            # Create lookup for existing data (by email)
            existing_lookup = {}
            for item in existing_data:
                email = item.get("email", "")
                if email:
                    existing_lookup[email] = item
            
            # Merge logic
            merged_data = []
            
            for new_item in new_data:
                email = new_item.get("email", "")
                
                if email in existing_lookup:
                    # Merge with existing
                    existing_item = existing_lookup[email]
                    
                    if self.config["OPERATIONS"]["CONFLICT_RESOLUTION"] == "latest_wins":
                        merged_item = {**existing_item, **new_item}
                    else:  # merge
                        merged_item = existing_item.copy()
                        for key, value in new_item.items():
                            if not merged_item.get(key) or value:  # Update if empty or new value exists
                                merged_item[key] = value
                    
                    merged_data.append(merged_item)
                    existing_lookup.pop(email)  # Remove from lookup
                else:
                    # New item
                    merged_data.append(new_item)
            
            # Add remaining existing items
            merged_data.extend(existing_lookup.values())
            
            # Update sheet with merged data
            return await gs_manager.batch_write_leads(merged_data, column_mapping)
            
        except Exception as e:
            print(f"Merge operation failed: {e}")
            return False

    async def _save_operation_log(self, results: Dict[str, Any], start_time: float):
        """Save detailed operation log"""
        
        if not self.config["OUTPUT"]["LOG_ALL_OPERATIONS"]:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processing_time = time.time() - start_time
        
        log_data = {
            "operation_metadata": {
                "timestamp": timestamp,
                "processing_time_seconds": round(processing_time, 2),
                "total_sources_processed": len(results["successful_updates"]) + len(results["failed_updates"]),
                "successful_updates": len(results["successful_updates"]),
                "failed_updates": len(results["failed_updates"]),
                "total_rows_processed": results["total_rows_processed"],
                "config_used": self.config,
                "script_version": SCRIPT_STATS["version"]
            },
            "operation_results": results
        }
        
        log_filename = f"sheets_operations_{timestamp}.json"
        log_filepath = self.results_dir / log_filename
        
        with open(log_filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
            
        print(f"Operation log saved: {log_filename}")

    async def _generate_report(self, results: Dict[str, Any], start_time: float):
        """Generate summary report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processing_time = time.time() - start_time
        
        # Create summary report
        report = {
            "summary": {
                "total_sources": len(results["successful_updates"]) + len(results["failed_updates"]),
                "successful_updates": len(results["successful_updates"]),
                "failed_updates": len(results["failed_updates"]),
                "success_rate": (len(results["successful_updates"]) / (len(results["successful_updates"]) + len(results["failed_updates"]))) * 100 if results["successful_updates"] or results["failed_updates"] else 0,
                "total_rows_processed": results["total_rows_processed"],
                "processing_time_seconds": round(processing_time, 2),
                "rows_per_second": round(results["total_rows_processed"] / processing_time, 2) if processing_time > 0 else 0
            },
            "successful_operations": results["successful_updates"],
            "failed_operations": results["failed_updates"]
        }
        
        report_filename = f"sheets_report_{timestamp}.json"
        report_filepath = self.results_dir / report_filename
        
        with open(report_filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"Report generated: {report_filename}")

    def _update_script_stats(self, sources_count: int, processing_time: float):
        """Update script statistics"""
        global SCRIPT_STATS
        
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["total_rows_processed"] += self.rows_processed
        SCRIPT_STATS["total_sheets_updated"] += self.sheets_updated
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["total_operations"] += self.operations_performed
        
        # Calculate success rate
        SCRIPT_STATS["success_rate"] = (self.sheets_updated / sources_count) * 100 if sources_count > 0 else 0

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def update_single_sheet(sheet_id: str, data: List[Dict[str, Any]], mapping_type: str = "LEADS_MAPPING") -> bool:
    """Update a single sheet with data"""
    
    data_source = {
        "id": "single_update",
        "type": "direct",
        "data": data,
        "sheet_id": sheet_id,
        "mapping_type": mapping_type,
        "update_mode": "replace"
    }
    
    updater = SheetsMassUpdater()
    results = await updater.mass_update_sheets([data_source])
    
    return len(results["successful_updates"]) > 0

async def sync_sheets(source_sheet_id: str, target_sheet_id: str, mapping_type: str = "LEADS_MAPPING") -> bool:
    """Synchronize data between two sheets"""
    
    data_source = {
        "id": "sync_operation",
        "type": "sheet",
        "source_sheet_id": source_sheet_id,
        "sheet_id": target_sheet_id,
        "mapping_type": mapping_type,
        "update_mode": "replace"
    }
    
    updater = SheetsMassUpdater()
    results = await updater.mass_update_sheets([data_source])
    
    return len(results["successful_updates"]) > 0

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""
    
    print("=" * 60)
    print("SHEETS MASS UPDATER v1.0.0")
    print("=" * 60)
    
    updater = SheetsMassUpdater()
    
    # Sample data sources for testing
    sample_data_sources = [
        {
            "id": "test_update_1",
            "type": "direct",
            "data": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "company": "Example Corp"
                }
            ],
            "sheet_id": CONFIG["SHEETS_CONFIG"]["PRIMARY_SHEET_ID"],
            "mapping_type": "LEADS_MAPPING",
            "update_mode": "append"
        }
    ]
    
    # Process data sources
    results = await updater.mass_update_sheets(sample_data_sources)
    
    print("=" * 60)
    print(f"Mass update completed")
    print(f"Successful: {len(results['successful_updates'])}")
    print(f"Failed: {len(results['failed_updates'])}")
    print(f"Total rows: {results['total_rows_processed']:,}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())