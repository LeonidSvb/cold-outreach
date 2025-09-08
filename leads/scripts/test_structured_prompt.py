#!/usr/bin/env python3
"""Test structured prompt"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import clean_company_name_ai, load_api_key, load_prompt
from openai import OpenAI

def test_structured():
    api_key = load_api_key()
    if not api_key:
        print("No API key found!")
        return
    
    client = OpenAI(api_key=api_key)
    
    try:
        prompt_templates = load_prompt()
        system_prompt, user_prompt = prompt_templates
        
        print("STRUCTURED PROMPT TEST")
        print("=" * 50)
        print("SYSTEM PROMPT:")
        print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
        print("\nUSER PROMPT TEMPLATE:")  
        print(user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt)
        print("=" * 50)
        
        # Test one company
        test_company = "The Think Tank (TTT)"
        result = clean_company_name_ai(test_company, client, prompt_templates)
        
        print(f"\nTEST:")
        print(f"Input: {test_company}")
        print(f"Output: {result}")
        print(f"Expected: TTT")
        print(f"Success: {result == 'TTT'}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_structured()