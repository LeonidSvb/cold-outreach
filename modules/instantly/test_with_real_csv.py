#!/usr/bin/env python3
"""
Test CSV uploader with real CSV file
"""

import sys
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

# Import our uploader
from instantly_csv_uploader import InstantlyCsvUploader

def main():
    """Test with real CSV file"""
    print("=== TESTING WITH REAL CSV FILE ===")
    print()

    # Create uploader instance
    uploader = InstantlyCsvUploader()

    # Enable test mode for safety
    uploader.config["LEAD_UPLOAD"]["TEST_MODE"] = True
    uploader.config["LEAD_UPLOAD"]["CAMPAIGN_ID"] = "demo-campaign-123"

    # Override API key check for demo
    uploader.api_key = "demo-api-key"

    # Test with the test_companies.csv file
    csv_file = "../../data/input/test_companies.csv"
    print(f"Testing with CSV file: {csv_file}")

    try:
        results = uploader.upload_companies_from_csv(csv_file)

        if results:
            stats = results.get('statistics', {})
            print(f"\nProcessing Results:")
            print(f"  Total companies: {stats.get('total_companies', 0)}")
            print(f"  Leads created: {stats.get('leads_created', 0)}")
            print(f"  Successful: {stats.get('successful_count', 0)}")
            print(f"  Failed: {stats.get('failed_count', 0)}")
            print(f"  Skipped: {stats.get('skipped_count', 0)}")
            print(f"  Success rate: {stats.get('success_rate', 0):.1f}%")

            print(f"\nSuccessful uploads:")
            for lead in results.get('successful', [])[:3]:  # Show first 3
                print(f"  - {lead.get('company_name', 'Unknown')} ({lead.get('email', 'No email')})")

            if results.get('skipped'):
                print(f"\nSkipped companies:")
                for skip in results.get('skipped', [])[:3]:  # Show first 3
                    print(f"  - {skip.get('company', 'Unknown')}: {skip.get('reason', 'No reason')}")

        else:
            print("No results returned")

    except Exception as e:
        print(f"Error during testing: {e}")

    print("\nTest completed!")

if __name__ == "__main__":
    main()