#!/usr/bin/env python3
"""Test the fixed prompt with problematic cases"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from batch_processor import process_batch_openai, load_api_key
from openai import OpenAI

def test_fixes():
    # Test the problematic cases from user
    test_companies = [
        "The Think Tank (TTT)",
        "Canspan BMG Inc.", 
        "Cubicle Fugitive Inc.",
        "MEDIAFORCE Digital Marketing",
        "CIMORONI",
        "SEO Masters: Digital Marketing Agency"
    ]
    
    expected = [
        "TTT",
        "Canspan", 
        "Cubicle Fugitive",
        "Mediaforce",
        "Cimoroni", 
        "Seo Masters"
    ]
    
    api_key = load_api_key()
    if not api_key:
        print("No API key found!")
        return
    
    client = OpenAI(api_key=api_key)
    
    print("Testing ITERATION #3 fixes:")
    print("=" * 60)
    
    results = process_batch_openai(test_companies, client)
    
    correct = 0
    for i, (original, cleaned, expected_result) in enumerate(zip(test_companies, results, expected), 1):
        status = "OK" if cleaned == expected_result else "FAIL"
        if cleaned == expected_result:
            correct += 1
        
        print(f"{i:2d}. '{original}'")
        print(f"    -> '{cleaned}' {status}")
        print(f"    Expected: '{expected_result}'")
        print()
    
    score = correct / len(test_companies) * 10
    print(f"SCORE: {correct}/{len(test_companies)} = {score:.1f}/10")
    print("=" * 60)
    
    if score >= 9:
        print("EXCELLENT! Prompt is ready for production")
    elif score >= 7:
        print("GOOD! Minor tweaks needed")
    else:
        print("NEEDS MORE WORK")
    
    return score

if __name__ == "__main__":
    test_fixes()