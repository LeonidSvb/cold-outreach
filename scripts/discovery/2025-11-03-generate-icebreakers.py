#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Icebreaker Generator - Simple Version
"""

import sys
import os
import pandas as pd

# Determine paths
csv_path = r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv"
output_dir = r"C:\Users\79818\Desktop\Outreach - new\data\processed"

# Ensure output dir exists
os.makedirs(output_dir, exist_ok=True)

# Test 1: Load CSV
print("[1/3] Loading CSV...")
try:
    df = pd.read_csv(csv_path)
    print(f"SUCCESS: Loaded {len(df)} rows")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# Test 2: Import Anthropic
print("[2/3] Importing Anthropic...")
try:
    import anthropic
    print("SUCCESS: anthropic imported")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

# Test 3: Initialize client
print("[3/3] Initializing API client...")
try:
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    print("SUCCESS: API client ready")

    # Try a test message
    test_response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=30,
        messages=[{"role": "user", "content": "Say OK"}]
    )
    print(f"API TEST: {test_response.content[0].text.strip()}")

except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

print("\nALL CHECKS PASSED!")
print(f"Ready to process {len(df)} rows")
print(f"Output will be saved to: {output_dir}")
