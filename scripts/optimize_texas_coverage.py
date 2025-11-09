#!/usr/bin/env python3
"""
Analyze optimal Texas city coverage to minimize duplicates and costs
"""

# Texas cities by size (population & HVAC market)
TEXAS_CITIES_BY_SIZE = {
    "tier_1": {  # Major metros (600-800 HVAC companies)
        "cities": [
            ("Houston", "TX"),
            ("Dallas", "TX"),
            ("San Antonio", "TX"),
            ("Austin", "TX")
        ],
        "avg_hvac_companies": 700,
        "duplicate_risk": "Low (10-15%)"  # Only chains
    },
    "tier_2": {  # Large cities (400-600 companies)
        "cities": [
            ("Fort Worth", "TX"),
            ("El Paso", "TX"),
            ("Arlington", "TX"),
            ("Plano", "TX")
        ],
        "avg_hvac_companies": 500,
        "duplicate_risk": "Low (5-10%)"
    },
    "tier_3": {  # Medium cities (200-400 companies)
        "cities": [
            ("Corpus Christi", "TX"),
            ("Laredo", "TX"),
            ("Lubbock", "TX"),
            ("Irving", "TX"),
            ("Garland", "TX"),
            ("Frisco", "TX")
        ],
        "avg_hvac_companies": 300,
        "duplicate_risk": "Very Low (<5%)"
    }
}

def calculate_strategy(budget_dollars: float, target_emails: int):
    """Calculate optimal city selection for budget and target"""

    cost_per_result = 0.006  # $6 per 1000 with contact enrichment
    email_success_rate = 0.67
    dedup_loss = 0.10  # 10% duplicates
    quality_filter_loss = 0.20  # 20% filtered out (no website, <5 reviews)

    print(f"=== TEXAS HVAC OPTIMIZATION ===\n")
    print(f"Target: {target_emails} emails")
    print(f"Budget: ${budget_dollars:.2f}")
    print(f"Cost per result: ${cost_per_result:.4f}\n")

    # Calculate raw results needed
    results_after_filters = target_emails / email_success_rate
    results_after_dedup = results_after_filters / (1 - dedup_loss)
    raw_results_needed = results_after_dedup / (1 - quality_filter_loss)

    print(f"Calculation:")
    print(f"  Need {target_emails} emails")
    print(f"  ÷ 67% email rate = {results_after_filters:.0f} quality results")
    print(f"  ÷ 90% after dedup = {results_after_dedup:.0f} with duplicates")
    print(f"  ÷ 80% after filter = {raw_results_needed:.0f} raw results needed\n")

    total_cost = raw_results_needed * cost_per_result

    print(f"Cost: {raw_results_needed:.0f} × ${cost_per_result:.4f} = ${total_cost:.2f}\n")

    # Recommend city distribution
    print(f"RECOMMENDED CITY DISTRIBUTION:\n")

    tier1_cities = TEXAS_CITIES_BY_SIZE["tier_1"]
    tier2_cities = TEXAS_CITIES_BY_SIZE["tier_2"]
    tier3_cities = TEXAS_CITIES_BY_SIZE["tier_3"]

    # Strategy: Start with Tier 1 (best ROI), then Tier 2, then Tier 3

    results_budget = raw_results_needed
    total_cities = 0

    # Tier 1
    tier1_count = min(len(tier1_cities["cities"]), int(results_budget / tier1_cities["avg_hvac_companies"]))
    tier1_results = tier1_count * tier1_cities["avg_hvac_companies"]
    results_budget -= tier1_results
    total_cities += tier1_count

    print(f"Tier 1 (Major metros):")
    print(f"  Cities: {tier1_count} × {tier1_cities['avg_hvac_companies']} avg = {tier1_results:.0f} results")
    print(f"  {tier1_cities['cities'][:tier1_count]}")
    print(f"  Duplicate risk: {tier1_cities['duplicate_risk']}\n")

    # Tier 2
    if results_budget > 0:
        tier2_count = min(len(tier2_cities["cities"]), int(results_budget / tier2_cities["avg_hvac_companies"]))
        tier2_results = tier2_count * tier2_cities["avg_hvac_companies"]
        results_budget -= tier2_results
        total_cities += tier2_count

        print(f"Tier 2 (Large cities):")
        print(f"  Cities: {tier2_count} × {tier2_cities['avg_hvac_companies']} avg = {tier2_results:.0f} results")
        print(f"  {tier2_cities['cities'][:tier2_count]}")
        print(f"  Duplicate risk: {tier2_cities['duplicate_risk']}\n")

    # Tier 3
    if results_budget > 0:
        tier3_count = min(len(tier3_cities["cities"]), int(results_budget / tier3_cities["avg_hvac_companies"]))
        tier3_results = tier3_count * tier3_cities["avg_hvac_companies"]
        total_cities += tier3_count

        print(f"Tier 3 (Medium cities):")
        print(f"  Cities: {tier3_count} × {tier3_cities['avg_hvac_companies']} avg = {tier3_results:.0f} results")
        print(f"  {tier3_cities['cities'][:tier3_count]}")
        print(f"  Duplicate risk: {tier3_cities['duplicate_risk']}\n")

    print(f"{'='*60}")
    print(f"TOTAL: {total_cities} cities")
    print(f"Expected raw results: {raw_results_needed:.0f}")
    print(f"After filters & dedup: {target_emails:.0f} emails")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"{'='*60}\n")

# Run calculations for different scenarios
print("\n" + "="*60)
print("SCENARIO 1: MEDIUM RUN (1500 emails, ~$12)")
print("="*60 + "\n")
calculate_strategy(12.00, 1500)

print("\n" + "="*60)
print("SCENARIO 2: FULL RUN (3500 emails, ~$36)")
print("="*60 + "\n")
calculate_strategy(36.00, 3500)

print("\n" + "="*60)
print("SCENARIO 3: EXTENDED (5000 emails, ~$52)")
print("="*60 + "\n")
calculate_strategy(52.00, 5000)

print("\n" + "="*60)
print("KEY INSIGHTS:")
print("="*60)
print("""
1. Use CITY-SPECIFIC searches (not "HVAC Texas")
   - Minimizes overlapping results
   - Each city is independent market

2. Use SINGLE search term per city
   - "HVAC contractors {city}"
   - DON'T add "AC repair", "heating" etc (same companies!)

3. Avoid OVERLAPPING cities
   - Dallas ✅
   - Dallas-Fort Worth metro ❌ (overlaps with Dallas)
   - Fort Worth ✅ (different city)

4. DEDUPLICATION strategy
   - By place_id (Google's unique ID)
   - By phone number (same business)
   - By website domain (same company)

5. Expected duplicates: 10-15%
   - Chain locations (Aire Serv, One Hour, etc)
   - Companies serving multiple cities
   - THIS IS NORMAL - we filter them out

6. Cost optimization
   - Filter "only with website" (saves 20%)
   - Filter "min 5 reviews" (saves 15%)
   - Total savings: ~30-35%
""")
