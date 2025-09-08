#!/usr/bin/env python3
"""Debug prompt parsing"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import load_prompt

def debug_parsing():
    try:
        system_prompt, base_messages = load_prompt()
        
        print("=== SYSTEM PROMPT ===")
        print(repr(system_prompt))
        print()
        
        print("=== BASE MESSAGES ===")
        for i, msg in enumerate(base_messages):
            print(f"{i+1}. Role: {msg['role']}")
            print(f"   Content: {repr(msg['content'])}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parsing()