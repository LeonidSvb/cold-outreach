#!/usr/bin/env python3
"""
=== PERSONALIZATION EXTRACTOR ===
Version: 1.0.0 | Created: 2025-09-09

PURPOSE: 
Extract golden nuggets from website content for cold outreach personalization

CREATOR VISION:
- Analyze scraped website content to find unique, specific insights
- Extract personal details, recent achievements, company initiatives
- Identify conversation starters, shared interests, timely hooks
- Generate actionable personalization insights, not generic summaries

DEVELOPER IMPLEMENTATION:
- Process raw website content from previous pipeline stage
- Use dialogue-style prompting for consistent high-quality extraction
- Track costs, performance, and prompt versioning
- Output structured insights for icebreaker generation

USAGE:
extractor = PersonalizationExtractor()
insights = extractor.extract_insights(raw_content_data, company_name, contact_name)
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
    "companies_processed": 0,
    "insights_extracted": 0,
    "avg_insights_per_company": 0.0,
    "success_rate": 0.0,
    "avg_processing_time_seconds": 0.0,
    "avg_cost_per_company": 0.0,
    "prompt_version": "1.0.0",
    "last_updated": None,
    "changelog": {
        "1.0.0": "Initial implementation with golden nuggets extraction from website content"
    }
}

class PersonalizationExtractor:
    """Extract golden nuggets for personalization from website content"""
    
    def __init__(self):
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "companies_processed": 0,
            "total_insights_extracted": 0,
            "api_calls": 0,
            "total_tokens_used": 0,
            "total_cost_usd": 0.0,
            "processing_time_seconds": 0.0,
            "errors": [],
            "company_results": []
        }
        self.start_time = time.time()
        
        # Load API key and prompt
        env_path = os.path.join(os.path.dirname(__file__), '../../.env')
        api_key = None
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
            
        self.openai_client = OpenAI(api_key=api_key)
        self.prompt_template = self._load_prompt_template()
        
        print(f"Personalization Extractor v{SCRIPT_STATS['version']} initialized")
    
    def _load_prompt_template(self):
        """Load dialogue-style prompt template"""
        prompt_path = os.path.join(os.path.dirname(__file__), '../prompts/personalization_extractor.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"WARNING  Prompt file not found at {prompt_path}, using built-in prompt")
            return self._get_builtin_prompt()
    
    def _get_builtin_prompt(self):
        """Built-in prompt template as fallback"""
        return """You are an expert B2B sales researcher specialized in extracting personalization insights from website content.

Your task is to analyze website content and extract GOLDEN NUGGETS - specific, unique, actionable insights that can be used for highly personalized cold outreach.

FOCUS ON FINDING:
**Recent Achievements** - Awards, milestones, new launches, expansions
**Company Initiatives** - New services, strategic shifts, partnerships, hiring
**Personal Details** - Leadership backgrounds, interests, speaking engagements
**Business Insights** - Growth metrics, client wins, market positioning
**Unique Approaches** - Distinctive methodologies, philosophies, specializations
🔗 **Conversation Starters** - Shared connections, industry events, common interests

AVOID GENERIC INFORMATION:
AVOID: Basic company descriptions ("we provide marketing services")
AVOID: Standard service listings without unique angles
AVOID: Generic mission statements or boilerplate content
AVOID: Common industry buzzwords without specific context

OUTPUT REQUIREMENTS:
- 3-8 specific insights per company
- Each insight must be actionable for outreach personalization
- Include the source page/section for each insight
- Rate personalization value: HIGH, MEDIUM, LOW
- Explain HOW each insight can be used in outreach

Company: {company_name}
Contact Name: {contact_name}

Website content to analyze:
{website_content}

Respond in JSON format:
{
  "personalization_insights": [
    {
      "insight": "Specific insight extracted from content",
      "source": "URL or section where found",
      "personalization_value": "HIGH|MEDIUM|LOW",
      "outreach_application": "How to use this in cold outreach",
      "insight_type": "achievement|initiative|personal|business|unique_approach|conversation_starter"
    }
  ],
  "summary": "2-3 sentence summary of the most compelling personalization angles",
  "recommended_approach": "Suggested outreach strategy based on insights found"
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
    
    def extract_insights(self, raw_content_data, company_name, contact_name=None):
        """
        Extract personalization insights from raw website content
        
        Args:
            raw_content_data: Dict of URL -> content from website_intelligence_processor
            company_name: Company name for context
            contact_name: Optional contact name for personalized extraction
            
        Returns:
            Dict with personalization insights and metadata
        """
        start_time = time.time()
        result = {
            'company_name': company_name,
            'contact_name': contact_name,
            'personalization_insights': [],
            'summary': '',
            'recommended_approach': '',
            'processing_stats': {
                'pages_analyzed': 0,
                'insights_extracted': 0,
                'processing_time_seconds': 0,
                'api_cost_usd': 0.0,
                'success': False,
                'errors': []
            }
        }
        
        try:
            print(f"\nExtracting personalization insights: {company_name}")
            
            if not raw_content_data:
                error_msg = "No website content provided for analysis"
                result['processing_stats']['errors'].append(error_msg)
                print(f"AVOID: {error_msg}")
                return result
            
            # Prepare content for analysis
            content_for_analysis = []
            for url, content in raw_content_data.items():
                if content.get('text') and len(content['text'].strip()) > 50:
                    content_for_analysis.append({
                        'url': url,
                        'title': content.get('title', ''),
                        'text': content['text'][:2000],  # Limit for cost efficiency
                        'word_count': content.get('word_count', 0)
                    })
            
            if not content_for_analysis:
                error_msg = "No meaningful content found for analysis"
                result['processing_stats']['errors'].append(error_msg)
                print(f"AVOID: {error_msg}")
                return result
                
            result['processing_stats']['pages_analyzed'] = len(content_for_analysis)
            
            # Prepare prompt with content
            website_content_text = "\n\n".join([
                f"=== {content['title']} ({content['url']}) ===\n{content['text']}"
                for content in content_for_analysis
            ])
            
            # Format prompt - handle JSON placeholders by replacing them temporarily
            prompt_to_format = self.prompt_template
            prompt_to_format = prompt_to_format.replace('{', '{{').replace('}', '}}')
            prompt_to_format = prompt_to_format.replace('{{company_name}}', '{company_name}')
            prompt_to_format = prompt_to_format.replace('{{contact_name}}', '{contact_name}')  
            prompt_to_format = prompt_to_format.replace('{{website_content}}', '{website_content}')
            
            formatted_prompt = prompt_to_format.format(
                company_name=company_name,
                contact_name=contact_name or "the decision maker",
                website_content=website_content_text
            )
            
            print(f"Analyzing {len(content_for_analysis)} pages with OpenAI...")
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert B2B sales researcher. Extract specific, actionable personalization insights from website content."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Log API usage
            tokens_used = response.usage.total_tokens
            api_cost = self.log_api_call(tokens_used)
            result['processing_stats']['api_cost_usd'] = api_cost
            
            print(f"API cost: ${api_cost:.4f} ({tokens_used} tokens)")
            
            # Parse response
            try:
                insights_data = json.loads(response.choices[0].message.content)
                
                result['personalization_insights'] = insights_data.get('personalization_insights', [])
                result['summary'] = insights_data.get('summary', '')
                result['recommended_approach'] = insights_data.get('recommended_approach', '')
                result['processing_stats']['insights_extracted'] = len(result['personalization_insights'])
                result['processing_stats']['success'] = True
                
                self.stats["total_insights_extracted"] += len(result['personalization_insights'])
                
                print(f"SUCCESS: Extracted {len(result['personalization_insights'])} personalization insights")
                
                # Display insights preview
                for i, insight in enumerate(result['personalization_insights'][:3], 1):
                    print(f"   {i}. [{insight.get('personalization_value', 'UNKNOWN')}] {insight.get('insight', '')[:80]}...")
                
            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse OpenAI response as JSON: {str(e)}"
                result['processing_stats']['errors'].append(error_msg)
                print(f"AVOID: {error_msg}")
                print(f"Raw response: {response.choices[0].message.content[:200]}...")
                
        except Exception as e:
            error_msg = f"Critical error during insight extraction: {str(e)}"
            result['processing_stats']['errors'].append(error_msg)
            self.stats["errors"].append(error_msg)
            print(f"CRITICAL ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        
        # Calculate processing stats
        processing_time = time.time() - start_time
        result['processing_stats']['processing_time_seconds'] = processing_time
        
        self.stats["companies_processed"] += 1
        self.stats["processing_time_seconds"] += processing_time
        
        # Log company result
        self.stats["company_results"].append({
            'company_name': company_name,
            'pages_analyzed': result['processing_stats']['pages_analyzed'],
            'insights_extracted': result['processing_stats']['insights_extracted'],
            'processing_time': processing_time,
            'api_cost': result['processing_stats']['api_cost_usd'],
            'success': result['processing_stats']['success']
        })
        
        if result['processing_stats']['success']:
            print(f"SUCCESS: SUCCESS: {company_name} - {result['processing_stats']['insights_extracted']} insights in {processing_time:.2f}s")
        else:
            print(f"WARNING  FAILED: {company_name} - no insights extracted")
            
        return result
    
    def process_batch(self, website_intelligence_results):
        """Process multiple companies from website intelligence results"""
        print(f"\nProcessing personalization insights batch...")
        
        results = []
        
        for company_data in website_intelligence_results:
            if not company_data.get('raw_content_data'):
                print(f"WARNING  Skipping {company_data.get('company_name', 'Unknown')} - no content data")
                continue
                
            result = self.extract_insights(
                company_data['raw_content_data'],
                company_data.get('company_name', ''),
                company_data.get('contact_name')  # If available
            )
            results.append(result)
            
            # Brief pause between API calls
            time.sleep(0.5)
        
        return results
    
    def save_results(self, results, output_path=None):
        """Save personalization results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"../../leads/enriched/personalization_insights_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Prepare final output with metadata
        output_data = {
            'metadata': {
                'extractor_version': SCRIPT_STATS['version'],
                'prompt_version': SCRIPT_STATS['prompt_version'],
                'generated_at': datetime.now().isoformat(),
                'total_companies': len(results),
                'session_stats': self.stats,
                'global_stats': SCRIPT_STATS
            },
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Personalization insights saved to: {output_path}")
        return output_path
    
    def generate_session_report(self):
        """Generate detailed session report"""
        total_time = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print(f"PERSONALIZATION EXTRACTOR - SESSION REPORT")
        print(f"{'='*60}")
        print(f"Companies Processed: {self.stats['companies_processed']}")
        print(f"Total Insights Extracted: {self.stats['total_insights_extracted']}")
        print(f"API Calls Made: {self.stats['api_calls']}")
        print(f"Total Tokens Used: {self.stats['total_tokens_used']}")
        print(f" Total Processing Time: {total_time:.2f} seconds")
        print(f"Total API Cost: ${self.stats['total_cost_usd']:.4f}")
        
        if self.stats['companies_processed'] > 0:
            avg_insights = self.stats['total_insights_extracted'] / self.stats['companies_processed']
            avg_time = total_time / self.stats['companies_processed']
            avg_cost = self.stats['total_cost_usd'] / self.stats['companies_processed']
            success_rate = len([r for r in self.stats['company_results'] if r['success']]) / self.stats['companies_processed'] * 100
            
            print(f"Average Insights per Company: {avg_insights:.1f}")
            print(f" Average Time per Company: {avg_time:.2f} seconds")
            print(f"Average Cost per Company: ${avg_cost:.4f}")
            print(f"Success Rate: {success_rate:.1f}%")
        
        if self.stats['errors']:
            print(f"\nErrors Encountered ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][-3:]:  # Show last 3 errors
                print(f"   • {error}")
        
        print(f"{'='*60}")
        
        # Update global stats
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["companies_processed"] += self.stats['companies_processed']
        SCRIPT_STATS["insights_extracted"] += self.stats['total_insights_extracted']
        SCRIPT_STATS["last_updated"] = datetime.now().isoformat()
        
        if SCRIPT_STATS["companies_processed"] > 0:
            SCRIPT_STATS["avg_insights_per_company"] = SCRIPT_STATS["insights_extracted"] / SCRIPT_STATS["companies_processed"]
            SCRIPT_STATS["success_rate"] = len([r for r in self.stats['company_results'] if r['success']]) / SCRIPT_STATS["companies_processed"] * 100
            SCRIPT_STATS["avg_processing_time_seconds"] = total_time / self.stats['companies_processed']
            SCRIPT_STATS["avg_cost_per_company"] = self.stats['total_cost_usd'] / self.stats['companies_processed']


if __name__ == "__main__":
    import sys
    
    extractor = PersonalizationExtractor()
    
    # Test with sample data
    if len(sys.argv) > 1:
        # Load test data from file
        input_file = sys.argv[1]
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            if 'results' in test_data:  # Website intelligence format
                results = extractor.process_batch(test_data['results'])
                extractor.save_results(results)
                extractor.generate_session_report()
            else:
                print("AVOID: Invalid input file format")
                
        except Exception as e:
            print(f"CRITICAL ERROR: Error loading test data: {str(e)}")
    else:
        print("Usage: python personalization_extractor.py website_intelligence_results.json")
        print("Example: python personalization_extractor.py ../../leads/enriched/website_intelligence_20250909_123456.json")