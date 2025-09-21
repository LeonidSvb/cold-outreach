#!/usr/bin/env python3
"""
Offline demo of CSV uploader functionality
Shows full processing without API calls
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
import sys
import re

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def extract_domain(website):
    """Extract clean domain from website URL"""
    if not website:
        return None

    website = website.strip()
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website

    try:
        pattern = r'https?://(?:www\.)?([^/]+)'
        match = re.search(pattern, website)
        if match:
            domain = match.group(1).lower()
            domain = domain.split(':')[0]
            return domain
    except Exception as e:
        print(f"Error extracting domain from {website}: {e}")

    return None

def generate_emails(domain):
    """Generate potential email addresses"""
    if not domain:
        return []

    patterns = [
        f"info@{domain}",
        f"contact@{domain}",
        f"hello@{domain}",
        f"sales@{domain}",
        f"support@{domain}",
        f"admin@{domain}"
    ]

    return patterns

def create_lead_data(company, email):
    """Create lead data structure"""
    return {
        "email": email,
        "first_name": "Business",
        "last_name": "Owner",
        "company_name": company.get('company_name', ''),
        "website": company.get('website', ''),
        "country": company.get('country', ''),
        "status": "lead",
        "notes": company.get('content_summary', '')
    }

def main():
    """Main demo function"""
    print("=== INSTANTLY CSV UPLOADER - OFFLINE DEMO ===")
    print("Processing CSV files and generating lead data without API calls")
    print()

    # Find CSV files
    input_dir = Path("../../data/input")
    csv_files = list(input_dir.glob("*.csv")) if input_dir.exists() else []

    if not csv_files:
        print("No CSV files found in input directory")
        return

    print(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {f.name}")

    # Process the first CSV file
    csv_file = csv_files[0]
    print(f"\nProcessing: {csv_file.name}")

    results = {
        "successful": [],
        "failed": [],
        "skipped": [],
        "statistics": {}
    }

    companies_processed = 0
    leads_created = 0

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            print(f"CSV columns: {reader.fieldnames}")
            print()

            for row in reader:
                companies_processed += 1

                if not row.get('company_name') or not row.get('website'):
                    results["skipped"].append({
                        "company": row.get('company_name', 'Unknown'),
                        "reason": "Missing company name or website"
                    })
                    continue

                # Extract domain
                domain = extract_domain(row.get('website', ''))
                if not domain:
                    results["skipped"].append({
                        "company": row.get('company_name', 'Unknown'),
                        "reason": "Invalid domain"
                    })
                    continue

                # Generate emails
                emails = generate_emails(domain)
                if not emails:
                    results["skipped"].append({
                        "company": row.get('company_name', 'Unknown'),
                        "reason": "No valid emails generated"
                    })
                    continue

                # Create lead data
                preferred_email = emails[0]  # Use first email (info@)
                lead_data = create_lead_data(row, preferred_email)

                results["successful"].append(lead_data)
                leads_created += 1

                # Safely print with ASCII encoding
                company_name = row.get('company_name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                print(f"+ Processed: {company_name} -> {preferred_email}")

    except Exception as e:
        print(f"Error processing CSV: {e}")
        return

    # Calculate statistics
    success_rate = (leads_created / companies_processed * 100) if companies_processed > 0 else 0

    results["statistics"] = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total_companies": companies_processed,
        "leads_created": leads_created,
        "success_rate": success_rate,
        "successful_count": len(results["successful"]),
        "failed_count": len(results["failed"]),
        "skipped_count": len(results["skipped"])
    }

    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = results_dir / f"instantly_offline_demo_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Display results
    print(f"\n{'='*60}")
    print("PROCESSING SUMMARY:")
    print(f"{'='*60}")
    print(f"Total companies processed: {companies_processed}")
    print(f"Leads created: {leads_created}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Skipped: {len(results['skipped'])}")

    if results["successful"]:
        print(f"\nSample successful leads:")
        for lead in results["successful"][:5]:
            print(f"  - {lead['company_name']} ({lead['email']})")

    if results["skipped"]:
        print(f"\nSkipped companies:")
        for skip in results["skipped"]:
            print(f"  - {skip['company']}: {skip['reason']}")

    print(f"\nResults saved to: {output_file}")

    print(f"\n{'='*60}")
    print("WHAT THIS SCRIPT WOULD DO WITH REAL API:")
    print(f"{'='*60}")
    print("1. Connect to Instantly API using valid API key")
    print("2. For each lead created, make POST request to /api/v2/leads")
    print("3. Add leads to specified campaign")
    print("4. Handle rate limiting and retries")
    print("5. Save detailed success/failure logs")
    print()
    print("To use with real API:")
    print("1. Get valid INSTANTLY_API_KEY from Instantly dashboard")
    print("2. Get campaign ID where you want to add leads")
    print("3. Update .env file with correct API key")
    print("4. Set TEST_MODE = False in instantly_csv_uploader.py")
    print("5. Run: python instantly_csv_uploader.py")

if __name__ == "__main__":
    main()