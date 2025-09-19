#!/usr/bin/env python3
"""
Final performance test and metrics
"""

from website_intelligence_processor import WebsiteIntelligenceProcessor
import time
import csv
import json

def main():
    print("WEBSITE INTELLIGENCE - FINAL PERFORMANCE TEST")
    print("="*60)
    
    # Load test data
    csv_path = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"SOURCE DATA:")
    print(f"Total companies in CSV: {len(rows)}")
    print(f"Columns: {len(reader.fieldnames)}")
    
    # Get first 3 test domains
    test_domains = []
    for row in rows[:5]:
        domain = row.get('company_domain', '').strip()
        company = row.get('cleaned_company_name', '').strip()
        if domain and company:
            test_domains.append((domain, company))
            if len(test_domains) >= 3:
                break
    
    print(f"Test domains ready: {len(test_domains)}")
    print()
    
    # Initialize processor
    processor = WebsiteIntelligenceProcessor()
    
    # Test each domain
    results = []
    total_start = time.time()
    
    for i, (domain, company) in enumerate(test_domains):
        print(f"TEST {i+1}/3: {company} ({domain})")
        
        start = time.time()
        result = processor.process_domain(domain)
        elapsed = time.time() - start
        
        if result:
            test_result = {
                'company': company,
                'domain': domain,
                'success': True,
                'processing_time': elapsed,
                'pages_found': result['total_pages_found'],
                'pages_selected': len(result['selected_pages']),
                'ai_cost': result.get('analysis_cost', 0),
                'selected_pages': result['selected_pages'],
                'reasoning': result.get('selection_reasoning', 'N/A')
            }
            print(f"SUCCESS in {elapsed:.1f}s")
            print(f"  Pages: {result['total_pages_found']} found, {len(result['selected_pages'])} selected")
            print(f"  Cost: ${result.get('analysis_cost', 0):.4f}")
        else:
            test_result = {
                'company': company,
                'domain': domain,
                'success': False,
                'processing_time': elapsed
            }
            print(f"FAILED in {elapsed:.1f}s")
        
        results.append(test_result)
        print()
    
    total_elapsed = time.time() - total_start
    
    # Generate comprehensive metrics
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print("="*60)
    print("COMPREHENSIVE METRICS")
    print("="*60)
    
    print(f"PROCESSING RESULTS:")
    print(f"  Total domains tested: {len(results)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Success rate: {len(successful)/len(results)*100:.1f}%")
    
    if successful:
        avg_time = sum(r['processing_time'] for r in successful) / len(successful)
        avg_pages_found = sum(r['pages_found'] for r in successful) / len(successful)
        avg_pages_selected = sum(r['pages_selected'] for r in successful) / len(successful)
        total_cost = sum(r['ai_cost'] for r in successful)
        avg_cost = total_cost / len(successful)
        
        print(f"PERFORMANCE:")
        print(f"  Average processing time: {avg_time:.1f} seconds")
        print(f"  Total test time: {total_elapsed:.1f} seconds")
        print(f"  Average pages found: {avg_pages_found:.1f}")
        print(f"  Average pages selected: {avg_pages_selected:.1f}")
        print(f"  Total API cost: ${total_cost:.4f}")
        print(f"  Average cost per domain: ${avg_cost:.4f}")
    
    # Session report from processor
    session_report = processor.get_session_report()
    session = session_report['session_summary']
    
    print(f"PROCESSOR SESSION:")
    print(f"  Domains processed: {session['domains_processed']}")
    print(f"  Total pages discovered: {session['total_pages_found']}")
    print(f"  AI prioritizations successful: {session['successful_ai_prioritizations']}")
    print(f"  Session success rate: {session['success_rate']}%")
    print(f"  Session total cost: ${session['total_cost']}")
    print(f"  Session runtime: {session['total_runtime']:.1f}s")
    
    # PROJECTIONS FOR FULL DATASET
    if successful:
        print(f"FULL DATASET PROJECTIONS ({len(rows)} companies):")
        estimated_time = avg_time * len(rows)
        estimated_cost = avg_cost * len(rows)
        estimated_pages = avg_pages_found * len(rows)
        
        print(f"  Estimated total time: {estimated_time/3600:.1f} hours")
        print(f"  Estimated total cost: ${estimated_cost:.2f}")
        print(f"  Estimated pages discovered: {estimated_pages:.0f}")
        print(f"  Estimated pages selected: {avg_pages_selected * len(rows):.0f}")
    
    # DETAILED RESULTS
    print(f"DETAILED RESULTS:")
    for i, result in enumerate(successful):
        print(f"  {i+1}. {result['company']} ({result['domain']})")
        print(f"     Time: {result['processing_time']:.1f}s | Cost: ${result['ai_cost']:.4f}")
        print(f"     Pages: {result['pages_found']} -> {result['pages_selected']}")
        print(f"     Selected: {result['selected_pages']}")
        print(f"     AI Reasoning: {result['reasoning'][:100]}...")
        print()
    
    # Save results
    output_file = "../../leads/enriched/final_test_results.json"
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    final_data = {
        'test_metadata': {
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_companies_in_csv': len(rows),
            'domains_tested': len(results),
            'test_duration': total_elapsed
        },
        'performance_metrics': {
            'success_rate': len(successful)/len(results)*100,
            'avg_processing_time': avg_time if successful else 0,
            'avg_pages_found': avg_pages_found if successful else 0,
            'avg_pages_selected': avg_pages_selected if successful else 0,
            'total_api_cost': total_cost if successful else 0,
            'avg_cost_per_domain': avg_cost if successful else 0
        },
        'projections': {
            'estimated_full_time_hours': estimated_time/3600 if successful else 0,
            'estimated_full_cost': estimated_cost if successful else 0,
            'estimated_total_pages': estimated_pages if successful else 0
        },
        'detailed_results': results,
        'session_report': session_report
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()