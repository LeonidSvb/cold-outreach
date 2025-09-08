#!/usr/bin/env python3
"""
Process full CSV file with company name cleaner
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import process_csv_batch

def main():
    csv_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada.csv"
    
    print("Processing full CSV file with company name cleaner...")
    print("=" * 60)
    print(f"Input file: {csv_file}")
    
    # Process with batch size of 20 for efficiency
    output_file = process_csv_batch(csv_file, batch_size=20)
    
    if output_file:
        print(f"\n✓ SUCCESS!")
        print(f"✓ Output file: {output_file}")
        print("✓ New column 'cleaned_company_name' has been added")
    else:
        print("✗ FAILED to process CSV file")

if __name__ == "__main__":
    main()