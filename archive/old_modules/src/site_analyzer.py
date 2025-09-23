#!/usr/bin/env python3
"""
=== SITE ANALYZER ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
Analyzes websites to determine optimal scraping method (HTTP vs Apify).
Detects JavaScript dependency, bot protection, and content accessibility.

FEATURES:
- HTTP accessibility testing
- JavaScript framework detection (React, Angular, Vue)
- Bot protection identification
- Content quality assessment
- Confidence scoring for routing decisions

USAGE:
from site_analyzer import SiteAnalyzer
analyzer = SiteAnalyzer()
result = analyzer.analyze_site("https://example.com")

IMPROVEMENTS:
v1.0.0 - Initial implementation based on archive/old_core analysis
"""

import requests
import time
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import warnings
warnings.filterwarnings("ignore")

class SiteAnalyzer:
    """Analyzes websites for optimal scraping method determination"""

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
        """
        Analyze a single website to determine scraping method

        Args:
            url: Website URL to analyze

        Returns:
            Dict with analysis results and recommendations
        """

        result = {
            "url": url,
            "scraping_method": "unknown",
            "confidence": 0.0,
            "content_quality": "unknown",
            "reasons": [],
            "http_test": {},
            "js_indicators": {},
            "recommendation": "",
            "analysis_time": 0
        }

        start_time = time.time()

        try:
            # Step 1: HTTP accessibility test
            http_result = self._test_http_scraping(url)
            result["http_test"] = http_result

            if not http_result.get("accessible"):
                result["scraping_method"] = "apify"
                result["confidence"] = 0.9
                result["reasons"].append("Site not accessible via HTTP")
                result["recommendation"] = "Use Apify - site blocked/protected"
                result["analysis_time"] = time.time() - start_time
                return result

            # Step 2: Content quality analysis
            content_analysis = self._analyze_content_quality(http_result.get("html", ""))
            result["content_quality"] = content_analysis["quality"]

            # Step 3: JavaScript dependency detection
            js_analysis = self._detect_javascript_dependency(http_result.get("html", ""))
            result["js_indicators"] = js_analysis

            # Step 4: Make final recommendation
            recommendation = self._make_recommendation(http_result, content_analysis, js_analysis)
            result.update(recommendation)

            result["analysis_time"] = time.time() - start_time
            return result

        except Exception as e:
            result["error"] = str(e)
            result["scraping_method"] = "apify"
            result["confidence"] = 0.5
            result["reasons"].append(f"Error during analysis: {e}")
            result["recommendation"] = "Use Apify - analysis failed"
            result["analysis_time"] = time.time() - start_time
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
            "content_sample": "",
            "redirect_count": 0
        }

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=15, allow_redirects=True)
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.status_code
            result["redirect_count"] = len(response.history)

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
            return {"quality": "none", "score": 0, "indicators": [], "text_length": 0}

        try:
            soup = BeautifulSoup(html, 'html.parser')
            text_content = soup.get_text()

            # Quality indicators scoring
            score = 0
            indicators = []

            # Text length scoring
            text_len = len(text_content)
            if text_len > 5000:
                score += 40
                indicators.append("Rich text content")
            elif text_len > 2000:
                score += 25
                indicators.append("Good text content")
            elif text_len > 500:
                score += 10
                indicators.append("Moderate text content")

            # Structured content detection
            if soup.find_all(['h1', 'h2', 'h3']):
                score += 20
                indicators.append("Has structured headings")

            if soup.find_all(['p']):
                score += 15
                indicators.append("Has paragraph content")

            # Navigation and links
            nav_elements = soup.find_all('nav') or soup.find_all('a')
            if nav_elements:
                score += 10
                indicators.append("Has navigation structure")

            # Business-relevant content detection
            business_keywords = [
                'about', 'services', 'contact', 'team', 'products',
                'solutions', 'company', 'business', 'support'
            ]
            content_lower = text_content.lower()
            keyword_matches = sum(1 for keyword in business_keywords if keyword in content_lower)
            score += min(keyword_matches * 2, 10)

            if keyword_matches > 3:
                indicators.append("Business-relevant content")

            # Meta information
            if soup.find("meta", attrs={"name": "description"}):
                score += 5
                indicators.append("Has meta description")

            if soup.title and soup.title.string:
                score += 5
                indicators.append("Has page title")

            # Determine quality level
            if score >= 70:
                quality = "high"
            elif score >= 40:
                quality = "medium"
            elif score >= 20:
                quality = "low"
            else:
                quality = "very_low"

            return {
                "quality": quality,
                "score": score,
                "indicators": indicators,
                "text_length": text_len,
                "keyword_matches": keyword_matches
            }

        except Exception as e:
            return {"quality": "error", "score": 0, "error": str(e)}

    def _detect_javascript_dependency(self, html: str) -> Dict[str, Any]:
        """Detect if site heavily depends on JavaScript"""

        indicators = {
            "has_spa_framework": False,
            "has_async_content": False,
            "has_dynamic_loading": False,
            "protection_detected": False,
            "js_frameworks": [],
            "risk_score": 0,
            "risk_factors": []
        }

        if not html:
            return indicators

        html_lower = html.lower()

        # SPA Framework detection
        spa_frameworks = {
            'react': ['react', 'react-dom', 'reactjs', '__react'],
            'angular': ['angular', 'ng-app', 'ng-controller', '@angular'],
            'vue': ['vue', 'vue.js', 'vuejs', 'v-if', 'v-for'],
            'ember': ['ember', 'ember.js', 'emberjs'],
            'backbone': ['backbone', 'backbone.js'],
            'svelte': ['svelte', '_svelte']
        }

        for framework, patterns in spa_frameworks.items():
            for pattern in patterns:
                if pattern in html_lower:
                    indicators["has_spa_framework"] = True
                    indicators["js_frameworks"].append(framework)
                    indicators["risk_score"] += 30
                    indicators["risk_factors"].append(f"SPA framework: {framework}")
                    break

        # Dynamic loading indicators
        dynamic_patterns = [
            'document.addeventlistener',
            'window.onload',
            'ajax',
            'fetch(',
            'xmlhttprequest',
            'loadmore',
            'infinite-scroll',
            'lazy-load',
            'async',
            'defer'
        ]

        dynamic_found = []
        for pattern in dynamic_patterns:
            if pattern in html_lower:
                dynamic_found.append(pattern)

        if dynamic_found:
            indicators["has_dynamic_loading"] = True
            indicators["risk_score"] += min(len(dynamic_found) * 5, 20)
            indicators["risk_factors"].append(f"Dynamic loading: {len(dynamic_found)} patterns")

        # Content loading patterns
        loading_patterns = ['loading...', 'spinner', 'please wait', 'loading content']
        loading_found = [p for p in loading_patterns if p in html_lower]

        if loading_found:
            indicators["has_async_content"] = True
            indicators["risk_score"] += 15
            indicators["risk_factors"].append("Async content loading detected")

        # Protection detection
        protection_patterns = [
            'cloudflare', 'captcha', 'bot detection', 'access denied',
            'blocked', 'security check', 'ddos protection', 'rate limit'
        ]

        protection_found = [p for p in protection_patterns if p in html_lower]
        if protection_found:
            indicators["protection_detected"] = True
            indicators["risk_score"] += 40
            indicators["risk_factors"].append(f"Protection: {', '.join(protection_found)}")

        # Content density check
        soup = BeautifulSoup(html, 'html.parser')
        script_tags = soup.find_all('script')
        if len(script_tags) > 10:
            indicators["risk_score"] += 10
            indicators["risk_factors"].append(f"Heavy JS usage: {len(script_tags)} script tags")

        # Empty content check (JS-rendered content)
        text_content = soup.get_text().strip()
        if len(text_content) < 200 and len(html) > 5000:
            indicators["risk_score"] += 25
            indicators["risk_factors"].append("Minimal text content (likely JS-rendered)")

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

        # Content quality assessment
        content_quality = content_analysis.get("quality", "low")
        content_score = content_analysis.get("score", 0)

        if content_quality == "high":
            confidence += 0.3
            reasons.append(f"High quality HTTP content (score: {content_score})")
        elif content_quality == "medium":
            confidence += 0.1
            reasons.append(f"Moderate HTTP content quality (score: {content_score})")
        else:
            confidence -= 0.2
            reasons.append(f"Low quality HTTP content (score: {content_score})")

        # JavaScript dependency assessment
        js_risk = js_analysis.get("risk_score", 0)
        js_frameworks = js_analysis.get("js_frameworks", [])

        if js_risk >= 60:
            confidence -= 0.4
            reasons.append(f"High JavaScript dependency (risk: {js_risk})")
            if js_frameworks:
                reasons.append(f"SPA frameworks detected: {', '.join(js_frameworks)}")
        elif js_risk >= 30:
            confidence -= 0.2
            reasons.append(f"Moderate JavaScript usage (risk: {js_risk})")
        else:
            confidence += 0.2
            reasons.append(f"Low JavaScript dependency (risk: {js_risk})")

        # Protection check (override other factors)
        if js_analysis.get("protection_detected"):
            return {
                "scraping_method": "apify",
                "confidence": 0.95,
                "reasons": reasons + ["Bot protection detected"],
                "recommendation": "Use Apify - site has anti-bot protection"
            }

        # Response time factor
        response_time = http_result.get("response_time", 0)
        if response_time > 10:
            confidence -= 0.1
            reasons.append(f"Slow response time: {response_time:.1f}s")

        # Final decision logic
        confidence = max(0.1, min(0.95, confidence))

        if confidence >= 0.7:
            method = "http"
            recommendation = f"Use HTTP scraping - reliable content available (confidence: {confidence:.2f})"
        elif confidence >= 0.4:
            method = "http"
            recommendation = f"Try HTTP first, fallback to Apify if needed (confidence: {confidence:.2f})"
        else:
            method = "apify"
            recommendation = f"Use Apify - better reliability expected (confidence: {confidence:.2f})"

        return {
            "scraping_method": method,
            "confidence": confidence,
            "reasons": reasons,
            "recommendation": recommendation
        }

    def analyze_multiple_sites(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple websites for scraping method recommendation

        Args:
            urls: List of URLs to analyze

        Returns:
            List of analysis results
        """

        results = []

        print(f"Analyzing {len(urls)} websites for scraping optimization...")

        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Analyzing: {url}")
            try:
                result = self.analyze_site(url)
                results.append(result)
                time.sleep(0.5)  # Be polite to servers
            except Exception as e:
                print(f"Error analyzing {url}: {e}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "scraping_method": "apify",
                    "confidence": 0.5,
                    "recommendation": "Use Apify - analysis failed"
                })

        return results

# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

def main():
    """Test the analyzer with sample URLs"""

    test_urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com"
    ]

    analyzer = SiteAnalyzer()

    print("Testing Site Analyzer...")
    print("=" * 50)

    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        result = analyzer.analyze_site(url)

        print(f"Method: {result['scraping_method']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Quality: {result['content_quality']}")
        print(f"Recommendation: {result['recommendation']}")

        if result.get('js_indicators', {}).get('js_frameworks'):
            frameworks = result['js_indicators']['js_frameworks']
            print(f"JS Frameworks: {', '.join(frameworks)}")

        print("-" * 30)

if __name__ == "__main__":
    main()