#!/usr/bin/env python3
"""
CSV Updater - Add website intelligence column to leads CSV
"""

import sys
import os
import csv
import json
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from website_intelligence_processor import WebsiteIntelligenceProcessor

def process_csv_with_intelligence(input_file, output_file, test_limit=3):
    """Process CSV and add website intelligence column"""
    
    print(f"Processing CSV: {input_file}")
    print(f"Test limit: {test_limit} companies")
    
    # Read input file
    rows = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        rows = list(reader)
    
    print(f"Loaded {len(rows)} rows from CSV")
    
    # Add new column if not exists
    if 'website_intelligence' not in headers:
        headers.append('website_intelligence')
        print("Added 'website_intelligence' column")
    
    # Initialize processor
    processor = WebsiteIntelligenceProcessor()
    
    # Process limited number of companies
    processed_count = 0
    for i, row in enumerate(rows):
        if test_limit and processed_count >= test_limit:
            break
            
        domain = row.get('company_domain', '').strip()
        company_name = row.get('cleaned_company_name', '').strip()
        
        if not domain or not company_name:
            print(f"Skipping row {i+1}: missing domain or company name")
            continue
            
        if row.get('website_intelligence'):
            print(f"Skipping row {i+1}: already processed")
            continue
            
        print(f"\nProcessing {processed_count+1}/{test_limit}: {company_name} ({domain})")
        
        try:
            # Process domain
            result = processor.process_domain(domain)
            
            if result:
                # Create intelligence data
                intelligence_data = {
                    "all_pages": result["all_pages"],
                    "selected_pages": result["selected_pages"], 
                    "prompt_used": result["prompt_used"],
                    "selection_reasoning": result["selection_reasoning"],
                    "processing_time": result["processing_time"],
                    "total_pages_found": result["total_pages_found"],
                    "analysis_cost": result.get("analysis_cost", 0),
                    "analysis_date": result["analysis_date"],
                    "status": "success"
                }
                
                # Store as JSON string
                row['website_intelligence'] = json.dumps(intelligence_data, ensure_ascii=False)
                
                print(f"SUCCESS: {len(result['all_pages'])} pages found, {len(result['selected_pages'])} selected")
                print(f"Processing time: {result['processing_time']}s")
                print(f"Cost: ${result.get('analysis_cost', 0):.4f}")
                
            else:
                # Store error
                error_data = {
                    "error": "Failed to process domain",
                    "analysis_date": datetime.now().isoformat(),
                    "status": "failed"
                }
                row['website_intelligence'] = json.dumps(error_data, ensure_ascii=False)
                print("FAILED to process domain")
                
        except Exception as e:
            # Store exception
            error_data = {
                "error": f"Exception: {str(e)}",
                "analysis_date": datetime.now().isoformat(),
                "status": "error"
            }
            row['website_intelligence'] = json.dumps(error_data, ensure_ascii=False)
            print(f"ERROR: {str(e)}")
            
        processed_count += 1
    
    # Write updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nCSV updated and saved to: {output_file}")
    
    # Generate session report
    session_report = processor.get_session_report()
    
    print(f"\n{'='*60}")
    print("PROCESSING REPORT")
    print(f"{'='*60}")
    
    session = session_report["session_summary"]
    print(f"Companies processed: {processed_count}")
    print(f"Domains successfully analyzed: {session['domains_processed']}")
    print(f"Total pages discovered: {session['total_pages_found']}")
    print(f"AI prioritizations successful: {session['successful_ai_prioritizations']}")
    print(f"Success rate: {session['success_rate']}%")
    print(f"Total API cost: ${session['total_cost']}")
    print(f"Total runtime: {session['total_runtime']}s")
    print(f"Average time per domain: {session['average_time_per_domain']}s")
    
    return output_file, session_report

if __name__ == "__main__":
    input_file = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    output_file = "../../leads/1-raw/Lumid - verification - Canada_with_intelligence.csv"
    
    result_file, report = process_csv_with_intelligence(input_file, output_file, test_limit=3)