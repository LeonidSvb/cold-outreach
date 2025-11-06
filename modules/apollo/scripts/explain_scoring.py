#!/usr/bin/env python3
"""
Explain ICP scoring logic with examples
"""

import pandas as pd
import json

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_processed_20251103_143944.csv')

print("="*100)
print("ICP SCORING LOGIC EXPLANATION")
print("="*100)

print("\n### SCORING CRITERIA ###\n")
print("I analyzed these fields for EACH company:")
print("  1. company_name - company name")
print("  2. title - job title of the contact")
print("  3. industry - industry classification")
print("  4. keywords - Apollo keywords (most important!)")
print("  5. headline - professional headline")
print("\n")

print("### PERFECT MATCH (Score = 2) - Indicators ###")
print("Must contain ONE of these in ANY field:")
perfect_indicators = [
    'call center', 'contact center', 'customer service center',
    'telemarketing', 'outbound call', 'inbound call',
    'bpo', 'call centre', 'telefundraising',
    'outbound sales', 'telesales', 'phone sales',
    'call operations', 'dialer', 'predictive dialing'
]
for ind in perfect_indicators:
    print(f"  - '{ind}'")

print("\n### MAYBE MATCH (Score = 1) - Indicators ###")
maybe_indicators = [
    'customer support', 'customer service', 'customer experience',
    'sales calls', 'phone support', 'technical support',
    'help desk', 'customer success', 'lead generation',
    'appointment setting', 'cold calling', 'outsourcing',
    'offshoring', 'telecommunications'
]
for ind in maybe_indicators:
    print(f"  - '{ind}'")

print("\n### SPECIAL: Industry = 'outsourcing/offshoring' -> Automatic Score 2 ###")

print("\n" + "="*100)
print("EXAMPLES - PERFECT MATCHES (Score = 2)")
print("="*100)

perfect = df[df['ICP Match Score'] == 2].head(5)
for idx, row in perfect.iterrows():
    company = row['company_name']
    industry = row['industry']
    title = row['title']
    keywords_raw = row['keywords']

    # Parse keywords
    try:
        keywords = json.loads(keywords_raw) if isinstance(keywords_raw, str) and keywords_raw.startswith('[') else []
    except:
        keywords = []

    print(f"\n{idx+1}. COMPANY: {company}")
    print(f"   Industry: {industry}")
    print(f"   Contact Title: {title}")
    print(f"   Keywords: {keywords[:5] if len(keywords) > 0 else 'None'}")

    # Explain why score = 2
    combined = f"{company} {industry} {title} {keywords_raw}".lower()
    found_indicators = []
    for indicator in perfect_indicators:
        if indicator in combined:
            found_indicators.append(indicator)

    if industry == 'outsourcing/offshoring':
        print(f"   [MATCHED] Industry = 'outsourcing/offshoring' (automatic perfect match)")

    if found_indicators:
        print(f"   [MATCHED] Found indicators: {found_indicators[:3]}")

    print(f"   >> Score: 2 (PERFECT - High call volume likely)")

print("\n" + "="*100)
print("EXAMPLES - MAYBE MATCHES (Score = 1)")
print("="*100)

maybe = df[df['ICP Match Score'] == 1].head(5)
for idx, row in maybe.iterrows():
    company = row['company_name']
    industry = row['industry']
    title = row['title']
    keywords_raw = row['keywords']

    try:
        keywords = json.loads(keywords_raw) if isinstance(keywords_raw, str) and keywords_raw.startswith('[') else []
    except:
        keywords = []

    print(f"\n{idx+1}. COMPANY: {company}")
    print(f"   Industry: {industry}")
    print(f"   Contact Title: {title}")
    print(f"   Keywords: {keywords[:5] if len(keywords) > 0 else 'None'}")

    # Explain why score = 1
    combined = f"{company} {industry} {title} {keywords_raw}".lower()
    found_indicators = []
    for indicator in maybe_indicators:
        if indicator in combined:
            found_indicators.append(indicator)

    if found_indicators:
        print(f"   [MAYBE] Found indicators: {found_indicators[:3]}")

    print(f"   >> Score: 1 (MAYBE - Some customer calls, but unclear volume)")

print("\n" + "="*100)
print("EXAMPLES - NO MATCH (Score = 0)")
print("="*100)

no_match = df[df['ICP Match Score'] == 0].head(5)
for idx, row in no_match.iterrows():
    company = row['company_name']
    industry = row['industry']
    title = row['title']
    keywords_raw = row['keywords']

    try:
        keywords = json.loads(keywords_raw) if isinstance(keywords_raw, str) and keywords_raw.startswith('[') else []
    except:
        keywords = []

    print(f"\n{idx+1}. COMPANY: {company}")
    print(f"   Industry: {industry}")
    print(f"   Contact Title: {title}")
    print(f"   Keywords: {keywords[:5] if len(keywords) > 0 else 'None'}")

    print(f"   [NO MATCH] No call center indicators found")
    print(f"   >> Score: 0 (NOT A FIT - Not a call center)")

print("\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"Total analyzed: {len(df)} companies")
print(f"Perfect (2): {len(df[df['ICP Match Score']==2])} - Call centers with high call volume")
print(f"Maybe (1): {len(df[df['ICP Match Score']==1])} - Some calling activity, unclear volume")
print(f"No match (0): {len(df[df['ICP Match Score']==0])} - Not call centers")
