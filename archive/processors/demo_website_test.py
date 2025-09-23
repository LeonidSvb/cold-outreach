#!/usr/bin/env python3
"""
=== DEMO WEBSITE EXTRACTION TEST ===
Version: 1.0.0 | Created: 2025-09-09

Test website intelligence processor with sample companies
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(__file__))
from website_intelligence_processor import WebsiteIntelligenceProcessor

def test_sample_companies():
    """Test with sample companies to demonstrate functionality"""
    
    # Sample companies for testing
    test_companies = [
        {
            'company_name': 'Big Fish Creative',
            'domain': 'bigfishcreative.ca',
            'contact_name': 'Brent G'
        },
        {
            'company_name': 'Stryve Digital Marketing', 
            'domain': 'stryvemarketing.com',
            'contact_name': 'Grace Cole'
        },
        {
            'company_name': 'Work Party Creative Group',
            'domain': 'workparty.ca', 
            'contact_name': 'Christie Coughlan'
        },
        {
            'company_name': 'Kipling Media',
            'domain': 'kiplingmedia.com',
            'contact_name': 'Maya Pankalla'
        },
        {
            'company_name': 'Greenhouse Marketing',
            'domain': 'greenhousemarketing.ca',
            'contact_name': 'Heather Green'
        }
    ]
    
    print("=== WEBSITE INTELLIGENCE PROCESSOR DEMO ===")
    print(f"Testing {len(test_companies)} sample companies")
    
    # Initialize processor
    try:
        processor = WebsiteIntelligenceProcessor()
        print("Processor initialized successfully")
    except Exception as e:
        print(f"Failed to initialize: {str(e)}")
        return
    
    # Test results
    all_results = []
    
    for i, company in enumerate(test_companies):
        print(f"\n--- TEST {i+1}/5: {company['company_name']} ---")
        
        try:
            start_time = time.time()
            result = processor.process_company(company['domain'], company['company_name'])
            processing_time = time.time() - start_time
            
            # Extract key metrics
            pages_discovered = len(result.get('all_pages_discovered', []))
            pages_selected = len(result.get('selected_pages', []))
            content_extracted = len(result.get('raw_content_data', {}))
            success = result['processing_stats']['success']
            
            print(f"Results for {company['company_name']}:")
            print(f"  Success: {success}")
            print(f"  Processing Time: {processing_time:.2f} seconds")
            print(f"  Pages Discovered: {pages_discovered}")
            print(f"  Pages Selected by AI: {pages_selected}")
            print(f"  Content Extracted: {content_extracted}")
            
            if success:
                print(f"  Data Flow: {pages_discovered} discovered -> {pages_selected} selected -> {content_extracted} extracted")
                
                # Show selected pages
                if result.get('selected_pages'):
                    print(f"  AI Selected Pages:")
                    for j, page in enumerate(result['selected_pages'][:3]):
                        print(f"    {j+1}. {page}")
                
                # Show sample content
                raw_content = result.get('raw_content_data', {})
                if raw_content:
                    sample_url = list(raw_content.keys())[0]
                    sample_content = raw_content[sample_url]
                    print(f"  Sample Content from {sample_url}:")
                    print(f"    Title: {sample_content.get('title', 'No title')}")
                    print(f"    Word Count: {sample_content.get('word_count', 0)}")
                    print(f"    AI Priority: {sample_content.get('ai_priority', 'unknown')}")
                    print(f"    Text Preview: {sample_content.get('text', '')[:200]}...")
            else:
                print(f"  Errors: {result['processing_stats'].get('errors', [])}")
            
            all_results.append({
                'company': company['company_name'],
                'success': success,
                'pages_discovered': pages_discovered,
                'pages_selected': pages_selected,
                'content_extracted': content_extracted,
                'processing_time': processing_time
            })
            
            print(f"Test {i+1} completed")
            
            # Pause between tests
            time.sleep(3)
            
        except Exception as e:
            print(f"Error testing {company['company_name']}: {str(e)}")
            all_results.append({
                'company': company['company_name'],
                'success': False,
                'error': str(e),
                'processing_time': 0
            })
    
    # Summary report
    print(f"\n=== SUMMARY REPORT ===")
    successful = sum(1 for r in all_results if r.get('success', False))
    total_time = sum(r['processing_time'] for r in all_results)
    
    print(f"Companies Tested: {len(all_results)}")
    print(f"Successful: {successful}")
    print(f"Success Rate: {(successful/len(all_results)*100):.1f}%")
    print(f"Total Time: {total_time:.1f} seconds")
    print(f"Average Time: {(total_time/len(all_results)):.1f} seconds per company")
    
    # Detailed breakdown
    print(f"\nDETAILED BREAKDOWN:")
    for result in all_results:
        if result.get('success'):
            print(f"  {result['company']}: {result['pages_discovered']}D -> {result['pages_selected']}S -> {result['content_extracted']}E")
        else:
            print(f"  {result['company']}: FAILED - {result.get('error', 'Unknown error')}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"../../leads/enriched/demo_test_{timestamp}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_session': f'demo_{timestamp}',
            'completed_at': datetime.now().isoformat(),
            'results': all_results,
            'summary': {
                'total_companies': len(all_results),
                'successful': successful,
                'success_rate': successful/len(all_results)*100,
                'total_time': total_time,
                'avg_time': total_time/len(all_results)
            }
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    # Generate session report
    processor.generate_session_report()

if __name__ == "__main__":
    test_sample_companies()