#!/usr/bin/env python3
"""
=== APOLLO EMAIL EXTRACTOR FOR TOP 50 COMPANIES ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Extract contact emails for top 50 cold calling agencies using Apollo API.
Smart usage of 50 free email credits.

FEATURES:
- Loads top 50 companies from Apollo results
- Searches for decision makers (CEO, VP Sales, etc.)
- Extracts emails using free credits
- Priority-based contact selection
- JSON export with full contact data

USAGE:
1. Run after cold_calling_agencies_apollo.py
2. Uses 50 free email credits
3. Results saved with contact information

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import sys
from pathlib import Path
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "APOLLO_API_KEY": "vSJb2-hxp_tbdxy7K8tvgw",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "TOP_COMPANIES_COUNT": 50,
    "EMAIL_CREDITS_LIMIT": 50,
    "RATE_LIMIT_DELAY": 2.0,
}

# Target job titles for decision makers
TARGET_TITLES = [
    "CEO", "Chief Executive Officer",
    "Founder", "Co-Founder",
    "President", "VP Sales", "Vice President Sales",
    "Head of Sales", "Director of Sales",
    "Head of Business Development", "VP Business Development",
    "Chief Revenue Officer", "CRO",
    "Sales Manager", "Business Development Manager"
]


class ApolloEmailExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        self.emails_extracted = 0
        self.api_calls = 0
        self.enriched_companies = []

    def load_apollo_results(self) -> List[Dict]:
        """Load latest Apollo collection results"""
        results_dir = CONFIG["OUTPUT_DIR"]
        json_files = sorted(results_dir.glob("apollo_cold_calling_agencies_*.json"), reverse=True)

        if not json_files:
            raise FileNotFoundError("No Apollo results found. Run cold_calling_agencies_apollo.py first")

        logger.info(f"Loading from: {json_files[0].name}")
        print(f"Loading companies from: {json_files[0].name}")

        with open(json_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
            companies = data.get("companies", [])

        # Return top 50 by quality score
        return companies[:CONFIG["TOP_COMPANIES_COUNT"]]

    def search_people(self, organization_id: str, company_name: str) -> List[Dict]:
        """Search for people at a company"""
        logger.info(f"Searching people at: {company_name}")

        search_payload = {
            "organization_ids": [organization_id],
            "person_titles": TARGET_TITLES[:5],  # Limit to top 5 titles
            "page": 1,
            "per_page": 5,  # Only get top 5 contacts per company
        }

        try:
            response = requests.post(
                f"{self.base_url}/mixed_people/search",
                headers=self.headers,
                json=search_payload,
                timeout=30
            )

            self.api_calls += 1

            if response.status_code == 200:
                data = response.json()
                people = data.get('people', [])
                logger.info(f"Found {len(people)} people at {company_name}")
                return people

            elif response.status_code == 429:
                logger.warning("Rate limit hit")
                print("  Rate limit hit, waiting...")
                time.sleep(60)
                return self.search_people(organization_id, company_name)

            else:
                logger.error(f"People search failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error("People search error", error=e)
            return []

    def extract_contact_email(self, person: Dict) -> Optional[str]:
        """Extract email from person data"""
        # Apollo may already provide email in search results
        email = person.get('email')

        if email:
            self.emails_extracted += 1
            return email

        return None

    def enrich_company_with_contacts(self, company: Dict) -> Dict:
        """Enrich company with contact information"""
        organization_id = company.get('apollo_id')
        company_name = company.get('name', 'Unknown')

        if not organization_id:
            logger.warning(f"No apollo_id for {company_name}")
            return company

        # Safe print with encoding handling
        safe_name = company_name.encode('ascii', 'ignore').decode('ascii')
        print(f"  Processing: {safe_name}")

        # Search for people
        people = self.search_people(organization_id, company_name)

        # Extract contacts
        contacts = []
        for person in people:
            if self.emails_extracted >= CONFIG["EMAIL_CREDITS_LIMIT"]:
                logger.warning("Email credits limit reached")
                print(f"    Email credits limit reached ({CONFIG['EMAIL_CREDITS_LIMIT']})")
                break

            email = self.extract_contact_email(person)

            contact = {
                "name": person.get('name'),
                "title": person.get('title'),
                "email": email,
                "linkedin_url": person.get('linkedin_url'),
                "phone": person.get('sanitized_phone'),
                "seniority": person.get('seniority'),
            }

            contacts.append(contact)

            if email:
                print(f"    Found: {contact['name']} ({contact['title']}) - {email}")

        # Add contacts to company
        enriched = company.copy()
        enriched['contacts'] = contacts
        enriched['contacts_count'] = len(contacts)
        enriched['emails_found'] = sum(1 for c in contacts if c.get('email'))

        return enriched

    def extract_emails(self, companies: List[Dict]):
        """Extract emails for all companies"""
        logger.info(f"Starting email extraction for {len(companies)} companies")
        print(f"\nExtracting emails for top {len(companies)} companies...")
        print(f"Email credits available: {CONFIG['EMAIL_CREDITS_LIMIT']}\n")

        for i, company in enumerate(companies, 1):
            if self.emails_extracted >= CONFIG["EMAIL_CREDITS_LIMIT"]:
                logger.info("Email credits limit reached, stopping")
                print(f"\nEmail credits limit reached. Processed {i-1} companies.")
                break

            company_name = company.get('name', 'Unknown').encode('ascii', 'ignore').decode('ascii')
            print(f"[{i}/{len(companies)}] {company_name}")

            enriched = self.enrich_company_with_contacts(company)
            self.enriched_companies.append(enriched)

            # Rate limiting
            if i < len(companies):
                time.sleep(CONFIG["RATE_LIMIT_DELAY"])

        logger.info(f"Email extraction complete. {self.emails_extracted} emails extracted")
        print(f"\nExtraction complete!")
        print(f"  Companies processed: {len(self.enriched_companies)}")
        print(f"  Emails extracted: {self.emails_extracted}")

    def save_results(self):
        """Save enriched results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = CONFIG["OUTPUT_DIR"] / f"apollo_cold_calling_WITH_EMAILS_{timestamp}.json"

        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_companies": len(self.enriched_companies),
                "emails_extracted": self.emails_extracted,
                "api_calls": self.api_calls,
                "version": "1.0.0",
            },
            "companies": self.enriched_companies,
            "statistics": {
                "total_companies": len(self.enriched_companies),
                "companies_with_contacts": sum(1 for c in self.enriched_companies if c.get('contacts_count', 0) > 0),
                "companies_with_emails": sum(1 for c in self.enriched_companies if c.get('emails_found', 0) > 0),
                "total_contacts": sum(c.get('contacts_count', 0) for c in self.enriched_companies),
                "total_emails": sum(c.get('emails_found', 0) for c in self.enriched_companies),
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_file}")
        return output_file


def main():
    logger.info("Starting Apollo email extractor")

    print("\n" + "="*70)
    print("APOLLO EMAIL EXTRACTOR - TOP 50 COMPANIES")
    print("="*70)

    try:
        # Initialize extractor
        extractor = ApolloEmailExtractor(CONFIG["APOLLO_API_KEY"])

        # Load top companies
        print("\nLoading top 50 companies...")
        companies = extractor.load_apollo_results()
        print(f"Loaded {len(companies)} companies for email extraction\n")

        # Extract emails
        extractor.extract_emails(companies)

        # Save results
        output_file = extractor.save_results()

        # Print summary
        print("\n" + "="*70)
        print("EMAIL EXTRACTION SUMMARY")
        print("="*70)
        print(f"Companies Processed: {len(extractor.enriched_companies)}")
        print(f"Total Emails Extracted: {extractor.emails_extracted}/{CONFIG['EMAIL_CREDITS_LIMIT']}")
        print(f"Total Contacts Found: {sum(c.get('contacts_count', 0) for c in extractor.enriched_companies)}")
        print(f"Companies with Emails: {sum(1 for c in extractor.enriched_companies if c.get('emails_found', 0) > 0)}")

        print(f"\nTop 5 Companies with Most Contacts:")
        sorted_by_contacts = sorted(extractor.enriched_companies, key=lambda x: x.get('contacts_count', 0), reverse=True)
        for i, company in enumerate(sorted_by_contacts[:5], 1):
            print(f"  {i}. {company['name']} - {company.get('contacts_count', 0)} contacts, {company.get('emails_found', 0)} emails")

        print(f"\nResults saved to:")
        print(f"  {output_file}")
        print("="*70)

        logger.info("Email extraction completed successfully")

    except Exception as e:
        logger.error("Email extraction failed", error=e)
        print(f"\nERROR: {str(e)}")
        raise


if __name__ == "__main__":
    main()
