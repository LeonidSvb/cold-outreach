#!/usr/bin/env python3
"""
=== AI PAGE PRIORITIZER ===
Version: 1.0.0 | Created: 2025-09-08

PURPOSE: 
AI-powered page prioritization for cold outreach research using OpenAI dialogue-style prompting

IMPROVEMENTS:
- 2025-09-08: Initial implementation with dialogue-style prompting ✅
- 2025-09-08: Dynamic priority classification for outreach intelligence ✅
- 2025-09-08: Editable prompt system for easy adjustments ✅

WHAT THIS DOES:
1. Takes discovered page URLs and titles
2. Uses OpenAI to classify pages by outreach value
3. Prioritizes: HIRING > BLOG > ABOUT > SERVICES > TEAM > CASE STUDIES
4. Returns structured priority categories for selective scraping

USAGE:
python page_prioritizer.py                    # Test with sample data
python page_prioritizer.py pages.json        # Process pages from JSON file
"""

import json
import os
import sys
import openai
from datetime import datetime

# Self-documenting statistics
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "successful_classifications": 0,
    "failed_classifications": 0,
    "avg_pages_per_domain": 0,
    "last_updated": "2025-09-08",
    "last_run": None
}

RUN_HISTORY = []

class PagePrioritizer:
    """AI-powered page prioritization for outreach research"""
    
    def __init__(self, openai_api_key):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.prompt_template = self.load_prompt_template()
        
    def load_prompt_template(self):
        """Load dialogue-style prompt template"""
        prompt_file = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'page_prioritizer.txt')
        
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
            
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse prompt sections
        sections = {}
        current_section = None
        lines = content.split('\n')
        
        for line in lines:
            if line.strip() and line.strip().endswith(':'):
                current_section = line.strip().rstrip(':')
                sections[current_section] = []
            elif current_section and line.strip():
                sections[current_section].append(line)
                
        return sections
    
    def build_messages(self, pages_data):
        """Build dialogue-style messages for OpenAI API"""
        
        # System message
        system_content = '\n'.join(self.prompt_template.get('SYSTEM_PROMPT', []))
        
        # User instructions
        user_instructions = '\n'.join(self.prompt_template.get('USER_INSTRUCTIONS', []))
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_instructions}
        ]
        
        # Add examples (dialogue style)
        example_pairs = [
            ('USER_EXAMPLE_1', 'ASSISTANT_EXAMPLE_1'),
            ('USER_EXAMPLE_2', 'ASSISTANT_EXAMPLE_2'),
            ('USER_EXAMPLE_3', 'ASSISTANT_EXAMPLE_3')
        ]
        
        for user_key, assistant_key in example_pairs:
            if user_key in self.prompt_template and assistant_key in self.prompt_template:
                user_example = '\n'.join(self.prompt_template[user_key])
                assistant_example = '\n'.join(self.prompt_template[assistant_key])
                
                messages.append({"role": "user", "content": user_example})
                messages.append({"role": "assistant", "content": assistant_example})
        
        # Real input
        pages_json = json.dumps(pages_data, indent=2, ensure_ascii=False)
        messages.append({"role": "user", "content": pages_json})
        
        return messages
    
    def classify_pages(self, pages_data):
        """Classify pages using OpenAI dialogue-style prompting"""
        
        try:
            messages = self.build_messages(pages_data)
            
            print(f"Classifying {len(pages_data)} pages using OpenAI...")
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                classification = json.loads(result_text)
                
                # Validate structure
                required_keys = ['high_priority', 'medium_priority', 'low_priority', 'skip']
                if all(key in classification for key in required_keys):
                    return classification
                else:
                    print(f"Warning: Invalid classification structure: {list(classification.keys())}")
                    return None
                    
            except json.JSONDecodeError as e:
                print(f"Error parsing AI response as JSON: {e}")
                print(f"Raw response: {result_text}")
                return None
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None
    
    def process_domain_pages(self, domain, pages_with_titles):
        """Process pages for a single domain"""
        
        # Format pages for AI
        pages_data = [
            {"url": page["url"], "title": page.get("title", "No title")}
            for page in pages_with_titles
        ]
        
        classification = self.classify_pages(pages_data)
        
        if classification:
            # Add metadata
            result = {
                "domain": domain,
                "total_pages": len(pages_data),
                "classification": classification,
                "processed_at": datetime.now().isoformat(),
                "priorities_count": {
                    "high": len(classification["high_priority"]),
                    "medium": len(classification["medium_priority"]), 
                    "low": len(classification["low_priority"]),
                    "skip": len(classification["skip"])
                }
            }
            
            # Update stats
            global SCRIPT_STATS
            SCRIPT_STATS["successful_classifications"] += 1
            SCRIPT_STATS["total_runs"] += 1
            SCRIPT_STATS["last_run"] = datetime.now().isoformat()
            
            # Log run
            RUN_HISTORY.append({
                "domain": domain,
                "pages_processed": len(pages_data),
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
        else:
            # Update failure stats
            SCRIPT_STATS["failed_classifications"] += 1
            SCRIPT_STATS["total_runs"] += 1
            
            return None
    
    def save_results(self, results, filename_suffix="prioritized"):
        """Save prioritization results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pages_{filename_suffix}_{timestamp}.json"
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'prioritized')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        # Include stats in output
        full_results = {
            "results": results,
            "script_stats": SCRIPT_STATS,
            "run_history": RUN_HISTORY[-10:]  # Last 10 runs
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved: {filename}")
        return output_path

def load_sample_pages():
    """Load sample page data for testing"""
    return [
        {"url": "https://stryvemarketing.com/careers", "title": "Careers - Join Our Growing Team"},
        {"url": "https://stryvemarketing.com/about", "title": "About Stryve Marketing"},
        {"url": "https://stryvemarketing.com/blog/digital-trends-2024", "title": "Top Digital Marketing Trends 2024"},
        {"url": "https://stryvemarketing.com/services", "title": "Our Marketing Services"},
        {"url": "https://stryvemarketing.com/privacy-policy", "title": "Privacy Policy"},
        {"url": "https://stryvemarketing.com/approach", "title": "Our Approach to Marketing"},
        {"url": "https://stryvemarketing.com/team", "title": "Meet Our Team"},
        {"url": "https://stryvemarketing.com/case-studies", "title": "Client Success Stories"}
    ]

def load_api_key():
    """Load OpenAI API key from .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    
    if not os.path.exists(env_path):
        return None
        
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY='):
                return line.split('=', 1)[1].strip()
    
    return None

def main():
    """Main execution function"""
    
    print("=== AI PAGE PRIORITIZER ===")
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Initialize prioritizer
    try:
        prioritizer = PagePrioritizer(api_key)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Load pages data
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        # Load from JSON file
        pages_file = sys.argv[1]
        try:
            with open(pages_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                pages_data = data if isinstance(data, list) else data.get('pages', [])
                domain = data.get('domain', 'unknown') if isinstance(data, dict) else 'unknown'
        except Exception as e:
            print(f"Error loading pages file: {e}")
            return
    else:
        # Use sample data
        pages_data = load_sample_pages()
        domain = "stryvemarketing.com"
        print("Using sample page data for testing...")
    
    # Process pages
    result = prioritizer.process_domain_pages(domain, pages_data)
    
    if result:
        print(f"\n=== PRIORITIZATION RESULTS ===")
        print(f"Domain: {result['domain']}")
        print(f"Total pages: {result['total_pages']}")
        print(f"High priority: {result['priorities_count']['high']}")
        print(f"Medium priority: {result['priorities_count']['medium']}")
        print(f"Low priority: {result['priorities_count']['low']}")
        print(f"Skip: {result['priorities_count']['skip']}")
        
        print(f"\n=== HIGH PRIORITY PAGES ===")
        for url in result['classification']['high_priority']:
            print(f"  • {url}")
            
        print(f"\n=== MEDIUM PRIORITY PAGES ===")
        for url in result['classification']['medium_priority']:
            print(f"  • {url}")
        
        # Save results
        prioritizer.save_results([result])
        
        print(f"\n[SUCCESS] Page prioritization completed!")
        
    else:
        print(f"\n[FAILED] Could not classify pages")

if __name__ == "__main__":
    main()