#!/usr/bin/env python3
"""
Test stryve with manual page list to prove concept works
"""

import os
from domain_intelligence_extractor import WebsiteIntelligenceExtractor

class TestExtractor(WebsiteIntelligenceExtractor):
    """Test version that adds known pages manually"""
    
    def discover_pages(self, domain: str):
        """Override to add known pages for stryvemarketing.com"""
        if 'stryvemarketing' in domain.lower():
            # Add known important pages
            pages = {
                'https://www.stryvemarketing.com',
                'https://www.stryvemarketing.com/about', 
                'https://www.stryvemarketing.com/approach',
                'https://www.stryvemarketing.com/services',
                'https://www.stryvemarketing.com/careers',
                'https://www.stryvemarketing.com/contact'
            }
            print(f"Using manual page list: {len(pages)} pages")
            return pages
        else:
            # Use regular discovery for other domains
            return super().discover_pages(domain)

def main():
    """Test extraction with manual page list"""
    
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
    
    # Initialize test extractor
    extractor = TestExtractor(openai_api_key)
    
    # Test with manual page list
    domain_info = {
        'domain': 'stryvemarketing.com',
        'company_name': 'Stryve Digital Marketing', 
        'row_index': 1
    }
    
    print("Testing extraction with manual page discovery...")
    result = extractor.process_domain(domain_info)
    
    print(f"\n=== RESULTS ===")
    print(f"Success: {result['success']}")
    print(f"Pages found: {result['pages_found']}")
    print(f"Pages processed: {result['pages_processed']}")
    print(f"Content extracted: {result['content_extracted']}")
    
    if result.get('ai_analysis'):
        print(f"\nAI Analysis keys: {list(result['ai_analysis'].keys())}")
        
        # Show a sample of the analysis
        if 'raw_analysis' in result['ai_analysis']:
            analysis = result['ai_analysis']['raw_analysis']
            if len(analysis) > 500:
                print(f"Sample analysis (first 500 chars):\n{analysis[:500]}...")
            else:
                print(f"Full analysis:\n{analysis}")
    
    if result.get('errors'):
        print(f"\nErrors: {result['errors']}")
    
    # Save result
    extractor.save_results([result], "stryve_manual_test")
    
    if result['success'] and result['pages_processed'] > 1:
        print(f"\n[SUCCESS] Processed {result['pages_processed']} pages successfully!")
        print("This proves the concept works - now we just need to fix automatic page discovery")
    else:
        print(f"\n[PARTIAL] Only processed {result['pages_processed']} pages")

if __name__ == "__main__":
    main()