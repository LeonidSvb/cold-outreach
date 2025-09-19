#!/usr/bin/env python3
"""
=== CONTENT SUMMARIZER MODULE ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Extract key facts and insights from scraped content for personalization

INPUT: 
- content_data (Dict): Scraped content from content_scraper module
- focus_areas (List[str]): Specific areas to focus on (optional)
- output_format (str): 'detailed' or 'concise' (default: 'detailed')

OUTPUT: 
Dict with structured business intelligence and personalization hooks

FEATURES:
- Business intelligence extraction
- Personalization hook identification  
- Competitive advantage analysis
- Recent developments tracking
- Key contact extraction
- Rule-based + AI-powered analysis
"""

import sys
import os
import json
import time
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics (auto-updated by logger)
MODULE_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "content_analyzed": 0,
    "insights_extracted": 0,
    "last_run": None,
    "success_rate": 100.0
}

class ContentSummarizer:
    """Extracts business insights from scraped content"""
    
    def __init__(self, output_format: str = 'detailed'):
        self.output_format = output_format
        self.prompt_path = Path(__file__).parent.parent.parent / "prompts" / "summarization.txt"
        
        # Load summarization prompt
        if self.prompt_path.exists():
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                self.summarization_prompt = f.read()
        else:
            self.summarization_prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Default summarization prompt if file not found"""
        return """Extract key business information from this content for personalization:
        
        Focus on: company services, recent developments, competitive advantages, 
        personalization opportunities, and key contacts.
        
        Return structured JSON with these insights."""
    
    def _extract_company_info(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic company information"""
        metadata = content.get('metadata', {})
        main_content = content.get('content', {}).get('main_content', '')
        headings = content.get('content', {}).get('headings', [])
        
        company_info = {
            'business_focus': '',
            'industry': '',
            'size_indicators': '',
            'founding_info': ''
        }
        
        # Extract from title and description
        title = metadata.get('title', '')
        description = metadata.get('description', '')
        
        # Look for business focus in title/description
        if title:
            company_info['business_focus'] = title
        elif description:
            company_info['business_focus'] = description[:200]
        
        # Look for industry keywords
        industry_patterns = {
            'technology': ['software', 'tech', 'digital', 'AI', 'automation', 'development'],
            'marketing': ['marketing', 'advertising', 'branding', 'SEO', 'social media'],
            'consulting': ['consulting', 'advisory', 'strategy', 'transformation'],
            'finance': ['finance', 'accounting', 'investment', 'banking', 'fintech'],
            'healthcare': ['healthcare', 'medical', 'pharma', 'health', 'wellness'],
            'education': ['education', 'training', 'learning', 'courses', 'academy']
        }
        
        text_to_analyze = (main_content + ' ' + title + ' ' + description).lower()
        
        for industry, keywords in industry_patterns.items():
            if any(keyword in text_to_analyze for keyword in keywords):
                company_info['industry'] = industry
                break
        
        # Look for size indicators
        size_patterns = [
            r'(\d+)\s*(?:employees?|team members?|people)',
            r'founded in (\d{4})',
            r'since (\d{4})',
            r'(\d+)\s*(?:years?|offices?|locations?)'
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, text_to_analyze)
            if matches:
                company_info['size_indicators'] = ', '.join(matches[:3])
                break
        
        return company_info
    
    def _extract_services(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract services and solutions"""
        main_content = content.get('content', {}).get('main_content', '')
        headings = content.get('content', {}).get('headings', [])
        
        services = []
        
        # Look for service-related headings
        service_keywords = ['service', 'solution', 'offering', 'product', 'expertise']
        service_headings = []
        
        for heading in headings:
            heading_text = heading.get('text', '').lower()
            if any(keyword in heading_text for keyword in service_keywords):
                service_headings.append(heading['text'])
        
        # Extract services from headings and nearby content
        for heading in service_headings[:5]:  # Limit to top 5
            services.append({
                'name': heading,
                'description': f"Service related to {heading}",
                'unique_value': 'Specialized offering'
            })
        
        return services
    
    def _extract_recent_developments(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract recent news and developments"""
        main_content = content.get('content', {}).get('main_content', '')
        
        developments = []
        
        # Look for time indicators
        recent_patterns = [
            r'(recently|new|latest|just|announced|launched|introducing)',
            r'(2024|2025|this year|last month)',
            r'(partnership|collaboration|award|expansion|growth)'
        ]
        
        sentences = main_content.split('.')
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            sentence_lower = sentence.lower()
            
            for pattern in recent_patterns:
                if re.search(pattern, sentence_lower):
                    developments.append({
                        'type': 'general',
                        'description': sentence.strip()[:200],
                        'date_indicator': 'Recent'
                    })
                    break
        
        return developments[:3]  # Limit to top 3
    
    def _extract_competitive_advantages(self, content: Dict[str, Any]) -> List[str]:
        """Extract competitive advantages"""
        main_content = content.get('content', {}).get('main_content', '')
        
        advantages = []
        
        # Look for advantage indicators
        advantage_patterns = [
            r'(unique|exclusive|proprietary|specialized|expert)',
            r'(award-winning|certified|accredited|recognized)',
            r'(leading|top|best|premier|trusted)'
        ]
        
        sentences = main_content.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            for pattern in advantage_patterns:
                if re.search(pattern, sentence_lower) and len(sentence.strip()) > 20:
                    advantages.append(sentence.strip()[:150])
                    break
        
        return list(set(advantages))[:3]  # Remove duplicates, limit to 3
    
    def _extract_personalization_hooks(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract personalization opportunities"""
        main_content = content.get('content', {}).get('main_content', '')
        
        hooks = []
        
        # Look for pain points
        pain_patterns = [
            r'(challenge|problem|difficulty|struggle|issue)',
            r'(solve|address|overcome|tackle|handle)'
        ]
        
        # Look for specializations
        spec_patterns = [
            r'(specialize|focus|expert|dedicated)',
            r'(industry|sector|market|niche)'
        ]
        
        sentences = main_content.split('.')
        
        for sentence in sentences[:15]:
            sentence_lower = sentence.lower()
            
            for pattern in pain_patterns:
                if re.search(pattern, sentence_lower):
                    hooks.append({
                        'hook_type': 'pain_point',
                        'description': sentence.strip()[:150]
                    })
                    break
        
        return hooks[:5]  # Limit to top 5
    
    def _extract_key_contacts(self, content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract key contacts mentioned"""
        main_content = content.get('content', {}).get('main_content', '')
        
        contacts = []
        
        # Look for name patterns with titles
        name_patterns = [
            r'(CEO|CTO|CMO|VP|Director|Manager|Founder)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(CEO|CTO|CMO|VP|Director|Manager|Founder)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, main_content)
            for match in matches[:3]:  # Limit to 3
                if isinstance(match, tuple) and len(match) == 2:
                    contacts.append({
                        'name': match[1] if match[1].replace(' ', '').isalpha() else match[0],
                        'role': match[0] if match[0] in ['CEO', 'CTO', 'CMO', 'VP', 'Director', 'Manager', 'Founder'] else match[1],
                        'context': 'Mentioned on website'
                    })
        
        return contacts
    
    def _summarize_content(self, content_data: Dict[str, Any], 
                          focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Main summarization logic"""
        
        # If multiple URLs in content_data, process each
        if isinstance(content_data, dict) and any(isinstance(v, dict) and 'content' in v for v in content_data.values()):
            # Multiple URLs format
            all_summaries = {}
            
            for url, content in content_data.items():
                if content.get('success', False):
                    all_summaries[url] = self._summarize_single_content(content, focus_areas)
                else:
                    all_summaries[url] = {
                        'error': content.get('error', 'Failed to scrape'),
                        'success': False
                    }
            
            return all_summaries
        else:
            # Single content format
            return self._summarize_single_content(content_data, focus_areas)
    
    def _summarize_single_content(self, content: Dict[str, Any], 
                                 focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """Summarize single piece of content"""
        
        summary = {
            'url': content.get('url', 'unknown'),
            'summarized_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'company_summary': self._extract_company_info(content),
            'services': self._extract_services(content),
            'recent_developments': self._extract_recent_developments(content),
            'competitive_advantages': self._extract_competitive_advantages(content),
            'personalization_hooks': self._extract_personalization_hooks(content),
            'key_contacts': self._extract_key_contacts(content),
            'engagement_opportunities': [
                'Website contact form',
                'LinkedIn outreach',
                'Email to general contact'
            ]
        }
        
        # Filter by focus areas if specified
        if focus_areas:
            filtered_summary = {'url': summary['url'], 'summarized_at': summary['summarized_at']}
            for area in focus_areas:
                if area in summary:
                    filtered_summary[area] = summary[area]
            return filtered_summary
        
        return summary

@auto_log("content_summarizer")
def summarize_for_personalization(content_data: Dict[str, Any], 
                                focus_areas: Optional[List[str]] = None,
                                output_format: str = 'detailed') -> Dict[str, Any]:
    """
    Extract key facts and insights from scraped content for personalization
    
    Args:
        content_data: Scraped content from content_scraper module
        focus_areas: Specific areas to focus on (optional)
        output_format: 'detailed' or 'concise' (default: 'detailed')
    
    Returns:
        Dict with structured business intelligence and personalization hooks
    
    Example:
        scraped_data = scrape_urls_to_clean_json(["https://example.com"])
        insights = summarize_for_personalization(scraped_data)
        
        for url, summary in insights.items():
            print(f"Company: {summary['company_summary']['business_focus']}")
            print(f"Services: {len(summary['services'])}")
            print(f"Hooks: {len(summary['personalization_hooks'])}")
    """
    
    # Update module stats
    MODULE_STATS["total_runs"] += 1
    MODULE_STATS["content_analyzed"] += len(content_data) if isinstance(content_data, dict) else 1
    
    try:
        summarizer = ContentSummarizer(output_format=output_format)
        result = summarizer._summarize_content(content_data, focus_areas)
        
        # Count insights extracted
        if isinstance(result, dict):
            insights_count = 0
            for summary in result.values() if isinstance(result, dict) and 'url' not in result else [result]:
                if isinstance(summary, dict):
                    insights_count += len(summary.get('services', []))
                    insights_count += len(summary.get('recent_developments', []))
                    insights_count += len(summary.get('competitive_advantages', []))
                    insights_count += len(summary.get('personalization_hooks', []))
                    insights_count += len(summary.get('key_contacts', []))
            
            MODULE_STATS["insights_extracted"] += insights_count
        
        MODULE_STATS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Content summarization complete!")
        return result
        
    except Exception as e:
        print(f"Error summarizing content: {e}")
        raise

def main():
    """CLI interface for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Summarize scraped content for personalization")
    parser.add_argument("input", help="Input JSON file with scraped content")
    parser.add_argument("--output", help="Output JSON file for summaries")
    parser.add_argument("--format", choices=['detailed', 'concise'], default='detailed',
                       help="Output format")
    parser.add_argument("--focus", nargs='+', help="Focus areas (e.g., services recent_developments)")
    
    args = parser.parse_args()
    
    print(f"Content Summarizer v{MODULE_STATS['version']}")
    print("=" * 50)
    
    # Load scraped content
    with open(args.input, 'r', encoding='utf-8') as f:
        content_data = json.load(f)
    
    print(f"Loaded content from {args.input}")
    
    # Summarize content
    summaries = summarize_for_personalization(
        content_data,
        focus_areas=args.focus,
        output_format=args.format
    )
    
    # Save summaries
    output_path = Path(args.output) if args.output else Path(args.input).with_name('summaries.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    
    print(f"Summaries saved to {output_path}")
    
    # Show quick stats
    if isinstance(summaries, dict):
        total_insights = 0
        for summary in summaries.values():
            if isinstance(summary, dict) and 'services' in summary:
                total_insights += len(summary.get('services', []))
                total_insights += len(summary.get('recent_developments', []))
                total_insights += len(summary.get('personalization_hooks', []))
        
        print(f"Extracted {total_insights} total insights")
    
    print(f"Module Stats: {MODULE_STATS}")

if __name__ == "__main__":
    main()