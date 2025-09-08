#!/usr/bin/env python3
"""
Final test of improved extraction
"""

import os
from domain_intelligence_extractor import WebsiteIntelligenceExtractor

def main():
    """Test with stryvemarketing.com with verbose output"""
    
    # Load API key from environment
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    openai_api_key = None
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    openai_api_key = line.split('=', 1)[1].strip()
                    break
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Initialize extractor
    extractor = WebsiteIntelligenceExtractor(openai_api_key)
    
    # Test page discovery only first
    print("Testing page discovery for stryvemarketing.com...")
    pages = extractor.discover_pages('stryvemarketing.com')
    
    print(f"Pages found: {len(pages)}")
    for i, page in enumerate(sorted(pages), 1):
        print(f"  {i}. {page}")
    
    if len(pages) > 1:
        print(f"\n[SUCCESS] Found {len(pages)} pages! Now running full extraction...")
        
        # Test full extraction if pages found
        domain_info = {
            'domain': 'stryvemarketing.com', 
            'company_name': 'Stryve Digital Marketing',
            'row_index': 1
        }
        
        result = extractor.process_domain(domain_info)
        
        print(f"\n=== RESULTS ===")
        print(f"Success: {result['success']}")
        print(f"Pages found: {result['pages_found']}")  
        print(f"Pages processed: {result['pages_processed']}")
        
        if result.get('ai_analysis'):
            print(f"AI Analysis: Generated successfully")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        
        # Save result
        extractor.save_results([result], "final_test_stryvemarketing")
        
    else:
        print(f"\n[ERROR] Only found {len(pages)} page(s). Page discovery still not working.")

if __name__ == "__main__":
    main()