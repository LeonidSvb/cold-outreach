#!/usr/bin/env python3
# Simple test to check if everything is set up correctly

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test 1: CSV
try:
    import pandas as pd
    csv_path = r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv"
    df = pd.read_csv(csv_path)
    print(f"[OK] CSV loaded: {len(df)} rows")
except Exception as e:
    print(f"[FAIL] CSV: {e}")
    sys.exit(1)

# Test 2: API Key
import os
api_key = os.environ.get('ANTHROPIC_API_KEY')
if api_key:
    print(f"[OK] API Key: present ({len(api_key)} chars)")
else:
    print("[FAIL] API Key: not found in environment")
    sys.exit(1)

# Test 3: Anthropic
try:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    print("[OK] Anthropic client: initialized")
except Exception as e:
    print(f"[FAIL] Anthropic: {e}")
    sys.exit(1)

# Test 4: API Call
try:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=30,
        messages=[{"role": "user", "content": "Say TEST OK"}]
    )
    text = response.content[0].text.strip()
    print(f"[OK] API call: {text}")
except Exception as e:
    print(f"[FAIL] API call: {e}")
    sys.exit(1)

# Test 5: Output directory
output_dir = r"C:\Users\79818\Desktop\Outreach - new\data\processed"
try:
    os.makedirs(output_dir, exist_ok=True)
    test_file = os.path.join(output_dir, "test.txt")
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
    print(f"[OK] Output directory: {output_dir}")
except Exception as e:
    print(f"[FAIL] Output directory: {e}")
    sys.exit(1)

print("\n[SUCCESS] All setup checks passed! Ready to run generator.")
