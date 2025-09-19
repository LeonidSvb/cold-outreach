#!/usr/bin/env python3
"""
Quick test for multiple domains
"""

import sys
import os
import csv
sys.path.append(os.path.dirname(__file__))

from website_intelligence_processor import WebsiteIntelligenceProcessor

def test_multiple_domains():
    """Test 5 domains from CSV"""
    
    # Load domains from CSV
    csv_path = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    
    domains = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:  # First 5 domains
                break
            domain = row.get('company_domain', '').strip()
            company_name = row.get('cleaned_company_name', '').strip()
            if domain and company_name:
                domains.append((domain, company_name))
    
    print(f"Testing {len(domains)} domains...")
    
    processor = WebsiteIntelligenceProcessor()
    results = []
    
    for i, (domain, company_name) in enumerate(domains):
        print(f"\n=== TEST {i+1}/5: {company_name} ({domain}) ===")
        
        result = processor.process_domain(domain)
        
        if result:
            results.append({
                'domain': domain,
                'company': company_name,
                'pages_found': result['total_pages_found'],
                'pages_selected': len(result['selected_pages']),
                'processing_time': result['processing_time'],
                'cost': result.get('analysis_cost', 0),
                'success': True
            })
            print(f"SUCCESS: {result['total_pages_found']} pages found, {len(result['selected_pages'])} selected")
        else:
            results.append({
                'domain': domain,
                'company': company_name,
                'success': False
            })
            print("FAILED")
    
    # Summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Successful: {len(successful)}/{len(results)}")
    print(f"Failed: {len(failed)}/{len(results)}")
    
    if successful:
        avg_pages = sum(r['pages_found'] for r in successful) / len(successful)
        avg_selected = sum(r['pages_selected'] for r in successful) / len(successful)
        avg_time = sum(r['processing_time'] for r in successful) / len(successful)
        total_cost = sum(r['cost'] for r in successful)
        
        print(f"Average pages found: {avg_pages:.1f}")
        print(f"Average pages selected: {avg_selected:.1f}")
        print(f"Average processing time: {avg_time:.1f}s")
        print(f"Total cost: ${total_cost:.4f}")
    
    session_report = processor.get_session_report()
    print(f"\nSession stats:")
    print(f"- Domains processed: {session_report['session_summary']['domains_processed']}")
    print(f"- Success rate: {session_report['session_summary']['success_rate']}%")
    print(f"- Total cost: ${session_report['session_summary']['total_cost']}")

if __name__ == "__main__":
    test_multiple_domains()