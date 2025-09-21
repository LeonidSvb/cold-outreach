#!/usr/bin/env python3
"""
Demo test of CSV upload functionality
Runs in TEST_MODE to demonstrate functionality without API calls
"""

import sys
import os
from pathlib import Path

# Add the current directory to the path
sys.path.append(str(Path(__file__).parent))

# Import our uploader
from instantly_csv_uploader import InstantlyCsvUploader

def main():
    """Demo function"""
    print("=== INSTANTLY CSV UPLOADER DEMO ===")
    print("Running in TEST_MODE - no actual API calls will be made")
    print()

    # Create uploader instance
    uploader = InstantlyCsvUploader()

    # Enable test mode
    uploader.config["LEAD_UPLOAD"]["TEST_MODE"] = True
    uploader.config["LEAD_UPLOAD"]["CAMPAIGN_ID"] = "demo-campaign-123"

    # Override API key check for demo
    uploader.api_key = "demo-api-key"

    print("Config settings:")
    print(f"  Test Mode: {uploader.config['LEAD_UPLOAD']['TEST_MODE']}")
    print(f"  Campaign ID: {uploader.config['LEAD_UPLOAD']['CAMPAIGN_ID']}")
    print(f"  Email patterns: {uploader.config['EMAIL_GENERATION']['PATTERNS']}")
    print(f"  Batch size: {uploader.config['CSV_PROCESSING']['BATCH_SIZE']}")
    print()

    # Test email generation
    print("Testing email generation:")
    test_domain = "example.com"
    test_company = "Example Corp"
    emails = uploader._generate_emails(test_domain, test_company)
    print(f"  Domain: {test_domain}")
    print(f"  Generated emails: {emails}")
    print()

    # Test domain extraction
    print("Testing domain extraction:")
    test_urls = [
        "https://www.example.com",
        "http://example.com/path",
        "example.com",
        "https://sub.example.com:8080/page"
    ]

    for url in test_urls:
        domain = uploader._extract_domain(url)
        print(f"  {url} -> {domain}")
    print()

    # Test CSV processing
    print("Testing CSV processing with sample data:")

    # Create a sample company record
    sample_company = {
        'company_name': 'Altitude Strategies',
        'website': 'https://www.altitudestrategies.ca',
        'country': 'Canada',
        'content_summary': 'Marketing agency providing digital marketing services'
    }

    # Test lead data creation
    domain = uploader._extract_domain(sample_company['website'])
    emails = uploader._generate_emails(domain, sample_company['company_name'])

    if emails:
        lead_data = uploader._create_lead_data(sample_company, emails[0])
        print(f"Sample lead data created:")
        import json
        print(json.dumps(lead_data, indent=2))
    else:
        print("No emails generated for sample company")

    print("\nDemo completed successfully!")
    print("To use with real data:")
    print("1. Ensure valid INSTANTLY_API_KEY in .env")
    print("2. Get a valid campaign ID from Instantly dashboard")
    print("3. Set TEST_MODE to False in config")
    print("4. Run the main script")

if __name__ == "__main__":
    main()