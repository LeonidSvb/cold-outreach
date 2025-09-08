#!/usr/bin/env python3
"""
Debug script to inspect Apollo API response structure
"""

import requests
import json
from pprint import pprint

def debug_apollo_response():
    api_key = "vSJb2-hxp_tbdxy7K8tvgw"
    base_url = "https://api.apollo.io/v1"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    # Simple search payload
    search_payload = {
        "page": 1,
        "per_page": 5,  # Just get a few to inspect
        "organization_locations": ["United States"],
        "organization_num_employees_ranges": ["11,20", "21,50"],
        "q_organization_keyword_tags": ["marketing agency"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/organizations/search",
            headers=headers,
            json=search_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get('organizations', [])
            
            if organizations:
                print("="*80)
                print("SAMPLE ORGANIZATION DATA STRUCTURE")
                print("="*80)
                
                # Print first organization structure
                sample_org = organizations[0]
                print(f"\nFirst organization keys:")
                print(list(sample_org.keys()))
                
                print(f"\nFirst organization sample data:")
                pprint(sample_org, width=100, depth=3)
                
                # Check specific fields we're using in scoring
                print(f"\n" + "="*50)
                print("SCORING FIELD ANALYSIS")
                print("="*50)
                
                for i, org in enumerate(organizations[:3]):
                    print(f"\nOrganization {i+1}: {org.get('name', 'Unknown')}")
                    print(f"  num_employees: {org.get('num_employees', 'N/A')}")
                    print(f"  estimated_annual_revenue: {org.get('estimated_annual_revenue', 'N/A')}")
                    print(f"  industry: {org.get('industry', 'N/A')}")
                    print(f"  founded_year: {org.get('founded_year', 'N/A')}")
                    print(f"  location: {org.get('location', 'N/A')}")
                    print(f"  keywords: {org.get('keywords', 'N/A')}")
                    print(f"  technologies: {org.get('technologies', 'N/A')}")
                    
        else:
            print(f"API Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_apollo_response()