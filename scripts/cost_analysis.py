#!/usr/bin/env python3
"""Cost analysis for different scraping strategies"""

print('=== COST ANALYSIS FOR 5000 HVAC COMPANIES ===\n')

# Apify pricing (estimated from tests)
pricing = {
    'basic_gmaps': 0.001,      # per company (just data, no emails)
    'contact_gmaps': 0.002,    # per company (with email extraction)
}

target = 5000

print('OPTION 1: Only Google Maps Contact Actor')
print('=' * 50)
cost1 = target * pricing['contact_gmaps']
emails1 = int(target * 0.67)
print(f'  Cost: ${cost1:.2f}')
print(f'  Expected emails: {emails1} (67%)')
print(f'  Cost per email: ${cost1/emails1:.3f}')
print(f'  Complexity: LOW (1 script)')
print(f'  Quality: HIGH (clean emails)')
print()

print('OPTION 2: Basic GMaps + HTTP Scraping')
print('=' * 50)
cost2_gmaps = target * pricing['basic_gmaps']
cost2_http = 0  # free
cost2_total = cost2_gmaps + cost2_http
emails2 = int(target * 0.25)  # 25% from HTTP
print(f'  Cost: ${cost2_total:.2f} (GMaps: ${cost2_gmaps:.2f}, HTTP: $0)')
print(f'  Expected emails: {emails2} (25%)')
print(f'  Cost per email: ${cost2_total/emails2:.3f}')
print(f'  Complexity: MEDIUM (2 modules)')
print(f'  Quality: MEDIUM (some dirty emails)')
print()

print('OPTION 3: Basic GMaps + HTTP + Contact fallback (HYBRID)')
print('=' * 50)
cost3_gmaps = target * pricing['basic_gmaps']
emails_from_http = int(target * 0.25)
remaining = target - emails_from_http
cost3_contact = remaining * pricing['contact_gmaps']
cost3_total = cost3_gmaps + cost3_contact
emails3_http = emails_from_http
emails3_gmaps = int(remaining * 0.67)
emails3_total = emails3_http + emails3_gmaps
print(f'  Cost: ${cost3_total:.2f}')
print(f'    Basic GMaps: ${cost3_gmaps:.2f}')
print(f'    Contact Actor: ${cost3_contact:.2f}')
print(f'  Expected emails:')
print(f'    From HTTP: {emails3_http} (25%)')
print(f'    From Contact Actor: {emails3_gmaps} (67% of {remaining})')
print(f'    TOTAL: {emails3_total} ({emails3_total/target*100:.0f}%)')
print(f'  Cost per email: ${cost3_total/emails3_total:.3f}')
print(f'  Complexity: HIGH (3 modules + orchestrator)')
print(f'  Quality: HIGH')
print()

print('RECOMMENDATION:')
print('=' * 50)
print('OPTION 1 is BEST if:')
print('  - You want simplicity (1 script, run and forget)')
print('  - Quality > Cost')
print(f'  - ${cost1:.2f} is acceptable budget')
print()
print('OPTION 3 is BEST if:')
print('  - You want max emails at lower cost')
print('  - You have time for development')
print(f'  - Same result ({emails3_total} emails) for ${cost3_total:.2f}')
print()
print(f'SAVINGS: Option 3 saves ${cost1 - cost3_total:.2f} ({(cost1-cost3_total)/cost1*100:.0f}%)')
print()
print('MY RECOMMENDATION: OPTION 1')
print('=' * 50)
print('Why? Because:')
print('  1. Saves your TIME (most valuable)')
print('  2. Higher quality data (clean emails)')
print('  3. Simpler to maintain and reuse')
print('  4. $10 is cheap for 3350 quality leads')
print('  5. You can start outreach TODAY')
print()
print('Option 3 saves $2.50 but requires:')
print('  - 4-6 hours development')
print('  - Debugging and testing')
print('  - More complex codebase')
print('  - NOT worth it for $2.50 savings!')
