#!/usr/bin/env python3
"""
Apollo API Lead Collector for Premium Marketing Agencies
Targets agencies with $180K-$600K annual revenue serving high-value clients
"""

import requests
import json
import time
import csv
from datetime import datetime
import sys
from typing import List, Dict, Optional

class ApolloLeadCollector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        }
        self.collected_leads = []
        self.total_calls = 0
        self.rate_limit_delay = 1.2  # seconds between calls
        
    def test_connection(self) -> bool:
        """Test Apollo API connection"""
        try:
            response = requests.get(
                f"{self.base_url}/auth/health", 
                headers=self.headers,
                timeout=30
            )
            if response.status_code == 200:
                print("SUCCESS: Apollo API connection successful")
                return True
            else:
                print(f"ERROR: Apollo API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"ERROR: Connection error: {str(e)}")
            return False
    
    def search_organizations(self, page: int = 1) -> Dict:
        """Search for premium marketing agencies using Apollo API"""
        
        # Search for premium marketing agencies
        search_payload = {
            "page": page,
            "per_page": 50,
            "organization_locations": ["United States", "United Kingdom", "Canada", "Australia"],
            "organization_num_employees_ranges": ["11,20", "21,50", "51,100"],
            "q_organization_keyword_tags": ["marketing agency", "digital marketing", "b2b marketing"]
        }
        
        try:
            print(f"Executing search - Page {page}...")
            response = requests.post(
                f"{self.base_url}/organizations/search",
                headers=self.headers,
                json=search_payload,
                timeout=30
            )
            
            self.total_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS: Page {page}: Found {len(data.get('organizations', []))} organizations")
                return data
            elif response.status_code == 429:
                print("Rate limit hit, waiting 60 seconds...")
                time.sleep(60)
                return self.search_organizations(page)
            else:
                print(f"ERROR: API Error {response.status_code}: {response.text}")
                return {"organizations": [], "pagination": {"total_pages": 0}}
                
        except Exception as e:
            print(f"ERROR: Search error: {str(e)}")
            return {"organizations": [], "pagination": {"total_pages": 0}}
    
    def calculate_lead_score(self, org: Dict) -> int:
        """Calculate lead score (0-100) based on criteria"""
        score = 0
        
        # Revenue scoring (max 30 points) - using organization_revenue
        revenue = org.get('organization_revenue', 0) or 0
        if revenue >= 500000:
            score += 30
        elif revenue >= 300000:
            score += 25
        elif revenue >= 180000:
            score += 20
        elif revenue >= 100000:
            score += 15  # Lower threshold to catch more agencies
        
        # Employee count scoring (max 20 points) - using estimated_num_employees
        employees = org.get('estimated_num_employees', 0) or 0
        if 20 <= employees <= 50:
            score += 20
        elif 15 <= employees <= 25:
            score += 18
        elif 10 <= employees <= 20:
            score += 15
        elif 5 <= employees <= 15:
            score += 10  # Lower threshold for smaller agencies
        
        # Location scoring (max 15 points) - country is directly in org
        country = str(org.get('country', '')).lower()
        if country in ['united states', 'usa', 'us']:
            score += 15
        elif country in ['united kingdom', 'uk', 'canada', 'australia']:
            score += 12
        
        # Industry relevance (max 15 points)
        industry = str(org.get('industry', '')).lower()
        industries = org.get('industries', [])
        industry_text = ' '.join([industry] + industries).lower()
        
        if any(keyword in industry_text for keyword in ['marketing', 'advertising']):
            score += 15
        elif 'information technology' in industry_text:
            score += 10
        elif 'software' in industry_text or 'saas' in industry_text:
            score += 12
        
        # Technology indicators (max 10 points)
        keywords = ' '.join(org.get('keywords', [])).lower()
        tech_keywords = ['hubspot', 'salesforce', 'marketo', 'pardot', 'zoominfo', 'digital marketing']
        marketing_keywords = ['b2b', 'growth marketing', 'performance marketing', 'marketing agency', 'lead generation']
        
        if any(tech in keywords for tech in tech_keywords):
            score += 10
        elif any(keyword in keywords for keyword in marketing_keywords):
            score += 8
        
        # Growth indicators (max 10 points)
        founded_year = org.get('founded_year', 0)
        if founded_year and 2018 <= founded_year <= 2022:
            score += 10
        elif founded_year and 2015 <= founded_year <= 2024:
            score += 5  # Broader range for growth
        
        return min(score, 100)
    
    def process_organization(self, org: Dict) -> Dict:
        """Process and enrich organization data"""
        processed = {
            'company_name': org.get('name', ''),
            'domain': org.get('primary_domain', ''),
            'website_url': org.get('website_url', ''),
            'linkedin_url': org.get('linkedin_url', ''),
            'industry': org.get('industry', ''),
            'sub_industry': ', '.join(org.get('secondary_industries', [])),
            'employee_count': org.get('estimated_num_employees', 0) or 0,
            'revenue': org.get('organization_revenue', 0) or 0,
            'revenue_range': org.get('organization_revenue_printed', ''),
            'location_city': org.get('city', ''),
            'location_state': org.get('state', ''),
            'location_country': org.get('country', ''),
            'founded_year': org.get('founded_year', ''),
            'technologies': '',  # Not available in this API response
            'keywords': ', '.join(org.get('keywords', [])),
            'description': '',  # Not available in this API response
            'phone': org.get('phone', ''),
            'collection_date': datetime.now().strftime('%Y-%m-%d'),
            'notes': f"Premium marketing agency - {org.get('industry', '')}",
            'target_persona': 'Marketing Director/VP/Founder',
            'enrichment_priority': 'High'
        }
        
        # Calculate lead score
        processed['lead_score'] = self.calculate_lead_score(org)
        
        return processed
    
    def collect_leads(self, target_count: int = 500) -> List[Dict]:
        """Collect leads with pagination until target reached"""
        page = 1
        total_collected = 0
        high_quality_leads = []
        
        print(f"Starting collection for {target_count} premium marketing agency leads...")
        
        while total_collected < target_count:
            # Respect rate limits
            if self.total_calls > 0:
                time.sleep(self.rate_limit_delay)
            
            # Get page data
            data = self.search_organizations(page)
            organizations = data.get('organizations', [])
            
            if not organizations:
                print("No more organizations found.")
                break
            
            # Process organizations
            for org in organizations:
                processed_lead = self.process_organization(org)
                
                # Filter for high-quality leads (score >= 70)
                if processed_lead['lead_score'] >= 60:  # Slightly lower threshold for more results
                    high_quality_leads.append(processed_lead)
                
                self.collected_leads.append(processed_lead)
                total_collected += 1
                
                if total_collected >= target_count:
                    break
            
            # Check if we have more pages
            pagination = data.get('pagination', {})
            if page >= pagination.get('total_pages', 1):
                break
                
            page += 1
            
            # Progress update
            print(f"Progress: {total_collected}/{target_count} leads collected, "
                  f"{len(high_quality_leads)} high-quality leads")
        
        print(f"\nSUCCESS: Collection completed:")
        print(f"  Total leads: {len(self.collected_leads)}")
        print(f"  High-quality leads (60+ score): {len(high_quality_leads)}")
        print(f"  API calls made: {self.total_calls}")
        
        return high_quality_leads
    
    def export_to_csv(self, leads: List[Dict], filename: str = None) -> str:
        """Export leads to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"premium_marketing_agencies_{timestamp}.csv"
        
        filepath = f"C:\\Users\\79818\\Desktop\\Outreach - new\\{filename}"
        
        if not leads:
            print("No leads to export.")
            return filepath
        
        # Define CSV columns
        columns = [
            'company_name', 'domain', 'website_url', 'linkedin_url', 'industry',
            'sub_industry', 'employee_count', 'revenue', 'revenue_range',
            'location_city', 'location_state', 'location_country', 'founded_year',
            'technologies', 'keywords', 'description', 'phone', 'lead_score',
            'collection_date', 'notes', 'target_persona', 'enrichment_priority'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                writer.writerows(leads)
            
            print(f"SUCCESS: Exported {len(leads)} leads to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"ERROR: Export error: {str(e)}")
            return filepath
    
    def generate_summary_report(self, leads: List[Dict]) -> None:
        """Generate collection summary report"""
        if not leads:
            return
        
        # Calculate statistics
        total_leads = len(leads)
        avg_score = sum(lead['lead_score'] for lead in leads) / total_leads
        
        # Industry breakdown
        industries = {}
        for lead in leads:
            industry = lead.get('industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
        
        # Location breakdown
        countries = {}
        for lead in leads:
            country = lead.get('location_country', 'Unknown')
            countries[country] = countries.get(country, 0) + 1
        
        # Score distribution
        high_score = len([l for l in leads if l['lead_score'] >= 80])
        medium_score = len([l for l in leads if 60 <= l['lead_score'] < 80])
        
        print(f"\n{'='*60}")
        print("COLLECTION SUMMARY REPORT")
        print(f"{'='*60}")
        print(f"Total Premium Marketing Agencies: {total_leads}")
        print(f"Average Lead Score: {avg_score:.1f}")
        print(f"High-Quality Leads (80+): {high_score}")
        print(f"Medium-Quality Leads (60-79): {medium_score}")
        print(f"API Calls Used: {self.total_calls}")
        
        print(f"\nTop Industries:")
        for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {industry}: {count} leads")
        
        print(f"\nCountry Distribution:")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count} leads")
        
        print(f"\nSUCCESS: Data ready for email enrichment and outreach campaigns")


def main():
    """Main execution function"""
    api_key = "vSJb2-hxp_tbdxy7K8tvgw"
    
    print("Apollo Lead Collector for Premium Marketing Agencies")
    print("=" * 60)
    
    collector = ApolloLeadCollector(api_key)
    
    # Test connection
    if not collector.test_connection():
        print("Failed to connect to Apollo API. Please check your API key.")
        return
    
    # Collect leads
    target_count = 500  # Aim for 500 total, filter for quality
    high_quality_leads = collector.collect_leads(target_count)
    
    # Export results
    if high_quality_leads:
        csv_file = collector.export_to_csv(high_quality_leads)
        collector.generate_summary_report(high_quality_leads)
    else:
        print("No high-quality leads found with current criteria.")
    
    print(f"\nSUCCESS: Lead collection completed successfully!")


if __name__ == "__main__":
    main()