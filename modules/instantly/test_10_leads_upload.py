#!/usr/bin/env python3
"""
Upload 10 test leads to new campaign
"""

import json
import csv
import subprocess
import re
from pathlib import Path

def extract_domain(website):
    """Extract domain from URL"""
    if not website:
        return None

    website = website.strip()
    if not website.startswith(('http://', 'https://')):
        website = 'https://' + website

    try:
        pattern = r'https?://(?:www\.)?([^/]+)'
        match = re.search(pattern, website)
        if match:
            domain = match.group(1).lower().split(':')[0]
            return domain
    except:
        pass

    return None

def upload_leads():
    """Upload 10 test leads"""
    print("=== UPLOADING 10 TEST LEADS TO NEW CAMPAIGN ===")

    # Load API key
    env_path = Path(__file__).parent.parent.parent / ".env"
    api_key = None

    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    if not api_key:
        print("No API key found")
        return

    # Campaign ID for new test campaign
    campaign_id = "608002a6-619e-4135-a4f7-02ee54e7ad54"
    print(f"Campaign ID: {campaign_id}")

    # Read CSV file
    csv_file = Path("../../data/input/test_10_leads.csv")

    if not csv_file.exists():
        print(f"CSV file not found: {csv_file}")
        return

    companies = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)

    print(f"Found {len(companies)} companies in CSV")

    # Process each company
    successful = 0
    failed = 0
    created_leads = []

    for i, company in enumerate(companies):
        print(f"\nProcessing {i+1}/{len(companies)}: {company['company_name']}")

        # Extract domain
        domain = extract_domain(company['website'])
        if not domain:
            print(f"  Skipped: Invalid domain")
            failed += 1
            continue

        # Generate email
        email = f"info@{domain}"
        print(f"  Generated email: {email}")

        # Create lead data
        lead_data = {
            "email": email,
            "first_name": "Business",
            "last_name": "Owner",
            "company_name": company['company_name'],
            "website": company['website'],
            "country": company['country'],
            "status": "lead",
            "campaign": campaign_id
        }

        if company.get('content_summary'):
            lead_data['notes'] = company['content_summary']

        # Create lead via curl
        cmd = [
            'curl', '-s', '-X', 'POST',
            '-H', f'Authorization: Bearer {api_key}',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps(lead_data),
            'https://api.instantly.ai/api/v2/leads'
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                response = json.loads(result.stdout)
                if 'id' in response:
                    print(f"  SUCCESS: Lead created! ID: {response['id']}")
                    successful += 1
                    created_leads.append({
                        'company': company['company_name'],
                        'email': email,
                        'lead_id': response['id']
                    })
                else:
                    print(f"  FAILED: Unexpected response: {response}")
                    failed += 1
            else:
                print(f"  FAILED: Curl error: {result.stderr}")
                failed += 1

        except Exception as e:
            print(f"  FAILED: Exception: {e}")
            failed += 1

    print(f"\n=== UPLOAD RESULTS ===")
    print(f"Total companies: {len(companies)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(companies)*100):.1f}%")

    # Save results
    results = {
        "campaign_id": campaign_id,
        "total_companies": len(companies),
        "successful": successful,
        "failed": failed,
        "success_rate": (successful/len(companies)*100) if len(companies) > 0 else 0,
        "created_leads": created_leads
    }

    results_file = Path("results/test_10_leads_upload_results.json")
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {results_file}")

    return results

if __name__ == "__main__":
    upload_leads()