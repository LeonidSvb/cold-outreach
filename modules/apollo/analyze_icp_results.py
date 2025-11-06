#!/usr/bin/env python3
"""
Quick analysis of ICP validation results
"""

import pandas as pd
from pathlib import Path

# Read processed file
file_path = Path(__file__).parent.parent.parent / "data" / "processed" / "apollo_call_centers_processed_20251103_145938.csv"
df = pd.read_csv(file_path)

print("\n" + "=" * 70)
print("DETAILED ICP ANALYSIS REPORT")
print("=" * 70)

# Overall stats
print(f"\nTOTAL RECORDS: {len(df)}")
print(f"\nICP SCORE DISTRIBUTION:")
for score in [2, 1, 0]:
    count = len(df[df['icp_score'] == score])
    pct = (count / len(df)) * 100
    print(f"  Score {score}: {count} companies ({pct:.1f}%)")

# Perfect fit companies (score 2)
print(f"\n" + "-" * 70)
print(f"PERFECT FIT COMPANIES (Score 2): {len(df[df['icp_score'] == 2])}")
print("-" * 70)

perfect = df[df['icp_score'] == 2]
print(f"\nTop industries:")
top_industries = perfect['industry'].value_counts().head(10)
for industry, count in top_industries.items():
    print(f"  {industry}: {count} companies")

print(f"\nTop locations:")
top_locations = perfect['normalized_location'].value_counts().head(10)
for loc, count in top_locations.items():
    print(f"  {loc}: {count} companies")

print(f"\nEmployee count distribution:")
print(f"  10-25: {len(perfect[perfect['estimated_num_employees'] <= 25])} companies")
print(f"  26-50: {len(perfect[(perfect['estimated_num_employees'] > 25) & (perfect['estimated_num_employees'] <= 50)])} companies")
print(f"  51-75: {len(perfect[(perfect['estimated_num_employees'] > 50) & (perfect['estimated_num_employees'] <= 75)])} companies")
print(f"  76-100: {len(perfect[(perfect['estimated_num_employees'] > 75) & (perfect['estimated_num_employees'] <= 100)])} companies")

# Maybe fit companies (score 1)
print(f"\n" + "-" * 70)
print(f"MAYBE FIT COMPANIES (Score 1): {len(df[df['icp_score'] == 1])}")
print("-" * 70)

maybe = df[df['icp_score'] == 1]
print(f"\nTop industries:")
top_industries_maybe = maybe['industry'].value_counts().head(10)
for industry, count in top_industries_maybe.items():
    print(f"  {industry}: {count} companies")

print(f"\nEmployee count distribution:")
print(f"  10-25: {len(maybe[maybe['estimated_num_employees'] <= 25])} companies")
print(f"  26-50: {len(maybe[(maybe['estimated_num_employees'] > 25) & (maybe['estimated_num_employees'] <= 50)])} companies")
print(f"  51-75: {len(maybe[(maybe['estimated_num_employees'] > 50) & (maybe['estimated_num_employees'] <= 75)])} companies")
print(f"  76-100: {len(maybe[(maybe['estimated_num_employees'] > 75) & (maybe['estimated_num_employees'] <= 100)])} companies")
print(f"  100+: {len(maybe[maybe['estimated_num_employees'] > 100])} companies")

# Not a fit companies (score 0)
print(f"\n" + "-" * 70)
print(f"NOT A FIT COMPANIES (Score 0): {len(df[df['icp_score'] == 0])}")
print("-" * 70)

no_fit = df[df['icp_score'] == 0]
print(f"\nReasons for filtering (top industries):")
top_industries_no = no_fit['industry'].value_counts().head(10)
for industry, count in top_industries_no.items():
    print(f"  {industry}: {count} companies")

print(f"\nEmployee count distribution:")
print(f"  0-9: {len(no_fit[no_fit['estimated_num_employees'] < 10])} companies (too small)")
print(f"  10+: {len(no_fit[no_fit['estimated_num_employees'] >= 10])} companies (wrong industry)")

# Seniority analysis
print(f"\n" + "-" * 70)
print(f"SENIORITY ANALYSIS (All companies)")
print("-" * 70)
print(f"\nSeniority distribution:")
seniority_dist = df['seniority'].value_counts()
for seniority, count in seniority_dist.items():
    print(f"  {seniority}: {count} contacts")

# Country distribution
print(f"\n" + "-" * 70)
print(f"COUNTRY DISTRIBUTION")
print("-" * 70)
country_dist = df['country'].value_counts()
for country, count in country_dist.items():
    print(f"  {country}: {count} contacts")

# Recommendations
print(f"\n" + "=" * 70)
print(f"RECOMMENDATIONS")
print("=" * 70)
print(f"""
1. IMMEDIATE OUTREACH (208 companies, score 2):
   - Clear call center/outsourcing/customer service focus
   - Right employee count (10-100)
   - High conversion probability

2. SECONDARY OUTREACH (1,460 companies, score 1):
   - Possible call center fit but less obvious
   - May include customer service departments within larger orgs
   - Worth qualifying with targeted messaging
   - Filter further by specific keywords or titles if needed

3. EXCLUDED (104 companies, score 0):
   - Too small (<10 employees)
   - Wrong industry focus
   - Not recommended for this campaign

NEXT STEPS:
- Start with score 2 companies for highest ROI
- Test messaging with small batch (20-30 contacts)
- If response rate is good, expand to score 1 companies
- Consider further segmentation by industry or location
""")

print("=" * 70)
