#!/usr/bin/env python3
"""
=== SMART ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-09-10

PURPOSE:
Dynamic icebreaker generation using template-based approach with CSV column analysis.
Simple, modular system with prompt-based templates and minimal JSON configs.

CREATOR VISION:
- Analyze CSV columns dynamically
- Select best template based on available data
- Generate casual, iPhone-style icebreakers
- Track template performance for optimization

USAGE:
python smart_icebreaker_generator.py input.csv
"""

import os
import csv
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from openai import OpenAI

# Self-documenting statistics
SCRIPT_STATS = {
    "version": "1.0.0",
    "created": "2025-09-10",
    "total_runs": 0,
    "contacts_processed": 0,
    "icebreakers_generated": 0,
    "avg_processing_time": 0.0,
    "template_usage": {},
    "success_rate": 0.0,
    "last_updated": None
}

class SmartIcebreakerGenerator:
    """Dynamic icebreaker generator with template-based approach"""
    
    def __init__(self):
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "contacts_processed": 0,
            "templates_used": {},
            "api_calls": 0,
            "total_cost": 0.0,
            "errors": []
        }
        
        # Load OpenAI client
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env")
        
        self.openai_client = OpenAI(api_key=api_key)
        
        # Load templates and configs
        self.templates = self._load_templates()
        self.template_config = self._load_template_config()
        self.styles = self._load_styles()
        self.offers = self._load_offers()
        
        print(f"🚀 Smart Icebreaker Generator v{SCRIPT_STATS['version']} initialized")
        print(f"📋 Loaded {len(self.templates)} templates")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load all icebreaker templates from prompts directory"""
        templates = {}
        templates_dir = os.path.join(os.path.dirname(__file__), '../prompts/icebreaker_templates')
        
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir, exist_ok=True)
            self._create_default_templates(templates_dir)
        
        for filename in os.listdir(templates_dir):
            if filename.endswith('.txt'):
                template_name = filename.replace('.txt', '')
                filepath = os.path.join(templates_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        templates[template_name] = f.read().strip()
                except Exception as e:
                    print(f"⚠️ Error loading template {filename}: {e}")
        
        return templates
    
    def _create_default_templates(self, templates_dir):
        """Create default template files if they don't exist"""
        default_templates = {
            "template_01_achievement": """Hey {first_name}! 

Just saw {company_name} {achievement_context}. That's pretty impressive tbh. 

Quick q - {relevant_question}?""",
            
            "template_02_location": """Hey {first_name}! 

Fellow {city} business owner here 👋 

Love what you're doing with {company_name}. {location_context}

Wondering - {relevant_question}?""",
            
            "template_03_company_size": """Hi {first_name},

{company_name} with {estimated_num_employees} people - nice size for {industry_context}.

We just helped a similar {industry} company {success_story}.

Quick question: {relevant_question}?""",
            
            "template_04_title_based": """Hey {first_name}!

As {title} at {company_name}, you probably deal with {title_challenge} daily.

We just helped another {similar_title} {specific_result}.

Curious - {relevant_question}?""",
            
            "template_05_casual_intro": """Hey {first_name}! 

{company_name} caught my eye - {company_observation}.

btw we just {recent_success} for a similar company in {city}.

Worth a quick chat about {relevant_topic}?"""
        }
        
        for template_name, content in default_templates.items():
            filepath = os.path.join(templates_dir, f"{template_name}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"✅ Created {len(default_templates)} default templates")
    
    def _load_template_config(self) -> Dict:
        """Load template selection configuration"""
        config_path = os.path.join(os.path.dirname(__file__), '../prompts/template_mapping.json')
        
        default_config = {
            "column_priority": ["title", "city", "estimated_num_employees", "company_name", "headline"],
            "template_rules": {
                "has_title_ceo_founder": "template_01_achievement",
                "has_city": "template_02_location", 
                "has_employees_count": "template_03_company_size",
                "has_title": "template_04_title_based",
                "default": "template_05_casual_intro"
            },
            "casual_phrases": [
                "tbh", "btw", "rn", "quick q", "worth a chat",
                "caught my eye", "pretty impressive", "wondering"
            ]
        }
        
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            print("✅ Created default template mapping config")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config, using defaults: {e}")
            return default_config
    
    def _load_styles(self) -> Dict[str, str]:
        """Load writing styles"""
        styles = {}
        styles_dir = os.path.join(os.path.dirname(__file__), '../prompts/styles')
        
        if not os.path.exists(styles_dir):
            os.makedirs(styles_dir, exist_ok=True)
            self._create_default_styles(styles_dir)
        
        for filename in os.listdir(styles_dir):
            if filename.endswith('.txt'):
                style_name = filename.replace('.txt', '')
                filepath = os.path.join(styles_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        styles[style_name] = f.read().strip()
                except Exception as e:
                    print(f"⚠️ Error loading style {filename}: {e}")
        
        return styles
    
    def _create_default_styles(self, styles_dir):
        """Create default style files"""
        default_styles = {
            "casual_iphone": """Write like texting from iPhone:
- Short sentences
- Use casual abbreviations (tbh, btw, rn)
- Occasional emoji (👋, 🚀)  
- Natural, conversational tone
- No formal business language
- Sound like messaging a friend""",
            
            "friendly_business": """Professional but approachable:
- Warm, genuine tone
- Clear and direct
- Respectful but not stuffy
- Focus on mutual benefit
- Sound interested, not desperate""",
            
            "direct_value": """Straight to the point:
- Lead with value
- No fluff or small talk
- Specific numbers/results when possible
- Action-oriented
- Confident but not pushy"""
        }
        
        for style_name, content in default_styles.items():
            filepath = os.path.join(styles_dir, f"{style_name}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _load_offers(self) -> Dict[str, str]:
        """Load offer descriptions"""
        offers = {}
        offers_dir = os.path.join(os.path.dirname(__file__), '../prompts/offers')
        
        if not os.path.exists(offers_dir):
            os.makedirs(offers_dir, exist_ok=True)
            self._create_default_offers(offers_dir)
        
        for filename in os.listdir(offers_dir):
            if filename.endswith('.txt'):
                offer_name = filename.replace('.txt', '')
                filepath = os.path.join(offers_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        offers[offer_name] = f.read().strip()
                except Exception as e:
                    print(f"⚠️ Error loading offer {filename}: {e}")
        
        return offers
    
    def _create_default_offers(self, offers_dir):
        """Create default offer files"""
        default_offers = {
            "ai_automation": """AI automation systems that eliminate manual work and scale operations. 
We help businesses save 15-30 hours/week through intelligent automation of repetitive tasks.""",
            
            "lead_generation": """High-quality B2B lead generation services using advanced targeting and AI.
We deliver 50-200 qualified leads per month with 85%+ accuracy rates.""",
            
            "cold_outreach": """Done-for-you cold outreach campaigns with 15-25% response rates.
Complete lead research, personalization, and follow-up sequences."""
        }
        
        for offer_name, content in default_offers.items():
            filepath = os.path.join(offers_dir, f"{offer_name}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def analyze_csv_columns(self, csv_path: str) -> Dict[str, Any]:
        """Analyze available columns in CSV file"""
        print(f"\n🔍 Analyzing CSV structure: {os.path.basename(csv_path)}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames
                
                # Sample first few rows for data quality
                sample_rows = []
                for i, row in enumerate(reader):
                    if i >= 3:  # Just first 3 rows
                        break
                    sample_rows.append(row)
        
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return {}
        
        # Analyze column availability and quality
        analysis = {
            "available_columns": columns,
            "column_quality": {},
            "personalization_potential": {},
            "recommended_templates": []
        }
        
        # Check data quality for each column
        for col in columns:
            non_empty_count = sum(1 for row in sample_rows if row.get(col, '').strip())
            quality_score = non_empty_count / len(sample_rows) if sample_rows else 0
            analysis["column_quality"][col] = {
                "fill_rate": quality_score,
                "samples": [row.get(col, '')[:50] for row in sample_rows[:2]]
            }
        
        print(f"📊 Found {len(columns)} columns:")
        for col in columns[:10]:  # Show first 10 columns
            quality = analysis["column_quality"][col]["fill_rate"]
            print(f"   {col}: {quality:.1%} filled")
        
        return analysis
    
    def select_best_template(self, row_data: Dict, analysis: Dict) -> str:
        """Select optimal template based on available data"""
        rules = self.template_config["template_rules"]
        
        # Check rules in order of preference
        if row_data.get('title', '').lower() in ['ceo', 'founder', 'owner', 'president']:
            return rules.get("has_title_ceo_founder", rules["default"])
        
        if row_data.get('city', '').strip():
            return rules.get("has_city", rules["default"])
        
        if row_data.get('estimated_num_employees', '').strip():
            return rules.get("has_employees_count", rules["default"])
        
        if row_data.get('title', '').strip():
            return rules.get("has_title", rules["default"])
        
        return rules["default"]
    
    def generate_icebreaker(self, row_data: Dict, template_name: str, style: str = "casual_iphone", offer: str = "ai_automation") -> Dict:
        """Generate single icebreaker using selected template"""
        start_time = time.time()
        
        result = {
            "contact_name": row_data.get('first_name', 'Friend'),
            "company_name": row_data.get('company_name', 'Your Company'),
            "template_used": template_name,
            "icebreaker_text": "",
            "processing_time": 0,
            "success": False,
            "error": None
        }
        
        try:
            # Get template and style
            template = self.templates.get(template_name, self.templates.get("template_05_casual_intro", ""))
            style_guide = self.styles.get(style, self.styles.get("casual_iphone", ""))
            offer_description = self.offers.get(offer, self.offers.get("ai_automation", ""))
            
            # Create personalized prompt
            prompt = f"""Generate a personalized icebreaker email using this template and data:

TEMPLATE:
{template}

STYLE GUIDE:
{style_guide}

CONTACT DATA:
- Name: {row_data.get('first_name', 'Friend')}
- Company: {row_data.get('company_name', 'Company')}
- Title: {row_data.get('title', 'Team Member')}
- City: {row_data.get('city', 'their city')}
- Company Size: {row_data.get('estimated_num_employees', 'their team')} employees
- Headline: {row_data.get('headline', '')}

YOUR OFFER:
{offer_description}

REQUIREMENTS:
1. Fill in ALL template variables with specific data
2. Keep it under 50 words total
3. Sound natural and casual (iPhone texting style)
4. End with a relevant question
5. No obvious sales pitch in opening

Return only the final icebreaker text, no explanations."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at writing casual, high-converting cold outreach icebreakers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            icebreaker_text = response.choices[0].message.content.strip()
            
            # Track usage
            self.stats["api_calls"] += 1
            tokens_used = response.usage.total_tokens
            api_cost = (tokens_used / 1000) * 0.002  # GPT-3.5-turbo pricing
            self.stats["total_cost"] += api_cost
            
            # Update template usage tracking
            if template_name not in self.stats["templates_used"]:
                self.stats["templates_used"][template_name] = 0
            self.stats["templates_used"][template_name] += 1
            
            result.update({
                "icebreaker_text": icebreaker_text,
                "success": True,
                "tokens_used": tokens_used,
                "api_cost": api_cost
            })
            
            print(f"✅ Generated: {icebreaker_text[:50]}...")
            
        except Exception as e:
            error_msg = f"Error generating icebreaker: {str(e)}"
            result["error"] = error_msg
            self.stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
        
        result["processing_time"] = time.time() - start_time
        return result
    
    def process_csv(self, csv_path: str, output_path: str = None, style: str = "casual_iphone", offer: str = "ai_automation", limit: int = None) -> List[Dict]:
        """Process entire CSV file and generate icebreakers"""
        print(f"\n🔄 Processing CSV: {os.path.basename(csv_path)}")
        
        # Analyze CSV structure first
        analysis = self.analyze_csv_columns(csv_path)
        if not analysis:
            return []
        
        results = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    if limit and i >= limit:
                        break
                    
                    print(f"\n👤 Processing {i+1}: {row.get('first_name', 'Unknown')} at {row.get('company_name', 'Unknown')}")
                    
                    # Select best template
                    template_name = self.select_best_template(row, analysis)
                    print(f"📋 Selected template: {template_name}")
                    
                    # Generate icebreaker
                    result = self.generate_icebreaker(row, template_name, style, offer)
                    results.append(result)
                    
                    self.stats["contacts_processed"] += 1
                    
                    # Brief pause between API calls
                    time.sleep(0.5)
        
        except Exception as e:
            print(f"❌ Error processing CSV: {e}")
            return results
        
        # Save results if output path specified
        if output_path:
            self.save_results(results, output_path)
        
        return results
    
    def save_results(self, results: List[Dict], output_path: str):
        """Save results to JSON file with analytics"""
        output_data = {
            "metadata": {
                "generator_version": SCRIPT_STATS["version"],
                "generated_at": datetime.now().isoformat(),
                "session_stats": self.stats,
                "total_contacts": len(results),
                "success_rate": len([r for r in results if r["success"]]) / len(results) if results else 0
            },
            "results": results
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_path}")
    
    def generate_session_report(self):
        """Generate session summary"""
        print(f"\n{'='*60}")
        print(f"🚀 SMART ICEBREAKER GENERATOR - SESSION REPORT")
        print(f"{'='*60}")
        print(f"👤 Contacts Processed: {self.stats['contacts_processed']}")
        print(f"🤖 API Calls: {self.stats['api_calls']}")
        print(f"💰 Total Cost: ${self.stats['total_cost']:.4f}")
        
        if self.stats["templates_used"]:
            print(f"\n📋 Templates Used:")
            for template, count in self.stats["templates_used"].items():
                print(f"   {template}: {count}x")
        
        if self.stats["errors"]:
            print(f"\n⚠️  Errors ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][-3:]:
                print(f"   • {error}")
        
        print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python smart_icebreaker_generator.py input.csv [limit] [style] [offer]")
        print("Example: python smart_icebreaker_generator.py leads/raw/lumid_canada_20250108.csv 10 casual_iphone ai_automation")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    style = sys.argv[3] if len(sys.argv) > 3 else "casual_iphone"
    offer = sys.argv[4] if len(sys.argv) > 4 else "ai_automation"
    
    # Generate output path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"../../leads/processed/icebreakers_{timestamp}.json"
    
    generator = SmartIcebreakerGenerator()
    results = generator.process_csv(csv_path, output_path, style, offer, limit)
    generator.generate_session_report()