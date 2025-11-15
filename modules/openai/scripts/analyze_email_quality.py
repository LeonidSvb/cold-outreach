#!/usr/bin/env python3
"""
Email Quality Analyzer - Find broken/invalid emails in database
"""

import pandas as pd
import re
from pathlib import Path
from collections import defaultdict

# Load museums data
csv_path = Path(r"C:\Users\79818\Downloads\Soviet Boots - Sheet3.csv")
df = pd.read_csv(csv_path)

# Email validation patterns
VALID_EMAIL_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9._-]*@[a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
SUSPICIOUS_PATTERNS = {
    'has_phone': r'\d{6,}',  # 6+ consecutive digits (likely phone number)
    'has_space': r'\s',
    'double_domain': r'@.*@',
    'missing_tld': r'@[^.]+$',
    'weird_chars': r'[^\w@.\-+]',
    'ends_weird': r'\.[a-z]{4,}$',  # TLD longer than 3 chars (e.g., .debis)
    'multiple_dots_before_at': r'\.\.+.*@',
    'starts_with_digit_sequence': r'^[\d\-]+[a-z]',  # starts like "253725-0info"
}

def analyze_email(email):
    """Analyze single email and return category + issues"""
    email = str(email).strip()

    # Check if valid format
    is_valid_format = bool(re.match(VALID_EMAIL_PATTERN, email))

    # Check for suspicious patterns
    issues = []
    for issue_name, pattern in SUSPICIOUS_PATTERNS.items():
        if re.search(pattern, email):
            issues.append(issue_name)

    # Categorize
    if not is_valid_format:
        category = 'INVALID'
    elif issues:
        category = 'SUSPICIOUS'
    else:
        category = 'VALID'

    return {
        'email': email,
        'category': category,
        'issues': ', '.join(issues) if issues else 'none',
        'valid_format': is_valid_format
    }

# Analyze all emails
print("=== ANALYZING EMAIL QUALITY ===\n")

all_emails = []
for emails_str in df['emails'].dropna():
    # Split multiple emails
    emails = [e.strip() for e in str(emails_str).split(',') if e.strip()]
    all_emails.extend(emails)

print(f"Total emails to analyze: {len(all_emails)}\n")

# Analyze each
results = [analyze_email(email) for email in all_emails]

# Categorize
categories = defaultdict(list)
for result in results:
    categories[result['category']].append(result)

# Print statistics
print("=== EMAIL QUALITY STATISTICS ===")
print(f"VALID: {len(categories['VALID'])} ({len(categories['VALID'])/len(results)*100:.1f}%)")
print(f"SUSPICIOUS: {len(categories['SUSPICIOUS'])} ({len(categories['SUSPICIOUS'])/len(results)*100:.1f}%)")
print(f"INVALID: {len(categories['INVALID'])} ({len(categories['INVALID'])/len(results)*100:.1f}%)")

# Show examples of each category
print("\n=== VALID EMAILS (first 10) ===")
for r in categories['VALID'][:10]:
    print(f"  {r['email']}")

print("\n=== SUSPICIOUS EMAILS (first 20) ===")
for r in categories['SUSPICIOUS'][:20]:
    print(f"  {r['email']} | Issues: {r['issues']}")

print("\n=== INVALID EMAILS (ALL) ===")
for r in categories['INVALID'][:50]:  # Show first 50
    print(f"  {r['email']} | Issues: {r['issues']}")

# Issue frequency
print("\n=== COMMON ISSUES ===")
issue_counts = defaultdict(int)
for r in results:
    if r['issues'] != 'none':
        for issue in r['issues'].split(', '):
            issue_counts[issue] += 1

for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{issue}: {count}")

# Save detailed report
output = pd.DataFrame(results)
output_path = Path(__file__).parent.parent / "results" / "email_quality_analysis.csv"
output.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\nDetailed report saved: {output_path}")

# Examples of specific bad patterns
print("\n=== SPECIFIC BAD PATTERNS ===")

# Phone numbers in emails
phone_emails = [r for r in results if 'has_phone' in r['issues']]
print(f"\nEmails with phone numbers ({len(phone_emails)}):")
for r in phone_emails[:10]:
    print(f"  {r['email']}")

# Weird TLDs
weird_tld = [r for r in results if 'ends_weird' in r['issues']]
print(f"\nWeird TLDs ({len(weird_tld)}):")
for r in weird_tld[:10]:
    print(f"  {r['email']}")

# Starts with digits
digit_start = [r for r in results if 'starts_with_digit_sequence' in r['issues']]
print(f"\nStarts with digit sequence ({len(digit_start)}):")
for r in digit_start[:10]:
    print(f"  {r['email']}")
