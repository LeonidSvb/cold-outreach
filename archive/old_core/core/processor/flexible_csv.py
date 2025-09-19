#!/usr/bin/env python3
"""
=== FLEXIBLE CSV PROCESSOR ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Universal CSV processor that can work with any column structure and combine modular functions

FEATURES:
- Auto-detect column types from any CSV structure
- Flexible workflow builder (combine any modules)  
- Progress tracking and resume capability
- Batch processing with limits
- Automatic backup creation
- Real-time statistics and logging
"""

import sys
import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# Add shared utilities and modules to path
sys.path.append(str(Path(__file__).parent.parent / "modules" / "_shared"))
sys.path.append(str(Path(__file__).parent.parent / "modules" / "link_extractor"))
sys.path.append(str(Path(__file__).parent.parent / "modules" / "link_filter"))
sys.path.append(str(Path(__file__).parent.parent / "modules" / "content_scraper"))
sys.path.append(str(Path(__file__).parent.parent / "modules" / "content_summarizer"))

from csv_handler import FlexibleCSVHandler
from logger import auto_log, get_module_stats

# Import module functions
try:
    # Try to import from individual modules
    from core.modules.link_extractor.function import extract_all_links
    from core.modules.link_filter.function import filter_relevant_links  
    from core.modules.content_scraper.function import scrape_urls_to_clean_json
    from core.modules.content_summarizer.function import summarize_for_personalization
except ImportError:
    # Fallback for direct execution
    import importlib.util
    
    def load_module_function(module_path, func_name):
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, func_name)
    
    base_path = Path(__file__).parent.parent / "modules"
    extract_all_links = load_module_function(base_path / "link_extractor" / "function.py", "extract_all_links")
    filter_relevant_links = load_module_function(base_path / "link_filter" / "function.py", "filter_relevant_links")
    scrape_urls_to_clean_json = load_module_function(base_path / "content_scraper" / "function.py", "scrape_urls_to_clean_json")
    summarize_for_personalization = load_module_function(base_path / "content_summarizer" / "function.py", "summarize_for_personalization")

class FlexibleCSVProcessor:
    """Universal CSV processor with modular workflow"""
    
    def __init__(self, csv_path: str):
        self.csv_handler = FlexibleCSVHandler(csv_path)
        self.available_workflows = {
            'extract_links': self._workflow_extract_links,
            'filter_links': self._workflow_filter_links,
            'scrape_content': self._workflow_scrape_content,
            'summarize_content': self._workflow_summarize_content
        }
        self.session_data = {
            'started_at': datetime.now().isoformat(),
            'csv_path': str(csv_path),
            'total_rows': len(self.csv_handler.df),
            'workflows_completed': [],
            'progress': {},
            'stats': {}
        }
        
    def set_limits(self, **kwargs):
        """Set processing limits"""
        self.limits = kwargs
        print(f"Processing limits set: {kwargs}")
    
    def preview_data(self, rows: int = 5):
        """Preview CSV data and column mapping"""
        print("CSV Preview:")
        print("=" * 50)
        print(self.csv_handler.preview(rows))
        print("\nDetected Column Mapping:")
        print(self.csv_handler.get_column_mapping())
        print(f"\nTotal Rows: {len(self.csv_handler.df)}")
    
    def _workflow_extract_links(self, row_data: Any, row_index: int, **kwargs) -> Any:
        """Workflow: Extract all links from website"""
        max_depth = kwargs.get('max_depth', 2)
        max_links = kwargs.get('max_links', 100)
        
        if not row_data or row_data == '':
            return []
        
        try:
            links = extract_all_links(str(row_data), max_depth=max_depth, max_links=max_links)
            self.csv_handler.update_column('links', row_index, json.dumps(links))
            return links
        except Exception as e:
            print(f"Error extracting links for row {row_index}: {e}")
            self.csv_handler.update_column('links', row_index, json.dumps([]))
            return []
    
    def _workflow_filter_links(self, row_data: Any, row_index: int, **kwargs) -> Any:
        """Workflow: Filter relevant links"""
        max_links = kwargs.get('max_links', 15)
        
        try:
            # Row data should be JSON string of links
            if isinstance(row_data, str):
                links = json.loads(row_data)
            elif isinstance(row_data, list):
                links = row_data
            else:
                links = []
            
            if not links:
                return []
            
            filtered = filter_relevant_links(links, max_links=max_links)
            self.csv_handler.update_column('filtered_links', row_index, json.dumps(filtered))
            return filtered
        except Exception as e:
            print(f"Error filtering links for row {row_index}: {e}")
            self.csv_handler.update_column('filtered_links', row_index, json.dumps([]))
            return []
    
    def _workflow_scrape_content(self, row_data: Any, row_index: int, **kwargs) -> Any:
        """Workflow: Scrape content from filtered links"""
        max_workers = kwargs.get('max_workers', 2)
        clean_level = kwargs.get('clean_level', 'basic')
        
        try:
            # Row data should be JSON string of filtered links
            if isinstance(row_data, str):
                links = json.loads(row_data)
            elif isinstance(row_data, list):
                links = row_data
            else:
                links = []
            
            if not links:
                return {}
            
            content = scrape_urls_to_clean_json(
                links, 
                max_workers=max_workers,
                clean_level=clean_level
            )
            
            self.csv_handler.update_column('scraped_content', row_index, json.dumps(content))
            return content
        except Exception as e:
            print(f"Error scraping content for row {row_index}: {e}")
            self.csv_handler.update_column('scraped_content', row_index, json.dumps({}))
            return {}
    
    def _workflow_summarize_content(self, row_data: Any, row_index: int, **kwargs) -> Any:
        """Workflow: Summarize scraped content"""
        focus_areas = kwargs.get('focus_areas', None)
        output_format = kwargs.get('output_format', 'detailed')
        
        try:
            # Row data should be JSON string of scraped content
            if isinstance(row_data, str):
                content = json.loads(row_data)
            elif isinstance(row_data, dict):
                content = row_data
            else:
                content = {}
            
            if not content:
                return {}
            
            summary = summarize_for_personalization(
                content,
                focus_areas=focus_areas,
                output_format=output_format
            )
            
            self.csv_handler.update_column('content_summary', row_index, json.dumps(summary))
            return summary
        except Exception as e:
            print(f"Error summarizing content for row {row_index}: {e}")
            self.csv_handler.update_column('content_summary', row_index, json.dumps({}))
            return {}
    
    def run_workflow(self, workflow_steps: List[str], **kwargs):
        """Run specified workflow steps"""
        print(f"Starting workflow: {' -> '.join(workflow_steps)}")
        print("=" * 50)
        
        # Create backup
        self.csv_handler.create_backup()
        
        # Process limits
        batch_size = kwargs.get('batch_size', 50)
        start_row = kwargs.get('start_row', 0)
        max_rows = kwargs.get('max_rows', None)
        
        total_rows = len(self.csv_handler.df)
        end_row = min(total_rows, start_row + max_rows) if max_rows else total_rows
        
        print(f"Processing rows {start_row} to {end_row-1} (total: {end_row-start_row})")
        
        for step_name in workflow_steps:
            if step_name not in self.available_workflows:
                print(f"Unknown workflow step: {step_name}")
                continue
            
            print(f"\n--- Running {step_name} ---")
            
            workflow_func = self.available_workflows[step_name]
            
            # Determine source and target fields
            field_mapping = {
                'extract_links': ('website', 'links'),
                'filter_links': ('links', 'filtered_links'), 
                'scrape_content': ('filtered_links', 'scraped_content'),
                'summarize_content': ('scraped_content', 'content_summary')
            }
            
            if step_name in field_mapping:
                source_field, target_field = field_mapping[step_name]
            else:
                source_field, target_field = 'website', step_name
            
            # Get rows that need processing 
            if step_name in field_mapping:
                source_field, target_field = field_mapping[step_name]
                # Get source data for this workflow step
                rows_to_process = []
                for i in range(start_row, min(end_row, len(self.csv_handler.df))):
                    if source_field in self.csv_handler.column_mapping:
                        source_col = self.csv_handler.column_mapping[source_field]
                        source_value = self.csv_handler.df.iloc[i][source_col]
                    else:
                        source_value = ""
                    
                    # Check if target field needs processing
                    target_needs_processing = True
                    if target_field in self.csv_handler.column_mapping:
                        target_col = self.csv_handler.column_mapping[target_field]
                        target_value = self.csv_handler.df.iloc[i][target_col]
                        if pd.notna(target_value) and str(target_value).strip():
                            target_needs_processing = False
                    
                    if target_needs_processing:
                        rows_to_process.append((i, source_value))
            else:
                rows_to_process = self.csv_handler.get_rows_for_processing(
                    target_field, filter_empty=True
                )[start_row:end_row]
            
            if not rows_to_process:
                print(f"No rows to process for {step_name}")
                continue
            
            print(f"Processing {len(rows_to_process)} rows...")
            
            # Process in batches
            for i in range(0, len(rows_to_process), batch_size):
                batch = rows_to_process[i:i+batch_size]
                
                print(f"Batch {i//batch_size + 1}: rows {i+1}-{min(i+batch_size, len(rows_to_process))}")
                
                for row_index, source_value in batch:
                    try:
                        result = workflow_func(source_value, row_index, **kwargs)
                        print(f"  [OK] Row {row_index+1}: {step_name} complete")
                    except Exception as e:
                        print(f"  [ERROR] Row {row_index+1}: Error - {e}")
                
                # Save progress after each batch
                self.csv_handler.save()
                time.sleep(0.5)  # Brief pause between batches
            
            self.session_data['workflows_completed'].append(step_name)
            print(f"[DONE] {step_name} completed for all rows")
        
        # Final save
        self.csv_handler.save()
        
        # Update session data
        self.session_data['completed_at'] = datetime.now().isoformat()
        self.session_data['duration'] = str(datetime.now() - datetime.fromisoformat(self.session_data['started_at']))
        
        print(f"\n[SUCCESS] Workflow completed successfully!")
        print(f"Results saved to: {self.csv_handler.csv_path}")
        
        return self.get_session_summary()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of processing session"""
        return {
            **self.session_data,
            'csv_stats': self.csv_handler.get_stats(),
            'module_stats': {
                module: get_module_stats(module) 
                for module in ['link_extractor', 'link_filter', 'content_scraper', 'content_summarizer']
            }
        }

@auto_log("flexible_csv_processor") 
def process_csv_with_workflow(csv_path: str, workflow: List[str], **kwargs) -> Dict[str, Any]:
    """
    Process CSV file with specified modular workflow
    
    Args:
        csv_path: Path to CSV file
        workflow: List of workflow steps (e.g., ['extract_links', 'filter_links'])
        **kwargs: Additional parameters for processing
    
    Returns:
        Dict with session summary and statistics
    
    Example:
        result = process_csv_with_workflow(
            'companies.csv',
            ['extract_links', 'filter_links', 'scrape_content'],
            max_depth=2,
            max_links=50,
            batch_size=10
        )
    """
    processor = FlexibleCSVProcessor(csv_path)
    return processor.run_workflow(workflow, **kwargs)

def main():
    """CLI interface for flexible CSV processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flexible CSV processor with modular workflows")
    parser.add_argument("csv_file", help="Path to CSV file")
    parser.add_argument("--workflow", nargs='+', required=True,
                       choices=['extract_links', 'filter_links', 'scrape_content', 'summarize_content'],
                       help="Workflow steps to execute")
    parser.add_argument("--preview", action='store_true', help="Preview data and exit")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--start-row", type=int, default=0, help="Start row index")
    parser.add_argument("--max-rows", type=int, help="Maximum rows to process")
    parser.add_argument("--max-depth", type=int, default=2, help="Link extraction depth")
    parser.add_argument("--max-links", type=int, default=100, help="Maximum links per domain")
    parser.add_argument("--max-workers", type=int, default=2, help="Parallel workers for scraping")
    
    args = parser.parse_args()
    
    print(f"Flexible CSV Processor v1.0.0")
    print("=" * 50)
    
    processor = FlexibleCSVProcessor(args.csv_file)
    
    if args.preview:
        processor.preview_data()
        return
    
    # Run workflow
    kwargs = {
        'batch_size': args.batch_size,
        'start_row': args.start_row,
        'max_rows': args.max_rows,
        'max_depth': args.max_depth,
        'max_links': args.max_links,
        'max_workers': args.max_workers
    }
    
    summary = processor.run_workflow(args.workflow, **kwargs)
    
    print(f"\n[STATS] Session Summary:")
    print(f"Total rows: {summary['csv_stats']['total_rows']}")
    print(f"Workflows completed: {summary['workflows_completed']}")
    print(f"Duration: {summary.get('duration', 'N/A')}")

if __name__ == "__main__":
    main()