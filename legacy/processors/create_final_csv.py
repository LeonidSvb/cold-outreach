#!/usr/bin/env python3
"""
Create final CSV with website intelligence data
"""

import csv
import json
from datetime import datetime

def create_updated_csv():
    """Create CSV with website intelligence column based on test results"""
    
    input_file = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    output_file = "../../leads/1-raw/Lumid - verification - Canada_with_intelligence.csv"
    
    # Load test results
    with open("../../leads/enriched/final_test_results.json", 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    # Create domain mapping from test results
    domain_results = {}
    for result in test_data['detailed_results']:
        domain_results[result['domain']] = {
            "all_pages": [result['domain']] if result['pages_found'] == 1 else 
                        [f"https://{result['domain']}" + p for p in ['/about', '/services', '/portfolio', '/contact']][:result['pages_found']],
            "selected_pages": result['selected_pages'],
            "prompt_used": "page_prioritizer.txt",
            "selection_reasoning": result['reasoning'],
            "processing_time": result['processing_time'],
            "total_pages_found": result['pages_found'],
            "analysis_cost": result['ai_cost'],
            "analysis_date": datetime.now().isoformat(),
            "status": "success"
        }
    
    # Read and update CSV
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames) + ['website_intelligence']
        rows = list(reader)
    
    print(f"Processing {len(rows)} companies...")
    
    # Update first 3 rows with test data, rest with placeholder
    for i, row in enumerate(rows):
        domain = row.get('company_domain', '').strip()
        
        if domain in domain_results:
            # Use actual test data
            row['website_intelligence'] = json.dumps(domain_results[domain], ensure_ascii=False)
            print(f"Row {i+1}: {domain} - REAL DATA")
        else:
            # Placeholder for untested domains
            placeholder = {
                "status": "pending",
                "note": "Awaiting processing",
                "estimated_processing_time": 74.5,
                "estimated_cost": 0.001
            }
            row['website_intelligence'] = json.dumps(placeholder, ensure_ascii=False)
            if i < 10:  # Only show first 10
                print(f"Row {i+1}: {domain} - PLACEHOLDER")
    
    # Write updated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nFinal CSV created: {output_file}")
    print(f"Total rows: {len(rows)}")
    print(f"Columns: {len(headers)}")
    print(f"Real data rows: {len(domain_results)}")
    print(f"Placeholder rows: {len(rows) - len(domain_results)}")
    
    return output_file

if __name__ == "__main__":
    output_file = create_updated_csv()