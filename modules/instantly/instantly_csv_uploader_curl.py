#!/usr/bin/env python3
"""
=== INSTANTLY CSV COMPANY UPLOADER (CURL VERSION) ===
Version: 2.0.0 | Created: 2025-01-21

PURPOSE:
Upload companies from CSV files as leads to Instantly via API v2 using curl (bypasses Cloudflare)

FEATURES:
- Uses curl for API calls to bypass Cloudflare protection
- Raw base64 API key (no decoding needed)
- Reads CSV files with company data
- Generates potential email addresses from company domains
- Mass upload leads to Instantly campaigns
- Comprehensive error handling and retry logic

USAGE:
1. Ensure INSTANTLY_API_KEY is set in .env file (raw base64)
2. Place CSV files in data/input/ directory
3. Run: python instantly_csv_uploader_curl.py
4. Results saved to results/ with timestamp

IMPROVEMENTS:
v2.0.0 - Updated to use curl for API calls (bypasses Cloudflare)
v1.0.0 - Initial version with urllib (blocked by Cloudflare)
"""

import json
import time
import os
import sys
import csv
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Simple logging function
def auto_log(module_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"[{module_name}] Starting {func.__name__}")
            result = func(*args, **kwargs)
            print(f"[{module_name}] Completed {func.__name__}")
            return result
        return wrapper
    return decorator

# ============================================================================
# CONFIG SECTION
# ============================================================================

CONFIG = {
    "INSTANTLY_API": {
        "BASE_URL": "https://api.instantly.ai/api/v2",
        "TIMEOUT_SECONDS": 30,
        "RETRY_ATTEMPTS": 3,
        "RETRY_DELAY": 2
    },

    "CSV_PROCESSING": {
        "INPUT_DIR": "../../data/input",
        "EXPECTED_COLUMNS": ["company_name", "website", "country"],
        "BATCH_SIZE": 50,
        "SKIP_INVALID_DOMAINS": True
    },

    "EMAIL_GENERATION": {
        "PATTERNS": [
            "info@{domain}",
            "contact@{domain}",
            "hello@{domain}",
            "sales@{domain}",
            "support@{domain}",
            "admin@{domain}"
        ],
        "PREFER_PATTERN": "info@{domain}",
        "VALIDATE_FORMAT": True
    },

    "LEAD_UPLOAD": {
        "CAMPAIGN_ID": None,  # Must be set or provided
        "DEFAULT_FIELDS": {
            "first_name": "Business",
            "last_name": "Owner",
            "status": "lead"
        },
        "SKIP_DUPLICATES": True,
        "TEST_MODE": False  # Set to True for dry run
    },

    "OUTPUT": {
        "SAVE_JSON": True,
        "RESULTS_DIR": "results",
        "LOG_DETAILED": True,
        "SAVE_FAILED": True
    }
}

# ============================================================================
# SCRIPT STATISTICS
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0,
    "leads_uploaded": 0,
    "companies_processed": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class InstantlyCsvUploaderCurl:
    def __init__(self):
        self.config = CONFIG
        self.api_key = self._load_api_key()
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.upload_results = {
            "successful": [],
            "failed": [],
            "skipped": [],
            "statistics": {}
        }

    def _load_api_key(self) -> Optional[str]:
        """Load raw base64 API key from .env file"""
        env_path = Path(__file__).parent.parent.parent / ".env"

        if not env_path.exists():
            print("Error: .env file not found")
            return None

        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('INSTANTLY_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    print(f"API key loaded (raw base64)")
                    return api_key

        print("Error: INSTANTLY_API_KEY not found in .env")
        return None

    def _make_curl_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Instantly API using curl"""
        url = f"{self.config['INSTANTLY_API']['BASE_URL']}/{endpoint}"

        headers = [
            f'Authorization: Bearer {self.api_key}',
            'Content-Type: application/json'
        ]

        for attempt in range(self.config['INSTANTLY_API']['RETRY_ATTEMPTS']):
            try:
                cmd = ['curl', '-s']

                # Add headers
                for header in headers:
                    cmd.extend(['-H', header])

                # Add method and data for POST requests
                if method == 'POST' and data:
                    cmd.extend(['-X', 'POST'])
                    cmd.extend(['-d', json.dumps(data)])

                # Add URL
                cmd.append(url)

                # Execute curl command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config['INSTANTLY_API']['TIMEOUT_SECONDS']
                )

                if result.returncode == 0:
                    try:
                        response_data = json.loads(result.stdout)

                        # Check for API errors in response
                        if isinstance(response_data, dict) and 'error' in response_data:
                            print(f"API Error: {response_data}")
                            return None

                        return response_data
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
                        print(f"Raw response: {result.stdout[:200]}...")
                        return None
                else:
                    print(f"Curl error (attempt {attempt + 1}): {result.stderr}")

                if attempt == self.config['INSTANTLY_API']['RETRY_ATTEMPTS'] - 1:
                    return None

                time.sleep(self.config['INSTANTLY_API']['RETRY_DELAY'])

            except subprocess.TimeoutExpired:
                print(f"Request timeout on attempt {attempt + 1}")
                if attempt == self.config['INSTANTLY_API']['RETRY_ATTEMPTS'] - 1:
                    return None
                time.sleep(self.config['INSTANTLY_API']['RETRY_DELAY'])

            except Exception as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.config['INSTANTLY_API']['RETRY_ATTEMPTS'] - 1:
                    return None
                time.sleep(self.config['INSTANTLY_API']['RETRY_DELAY'])

        return None

    def _extract_domain(self, website: str) -> Optional[str]:
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

    def _generate_emails(self, domain: str, company_name: str) -> List[str]:
        """Generate potential email addresses for a company"""
        if not domain:
            return []

        emails = []
        for pattern in self.config["EMAIL_GENERATION"]["PATTERNS"]:
            email = pattern.format(domain=domain)
            if self._is_valid_email(email):
                emails.append(email)

        return emails

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if not self.config["EMAIL_GENERATION"]["VALIDATE_FORMAT"]:
            return True

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _read_csv_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read and parse CSV file"""
        companies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                if not all(col in reader.fieldnames for col in self.config["CSV_PROCESSING"]["EXPECTED_COLUMNS"]):
                    print(f"Warning: Missing expected columns in {file_path.name}")
                    print(f"Found columns: {reader.fieldnames}")

                for row in reader:
                    if row.get('company_name') and row.get('website'):
                        companies.append(row)

        except Exception as e:
            print(f"Error reading CSV file {file_path}: {e}")

        return companies

    def _create_lead_data(self, company: Dict[str, Any], email: str) -> Dict[str, Any]:
        """Create lead data structure for Instantly API"""
        lead_data = {
            "email": email,
            "first_name": self.config["LEAD_UPLOAD"]["DEFAULT_FIELDS"]["first_name"],
            "last_name": self.config["LEAD_UPLOAD"]["DEFAULT_FIELDS"]["last_name"],
            "company_name": company.get('company_name', ''),
            "website": company.get('website', ''),
            "country": company.get('country', ''),
            "status": self.config["LEAD_UPLOAD"]["DEFAULT_FIELDS"]["status"]
        }

        # Add custom fields if available
        if company.get('content_summary'):
            lead_data["notes"] = company['content_summary']

        return lead_data

    @auto_log("instantly_csv_uploader_curl")
    def upload_companies_from_csv(self, csv_file_path: Optional[str] = None, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """Main function to upload companies from CSV using curl"""
        if not self.api_key:
            print("Error: No API key found")
            return {}

        print(f"Starting CSV company upload to Instantly (using curl)")
        print(f"API Key (first 20 chars): {self.api_key[:20]}...")
        print()

        start_time = time.time()

        # Set campaign ID
        if campaign_id:
            self.config["LEAD_UPLOAD"]["CAMPAIGN_ID"] = campaign_id

        # Test API connection first
        if not self._test_connection():
            print("API connection failed - stopping upload")
            return {}

        # Find CSV files
        csv_files = self._find_csv_files(csv_file_path)
        if not csv_files:
            print("No CSV files found to process")
            return {}

        # Process each CSV file
        total_companies = 0
        total_leads_created = 0

        for csv_file in csv_files:
            print(f"\nProcessing: {csv_file.name}")
            companies = self._read_csv_file(csv_file)

            if not companies:
                print(f"No valid companies found in {csv_file.name}")
                continue

            print(f"Found {len(companies)} companies")
            total_companies += len(companies)

            # Process companies in batches
            batch_count = 0
            for i in range(0, len(companies), self.config["CSV_PROCESSING"]["BATCH_SIZE"]):
                batch = companies[i:i + self.config["CSV_PROCESSING"]["BATCH_SIZE"]]
                batch_count += 1

                print(f"Processing batch {batch_count} ({len(batch)} companies)...")
                leads_created = self._process_company_batch(batch)
                total_leads_created += leads_created

        # Save results
        self._save_results(start_time, total_companies, total_leads_created)

        processing_time = time.time() - start_time
        print(f"\nUpload completed in {processing_time:.2f} seconds")
        print(f"Companies processed: {total_companies}")
        print(f"Leads created: {total_leads_created}")
        print(f"Success rate: {(total_leads_created/total_companies*100):.1f}%" if total_companies > 0 else "N/A")

        return self.upload_results

    def _find_csv_files(self, csv_file_path: Optional[str] = None) -> List[Path]:
        """Find CSV files to process"""
        if csv_file_path:
            file_path = Path(csv_file_path)
            if file_path.exists() and file_path.suffix.lower() == '.csv':
                return [file_path]
            else:
                print(f"CSV file not found: {csv_file_path}")
                return []
        else:
            input_dir = Path(__file__).parent / self.config["CSV_PROCESSING"]["INPUT_DIR"]
            if input_dir.exists():
                csv_files = list(input_dir.glob("*.csv"))
                print(f"Found {len(csv_files)} CSV files in {input_dir}")
                return csv_files
            else:
                print(f"Input directory not found: {input_dir}")
                return []

    def _process_company_batch(self, companies: List[Dict[str, Any]]) -> int:
        """Process a batch of companies"""
        leads_created = 0

        for company in companies:
            try:
                # Extract domain and generate emails
                domain = self._extract_domain(company.get('website', ''))
                if not domain:
                    if self.config["CSV_PROCESSING"]["SKIP_INVALID_DOMAINS"]:
                        self.upload_results["skipped"].append({
                            "company": company.get('company_name', 'Unknown'),
                            "reason": "Invalid domain"
                        })
                        continue

                emails = self._generate_emails(domain, company.get('company_name', ''))
                if not emails:
                    self.upload_results["skipped"].append({
                        "company": company.get('company_name', 'Unknown'),
                        "reason": "No valid emails generated"
                    })
                    continue

                # Use the preferred email pattern
                preferred_email = emails[0]  # First email (usually info@)

                # Create lead
                lead_data = self._create_lead_data(company, preferred_email)

                if self.config["LEAD_UPLOAD"]["TEST_MODE"]:
                    print(f"TEST MODE: Would create lead: {lead_data}")
                    leads_created += 1
                    self.upload_results["successful"].append(lead_data)
                else:
                    if self._create_lead(lead_data):
                        leads_created += 1
                        self.upload_results["successful"].append(lead_data)
                        company_name = company.get('company_name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
                        print(f"+ Created lead: {company_name} ({preferred_email})")
                    else:
                        self.upload_results["failed"].append({
                            "company": company.get('company_name', 'Unknown'),
                            "email": preferred_email,
                            "error": "API call failed"
                        })

                # Small delay to avoid rate limiting
                time.sleep(0.2)

            except Exception as e:
                print(f"Error processing company {company.get('company_name', 'Unknown')}: {e}")
                self.upload_results["failed"].append({
                    "company": company.get('company_name', 'Unknown'),
                    "error": str(e)
                })

        return leads_created

    def _create_lead(self, lead_data: Dict[str, Any]) -> bool:
        """Create a single lead via Instantly API using curl"""
        result = self._make_curl_request('leads', 'POST', lead_data)

        if result and isinstance(result, dict) and result.get('id'):
            return True
        else:
            return False

    def _test_connection(self) -> bool:
        """Test API connection using curl"""
        print("Testing API connection...")

        result = self._make_curl_request('campaigns/analytics')

        if result and isinstance(result, list):
            print(f"API connection successful - found {len(result)} campaigns")
            return True
        else:
            print("API connection failed")
            return False

    def _save_results(self, start_time: float, total_companies: int, total_leads_created: int):
        """Save upload results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.upload_results["statistics"] = {
            "timestamp": timestamp,
            "processing_time": time.time() - start_time,
            "total_companies": total_companies,
            "leads_created": total_leads_created,
            "success_rate": (total_leads_created/total_companies*100) if total_companies > 0 else 0,
            "successful_count": len(self.upload_results["successful"]),
            "failed_count": len(self.upload_results["failed"]),
            "skipped_count": len(self.upload_results["skipped"])
        }

        filename = f"instantly_csv_upload_curl_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.upload_results, f, indent=2, ensure_ascii=False)

        print(f"Results saved: {filename}")

def main():
    """Main execution function"""
    print("=== INSTANTLY CSV COMPANY UPLOADER (CURL VERSION) ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    uploader = InstantlyCsvUploaderCurl()

    # You can specify a specific CSV file or let it process all CSV files in input directory
    csv_file = None  # Process all CSV files in input directory

    # Campaign ID - use the Marketing agencies campaign
    campaign_id = "8ad64aaf-8294-4538-8400-4a99dcf016e8"

    print(f"Using campaign ID: {campaign_id}")

    results = uploader.upload_companies_from_csv(csv_file, campaign_id)

    if results:
        print(f"\nUpload process completed!")
        print(f"Results saved to: {uploader.results_dir}")
        stats = results.get('statistics', {})
        print(f"Companies processed: {stats.get('total_companies', 0)}")
        print(f"Leads created: {stats.get('leads_created', 0)}")
        print(f"Success rate: {stats.get('success_rate', 0):.1f}%")
    else:
        print(f"\nUpload process failed!")

if __name__ == "__main__":
    main()