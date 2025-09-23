#!/usr/bin/env python3
"""
Quick test for website intelligence processor
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from website_intelligence_processor import WebsiteIntelligenceProcessor

def test_single_domain():
    """Test single domain processing"""
    processor = WebsiteIntelligenceProcessor()
    
    # Test with first domain from CSV
    test_domain = "altitudestrategies.ca"
    print(f"Testing domain: {test_domain}")
    
    result = processor.process_domain(test_domain)
    
    if result:
        print("\nSUCCESS! Result:")
        print(f"- Total pages found: {result['total_pages_found']}")
        print(f"- Selected pages: {len(result['selected_pages'])}")
        print(f"- Processing time: {result['processing_time']}s")
        print(f"- AI cost: ${result.get('analysis_cost', 0):.4f}")
        
        print("\nSelected pages:")
        for page in result['selected_pages']:
            print(f"  - {page}")
            
        print(f"\nReasoning: {result.get('selection_reasoning', 'N/A')}")
    else:
        print("FAILED to process domain")

if __name__ == "__main__":
    test_single_domain()