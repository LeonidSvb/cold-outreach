#!/usr/bin/env python3
"""
Test single domain extraction with improved page discovery
"""

import os
from domain_intelligence_extractor import WebsiteIntelligenceExtractor

def main():
    """Test with stryvemarketing.com specifically"""
    
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
    
    # Test single domain
    domain_info = {
        'domain': 'stryvemarketing.com',
        'company_name': 'Stryve Digital Marketing',
        'row_index': 1
    }
    
    print(f"Testing improved extraction for: {domain_info['domain']}")
    
    result = extractor.process_domain(domain_info)
    
    # Save single result
    extractor.save_results([result], "stryvemarketing_test")
    
    print(f"\n=== RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Pages found: {result['pages_found']}")
    print(f"Pages processed: {result['pages_processed']}")
    if result.get('ai_analysis'):
        print(f"AI Analysis: Generated")
    if result.get('errors'):
        print(f"Errors: {result['errors']}")

if __name__ == "__main__":
    main()