#!/usr/bin/env python3
"""Direct test of individual company name cleaning"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import clean_company_name_ai, load_api_key, load_prompt
from openai import OpenAI

def direct_test():
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
    prompt_template = load_prompt()
    
    print("Direct individual test:")
    print("=" * 60)
    
    correct = 0
    for i, (original, expected_result) in enumerate(zip(test_companies, expected), 1):
        cleaned = clean_company_name_ai(original, client, prompt_template)
        status = "OK" if cleaned == expected_result else "FAIL"
        if cleaned == expected_result:
            correct += 1
        
        print(f"{i:2d}. '{original}'")
        print(f"    => '{cleaned}' {status}")
        print(f"    Expected: '{expected_result}'")
        print()
    
    score = correct / len(test_companies) * 10
    print(f"SCORE: {correct}/{len(test_companies)} = {score:.1f}/10")
    
    return score

if __name__ == "__main__":
    direct_test()