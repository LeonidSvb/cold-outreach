#!/usr/bin/env python3
"""Test the fixed format parsing"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from batch_processor import process_batch_openai, load_api_key
from openai import OpenAI

def test_format():
    # Test with the problematic companies
    test_companies = [
        "Twenty West",
        "BookmarkED", 
        "Arivano",
        "Thinkr Marketing",
        "TRGR Advertising",
        "Mezzanine Growth",
        "Involved Media Canada",
        "Tag Advertising",
        "Reflect Media"
    ]
    
    api_key = load_api_key()
    if not api_key:
        print("No API key found!")
        return
    
    client = OpenAI(api_key=api_key)
    
    print("Testing fixed format parsing:")
    print("=" * 50)
    
    results = process_batch_openai(test_companies, client)
    
    for i, (original, cleaned) in enumerate(zip(test_companies, results), 1):
        print(f"{i:2d}. '{original}' -> '{cleaned}'")
    
    print("=" * 50)
    print("Check: no duplicates with dash format?")

if __name__ == "__main__":
    test_format()