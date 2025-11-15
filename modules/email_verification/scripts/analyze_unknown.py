#!/usr/bin/env python3
"""Quick analysis of unknown emails"""
import pandas as pd

df = pd.read_csv(
    r'C:\Users\79818\Desktop\Outreach - new\modules\email_verification\results\museum_emails_VERIFIED_FULL_20251115_172422.csv',
    encoding='utf-8'
)

unknown = df[df['result'] == 'unknown']
unknown_60plus = unknown[unknown['score'] >= 60]
unknown_80plus = unknown[unknown['score'] >= 80]

print(f"Total unknown: {len(unknown)}")
print(f"Unknown with score 60+: {len(unknown_60plus)} ({len(unknown_60plus)/len(unknown)*100:.1f}%)")
print(f"Unknown with score 80+: {len(unknown_80plus)} ({len(unknown_80plus)/len(unknown)*100:.1f}%)")
print()

if len(unknown_60plus) > 0:
    print("HIGH-SCORE UNKNOWN EMAILS (60+):")
    print("=" * 80)
    for idx, row in unknown_60plus.head(15).iterrows():
        name = row['name'][:35] if len(row['name']) > 35 else row['name']
        email = row['email']
        score = row['score']
        print(f"{name:35} | {email:40} | {score}")
    print()

# Breakdown by score ranges
print("\nSCORE DISTRIBUTION:")
print(f"  80-100: {len(unknown[unknown['score'] >= 80])}")
print(f"  60-79:  {len(unknown[(unknown['score'] >= 60) & (unknown['score'] < 80)])}")
print(f"  40-59:  {len(unknown[(unknown['score'] >= 40) & (unknown['score'] < 60)])}")
print(f"  20-39:  {len(unknown[(unknown['score'] >= 20) & (unknown['score'] < 40)])}")
print(f"  0-19:   {len(unknown[unknown['score'] < 20])}")
