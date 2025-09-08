#!/usr/bin/env python3
"""
Fast batch processor for company names using OpenAI batch API
Processes multiple companies at once for maximum speed
"""

import os
import csv
import json
from datetime import datetime
from openai import OpenAI

def load_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    return os.getenv('OPENAI_API_KEY')

def load_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'prompts', 'company_name_shortener.txt')
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '---' in content:
        prompt = content.split('---')[0].strip()
    else:
        prompt = content.strip()
    
    return prompt

def create_batch_prompt(company_names):
    """Create a single prompt for multiple companies"""
    base_prompt = """Сократи названия компаний до разговорной формы - как сотрудники называют свои компании между собой.

ВАЖНО: ВСЕГДА сокращай, даже если название кажется коротким.

Правила:
1. Убери юридические суффиксы (Inc, Ltd, LLC, Corp, Co, etc)
2. Убери описательные слова (Marketing, Digital, Creative, Media, Group, Agency) 
3. Оставь только КЛЮЧЕВОЕ СЛОВО или максимум 2 главных слова
4. Если есть аббревиатура в скобках - используй её
5. Должно звучать как прозвище компании

Обработай следующие компании (отвечай в формате: номер. результат):

"""
    
    for i, company in enumerate(company_names, 1):
        base_prompt += f"{i}. {company}\n"
    
    base_prompt += "\nОтветь только списком сокращенных названий в том же порядке (БЕЗ исходных названий, только результаты):"
    
    return base_prompt

def process_batch_openai(company_batch, client):
    """Process a batch of companies through OpenAI"""
    try:
        batch_prompt = create_batch_prompt(company_batch)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert at shortening company names. Follow the examples exactly!"},
                {"role": "user", "content": batch_prompt}
            ],
            max_tokens=300,
            temperature=0.5
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse the results
        lines = result_text.split('\n')
        cleaned_names = []
        
        for line in lines:
            line = line.strip()
            if line and ('.' in line or len(line) > 0):
                # Remove number prefix if exists
                if line[0].isdigit() and '.' in line:
                    cleaned = line.split('.', 1)[1].strip()
                else:
                    cleaned = line
                
                # Remove "Original - Result" format, keep only the result after dash
                if ' - ' in cleaned:
                    cleaned = cleaned.split(' - ')[-1].strip()
                
                cleaned = cleaned.strip('"\'')
                cleaned_names.append(cleaned)
        
        # Ensure we have the same number of results as inputs
        while len(cleaned_names) < len(company_batch):
            cleaned_names.append(company_batch[len(cleaned_names)])
        
        return cleaned_names[:len(company_batch)]
        
    except Exception as e:
        print(f"Batch error: {e}")
        return company_batch  # Return originals if error

def fast_batch_process():
    csv_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada.csv"
    output_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada_cleaned.csv"
    
    api_key = load_api_key()
    if not api_key:
        print("No OpenAI API key found!")
        return None
    
    client = OpenAI(api_key=api_key)
    
    print(f"Fast batch processing: {csv_file}")
    print(f"Output: {output_file}")
    print("Loading CSV...")
    
    # Load all data first
    all_rows = []
    companies_to_process = []
    
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            all_rows.append(row)
            company_name = row.get('company_name', '').strip()
            if company_name:
                companies_to_process.append(company_name)
            else:
                companies_to_process.append("")
    
    print(f"Loaded {len(all_rows)} rows with {len([c for c in companies_to_process if c])} companies to process")
    print("Starting batch processing...")
    
    # Process in batches of 20 companies
    batch_size = 20
    all_cleaned = []
    
    for i in range(0, len(companies_to_process), batch_size):
        batch = companies_to_process[i:i+batch_size]
        
        # Filter out empty companies for processing
        non_empty_batch = [c for c in batch if c]
        
        if non_empty_batch:
            print(f"Processing batch {i//batch_size + 1}: {len(non_empty_batch)} companies")
            cleaned_batch = process_batch_openai(non_empty_batch, client)
        else:
            cleaned_batch = []
        
        # Map back to full batch (including empty ones)
        batch_results = []
        clean_idx = 0
        for company in batch:
            if company:
                if clean_idx < len(cleaned_batch):
                    batch_results.append(cleaned_batch[clean_idx])
                else:
                    batch_results.append(company)
                clean_idx += 1
            else:
                batch_results.append("")
        
        all_cleaned.extend(batch_results)
        
        print(f"Completed {min(i + batch_size, len(companies_to_process))}/{len(companies_to_process)}")
    
    # Add cleaned names to rows
    for i, row in enumerate(all_rows):
        if i < len(all_cleaned):
            row['cleaned_company_name'] = all_cleaned[i]
        else:
            row['cleaned_company_name'] = ""
    
    # Save results
    print("Saving results...")
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
    
    print(f"\nSUCCESS!")
    print(f"Processed {len(all_rows)} total rows")
    print(f"Cleaned {len([c for c in all_cleaned if c])} company names")
    print(f"Saved to: {output_file}")
    print(f"New column 'cleaned_company_name' added")
    
    return output_file

if __name__ == "__main__":
    fast_batch_process()