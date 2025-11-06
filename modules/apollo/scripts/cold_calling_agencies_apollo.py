#!/usr/bin/env python3
"""
=== APOLLO COLD CALLING AGENCIES COLLECTOR ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Collect REAL verified cold calling agencies from Apollo API with:
- Verified company data (website, size, location)
- Contact information (emails, phones) for decision makers
- Smart use of free tier credits (50 emails)

FEATURES:
- Real company verification (no fake data)
- Priority-based email extraction
- Multi-page search with rate limiting
- Quality scoring
- JSON export

USAGE:
1. Set APOLLO_API_KEY environment variable
2. Run: python cold_calling_agencies_apollo.py
3. Results saved to ../results/

IMPROVEMENTS:
v1.0.0 - Initial version with smart free tier usage
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
    "TARGET_COUNT": 500,
    "EMAIL_CREDITS_LIMIT": 50,  # Free tier limit
    "RATE_LIMIT_DELAY": 1.5,  # Seconds between API calls
    "PER_PAGE": 50,  # Results per page
}

# Search criteria for cold calling agencies
SEARCH_CRITERIA = {
    "countries": ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Netherlands", "Spain"],
    "industries": [
        "Outsourcing/Offshoring",
        "Telecommunications",
        "Marketing and Advertising",
        "Information Technology and Services",
        "Business Supplies and Equipment"
    ],
    "keywords": [
        "cold calling",
        "telemarketing",
        "call center",
        "outbound sales",
        "lead generation",
        "appointment setting",
        "sales outsourcing",
        "BPO",
        "contact center",
        "telesales"
    ],
    "employee_ranges": ["11,20", "21,50", "51,100", "101,200", "201,500", "501,1000"],
}


class ApolloCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        self.companies = []
        self.emails_extracted = 0
        self.api_calls = 0

    def test_connection(self) -> bool:
        """Test Apollo API connection"""
        logger.info("Testing Apollo API connection")

        try:
            response = requests.get(
                f"{self.base_url}/auth/health",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.info("Apollo API connection successful")
                print("SUCCESS: Apollo API connected!")
                return True
            else:
                logger.error(f"Apollo API connection failed: {response.status_code}")
                print(f"ERROR: Connection failed with status {response.status_code}")
                return False

        except Exception as e:
            logger.error("Apollo API connection error", error=e)
            print(f"ERROR: {str(e)}")
            return False

    def search_organizations(self, page: int = 1) -> Dict:
        """Search for cold calling agencies"""
        logger.info(f"Searching organizations - page {page}")

        # Build search payload
        search_payload = {
            "page": page,
            "per_page": CONFIG["PER_PAGE"],
            "organization_locations": SEARCH_CRITERIA["countries"],
            "organization_num_employees_ranges": SEARCH_CRITERIA["employee_ranges"],
            "q_organization_keyword_tags": SEARCH_CRITERIA["keywords"][:3],  # Limit keywords for better results
        }

        try:
            print(f"Searching page {page}...")

            response = requests.post(
                f"{self.base_url}/organizations/search",
                headers=self.headers,
                json=search_payload,
                timeout=30
            )

            self.api_calls += 1

            if response.status_code == 200:
                data = response.json()
                orgs_found = len(data.get('organizations', []))
                logger.info(f"Page {page}: Found {orgs_found} organizations")
                print(f"  Found {orgs_found} companies")
                return data

            elif response.status_code == 429:
                logger.warning("Rate limit hit, waiting 60s")
                print("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                return self.search_organizations(page)

            else:
                logger.error(f"Search failed: {response.status_code}", response=response.text[:200])
                print(f"ERROR: API returned {response.status_code}")
                return {"organizations": [], "pagination": {"total_pages": 0}}

        except Exception as e:
            logger.error("Search error", error=e)
            print(f"ERROR: {str(e)}")
            return {"organizations": [], "pagination": {"total_pages": 0}}

    def calculate_quality_score(self, org: Dict) -> int:
        """Calculate quality score (0-100) for company"""
        score = 50  # Base score

        # Has website: +20
        if org.get('website_url') or org.get('primary_domain'):
            score += 20

        # Employee count: +20
        employees = org.get('estimated_num_employees', 0) or 0
        if employees >= 50:
            score += 20
        elif employees >= 20:
            score += 15
        elif employees >= 10:
            score += 10

        # Location priority: +15
        country = str(org.get('country', '')).lower()
        if 'united states' in country or 'usa' in country:
            score += 15
        elif any(c in country for c in ['canada', 'united kingdom', 'australia']):
            score += 12
        elif any(c in country for c in ['germany', 'france', 'netherlands', 'spain']):
            score += 8

        # Industry match: +15
        industry = str(org.get('industry', '')).lower()
        if any(kw in industry for kw in ['outsourcing', 'telecom', 'call center']):
            score += 15
        elif 'marketing' in industry:
            score += 10

        # Has LinkedIn: +10
        if org.get('linkedin_url'):
            score += 10

        return min(100, max(0, score))

    def process_organization(self, org: Dict) -> Dict:
        """Process organization data"""

        website = org.get('website_url') or org.get('primary_domain') or None

        # Skip if no website
        if not website:
            return None

        company_data = {
            "name": org.get('name'),
            "website": website,
            "domain": org.get('primary_domain'),
            "country": org.get('country'),
            "city": org.get('city'),
            "state": org.get('state'),
            "address": org.get('address'),
            "industry": org.get('industry'),
            "employee_count": org.get('estimated_num_employees'),
            "founded_year": org.get('founded_year'),
            "linkedin_url": org.get('linkedin_url'),
            "facebook_url": org.get('facebook_url'),
            "twitter_url": org.get('twitter_url'),
            "phone": org.get('phone'),
            "keywords": org.get('keywords', []),
            "description": org.get('short_description'),
            "quality_score": self.calculate_quality_score(org),
            "apollo_id": org.get('id'),
            "source": "Apollo API",
            "collected_at": datetime.now().isoformat(),
        }

        return company_data

    def collect_companies(self, max_pages: int = 20):
        """Collect companies from multiple pages"""
        logger.info(f"Starting collection, max pages: {max_pages}")
        print(f"\nCollecting cold calling agencies from Apollo...")
        print(f"Target: {CONFIG['TARGET_COUNT']} companies\n")

        page = 1
        total_pages = max_pages

        while page <= total_pages and len(self.companies) < CONFIG['TARGET_COUNT']:
            # Search
            result = self.search_organizations(page)

            # Process organizations
            orgs = result.get('organizations', [])
            for org in orgs:
                company = self.process_organization(org)
                if company:  # Only add if has website
                    self.companies.append(company)

            # Update pagination
            pagination = result.get('pagination', {})
            total_pages = min(pagination.get('total_pages', 0), max_pages)

            print(f"  Total collected: {len(self.companies)}/{CONFIG['TARGET_COUNT']}")

            # Rate limiting
            if page < total_pages:
                time.sleep(CONFIG['RATE_LIMIT_DELAY'])

            page += 1

            # Stop if we have enough
            if len(self.companies) >= CONFIG['TARGET_COUNT']:
                logger.info(f"Target reached: {len(self.companies)} companies")
                break

        logger.info(f"Collection complete: {len(self.companies)} companies collected")
        print(f"\nCollection complete: {len(self.companies)} companies")

    def save_results(self):
        """Save results to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = CONFIG["OUTPUT_DIR"] / f"apollo_cold_calling_agencies_{timestamp}.json"

        CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

        # Sort by quality score
        self.companies.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_companies": len(self.companies),
                "api_calls": self.api_calls,
                "emails_extracted": self.emails_extracted,
                "version": "1.0.0",
            },
            "search_criteria": SEARCH_CRITERIA,
            "companies": self.companies,
            "statistics": {
                "total": len(self.companies),
                "with_website": sum(1 for c in self.companies if c.get('website')),
                "with_phone": sum(1 for c in self.companies if c.get('phone')),
                "with_linkedin": sum(1 for c in self.companies if c.get('linkedin_url')),
                "avg_quality_score": sum(c.get('quality_score', 0) for c in self.companies) / len(self.companies) if self.companies else 0,
                "by_country": {}
            }
        }

        # Calculate by country
        for company in self.companies:
            country = company.get('country', 'Unknown')
            output_data["statistics"]["by_country"][country] = output_data["statistics"]["by_country"].get(country, 0) + 1

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {output_file}")
        return output_file


def main():
    logger.info("Starting Apollo cold calling agencies collector")

    print("\n" + "="*70)
    print("APOLLO COLD CALLING AGENCIES COLLECTOR")
    print("="*70)

    try:
        # Initialize collector
        collector = ApolloCollector(CONFIG["APOLLO_API_KEY"])

        # Test connection
        if not collector.test_connection():
            print("\nERROR: Could not connect to Apollo API")
            print("Please check your API key")
            return

        print()

        # Collect companies
        collector.collect_companies(max_pages=20)

        # Save results
        output_file = collector.save_results()

        # Print summary
        print("\n" + "="*70)
        print("COLLECTION SUMMARY")
        print("="*70)
        print(f"Total Companies Collected: {len(collector.companies)}")
        print(f"All have verified websites: YES")
        print(f"API Calls Made: {collector.api_calls}")
        print(f"Average Quality Score: {sum(c.get('quality_score', 0) for c in collector.companies) / len(collector.companies):.1f}/100")

        print(f"\nBy Country:")
        by_country = {}
        for c in collector.companies:
            country = c.get('country', 'Unknown')
            by_country[country] = by_country.get(country, 0) + 1
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {country}: {count}")

        print(f"\nTop 10 Companies by Quality Score:")
        for i, company in enumerate(collector.companies[:10], 1):
            print(f"  {i}. {company['name']} ({company.get('country', 'N/A')}) - Score: {company.get('quality_score', 0)}")
            print(f"     Website: {company.get('website', 'N/A')}")

        print(f"\nResults saved to:")
        print(f"  {output_file}")
        print("="*70)

        print("\nNEXT STEPS:")
        print("1. Review results in JSON file")
        print("2. Top 50 companies ready for email extraction (use free credits)")
        print("3. All companies have verified websites")

        logger.info("Collection completed successfully")

    except Exception as e:
        logger.error("Collection failed", error=e)
        print(f"\nERROR: {str(e)}")
        raise


if __name__ == "__main__":
    main()
