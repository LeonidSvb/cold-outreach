#!/usr/bin/env python3
"""Test fixed email extraction on real problematic cases"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.text_utils_FIXED import extract_emails, extract_emails_from_html

# Real problematic cases from verification
test_cases = [
    ("info@sovjet-ereveld.nliban", "info@sovjet-ereveld.nl"),
    ("budapestinfo@flippermuzeum.huhorizon", "budapestinfo@flippermuzeum.hu"),
    ("verein-bl64@mhsz.chder", "verein-bl64@mhsz.ch"),
    ("paulandlindab@hotmail.co.ukregistered", "paulandlindab@hotmail.co.uk"),
    ("102info@army-surplus.cz", "info@army-surplus.cz"),
    ("664info@antique-vintage-berlin.de", "info@antique-vintage-berlin.de"),
    ("info@militex.chbewertungen", "info@militex.ch"),
    ("hstaebler@remove-this.crestawald.ch", None),  # Should filter spam trap
]

print("=== TESTING FIXED EMAIL EXTRACTION ===\n")
print("Testing on real problematic emails from verification...\n")

passed = 0
failed = 0

for broken_email, expected in test_cases:
    result = extract_emails(broken_email)

    if expected is None:
        # Should be filtered out
        if len(result) == 0:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
    else:
        # Should fix the email
        if len(result) == 1 and result[0] == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

    print(f"[{status}] {broken_email}")
    print(f"      Expected: {expected}")
    print(f"      Got:      {result}")
    print()

print(f"\n=== RESULTS ===")
print(f"Passed: {passed}/{len(test_cases)}")
print(f"Failed: {failed}/{len(test_cases)}")

if failed == 0:
    print("\nAll tests PASSED! Email extraction fixed.")
else:
    print(f"\n{failed} tests failed. Need more work.")
