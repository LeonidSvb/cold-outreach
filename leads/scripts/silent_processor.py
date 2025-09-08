#!/usr/bin/env python3
"""
Silent CSV processor - no detailed output to avoid encoding issues
"""

import os
import csv
from datetime import datetime
from openai import OpenAI

def load_api_key():
    """Load OpenAI API key from .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    return os.getenv('OPENAI_API_KEY')

def load_prompt():
    """Load prompt from prompts folder"""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'prompts', 'company_name_shortener.txt')
    
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '---' in content:
        prompt = content.split('---')[0].strip()
    else:
        prompt = content.strip()
    
    return prompt

def clean_company_name_ai(company_name, client, prompt_template):
    """Clean company name via OpenAI"""
    
    if not company_name or not company_name.strip():
        return ""
    
    try:
        prompt = prompt_template.format(company_name=company_name)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0.3
        )
        
        cleaned_name = response.choices[0].message.content.strip()
        cleaned_name = cleaned_name.strip('"\'')
        
        return cleaned_name
        
    except Exception as e:
        print(f"Error processing: {e}")
        return company_name

def process_csv_silent():
    csv_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada.csv"
    output_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada_cleaned.csv"
    
    api_key = load_api_key()
    if not api_key:
        print("No OpenAI API key found!")
        return None
    
    client = OpenAI(api_key=api_key)
    prompt_template = load_prompt()
    
    print(f"Processing: {csv_file}")
    print(f"Output: {output_file}")
    print("Starting processing...")
    
    results = []
    processed_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                original = row.get('company_name', '')
                
                if original:
                    cleaned = clean_company_name_ai(original, client, prompt_template)
                else:
                    cleaned = ""
                
                row['cleaned_company_name'] = cleaned
                results.append(row)
                
                processed_count += 1
                
                # Progress indicator every 50 companies
                if processed_count % 50 == 0:
                    print(f"Processed: {processed_count}")
        
        # Save results
        if results:
            fieldnames = list(results[0].keys())
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        print(f"\nSUCCESS!")
        print(f"Processed {processed_count} companies")
        print(f"Saved to: {output_file}")
        print(f"New column 'cleaned_company_name' added")
        
        return output_file
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    process_csv_silent()