#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import clean_company_name_ai, load_api_key, load_prompt
from openai import OpenAI

def safe_test():
    test_cases = [
        ("The Think Tank (TTT)", "TTT"),
        ("Canspan BMG Inc.", "Canspan"),
        ("Cubicle Fugitive Inc.", "Cubicle Fugitive"),
        ("MEDIAFORCE Digital Marketing", "Mediaforce"),
        ("CIMORONI", "Cimoroni"),
        ("SEO Masters: Digital Marketing Agency", "Seo Masters")
    ]
    
    api_key = load_api_key()
    client = OpenAI(api_key=api_key)
    prompt_template = load_prompt()
    
    print("Few-shot approach test results:")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for i, (original, expected) in enumerate(test_cases, 1):
        try:
            result = clean_company_name_ai(original, client, prompt_template)
            # Clean result from any encoding issues
            result = result.encode('ascii', 'ignore').decode('ascii').strip()
            
            match = result == expected
            if match:
                correct += 1
            
            print(f"{i}. Input: {original}")
            print(f"   Result: {result}")
            print(f"   Expected: {expected}")
            print(f"   Status: {'PASS' if match else 'FAIL'}")
            print()
            
        except Exception as e:
            print(f"{i}. ERROR: {e}")
            print()
    
    score = (correct / total) * 10
    print(f"Final Score: {correct}/{total} = {score:.1f}/10")
    
    if score >= 9:
        print("EXCELLENT! Ready for production!")
        return True
    elif score >= 7:
        print("GOOD! Minor issues remain")
        return False
    else:
        print("NEEDS MORE WORK")
        return False

if __name__ == "__main__":
    safe_test()