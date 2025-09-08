#!/usr/bin/env python3
"""
Advanced Company Name Cleaner with Built-in Analytics
Tracks performance, costs, improvements, and provides detailed metrics
"""

import os
import json
import csv
import time
from datetime import datetime
from openai import OpenAI

class CompanyNameCleanerAnalytics:
    def __init__(self):
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "total_processed": 0,
            "successful_cleanings": 0,
            "api_calls": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "processing_time_seconds": 0,
            "prompt_version": "",
            "model_used": "",
            "temperature": 0,
            "max_tokens": 0,
            "errors": [],
            "performance_samples": []
        }
        self.start_time = time.time()
        
    def log_api_call(self, tokens_used, model="gpt-3.5-turbo"):
        """Log API usage and calculate costs"""
        self.stats["api_calls"] += 1
        self.stats["total_tokens_used"] += tokens_used
        
        # GPT-3.5-turbo pricing (as of 2025)
        cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens
        call_cost = (tokens_used / 1000) * cost_per_1k_tokens
        self.stats["total_cost_usd"] += call_cost
        
    def log_success(self, original, cleaned, processing_time_ms):
        """Log successful processing"""
        self.stats["successful_cleanings"] += 1
        self.stats["total_processed"] += 1
        
        # Sample performance data
        if len(self.stats["performance_samples"]) < 10:
            self.stats["performance_samples"].append({
                "original": original,
                "cleaned": cleaned,
                "processing_time_ms": processing_time_ms,
                "timestamp": datetime.now().isoformat()
            })
    
    def log_error(self, original, error_message):
        """Log processing errors"""
        self.stats["total_processed"] += 1
        self.stats["errors"].append({
            "original": original,
            "error": str(error_message),
            "timestamp": datetime.now().isoformat()
        })
    
    def get_metrics(self):
        """Get current session metrics"""
        self.stats["processing_time_seconds"] = time.time() - self.start_time
        self.stats["success_rate"] = (self.stats["successful_cleanings"] / max(1, self.stats["total_processed"])) * 100
        self.stats["avg_cost_per_cleaning"] = self.stats["total_cost_usd"] / max(1, self.stats["successful_cleanings"])
        
        return self.stats
    
    def save_session_log(self, output_folder):
        """Save detailed session analytics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = os.path.join(output_folder, f"session_analytics_{timestamp}.json")
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_metrics(), f, indent=2, ensure_ascii=False)
        
        return log_path

def load_api_key():
    """Load OpenAI API key from .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    return os.getenv('OPENAI_API_KEY')

def load_prompt_with_metadata():
    """Load dialogue-style prompt and extract metadata"""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'company_name_shortener.txt')
    
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    metadata = {}
    if '---' in content:
        prompt_content, meta_content = content.split('---', 1)
        
        # Parse metadata
        for line in meta_content.split('\n'):
            if ':' in line and any(key in line.upper() for key in ['ИТЕРАЦИЯ', 'ЭФФЕКТИВНОСТЬ', 'МОДЕЛЬ', 'ТЕМПЕРАТУРА']):
                if 'ИТЕРАЦИЯ' in line:
                    metadata['version'] = line.split(':', 1)[1].strip()
                elif 'ЭФФЕКТИВНОСТЬ' in line:
                    metadata['effectiveness'] = line.split(':', 1)[1].strip()
                elif 'МОДЕЛЬ' in line:
                    metadata['model'] = line.split(':', 1)[1].strip()
                elif 'ТЕМПЕРАТУРА' in line:
                    metadata['temperature'] = line.split(':', 1)[1].strip()
    else:
        prompt_content = content.strip()
    
    # Parse dialogue structure
    lines = prompt_content.split('\n')
    system_prompt = ""
    base_messages = []
    
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('SYSTEM_PROMPT:'):
            if current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'system'
            current_content = []
        elif line.startswith('USER_INSTRUCTIONS:'):
            if current_section == 'system':
                system_prompt = '\n'.join(current_content).strip()
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'instructions'
            current_content = []
        elif line.startswith('USER_EXAMPLE_'):
            if current_section == 'instructions':
                base_messages.append({"role": "user", "content": '\n'.join(current_content).strip()})
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'user_example'
            current_content = []
        elif line.startswith('ASSISTANT_EXAMPLE_'):
            if current_section == 'user_example':
                base_messages.append({"role": "user", "content": '\n'.join(current_content).strip()})
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'assistant_example'
            current_content = []
        elif line.startswith('USER_REAL_INPUT:'):
            if current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            break
        elif line and not line.startswith(('SYSTEM_', 'USER_', 'ASSISTANT_')):
            current_content.append(line)
    
    return system_prompt, base_messages, metadata

def clean_company_name_with_analytics(company_name, client, prompt_data, analytics, model="gpt-3.5-turbo", temperature=0.1, max_tokens=20):
    """Clean company name with full analytics tracking"""
    
    if not company_name or not company_name.strip():
        return ""
    
    start_time = time.time()
    
    try:
        system_prompt, base_messages = prompt_data
        
        # Build full dialogue
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.extend(base_messages)
        messages.append({"role": "user", "content": company_name})
        
        # API call
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Extract and clean result
        cleaned_name = response.choices[0].message.content.strip()
        cleaned_name = cleaned_name.strip('"\'')
        
        # Clean artifacts
        if '\n' in cleaned_name:
            cleaned_name = cleaned_name.split('\n')[0]
        if '"' in cleaned_name:
            cleaned_name = cleaned_name.split('"')[0]
        if '->' in cleaned_name:
            cleaned_name = cleaned_name.split('->')[0]
        
        cleaned_name = cleaned_name.strip()
        
        # Log analytics
        processing_time = (time.time() - start_time) * 1000  # ms
        total_tokens = response.usage.total_tokens if hasattr(response, 'usage') else max_tokens
        
        analytics.log_api_call(total_tokens, model)
        analytics.log_success(company_name, cleaned_name, processing_time)
        
        return cleaned_name
        
    except Exception as e:
        analytics.log_error(company_name, str(e))
        return company_name  # Fallback to original

def process_csv_with_analytics(input_file, batch_size=20, output_file=None):
    """Process CSV with comprehensive analytics"""
    
    # Initialize analytics
    analytics = CompanyNameCleanerAnalytics()
    
    api_key = load_api_key()
    if not api_key:
        print("[ERROR] OpenAI API key not found!")
        return None
    
    client = OpenAI(api_key=api_key)
    
    try:
        system_prompt, base_messages, metadata = load_prompt_with_metadata()
        prompt_data = (system_prompt, base_messages)
        
        # Update analytics with prompt metadata
        analytics.stats["prompt_version"] = metadata.get("version", "Unknown")
        analytics.stats["model_used"] = metadata.get("model", "gpt-3.5-turbo")
        analytics.stats["temperature"] = 0.1
        analytics.stats["max_tokens"] = 20
        
    except Exception as e:
        print(f"[ERROR] Error loading prompt: {e}")
        return None
    
    if not output_file:
        base, ext = os.path.splitext(input_file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{base}_cleaned_{timestamp}{ext}"
    
    print(f"[START] Advanced Processing Started")
    print(f"[FILE] Input: {input_file}")
    print(f"[FILE] Output: {output_file}")
    print(f"[TARGET] Prompt Version: {analytics.stats['prompt_version']}")
    print("-" * 60)
    
    results = []
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        batch = []
        for row in reader:
            batch.append(row)
            
            if len(batch) >= batch_size:
                process_batch_with_analytics(batch, client, prompt_data, analytics, results)
                print(f"[STATS] Processed: {analytics.stats['total_processed']} | Success: {analytics.stats['successful_cleanings']} | Cost: ${analytics.stats['total_cost_usd']:.4f}")
                batch = []
        
        # Process remaining
        if batch:
            process_batch_with_analytics(batch, client, prompt_data, analytics, results)
    
    # Save results
    if results:
        fieldnames = list(results[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    # Generate analytics report
    final_stats = analytics.get_metrics()
    output_folder = os.path.dirname(output_file) or '.'
    analytics_path = analytics.save_session_log(output_folder)
    
    # Print summary
    print("\n" + "="*60)
    print("[ANALYTICS] SESSION ANALYTICS SUMMARY")
    print("="*60)
    print(f"[TARGET] Total Processed: {final_stats['total_processed']}")
    print(f"[OK] Successful: {final_stats['successful_cleanings']}")
    print(f"[STATS] Success Rate: {final_stats['success_rate']:.1f}%")
    print(f"[COST] Total Cost: ${final_stats['total_cost_usd']:.4f}")
    print(f"[SPEED] Avg Cost/Company: ${final_stats['avg_cost_per_cleaning']:.4f}")
    print(f"[API] API Calls: {final_stats['api_calls']}")
    print(f"[TOKENS] Total Tokens: {final_stats['total_tokens_used']}")
    print(f"[TIME]  Processing Time: {final_stats['processing_time_seconds']:.1f}s")
    if final_stats['errors']:
        print(f"[ERROR] Errors: {len(final_stats['errors'])}")
    print(f"[LOG] Analytics Log: {analytics_path}")
    print("="*60)
    
    return output_file

def process_batch_with_analytics(batch, client, prompt_data, analytics, results):
    """Process batch with individual analytics tracking"""
    
    for row in batch:
        original = row.get('company_name', '')
        
        if original:
            cleaned = clean_company_name_with_analytics(original, client, prompt_data, analytics)
        else:
            cleaned = ""
            analytics.stats["total_processed"] += 1
        
        row['cleaned_company_name'] = cleaned
        results.append(row)

if __name__ == "__main__":
    print("[AI] Company Name Cleaner with Advanced Analytics")
    print("=" * 60)
    
    csv_file = input("[FILE] Enter CSV file path: ").strip().strip('"')
    
    if csv_file and os.path.exists(csv_file):
        process_csv_with_analytics(csv_file)
    else:
        print("[ERROR] File not found!")
        
        # Demo mode with sample data
        print("\n[DEMO] Running demo mode...")
        demo_companies = [
            "The Think Tank (TTT)",
            "MEDIAFORCE Digital Marketing", 
            "Canspan BMG Inc.",
            "Apple Inc."
        ]
        
        # Initialize demo
        analytics = CompanyNameCleanerAnalytics()
        api_key = load_api_key()
        
        if api_key:
            client = OpenAI(api_key=api_key)
            system_prompt, base_messages, metadata = load_prompt_with_metadata()
            prompt_data = (system_prompt, base_messages)
            
            print("Demo Results:")
            for company in demo_companies:
                cleaned = clean_company_name_with_analytics(company, client, prompt_data, analytics)
                print(f"  '{company}' -> '{cleaned}'")
            
            # Show demo analytics
            stats = analytics.get_metrics()
            print(f"\nDemo Analytics: {stats['total_processed']} processed, ${stats['total_cost_usd']:.4f} cost")
        else:
            print("[ERROR] No API key for demo")