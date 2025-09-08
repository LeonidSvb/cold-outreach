#!/usr/bin/env python3
"""Test bracket and slash handling"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from batch_processor import process_batch_openai, load_api_key
from openai import OpenAI

def test_brackets():
    # Test companies with brackets and slashes
    test_companies = [
        "The One Group (OG) Agency",
        "Agence Polka/Arsenal", 
        "BookmarkED",
        "TRGR Advertising",
        "Victory Media Inc.",
        "Big Fish Creative (BFC) Ltd."
    ]
    
    api_key = load_api_key()
    if not api_key:
        print("No API key found!")
        return
    
    client = OpenAI(api_key=api_key)
    
    print("Testing bracket/slash handling:")
    print("=" * 50)
    
    results = process_batch_openai(test_companies, client)
    
    for i, (original, cleaned) in enumerate(zip(test_companies, results), 1):
        print(f"{i:2d}. '{original}' -> '{cleaned}'")
    
    print("=" * 50)
    print("Expected:")
    print("1. 'The One Group (OG) Agency' -> 'OG'")
    print("2. 'Agence Polka/Arsenal' -> 'Polka Arsenal'")

if __name__ == "__main__":
    test_brackets()