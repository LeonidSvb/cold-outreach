#!/usr/bin/env python3
"""Simple test of company name cleaner"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import clean_company_name_ai, load_api_key, load_prompt
from openai import OpenAI

def simple_test():
    # Test companies from your CSV
    test_companies = [
        "Altitude Strategies",
        "Big Fish Creative", 
        "Stryve Digital Marketing",
        "Work Party Creative Group",
        "Kipling Media",
        "Greenhouse Marketing, Sales & Recruitment",
        "RealtyNinja",
        "The One Group (OG) Agency",
        "Agence Polka/Arsenal",
        "Involved Media Canada"
    ]
    
    print("Company Name Cleaner Test")
    print("=" * 50)
    
    api_key = load_api_key()
    if not api_key:
        print("No OpenAI API key found!")
        return
        
    client = OpenAI(api_key=api_key)
    prompt_template = load_prompt()
    
    results = []
    
    for i, company in enumerate(test_companies, 1):
        try:
            cleaned = clean_company_name_ai(company, client, prompt_template)
            results.append({"original": company, "cleaned": cleaned})
            print(f"{i:2d}. '{company}' -> '{cleaned}'")
        except Exception as e:
            print(f"{i:2d}. '{company}' -> ERROR: {e}")
    
    print("=" * 50)
    
    # Simple analysis
    good = 0
    for result in results:
        original = result["original"]
        cleaned = result["cleaned"]
        
        # Check if it's actually shortened
        if len(cleaned.split()) <= len(original.split()) and cleaned != original:
            good += 1
    
    score = good / len(results) * 10 if results else 0
    print(f"Score: {good}/{len(results)} = {score:.1f}/10")
    
    return results, score

if __name__ == "__main__":
    simple_test()