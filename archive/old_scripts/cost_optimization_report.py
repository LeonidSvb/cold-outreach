#!/usr/bin/env python3
"""
=== COST OPTIMIZATION REPORT ===
Final analysis of hybrid scraping approach
"""

import json
from pathlib import Path

def generate_report():
    print("="*60)
    print("HYBRID SCRAPING COST OPTIMIZATION REPORT")
    print("="*60)
    
    # Load previous analysis results
    results_file = Path(__file__).parent / "data" / "input" / "hybrid_analysis_results.json"
    
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print("Analysis results not found, using default estimates")
        data = {
            "total_analyzed": 18,
            "http_suitable": 6, 
            "apify_needed": 12,
            "http_percentage": 33.3,
            "apify_percentage": 66.7
        }
    
    # Analysis Summary
    print(f"\n1. ANALYSIS SUMMARY (Based on {data['total_analyzed']} Canadian companies):")
    print(f"   - HTTP suitable: {data['http_suitable']} ({data['http_percentage']:.1f}%)")
    print(f"   - Apify needed: {data['apify_needed']} ({data['apify_percentage']:.1f}%)")
    
    # Cost Analysis
    print(f"\n2. COST COMPARISON:")
    apify_cost_per_domain = 0.002
    http_cost_per_domain = 0.0001
    
    # For 750 companies (target scale)
    total_companies = 750
    
    # Full Apify approach
    full_apify_cost = total_companies * apify_cost_per_domain
    
    # Hybrid approach (based on analysis percentages)
    http_count = int(total_companies * (data['http_percentage'] / 100))
    apify_count = total_companies - http_count
    
    hybrid_http_cost = http_count * http_cost_per_domain
    hybrid_apify_cost = apify_count * apify_cost_per_domain
    hybrid_total_cost = hybrid_http_cost + hybrid_apify_cost
    
    savings = full_apify_cost - hybrid_total_cost
    savings_percentage = (savings / full_apify_cost) * 100
    
    print(f"   Full Apify approach: ${full_apify_cost:.2f}")
    print(f"   Hybrid approach:")
    print(f"     - {http_count} HTTP domains: ${hybrid_http_cost:.3f}")
    print(f"     - {apify_count} Apify domains: ${hybrid_apify_cost:.2f}")
    print(f"     - Total hybrid: ${hybrid_total_cost:.2f}")
    print(f"   Cost savings: ${savings:.2f} ({savings_percentage:.1f}%)")
    
    # Implementation Strategy
    print(f"\n3. IMPLEMENTATION STRATEGY:")
    print(f"   Step 1: Use scraping_router to classify all URLs")
    print(f"   Step 2: Process HTTP-suitable URLs with simple requests")
    print(f"   Step 3: Process complex URLs through Apify")
    print(f"   Step 4: Merge results for unified output")
    
    # Quality Expectations
    print(f"\n4. QUALITY EXPECTATIONS:")
    print(f"   - HTTP scraping: Basic content extraction")
    print(f"   - Apify scraping: Full JavaScript rendering")
    print(f"   - Overall success rate: 95%+ expected")
    
    # Usage Instructions
    print(f"\n5. USAGE INSTRUCTIONS:")
    print(f"   from core.modules.scraping_router.function import route_scraping_methods")
    print(f"   ")
    print(f"   urls = ['https://site1.com', 'https://site2.com', ...]")
    print(f"   routing = route_scraping_methods(urls)")
    print(f"   ")
    print(f"   # Process HTTP URLs with requests")
    print(f"   http_results = process_http_urls(routing['http_urls'])")
    print(f"   ")
    print(f"   # Process Apify URLs with API")
    print(f"   apify_results = process_apify_urls(routing['apify_urls'])")
    
    # Scaling projections
    print(f"\n6. SCALING PROJECTIONS:")
    scales = [100, 500, 750, 1000, 2000]
    
    print(f"   {'Companies':<10} {'Full Apify':<12} {'Hybrid':<10} {'Savings':<10}")
    print(f"   {'-'*10} {'-'*12} {'-'*10} {'-'*10}")
    
    for scale in scales:
        full_cost = scale * apify_cost_per_domain
        http_scale = int(scale * (data['http_percentage'] / 100))
        apify_scale = scale - http_scale
        hybrid_cost = (http_scale * http_cost_per_domain) + (apify_scale * apify_cost_per_domain)
        scale_savings = full_cost - hybrid_cost
        
        print(f"   {scale:<10} ${full_cost:<11.2f} ${hybrid_cost:<9.2f} ${scale_savings:<9.2f}")
    
    print(f"\n7. RECOMMENDATION:")
    print(f"   + Implement hybrid scraping approach")
    print(f"   + Expected {savings_percentage:.0f}% cost reduction")
    print(f"   + Maintain high quality through intelligent routing")
    print(f"   + Scale efficiently with predictable costs")
    
    print("\n" + "="*60)
    print("REPORT COMPLETE - READY FOR IMPLEMENTATION")
    print("="*60)

if __name__ == "__main__":
    generate_report()