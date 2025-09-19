#!/usr/bin/env python3
"""
=== LINK FILTER MODULE ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Filter relevant links from a list using AI-powered analysis for business intelligence

INPUT: 
- links (List[str]): List of URLs to filter
- max_links (int): Maximum links to return (default: 15)
- criteria (str): Custom filtering criteria (optional)

OUTPUT: 
List[str] of filtered links most relevant for personalization

FEATURES:
- AI-powered relevance assessment
- Business intelligence focus
- Customizable filtering criteria
- Automatic priority scoring
- Fallback rule-based filtering
"""

import sys
import os
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics (auto-updated by logger)
MODULE_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "links_processed": 0,
    "avg_filtered_count": 0,
    "last_run": None,
    "success_rate": 100.0
}

class LinkFilter:
    """Filters links based on business relevance"""
    
    def __init__(self, max_links: int = 15):
        self.max_links = max_links
        self.prompt_path = Path(__file__).parent.parent.parent / "prompts" / "link_filtering.txt"
        
        # Load filtering prompt
        if self.prompt_path.exists():
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                self.filtering_prompt = f.read()
        else:
            self.filtering_prompt = self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Default filtering prompt if file not found"""
        return """Filter these website links to find the most valuable pages for business intelligence.
        
        Include pages about: services, about us, team, case studies, news, contact.
        Exclude pages like: privacy policy, terms, login, technical docs.
        
        Return JSON format: {"filtered_links": ["url1", "url2", ...]}"""
    
    def _rule_based_filter(self, links: List[str]) -> List[str]:
        """Smart rule-based filtering - max 3-5 links with mandatory home page"""
        # MANDATORY: Always include home page first
        home_pages = []
        other_links = []
        
        for link in links:
            parsed = urlparse(link)
            path = parsed.path.lower().strip('/')
            
            # Identify home page (root domain or minimal path)
            if not path or path in ['', '#', '#content', 'index', 'home']:
                home_pages.append(link)
            else:
                other_links.append(link)
        
        # Start with home page
        filtered_links = []
        if home_pages:
            # Take the cleanest home page (prefer root domain)
            home_pages.sort(key=lambda x: len(urlparse(x).path))
            filtered_links.append(home_pages[0])
        
        # Smart scoring for remaining links
        high_priority_keywords = [
            'about', 'services', 'solutions', 'products', 'team', 'company',
            'case-studies', 'portfolio', 'work', 'projects', 'contact'
        ]
        
        exclude_keywords = [
            'privacy', 'terms', 'legal', 'login', 'account', 'cart', 
            'checkout', 'api', 'docs', 'support', 'help', 'blog', 'news',
            'careers', 'jobs', 'employment', 'author', 'category', 'tag'
        ]
        
        scored_links = []
        
        for link in other_links:
            path = urlparse(link).path.lower()
            score = 0
            
            # High priority pages get big boost
            for keyword in high_priority_keywords:
                if keyword in path:
                    score += 10
            
            # Exclude low-value pages  
            for keyword in exclude_keywords:
                if keyword in path:
                    score -= 20
            
            # Prefer main category pages over deep sub-pages
            path_depth = len([p for p in path.split('/') if p])
            if path_depth == 1:
                score += 5  # Main category pages
            elif path_depth == 2:
                score += 2  # Sub-category pages
            elif path_depth > 3:
                score -= 3  # Too deep
            
            # Bonus for key business pages
            if any(word in path for word in ['services', 'solutions', 'about', 'contact']):
                score += 5
                
            if score > 0:
                scored_links.append((score, link))
        
        # Sort by score and take top 2-4 additional links (home page + 2-4)
        scored_links.sort(reverse=True, key=lambda x: x[0])
        remaining_slots = min(self.max_links - 1, 4)  # Reserve 1 slot for home page
        
        for score, link in scored_links[:remaining_slots]:
            filtered_links.append(link)
        
        return filtered_links[:self.max_links]
    
    def _ai_filter_links(self, links: List[str]) -> List[str]:
        """AI-powered link filtering (placeholder for future implementation)"""
        # For now, use rule-based filtering
        # In future versions, this could integrate with OpenAI API
        print("AI filtering not implemented yet, using rule-based filtering")
        return self._rule_based_filter(links)
    
    def filter_links(self, links: List[str], criteria: Optional[str] = None) -> List[str]:
        """Main filtering method"""
        if not links:
            return []
        
        print(f"Filtering {len(links)} links (max return: {self.max_links})")
        
        try:
            # Use AI filtering if available, otherwise rule-based
            filtered = self._ai_filter_links(links)
            
            print(f"Filtered to {len(filtered)} relevant links")
            return filtered
            
        except Exception as e:
            print(f"Error in AI filtering, using rule-based fallback: {e}")
            return self._rule_based_filter(links)

@auto_log("link_filter")
def filter_relevant_links(links: List[str], max_links: int = 5, 
                         criteria: Optional[str] = None) -> List[str]:
    """
    Filter links to find most relevant pages for business intelligence
    
    Args:
        links: List of URLs to filter
        max_links: Maximum links to return (default: 15)
        criteria: Custom filtering criteria (optional)
    
    Returns:
        List[str]: Filtered links most relevant for personalization
    
    Example:
        all_links = ["https://example.com/about", "https://example.com/privacy", ...]
        relevant = filter_relevant_links(all_links, max_links=10)
        print(f"Selected {len(relevant)} relevant pages")
    """
    
    # Update module stats
    MODULE_STATS["total_runs"] += 1
    MODULE_STATS["links_processed"] += len(links)
    
    try:
        filter_engine = LinkFilter(max_links=max_links)
        result = filter_engine.filter_links(links, criteria)
        
        # Update stats
        MODULE_STATS["avg_filtered_count"] = (
            (MODULE_STATS["avg_filtered_count"] * (MODULE_STATS["total_runs"] - 1) + len(result)) 
            / MODULE_STATS["total_runs"]
        )
        MODULE_STATS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return result
        
    except Exception as e:
        print(f"Error filtering links: {e}")
        raise

def main():
    """CLI interface for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter relevant links for business intelligence")
    parser.add_argument("input", help="Input file with links (one per line) or JSON file")
    parser.add_argument("--max-links", type=int, default=15, help="Maximum links to return")
    parser.add_argument("--output", help="Output file to save filtered links")
    parser.add_argument("--criteria", help="Custom filtering criteria")
    
    args = parser.parse_args()
    
    print(f"Link Filter v{MODULE_STATS['version']}")
    print("=" * 50)
    
    # Read input links
    input_path = Path(args.input)
    if input_path.suffix.lower() == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            links = data.get('links', data.get('filtered_links', []))
    else:
        with open(input_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(links)} links from {input_path}")
    
    # Filter links
    filtered = filter_relevant_links(links, args.max_links, args.criteria)
    
    # Save results
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix.lower() == '.json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({"filtered_links": filtered}, f, indent=2)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                for link in filtered:
                    f.write(link + '\n')
        print(f"Filtered links saved to {args.output}")
    else:
        print(f"\nFiltered {len(filtered)} relevant links:")
        for i, link in enumerate(filtered, 1):
            print(f"{i:2d}. {link}")
    
    print(f"\nModule Stats: {MODULE_STATS}")

if __name__ == "__main__":
    main()