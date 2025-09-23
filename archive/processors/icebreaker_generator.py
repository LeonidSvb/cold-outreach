#!/usr/bin/env python3
"""
=== ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-09-09

PURPOSE: 
Generate highly personalized icebreakers for cold outreach using extracted insights

CREATOR VISION:
- Transform personalization insights into compelling conversation openers
- Create authentic, non-salesy icebreakers that feel genuine
- Use proven examples and patterns for maximum response rates
- Generate multiple options per contact for A/B testing

DEVELOPER IMPLEMENTATION:
- Process personalization insights from previous pipeline stage
- Use dialogue-style prompting with proven icebreaker examples
- Generate 2-3 icebreaker variations per contact
- Include reasoning and expected response rates for each option

USAGE:
generator = IcebreakerGenerator()
icebreakers = generator.generate_icebreakers(insights_data, contact_info, offer_details)
"""

import os
import json
import time
from datetime import datetime
from openai import OpenAI

# Self-documenting statistics with versioning
SCRIPT_STATS = {
    "version": "1.0.0",
    "created": "2025-09-09",
    "total_runs": 0,
    "contacts_processed": 0,
    "icebreakers_generated": 0,
    "avg_icebreakers_per_contact": 0.0,
    "success_rate": 0.0,
    "avg_processing_time_seconds": 0.0,
    "avg_cost_per_contact": 0.0,
    "prompt_version": "1.0.0",
    "last_updated": None,
    "changelog": {
        "1.0.0": "Initial implementation with proven icebreaker patterns and examples"
    }
}

class IcebreakerGenerator:
    """Generate personalized icebreakers from insights data"""
    
    def __init__(self):
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "contacts_processed": 0,
            "total_icebreakers_generated": 0,
            "api_calls": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "processing_time_seconds": 0.0,
            "errors": [],
            "contact_results": []
        }
        self.start_time = time.time()
        
        # Load API key and prompt
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
            
        self.openai_client = OpenAI(api_key=api_key)
        self.prompt_template = self._load_prompt_template()
        
        print(f"💬 Icebreaker Generator v{SCRIPT_STATS['version']} initialized")
    
    def _load_prompt_template(self):
        """Load dialogue-style prompt template"""
        prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/icebreaker_generator.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"⚠️  Prompt file not found at {prompt_path}, using built-in prompt")
            return self._get_builtin_prompt()
    
    def _get_builtin_prompt(self):
        """Built-in prompt template as fallback"""
        return """You are an expert cold outreach copywriter specialized in creating high-converting icebreakers for B2B sales.

Your task is to create 2-3 personalized icebreaker variations using the provided insights about the prospect and their company.

ICEBREAKER REQUIREMENTS:
✅ **Authentic & Genuine** - Sound like a real person, not a sales bot
✅ **Specific & Researched** - Use actual details from their website/content  
✅ **Conversational** - Natural tone that invites a response
✅ **Value-Focused** - Lead with their interest, not your pitch
✅ **Concise** - 2-3 sentences maximum per icebreaker
✅ **Hook-Driven** - Create curiosity or desire to respond

PROVEN ICEBREAKER PATTERNS:

🎯 **Recent Achievement Pattern**
"Congrats on [specific achievement]. I noticed [specific detail] - that's impressive because [reason]. I'm curious about [relevant question]..."

🏢 **Company Initiative Pattern** 
"Saw you're expanding into [specific area]. We helped [similar company] with [similar challenge] and [specific result]. Wondering if [relevant question]..."

💡 **Insight/Observation Pattern**
"Your approach to [specific methodology] caught my attention, especially [specific detail]. Most agencies struggle with [common challenge]. How are you handling [relevant aspect]?"

🔗 **Connection/Common Ground Pattern**
"Fellow [shared connection/interest] here! Loved your thoughts on [specific content]. We've been working with similar companies on [relevant challenge]. Quick question: [relevant question]..."

❌ **AVOID THESE MISTAKES:**
- Generic compliments ("great website")
- Immediate sales pitches
- Fake urgency or pressure
- Overly long introductions
- Obvious templates or mass messaging

Contact: {contact_name} at {company_name}
Your Service/Offer: {offer_details}

Available Personalization Insights:
{personalization_insights}

Generate 2-3 icebreaker variations in JSON format:
{
  "icebreakers": [
    {
      "version": "A|B|C",
      "icebreaker_text": "The actual icebreaker message text (2-3 sentences)",
      "pattern_used": "achievement|initiative|insight|connection",
      "primary_insight": "Which specific insight this icebreaker leverages",
      "expected_response_rate": "HIGH|MEDIUM|LOW",
      "reasoning": "Why this icebreaker should work for this prospect",
      "follow_up_strategy": "Suggested next step if they respond positively"
    }
  ],
  "recommended_version": "A|B|C",
  "overall_strategy": "Brief explanation of the personalization approach used"
}"""
    
    def log_api_call(self, tokens_used, model="gpt-3.5-turbo"):
        """Track API usage and costs"""
        self.stats["api_calls"] += 1
        self.stats["total_tokens_used"] += tokens_used
        
        # GPT-3.5-turbo pricing (as of 2025)
        cost_per_1k_tokens = 0.002
        call_cost = (tokens_used / 1000) * cost_per_1k_tokens
        self.stats["total_cost_usd"] += call_cost
        
        return call_cost
    
    def generate_icebreakers(self, insights_data, contact_name=None, company_name=None, offer_details=None):
        """
        Generate personalized icebreakers from insights data
        
        Args:
            insights_data: Dict with personalization_insights from personalization_extractor
            contact_name: Name of the contact person
            company_name: Company name
            offer_details: Description of your service/offer
            
        Returns:
            Dict with generated icebreakers and metadata
        """
        start_time = time.time()
        
        # Extract data from insights_data if not provided directly
        if not company_name and 'company_name' in insights_data:
            company_name = insights_data['company_name']
        if not contact_name and 'contact_name' in insights_data:
            contact_name = insights_data['contact_name']
            
        result = {
            'contact_name': contact_name or 'Decision Maker',
            'company_name': company_name or 'Target Company',
            'offer_details': offer_details or 'Our services',
            'icebreakers': [],
            'recommended_version': '',
            'overall_strategy': '',
            'processing_stats': {
                'icebreakers_generated': 0,
                'processing_time_seconds': 0,
                'api_cost_usd': 0.0,
                'success': False,
                'errors': []
            }
        }
        
        try:
            print(f"\n💬 Generating icebreakers: {contact_name} at {company_name}")
            
            # Extract insights from data
            personalization_insights = insights_data.get('personalization_insights', [])
            
            if not personalization_insights:
                error_msg = "No personalization insights provided"
                result['processing_stats']['errors'].append(error_msg)
                print(f"❌ {error_msg}")
                return result
            
            # Format insights for prompt
            insights_text = "\n".join([
                f"• {insight.get('insight', '')} (Source: {insight.get('source', '')}) "
                f"[{insight.get('personalization_value', 'UNKNOWN')}] - {insight.get('outreach_application', '')}"
                for insight in personalization_insights
            ])
            
            # Default offer if not provided
            if not offer_details:
                offer_details = "AI automation and digital marketing solutions that help agencies scale their operations and improve client results"
            
            # Format prompt
            formatted_prompt = self.prompt_template.format(
                contact_name=result['contact_name'],
                company_name=result['company_name'],
                offer_details=offer_details,
                personalization_insights=insights_text
            )
            
            print(f"🤖 Generating icebreakers with {len(personalization_insights)} insights...")
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert cold outreach copywriter. Generate highly personalized, authentic icebreakers that feel genuine and invite responses."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,  # Slightly higher for creativity
                max_tokens=800
            )
            
            # Log API usage
            tokens_used = response.usage.total_tokens
            api_cost = self.log_api_call(tokens_used)
            result['processing_stats']['api_cost_usd'] = api_cost
            
            print(f"💰 API cost: ${api_cost:.4f} ({tokens_used} tokens)")
            
            # Parse response
            try:
                icebreaker_data = json.loads(response.choices[0].message.content)
                
                result['icebreakers'] = icebreaker_data.get('icebreakers', [])
                result['recommended_version'] = icebreaker_data.get('recommended_version', 'A')
                result['overall_strategy'] = icebreaker_data.get('overall_strategy', '')
                result['processing_stats']['icebreakers_generated'] = len(result['icebreakers'])
                result['processing_stats']['success'] = True
                
                self.stats["total_icebreakers_generated"] += len(result['icebreakers'])
                
                print(f"✅ Generated {len(result['icebreakers'])} icebreaker variations")
                
                # Display icebreakers preview
                for i, icebreaker in enumerate(result['icebreakers'], 1):
                    version = icebreaker.get('version', f'V{i}')
                    response_rate = icebreaker.get('expected_response_rate', 'UNKNOWN')
                    text_preview = icebreaker.get('icebreaker_text', '')[:100] + "..."
                    print(f"   {version} [{response_rate}]: {text_preview}")
                
                if result['recommended_version']:
                    print(f"🎯 Recommended version: {result['recommended_version']}")
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse OpenAI response as JSON: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"❌ {error_msg}")
                print(f"Raw response: {response.choices[0].message.content[:300]}...")
                
        except Exception as e:
            error_msg = f"Critical error during icebreaker generation: {str(e)}"
            result['processing_stats']['errors'].append(error_msg)
            self.stats["errors"].append(error_msg)
            print(f"💥 CRITICAL ERROR: {error_msg}")
        
        # Calculate processing stats
        processing_time = time.time() - start_time
        result['processing_stats']['processing_time_seconds'] = processing_time
        
        self.stats["contacts_processed"] += 1
        self.stats["processing_time_seconds"] += processing_time
        
        # Log contact result
        self.stats["contact_results"].append({
            'contact_name': result['contact_name'],
            'company_name': result['company_name'],
            'icebreakers_generated': result['processing_stats']['icebreakers_generated'],
            'processing_time': processing_time,
            'api_cost': result['processing_stats']['api_cost_usd'],
            'success': result['processing_stats']['success']
        })
        
        if result['processing_stats']['success']:
            print(f"🎉 SUCCESS: {result['processing_stats']['icebreakers_generated']} icebreakers in {processing_time:.2f}s")
        else:
            print(f"⚠️  FAILED: No icebreakers generated for {result['contact_name']}")
            
        return result
    
    def process_batch(self, personalization_results, offer_details=None):
        """Process multiple contacts from personalization results"""
        print(f"\n🔄 Processing icebreaker generation batch...")
        
        results = []
        
        for contact_data in personalization_results:
            result = self.generate_icebreakers(
                contact_data,
                contact_data.get('contact_name'),
                contact_data.get('company_name'),
                offer_details
            )
            results.append(result)
            
            # Brief pause between API calls
            time.sleep(0.5)
        
        return results
    
    def save_results(self, results, output_path=None):
        """Save icebreaker results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"../../leads/ready/icebreakers_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare final output with metadata
        output_data = {
            'metadata': {
                'generator_version': SCRIPT_STATS['version'],
                'prompt_version': SCRIPT_STATS['prompt_version'],
                'generated_at': datetime.now().isoformat(),
                'total_contacts': len(results),
                'session_stats': self.stats,
                'global_stats': SCRIPT_STATS
            },
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Icebreakers saved to: {output_path}")
        return output_path
    
    def generate_csv_output(self, results, output_path=None):
        """Generate CSV with final campaign-ready data"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"../../leads/ready/campaign_ready_{timestamp}.csv"
            
        import csv
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'company_name', 'contact_name', 'offer_details',
                'icebreaker_a', 'icebreaker_b', 'icebreaker_c',
                'recommended_version', 'personalization_summary', 
                'generation_date', 'processing_success'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Extract icebreakers
                icebreakers = result.get('icebreakers', [])
                icebreaker_dict = {}
                
                for i, icebreaker in enumerate(icebreakers[:3]):  # Max 3 variations
                    version_key = f'icebreaker_{["a","b","c"][i]}'
                    icebreaker_dict[version_key] = icebreaker.get('icebreaker_text', '')
                
                # Fill missing variations
                for version in ['a', 'b', 'c']:
                    if f'icebreaker_{version}' not in icebreaker_dict:
                        icebreaker_dict[f'icebreaker_{version}'] = ''
                
                writer.writerow({
                    'company_name': result.get('company_name', ''),
                    'contact_name': result.get('contact_name', ''),
                    'offer_details': result.get('offer_details', ''),
                    'icebreaker_a': icebreaker_dict.get('icebreaker_a', ''),
                    'icebreaker_b': icebreaker_dict.get('icebreaker_b', ''),
                    'icebreaker_c': icebreaker_dict.get('icebreaker_c', ''),
                    'recommended_version': result.get('recommended_version', 'A'),
                    'personalization_summary': result.get('overall_strategy', ''),
                    'generation_date': datetime.now().strftime('%Y-%m-%d'),
                    'processing_success': result['processing_stats']['success']
                })
        
        print(f"📊 Campaign-ready CSV saved to: {output_path}")
        return output_path
    
    def generate_session_report(self):
        """Generate detailed session report"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"💬 ICEBREAKER GENERATOR - SESSION REPORT")
        print(f"{'='*60}")
        print(f"👤 Contacts Processed: {self.stats['contacts_processed']}")
        print(f"💬 Total Icebreakers Generated: {self.stats['total_icebreakers_generated']}")
        print(f"🤖 API Calls Made: {self.stats['api_calls']}")
        print(f"🎯 Total Tokens Used: {self.stats['total_tokens_used']}")
        print(f"⏱️  Total Processing Time: {total_time:.2f} seconds")
        print(f"💰 Total API Cost: ${self.stats['total_cost_usd']:.4f}")
        
        if self.stats['contacts_processed'] > 0:
            avg_icebreakers = self.stats['total_icebreakers_generated'] / self.stats['contacts_processed']
            avg_time = total_time / self.stats['contacts_processed']
            avg_cost = self.stats['total_cost_usd'] / self.stats['contacts_processed']
            success_rate = len([r for r in self.stats['contact_results'] if r['success']]) / self.stats['contacts_processed'] * 100
            
            print(f"📊 Average Icebreakers per Contact: {avg_icebreakers:.1f}")
            print(f"⏱️  Average Time per Contact: {avg_time:.2f} seconds")
            print(f"💵 Average Cost per Contact: ${avg_cost:.4f}")
            print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors Encountered ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][-3:]:  # Show last 3 errors
                print(f"   • {error}")
        
        print(f"{'='*60}")
        
        # Update global stats
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["contacts_processed"] += self.stats['contacts_processed']
        SCRIPT_STATS["icebreakers_generated"] += self.stats['total_icebreakers_generated']
        SCRIPT_STATS["last_updated"] = datetime.now().isoformat()
        
        if SCRIPT_STATS["contacts_processed"] > 0:
            SCRIPT_STATS["avg_icebreakers_per_contact"] = SCRIPT_STATS["icebreakers_generated"] / SCRIPT_STATS["contacts_processed"]
            SCRIPT_STATS["success_rate"] = len([r for r in self.stats['contact_results'] if r['success']]) / SCRIPT_STATS["contacts_processed"] * 100
            SCRIPT_STATS["avg_processing_time_seconds"] = total_time / self.stats['contacts_processed']
            SCRIPT_STATS["avg_cost_per_contact"] = self.stats['total_cost_usd'] / self.stats['contacts_processed']


if __name__ == "__main__":
    import sys
    
    generator = IcebreakerGenerator()
    
    # Test with sample data
    if len(sys.argv) > 1:
        # Load personalization insights from file
        input_file = sys.argv[1]
        offer_details = sys.argv[2] if len(sys.argv) > 2 else None
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            if 'results' in test_data:  # Personalization insights format
                results = generator.process_batch(test_data['results'], offer_details)
                generator.save_results(results)
                generator.generate_csv_output(results)
                generator.generate_session_report()
            else:
                print("❌ Invalid input file format")
                
        except Exception as e:
            print(f"💥 Error loading test data: {str(e)}")
    else:
        print("Usage: python icebreaker_generator.py personalization_insights.json [offer_details]")
        print("Example: python icebreaker_generator.py ../../leads/enriched/personalization_insights_20250909_123456.json")