#!/usr/bin/env python3
"""
Website Intelligence Extraction Runner
Runs batch processing with configurable parameters
"""

import os
import sys
from domain_intelligence_extractor import WebsiteIntelligenceExtractor

def main():
    """Run website intelligence extraction with command line arguments"""
    
    # Default parameters
    batch_size = 10
    start_index = 0
    csv_filename = "Lumid - verification - Canada.csv"
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    if len(sys.argv) > 2:
        start_index = int(sys.argv[2])
    if len(sys.argv) > 3:
        csv_filename = sys.argv[3]
    
    print(f"Starting extraction with:")
    print(f"  Batch size: {batch_size}")
    print(f"  Start index: {start_index}")
    print(f"  CSV file: {csv_filename}")
    
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
    
    # Build CSV path
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'leads', csv_filename)
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    # Process batch
    try:
        results = extractor.process_batch(csv_path, batch_size=batch_size, start_index=start_index)
        print(f"\n✓ Batch processing complete!")
        
        # Show next batch suggestion
        if len(results) == batch_size:
            next_start = start_index + batch_size
            print(f"\nTo process next batch, run:")
            print(f"  python run_extraction.py {batch_size} {next_start} {csv_filename}")
            
    except KeyboardInterrupt:
        print(f"\n⚠ Processing interrupted by user")
    except Exception as e:
        print(f"\n✗ Processing failed: {e}")

if __name__ == "__main__":
    main()