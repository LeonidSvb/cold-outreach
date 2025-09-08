#!/usr/bin/env python3
"""Test few-shot approach"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import load_api_key
from openai import OpenAI

def few_shot_test():
    api_key = load_api_key()
    if not api_key:
        print("No API key found!")
        return
    
    client = OpenAI(api_key=api_key)
    
    # Few-shot prompt with the problematic cases
    prompt = '''Examples of shortening company names:

"The Think Tank (TTT)" → "TTT"
"Canspan BMG Inc." → "Canspan"
"Cubicle Fugitive Inc." → "Cubicle Fugitive"
"MEDIAFORCE Digital Marketing" → "Mediaforce"
"CIMORONI" → "Cimoroni"
"SEO Masters: Digital Marketing Agency" → "Seo Masters"
"The One Group (OG) Agency" → "OG"
"Big Fish Creative Inc." → "Big Fish"

Now continue the pattern:
"TRGR Advertising" → '''
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.1
    )
    
    result = response.choices[0].message.content.strip().strip('"')
    print(f"Few-shot test:")
    print(f"'TRGR Advertising' -> '{result}'")
    print(f"Expected: 'Trgr'")
    
    return result

if __name__ == "__main__":
    few_shot_test()