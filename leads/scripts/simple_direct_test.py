#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import clean_company_name_ai, load_api_key, load_prompt
from openai import OpenAI

def simple_test():
    api_key = load_api_key()
    client = OpenAI(api_key=api_key)
    prompt_template = load_prompt()
    
    result = clean_company_name_ai("The Think Tank (TTT)", client, prompt_template)
    
    # Remove any unicode issues
    result = result.encode('ascii', 'ignore').decode('ascii')
    
    print("Test: 'The Think Tank (TTT)'")
    print("Result:", result)
    print("Expected: TTT")
    print("Match:", result == "TTT")

if __name__ == "__main__":
    simple_test()