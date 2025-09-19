#!/usr/bin/env python3
"""
Hybrid Scraping Analysis - Test 100 Canadian domains
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent / "core" / "modules" / "_shared"))
sys.path.append(str(Path(__file__).parent / "core" / "modules" / "site_analyzer"))

from function import analyze_multiple_sites

def load_canadian_companies(limit=20):
    """Load Canadian companies from CSV"""
    csv_path = Path(__file__).parent / "leads" / "raw" / "lumid_canada_20250108.csv"
    
    print(f"Loading companies from: {csv_path}")
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return []
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} total companies")
    
    # Extract first 100 companies with valid websites
    urls = []
    for _, row in df.head(limit).iterrows():
        website = row.get('company_url', row.get('website', row.get('Website', '')))
        if website and isinstance(website, str) and website != '':
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            urls.append(website)
    
    print(f"Extracted {len(urls)} valid URLs for analysis")
    return urls

def main():
    print("=== HYBRID SCRAPING ANALYSIS ===")
    print("Testing 100 Canadian domains for optimal scraping method")
    print("-" * 60)
    
    # Load URLs
    urls = load_canadian_companies(20)
    
    if not urls:
        print("No URLs to analyze")
        return
    
    # Analyze all sites
    print(f"\nAnalyzing {len(urls)} domains...")
    results = analyze_multiple_sites(urls)
    
    # Generate analysis report
    http_suitable = []
    apify_needed = []
    errors = []
    
    for result in results:
        method = result.get('scraping_method', 'unknown')
        if method == 'http':
            http_suitable.append(result)
        elif method == 'apify':
            apify_needed.append(result)
        elif 'error' in result:
            errors.append(result)
    
    # Save detailed results
    output_file = Path(__file__).parent / "data" / "input" / "hybrid_analysis_results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    analysis_data = {
        "total_analyzed": len(results),
        "http_suitable": len(http_suitable),
        "apify_needed": len(apify_needed),
        "errors": len(errors),
        "http_percentage": (len(http_suitable) / len(results)) * 100,
        "apify_percentage": (len(apify_needed) / len(results)) * 100,
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2)
    
    # Print summary report
    print("\n" + "="*60)
    print("HYBRID SCRAPING ANALYSIS RESULTS")
    print("="*60)
    print(f"Total domains analyzed: {len(results)}")
    print(f"HTTP suitable: {len(http_suitable)} ({(len(http_suitable)/len(results)*100):.1f}%)")
    print(f"Apify needed: {len(apify_needed)} ({(len(apify_needed)/len(results)*100):.1f}%)")
    print(f"Errors: {len(errors)} ({(len(errors)/len(results)*100):.1f}%)")
    
    # Cost analysis
    apify_cost_per_domain = 0.002  # $0.002 based on previous test
    http_cost_per_domain = 0.0001  # Minimal HTTP cost
    
    total_cost_full_apify = len(results) * apify_cost_per_domain
    total_cost_hybrid = (len(http_suitable) * http_cost_per_domain) + (len(apify_needed) * apify_cost_per_domain)
    cost_savings = total_cost_full_apify - total_cost_hybrid
    
    print(f"\nCOST ANALYSIS:")
    print(f"Full Apify approach: ${total_cost_full_apify:.3f}")
    print(f"Hybrid approach: ${total_cost_hybrid:.3f}")
    print(f"Cost savings: ${cost_savings:.3f} ({(cost_savings/total_cost_full_apify*100):.1f}%)")
    
    # Scaling to 750 companies
    scaling_factor = 750 / len(results)
    scaled_full_apify = total_cost_full_apify * scaling_factor
    scaled_hybrid = total_cost_hybrid * scaling_factor
    scaled_savings = scaled_full_apify - scaled_hybrid
    
    print(f"\nSCALED TO 750 COMPANIES:")
    print(f"Full Apify: ${scaled_full_apify:.2f}")
    print(f"Hybrid: ${scaled_hybrid:.2f}")
    print(f"Savings: ${scaled_savings:.2f}")
    
    print(f"\nDetailed results saved to: {output_file}")
    
    return analysis_data

if __name__ == "__main__":
    main()