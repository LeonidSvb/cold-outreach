#!/usr/bin/env python3
"""
Check ALL Canadian sites for HTTP suitability
"""

import sys
import pandas as pd
import json
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent / "core" / "modules" / "scraping_router"))

from function import check_http_suitability

def load_all_canadian_sites():
    """Load all sites from CSV"""
    csv_path = Path(__file__).parent / "leads" / "raw" / "lumid_canada_20250108.csv"
    
    print(f"Loading all companies from: {csv_path}")
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return []
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} total companies")
    
    # Extract ALL companies with valid websites
    urls = []
    companies = []
    
    for _, row in df.iterrows():
        website = row.get('company_url', '')
        company_name = row.get('company_name', '')
        
        if website and isinstance(website, str) and website.strip() != '':
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website.strip()
            urls.append(website)
            companies.append({
                'company_name': company_name,
                'website': website
            })
    
    print(f"Extracted {len(urls)} valid URLs for checking")
    return urls, companies

def main():
    print("="*60)
    print("CHECKING ALL CANADIAN SITES FOR HTTP SUITABILITY")
    print("="*60)
    
    # Load ALL URLs
    urls, companies = load_all_canadian_sites()
    
    if not urls:
        print("No URLs to check")
        return
    
    print(f"\nChecking {len(urls)} Canadian company websites...")
    
    # Check all sites (this will take time)
    results = check_http_suitability(urls)
    
    # Combine with company info
    combined_results = []
    for i, result in enumerate(results):
        combined_result = result.copy()
        if i < len(companies):
            combined_result['company_name'] = companies[i]['company_name']
        combined_results.append(combined_result)
    
    # Save detailed results
    output_file = Path(__file__).parent / "data" / "output" / "all_sites_http_check.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, indent=2)
    
    # Generate summary
    http_suitable = [r for r in results if r['http_suitable']]
    needs_apify = [r for r in results if r['needs_apify']]
    errors = [r for r in results if r.get('error')]
    
    print("\n" + "="*60)
    print("FINAL RESULTS - ALL CANADIAN SITES")
    print("="*60)
    print(f"Total sites checked: {len(results)}")
    print(f"HTTP suitable: {len(http_suitable)} ({len(http_suitable)/len(results)*100:.1f}%)")
    print(f"Needs Apify: {len(needs_apify)} ({len(needs_apify)/len(results)*100:.1f}%)")
    print(f"Errors: {len(errors)} ({len(errors)/len(results)*100:.1f}%)")
    
    # Cost analysis for full dataset
    apify_cost_per_site = 0.002
    http_cost_per_site = 0.0001
    
    full_apify_cost = len(results) * apify_cost_per_site
    hybrid_cost = (len(http_suitable) * http_cost_per_site) + (len(needs_apify) * apify_cost_per_site)
    savings = full_apify_cost - hybrid_cost
    
    print(f"\nCOST ANALYSIS ({len(results)} sites):")
    print(f"Full Apify: ${full_apify_cost:.2f}")
    print(f"Hybrid: ${hybrid_cost:.2f}")
    print(f"Savings: ${savings:.2f} ({savings/full_apify_cost*100:.1f}%)")
    
    # Show some examples
    print(f"\nHTTP SUITABLE EXAMPLES:")
    for result in http_suitable[:5]:
        company_name = next((c['company_name'] for c in companies if c['website'] == result['url']), 'Unknown')
        print(f"  - {company_name}: {result['url']}")
    
    print(f"\nNEEDS APIFY EXAMPLES:")
    for result in needs_apify[:5]:
        company_name = next((c['company_name'] for c in companies if c['website'] == result['url']), 'Unknown')
        print(f"  - {company_name}: {result['url']}")
    
    print(f"\nResults saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()