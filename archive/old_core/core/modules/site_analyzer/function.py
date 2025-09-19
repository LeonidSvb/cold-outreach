#!/usr/bin/env python3
"""
=== SITE ANALYZER MODULE ===
Version: 1.0.0 | Created: 2025-09-12

PURPOSE: 
Analyze websites to determine optimal scraping method:
- HTTP-only scraping for simple sites
- Apify for JavaScript-heavy sites

OUTPUT:
{
    "url": "https://example.com",
    "scraping_method": "http|apify",
    "confidence": 0.85,
    "content_quality": "high|medium|low",
    "reasons": ["Static content", "No JavaScript rendering needed"],
    "http_test": {
        "status_code": 200,
        "content_length": 50000,
        "has_content": true,
        "content_sample": "..."
    },
    "js_indicators": {
        "has_spa_framework": false,
        "has_async_content": false,
        "protection_detected": false
    }
}
"""

import sys
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import re
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics
MODULE_STATS = {
    "version": "1.0.0", 
    "total_runs": 0,
    "sites_analyzed": 0,
    "http_suitable": 0,
    "apify_needed": 0,
    "last_run": None,
    "success_rate": 100.0
}

class SiteAnalyzer:
    """Analyzes websites to determine optimal scraping method"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def analyze_site(self, url: str) -> Dict[str, Any]:
        """Analyze a single website to determine scraping method"""
        
        result = {
            "url": url,
            "scraping_method": "unknown",
            "confidence": 0.0,
            "content_quality": "unknown",
            "reasons": [],
            "http_test": {},
            "js_indicators": {},
            "recommendation": ""
        }
        
        try:
            # Step 1: HTTP test
            http_result = self._test_http_scraping(url)
            result["http_test"] = http_result
            
            if not http_result.get("accessible"):
                result["scraping_method"] = "apify"
                result["confidence"] = 0.9
                result["reasons"].append("Site not accessible via HTTP")
                result["recommendation"] = "Use Apify - site blocked/protected"
                return result
            
            # Step 2: Content analysis
            content_analysis = self._analyze_content_quality(http_result.get("html", ""))
            result["content_quality"] = content_analysis["quality"]
            
            # Step 3: JavaScript detection
            js_analysis = self._detect_javascript_dependency(http_result.get("html", ""))
            result["js_indicators"] = js_analysis
            
            # Step 4: Make recommendation
            recommendation = self._make_recommendation(http_result, content_analysis, js_analysis)
            result.update(recommendation)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            result["scraping_method"] = "apify"
            result["confidence"] = 0.5
            result["reasons"].append(f"Error during analysis: {e}")
            result["recommendation"] = "Use Apify - analysis failed"
            return result
    
    def _test_http_scraping(self, url: str) -> Dict[str, Any]:
        """Test if site is accessible via simple HTTP"""
        
        result = {
            "accessible": False,
            "status_code": None,
            "content_length": 0,
            "response_time": 0,
            "has_content": False,
            "html": "",
            "content_sample": ""
        }
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10, allow_redirects=True)
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                result["accessible"] = True
                result["html"] = response.text
                result["content_length"] = len(response.text)
                
                # Check if we got meaningful content
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text().strip()
                
                if len(text_content) > 500:  # Minimum content threshold
                    result["has_content"] = True
                    result["content_sample"] = text_content[:300] + "..."
                
        except requests.exceptions.RequestException as e:
            result["error"] = str(e)
            
        return result
    
    def _analyze_content_quality(self, html: str) -> Dict[str, Any]:
        """Analyze quality of HTTP-scraped content"""
        
        if not html:
            return {"quality": "none", "score": 0}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()
            
            # Quality indicators
            score = 0
            indicators = []
            
            # Text length
            if len(text_content) > 2000:
                score += 30
                indicators.append("Rich text content")
            elif len(text_content) > 500:
                score += 15
                indicators.append("Moderate text content")
            
            # Structured content
            if soup.find_all(['h1', 'h2', 'h3']):
                score += 20
                indicators.append("Has structured headings")
                
            if soup.find_all(['p']):
                score += 15
                indicators.append("Has paragraph content")
                
            # Navigation and links
            if soup.find_all('nav') or soup.find_all('a'):
                score += 10
                indicators.append("Has navigation")
                
            # Business-relevant content
            business_keywords = ['about', 'services', 'contact', 'team', 'products', 'solutions']
            content_lower = text_content.lower()
            for keyword in business_keywords:
                if keyword in content_lower:
                    score += 3
                    
            # Determine quality level
            if score >= 60:
                quality = "high"
            elif score >= 30:
                quality = "medium"  
            else:
                quality = "low"
                
            return {
                "quality": quality,
                "score": score,
                "indicators": indicators,
                "text_length": len(text_content)
            }
            
        except Exception:
            return {"quality": "low", "score": 0}
    
    def _detect_javascript_dependency(self, html: str) -> Dict[str, Any]:
        """Detect if site heavily depends on JavaScript"""
        
        indicators = {
            "has_spa_framework": False,
            "has_async_content": False,
            "has_dynamic_loading": False,
            "protection_detected": False,
            "js_frameworks": [],
            "risk_score": 0
        }
        
        if not html:
            return indicators
            
        html_lower = html.lower()
        
        # SPA Framework detection
        spa_frameworks = ['react', 'angular', 'vue', 'ember', 'backbone']
        for framework in spa_frameworks:
            if framework in html_lower:
                indicators["has_spa_framework"] = True
                indicators["js_frameworks"].append(framework)
                indicators["risk_score"] += 25
        
        # Dynamic loading indicators
        dynamic_indicators = [
            'document.addeventlistener',
            'window.onload',
            'ajax',
            'fetch(',
            'xmlhttprequest',
            'loadmore',
            'infinite-scroll'
        ]
        
        for indicator in dynamic_indicators:
            if indicator in html_lower:
                indicators["has_dynamic_loading"] = True
                indicators["risk_score"] += 10
                break
        
        # Content loading patterns
        if 'loading...' in html_lower or 'spinner' in html_lower:
            indicators["has_async_content"] = True
            indicators["risk_score"] += 15
        
        # Protection detection
        protection_signs = ['cloudflare', 'captcha', 'bot detection', 'access denied']
        for sign in protection_signs:
            if sign in html_lower:
                indicators["protection_detected"] = True
                indicators["risk_score"] += 30
                break
        
        return indicators
    
    def _make_recommendation(self, http_result: Dict, content_analysis: Dict, js_analysis: Dict) -> Dict[str, Any]:
        """Make final recommendation based on all analysis"""
        
        reasons = []
        confidence = 0.5
        
        # HTTP accessibility check
        if not http_result.get("accessible"):
            return {
                "scraping_method": "apify",
                "confidence": 0.9,
                "reasons": ["Site not accessible via HTTP"],
                "recommendation": "Use Apify - site blocked or protected"
            }
        
        # Content quality check
        content_quality = content_analysis.get("quality", "low")
        if content_quality == "high":
            confidence += 0.3
            reasons.append("High quality HTTP content available")
        elif content_quality == "medium":
            confidence += 0.1
            reasons.append("Moderate HTTP content quality")
        else:
            confidence -= 0.2
            reasons.append("Low quality HTTP content")
        
        # JavaScript dependency check
        js_risk = js_analysis.get("risk_score", 0)
        if js_risk >= 50:
            confidence -= 0.4
            reasons.append("High JavaScript dependency detected")
        elif js_risk >= 25:
            confidence -= 0.2
            reasons.append("Moderate JavaScript usage")
        else:
            confidence += 0.2
            reasons.append("Low JavaScript dependency")
        
        # Protection check
        if js_analysis.get("protection_detected"):
            return {
                "scraping_method": "apify",
                "confidence": 0.95,
                "reasons": reasons + ["Bot protection detected"],
                "recommendation": "Use Apify - site has anti-bot protection"
            }
        
        # Final decision
        confidence = max(0.1, min(0.95, confidence))
        
        if confidence >= 0.7:
            method = "http"
            recommendation = "Use HTTP scraping - reliable content available"
        elif confidence >= 0.4:
            method = "http"
            recommendation = "Try HTTP first, fallback to Apify if needed"
        else:
            method = "apify"
            recommendation = "Use Apify - better reliability expected"
        
        return {
            "scraping_method": method,
            "confidence": confidence,
            "reasons": reasons,
            "recommendation": recommendation
        }

@auto_log("site_analyzer")
def analyze_website_scraping_method(url: str) -> Dict[str, Any]:
    """
    Analyze website to determine optimal scraping method
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Dict with analysis results and recommendations
    """
    analyzer = SiteAnalyzer()
    return analyzer.analyze_site(url)

@auto_log("site_analyzer")
def analyze_multiple_sites(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Analyze multiple websites for scraping method recommendation
    
    Args:
        urls: List of URLs to analyze
        
    Returns:
        List of analysis results
    """
    analyzer = SiteAnalyzer()
    results = []
    
    print(f"Analyzing {len(urls)} websites for scraping optimization...")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] Analyzing: {url}")
        try:
            result = analyzer.analyze_site(url)
            results.append(result)
            time.sleep(0.5)  # Be polite to servers
        except Exception as e:
            print(f"Error analyzing {url}: {e}")
            results.append({
                "url": url,
                "error": str(e),
                "scraping_method": "apify",
                "recommendation": "Use Apify - analysis failed"
            })
    
    return results

if __name__ == "__main__":
    # Test the analyzer
    test_urls = [
        "https://www.altitudestrategies.ca",
        "https://www.stryvemarketing.com", 
        "https://example.com"
    ]
    
    results = analyze_multiple_sites(test_urls)
    
    print(json.dumps(results, indent=2))