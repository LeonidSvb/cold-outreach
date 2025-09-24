#!/usr/bin/env python3
"""
=== SITE ANALYZER ===
Version: 2.0.0 | Created: 2025-09-25

PURPOSE:
Analyzes websites to determine optimal scraping method (HTTP vs Apify).
Detects JavaScript dependency, bot protection, and content accessibility.

FEATURES:
- HTTP accessibility testing with detailed analysis
- JavaScript framework detection (React, Angular, Vue)
- Bot protection identification
- Content quality assessment with scoring
- Confidence-based routing recommendations
- Cost estimation for HTTP vs Apify methods
- Batch processing with concurrent analysis

USAGE:
1. Configure target websites in CONFIG section below
2. Set analysis parameters and output settings
3. Run: python site_analyzer.py
4. Results automatically saved to results/ with timestamp

IMPROVEMENTS:
v2.0.0 - Complete rewrite with modular architecture, improved detection, cost analysis
v1.0.0 - Initial implementation based on archive analysis
"""

import asyncio
import aiohttp
import json
import time
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings("ignore")

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # ANALYSIS SETTINGS
    "ANALYSIS": {
        "TIMEOUT_SECONDS": 15,
        "MAX_REDIRECTS": 5,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "CONFIDENCE_THRESHOLD": 0.7,
        "MIN_CONTENT_LENGTH": 500,
        "CONCURRENT_REQUESTS": 20
    },

    # DETECTION PATTERNS
    "DETECTION": {
        "SPA_FRAMEWORKS": {
            'react': ['react', 'react-dom', 'reactjs', '__react', '_react'],
            'angular': ['angular', 'ng-app', 'ng-controller', '@angular', 'angularjs'],
            'vue': ['vue', 'vue.js', 'vuejs', 'v-if', 'v-for', 'v-model'],
            'ember': ['ember', 'ember.js', 'emberjs', 'ember-cli'],
            'svelte': ['svelte', '_svelte', 'svelte-'],
            'backbone': ['backbone', 'backbone.js']
        },
        "PROTECTION_PATTERNS": [
            'cloudflare', 'captcha', 'bot detection', 'access denied',
            'blocked', 'security check', 'ddos protection', 'rate limit',
            'please wait', 'checking your browser', 'anti-bot'
        ],
        "DYNAMIC_LOADING": [
            'loading...', 'please wait', 'spinner', 'loading content',
            'fetch(', 'xmlhttprequest', 'ajax', 'async', 'defer',
            'lazy-load', 'infinite-scroll', 'loadmore'
        ]
    },

    # COST CALCULATIONS
    "COSTS": {
        "HTTP_COST_PER_REQUEST": 0.0,
        "APIFY_COST_PER_DOMAIN": 0.002,
        "ANALYSIS_COST_FACTOR": 1.2
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "SAVE_CSV": True,
        "RESULTS_DIR": "../results",
        "INCLUDE_RAW_HTML": False,
        "DETAILED_LOGGING": True
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_runs": 0,
    "total_sites_analyzed": 0,
    "http_suitable_count": 0,
    "apify_required_count": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "last_run": None
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class SiteAnalyzer:
    """Advanced website analysis for scraping method optimization"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.session = None
        self.analysis_results = []
        self.stats = {
            "start_time": time.time(),
            "sites_processed": 0,
            "http_suitable": 0,
            "apify_required": 0,
            "hybrid_approach": 0,
            "total_cost_estimate": 0.0
        }

    @auto_log("site_analyzer")
    async def analyze_sites(self, websites: List[str]) -> List[Dict[str, Any]]:
        """Main function to analyze multiple websites for scraping optimization"""

        print(f"Starting Site Analysis v{SCRIPT_STATS['version']}")
        print(f"Total websites: {len(websites):,}")
        print(f"Concurrent requests: {self.config['ANALYSIS']['CONCURRENT_REQUESTS']}")
        print(f"Timeout: {self.config['ANALYSIS']['TIMEOUT_SECONDS']}s")
        print("=" * 60)

        start_time = time.time()

        # Initialize session with timeout
        timeout = aiohttp.ClientTimeout(total=self.config["ANALYSIS"]["TIMEOUT_SECONDS"])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session

            # Process websites in parallel batches
            results = await self._process_websites_parallel(websites)

        # Filter out None results
        valid_results = [r for r in results if r is not None]

        # Calculate final statistics
        await self._calculate_final_stats(valid_results, start_time)

        # Save results
        await self._save_results(valid_results)

        # Print summary
        self._print_summary(valid_results, time.time() - start_time)

        return valid_results

    async def _process_websites_parallel(self, websites: List[str]) -> List[Dict[str, Any]]:
        """Process websites in parallel with controlled concurrency"""

        semaphore = asyncio.Semaphore(self.config["ANALYSIS"]["CONCURRENT_REQUESTS"])

        async def analyze_with_semaphore(website):
            async with semaphore:
                return await self._analyze_single_site(website)

        # Create tasks for all websites
        tasks = [analyze_with_semaphore(site) for site in websites]

        # Process with progress tracking
        results = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1

            # Progress update every 10 sites or at milestones
            if completed % 10 == 0 or completed in [1, 5, len(websites)]:
                progress = (completed / len(websites)) * 100
                print(f"Progress: {progress:.1f}% ({completed}/{len(websites)} sites)")

        return results

    async def _analyze_single_site(self, website: str) -> Optional[Dict[str, Any]]:
        """Comprehensive analysis of a single website"""

        try:
            # Normalize URL
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website

            # Initialize result structure
            analysis = {
                "url": website,
                "analyzed_at": datetime.now().isoformat(),
                "recommendation": {},
                "technical_analysis": {},
                "cost_estimate": {},
                "confidence_factors": [],
                "processing_time": 0
            }

            site_start_time = time.time()

            # Step 1: HTTP accessibility test
            http_result = await self._test_http_accessibility(website)

            if not http_result.get("accessible", False):
                # Site not accessible via HTTP - recommend Apify
                analysis.update({
                    "recommendation": {
                        "method": "APIFY_REQUIRED",
                        "confidence": 0.95,
                        "reasoning": [f"HTTP accessibility failed: {http_result.get('error', 'Unknown error')}"]
                    },
                    "technical_analysis": {
                        "http_accessible": False,
                        "status_code": http_result.get("status_code"),
                        "error": http_result.get("error")
                    },
                    "cost_estimate": {
                        "http_cost": 0.0,
                        "apify_cost_usd": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"],
                        "recommended_cost": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"]
                    }
                })
                analysis["processing_time"] = time.time() - site_start_time
                return analysis

            # Step 2: Content quality analysis
            content_analysis = self._analyze_content_quality(http_result)

            # Step 3: JavaScript dependency detection
            js_analysis = self._detect_javascript_dependency(http_result.get("html", ""))

            # Step 4: Make final recommendation
            recommendation = self._make_final_recommendation(http_result, content_analysis, js_analysis)

            # Combine all analysis results
            analysis.update({
                "recommendation": recommendation["recommendation"],
                "technical_analysis": {
                    "http_accessible": True,
                    "status_code": http_result.get("status_code"),
                    "content_length": http_result.get("content_length", 0),
                    "response_time": http_result.get("response_time", 0),
                    "content_quality": content_analysis,
                    "javascript_analysis": js_analysis
                },
                "cost_estimate": recommendation["cost_estimate"],
                "processing_time": time.time() - site_start_time
            })

            self.stats["sites_processed"] += 1

            # Update method counters
            method = recommendation["recommendation"]["method"]
            if method == "HTTP_SUITABLE":
                self.stats["http_suitable"] += 1
            elif method == "APIFY_REQUIRED":
                self.stats["apify_required"] += 1
            else:
                self.stats["hybrid_approach"] += 1

            return analysis

        except Exception as e:
            print(f"Error analyzing {website}: {e}")
            return {
                "url": website,
                "analyzed_at": datetime.now().isoformat(),
                "error": str(e),
                "recommendation": {
                    "method": "APIFY_REQUIRED",
                    "confidence": 0.5,
                    "reasoning": [f"Analysis failed: {e}"]
                },
                "cost_estimate": {
                    "http_cost": 0.0,
                    "apify_cost_usd": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"],
                    "recommended_cost": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"]
                }
            }

    async def _test_http_accessibility(self, url: str) -> Dict[str, Any]:
        """Test if website is accessible via HTTP with detailed metrics"""

        result = {
            "accessible": False,
            "status_code": None,
            "content_length": 0,
            "response_time": 0,
            "html": "",
            "content_sample": "",
            "redirect_count": 0,
            "error": None
        }

        try:
            headers = {
                "User-Agent": self.config["ANALYSIS"]["USER_AGENT"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }

            start_time = time.time()

            async with self.session.get(
                url,
                headers=headers,
                allow_redirects=True,
                max_redirects=self.config["ANALYSIS"]["MAX_REDIRECTS"]
            ) as response:

                result["response_time"] = time.time() - start_time
                result["status_code"] = response.status
                result["redirect_count"] = len(response.history)

                if response.status == 200:
                    html_content = await response.text()
                    result["html"] = html_content
                    result["content_length"] = len(html_content)
                    result["accessible"] = True

                    # Extract text content sample
                    try:
                        soup = BeautifulSoup(html_content, 'html.parser')
                        text_content = soup.get_text().strip()
                        result["content_sample"] = text_content[:1000]
                    except Exception as e:
                        result["content_sample"] = "Failed to parse HTML"

        except asyncio.TimeoutError:
            result["error"] = "Request timeout"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_content_quality(self, http_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze quality and completeness of HTTP-accessible content"""

        html = http_result.get("html", "")
        if not html:
            return {
                "quality": "none",
                "score": 0,
                "indicators": [],
                "text_length": 0,
                "business_relevance": "none"
            }

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()

            text_content = soup.get_text()
            text_length = len(text_content)

            # Quality scoring
            score = 0
            indicators = []

            # Text length scoring
            if text_length > 5000:
                score += 40
                indicators.append("Rich text content (5000+ chars)")
            elif text_length > 2000:
                score += 25
                indicators.append("Good text content (2000+ chars)")
            elif text_length > self.config["ANALYSIS"]["MIN_CONTENT_LENGTH"]:
                score += 10
                indicators.append("Moderate text content")

            # Structural elements
            if soup.find_all(['h1', 'h2', 'h3']):
                score += 15
                indicators.append("Has structured headings")

            if soup.find_all(['p']):
                score += 10
                indicators.append("Has paragraph content")

            # Navigation and links
            links = soup.find_all('a')
            if len(links) > 10:
                score += 10
                indicators.append(f"Good navigation ({len(links)} links)")

            # Business content detection
            business_keywords = [
                'about', 'services', 'contact', 'team', 'products',
                'solutions', 'company', 'business', 'support', 'clients'
            ]
            content_lower = text_content.lower()
            keyword_matches = sum(1 for keyword in business_keywords if keyword in content_lower)

            if keyword_matches > 5:
                score += 15
                indicators.append(f"High business relevance ({keyword_matches} keywords)")
            elif keyword_matches > 2:
                score += 8
                indicators.append(f"Medium business relevance ({keyword_matches} keywords)")

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
                business_relevance = "high"
            elif score >= 40:
                quality = "medium"
                business_relevance = "medium"
            elif score >= 20:
                quality = "low"
                business_relevance = "low"
            else:
                quality = "very_low"
                business_relevance = "none"

            return {
                "quality": quality,
                "score": score,
                "indicators": indicators,
                "text_length": text_length,
                "business_relevance": business_relevance,
                "keyword_matches": keyword_matches
            }

        except Exception as e:
            return {
                "quality": "error",
                "score": 0,
                "error": str(e),
                "text_length": 0,
                "business_relevance": "none"
            }

    def _detect_javascript_dependency(self, html: str) -> Dict[str, Any]:
        """Detect JavaScript frameworks and dynamic loading patterns"""

        indicators = {
            "dependency_level": "none",
            "spa_frameworks": [],
            "dynamic_loading_patterns": [],
            "protection_detected": False,
            "risk_score": 0,
            "risk_factors": []
        }

        if not html:
            return indicators

        html_lower = html.lower()

        # SPA Framework detection
        for framework, patterns in self.config["DETECTION"]["SPA_FRAMEWORKS"].items():
            for pattern in patterns:
                if pattern in html_lower:
                    indicators["spa_frameworks"].append(framework)
                    indicators["risk_score"] += 25
                    indicators["risk_factors"].append(f"SPA framework: {framework}")
                    break

        # Dynamic loading detection
        dynamic_found = []
        for pattern in self.config["DETECTION"]["DYNAMIC_LOADING"]:
            if pattern in html_lower:
                dynamic_found.append(pattern)

        if dynamic_found:
            indicators["dynamic_loading_patterns"] = dynamic_found
            indicators["risk_score"] += min(len(dynamic_found) * 5, 20)
            indicators["risk_factors"].append(f"Dynamic loading: {len(dynamic_found)} patterns")

        # Protection detection
        protection_found = []
        for pattern in self.config["DETECTION"]["PROTECTION_PATTERNS"]:
            if pattern in html_lower:
                protection_found.append(pattern)

        if protection_found:
            indicators["protection_detected"] = True
            indicators["risk_score"] += 40
            indicators["risk_factors"].append(f"Protection: {', '.join(protection_found)}")

        # Script tag analysis
        script_count = html_lower.count('<script')
        if script_count > 15:
            indicators["risk_score"] += 15
            indicators["risk_factors"].append(f"Heavy JS usage: {script_count} script tags")
        elif script_count > 5:
            indicators["risk_score"] += 5
            indicators["risk_factors"].append(f"Moderate JS usage: {script_count} script tags")

        # Determine dependency level
        if indicators["risk_score"] >= 60:
            indicators["dependency_level"] = "heavy"
        elif indicators["risk_score"] >= 30:
            indicators["dependency_level"] = "moderate"
        elif indicators["risk_score"] >= 10:
            indicators["dependency_level"] = "light"
        else:
            indicators["dependency_level"] = "none"

        return indicators

    def _make_final_recommendation(self, http_result: Dict, content_analysis: Dict, js_analysis: Dict) -> Dict[str, Any]:
        """Make final scraping method recommendation with confidence scoring"""

        confidence = 0.5
        reasons = []

        # Content quality factor
        content_score = content_analysis.get("score", 0)
        if content_score >= 50:
            confidence += 0.2
            reasons.append(f"High quality HTTP content (score: {content_score})")
        elif content_score >= 25:
            confidence += 0.1
            reasons.append(f"Moderate HTTP content quality (score: {content_score})")
        else:
            confidence -= 0.1
            reasons.append(f"Low quality HTTP content (score: {content_score})")

        # JavaScript dependency factor
        risk_score = js_analysis.get("risk_score", 0)
        dependency_level = js_analysis.get("dependency_level", "none")

        if dependency_level == "heavy":
            confidence -= 0.3
            reasons.append(f"Heavy JavaScript dependency (risk: {risk_score})")
        elif dependency_level == "moderate":
            confidence -= 0.15
            reasons.append(f"Moderate JavaScript usage (risk: {risk_score})")
        else:
            confidence += 0.15
            reasons.append(f"Low JavaScript dependency (risk: {risk_score})")

        # SPA frameworks strongly suggest Apify
        spa_frameworks = js_analysis.get("spa_frameworks", [])
        if spa_frameworks:
            confidence -= 0.25
            reasons.append(f"SPA frameworks detected: {', '.join(spa_frameworks)}")

        # Bot protection override
        if js_analysis.get("protection_detected", False):
            return {
                "recommendation": {
                    "method": "APIFY_REQUIRED",
                    "confidence": 0.95,
                    "reasoning": reasons + ["Bot protection detected"]
                },
                "cost_estimate": {
                    "http_cost": 0.0,
                    "apify_cost_usd": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"],
                    "recommended_cost": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"]
                }
            }

        # Response time factor
        response_time = http_result.get("response_time", 0)
        if response_time > 10:
            confidence -= 0.1
            reasons.append(f"Slow response time: {response_time:.1f}s")

        # Normalize confidence
        confidence = max(0.1, min(0.95, confidence))

        # Final decision logic
        if confidence >= self.config["ANALYSIS"]["CONFIDENCE_THRESHOLD"]:
            method = "HTTP_SUITABLE"
            cost = self.config["COSTS"]["HTTP_COST_PER_REQUEST"]
            reasoning = f"HTTP scraping recommended - reliable content available (confidence: {confidence:.2f})"
        elif confidence >= 0.4:
            method = "HYBRID_APPROACH"
            cost = self.config["COSTS"]["APIFY_COST_PER_DOMAIN"] * 0.5
            reasoning = f"Try HTTP first, fallback to Apify if needed (confidence: {confidence:.2f})"
        else:
            method = "APIFY_REQUIRED"
            cost = self.config["COSTS"]["APIFY_COST_PER_DOMAIN"]
            reasoning = f"Apify recommended - better reliability expected (confidence: {confidence:.2f})"

        return {
            "recommendation": {
                "method": method,
                "confidence": confidence,
                "reasoning": reasons + [reasoning]
            },
            "cost_estimate": {
                "http_cost": 0.0,
                "apify_cost_usd": self.config["COSTS"]["APIFY_COST_PER_DOMAIN"],
                "recommended_cost": cost
            }
        }

    async def _calculate_final_stats(self, results: List[Dict[str, Any]], start_time: float):
        """Calculate final processing statistics"""

        processing_time = time.time() - start_time

        # Cost calculations
        total_cost = sum(r.get("cost_estimate", {}).get("recommended_cost", 0) for r in results)
        self.stats["total_cost_estimate"] = total_cost

        # Success rate
        successful = len([r for r in results if "error" not in r])
        success_rate = (successful / len(results) * 100) if results else 0

        # Update global stats
        global SCRIPT_STATS
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["total_sites_analyzed"] += len(results)
        SCRIPT_STATS["success_rate"] = success_rate
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()

        # Method distribution
        method_counts = {}
        for result in results:
            method = result.get("recommendation", {}).get("method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1

        SCRIPT_STATS["http_suitable_count"] = method_counts.get("HTTP_SUITABLE", 0)
        SCRIPT_STATS["apify_required_count"] = method_counts.get("APIFY_REQUIRED", 0)

    async def _save_results(self, results: List[Dict[str, Any]]):
        """Save analysis results to JSON and CSV"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Prepare results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "script_version": SCRIPT_STATS["version"],
                "total_sites": len(results),
                "processing_time_seconds": self.stats.get("processing_time", 0),
                "cost_estimate_usd": self.stats["total_cost_estimate"],
                "method_distribution": {
                    "http_suitable": self.stats["http_suitable"],
                    "apify_required": self.stats["apify_required"],
                    "hybrid_approach": self.stats["hybrid_approach"]
                },
                "config_used": self.config
            },
            "results": results
        }

        # Save JSON
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"site_analysis_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"JSON results saved: {json_filename}")

        # Save CSV summary
        if self.config["OUTPUT"]["SAVE_CSV"]:
            csv_filename = f"site_analysis_summary_{timestamp}.csv"
            csv_filepath = self.results_dir / csv_filename

            import csv
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'URL', 'Method', 'Confidence', 'Content_Quality',
                    'JS_Dependency', 'Cost_USD', 'Processing_Time', 'Status'
                ])

                for result in results:
                    rec = result.get("recommendation", {})
                    tech = result.get("technical_analysis", {})
                    cost = result.get("cost_estimate", {})

                    writer.writerow([
                        result.get("url", ""),
                        rec.get("method", ""),
                        f"{rec.get('confidence', 0):.2f}",
                        tech.get("content_quality", {}).get("quality", ""),
                        tech.get("javascript_analysis", {}).get("dependency_level", ""),
                        f"{cost.get('recommended_cost', 0):.3f}",
                        f"{result.get('processing_time', 0):.2f}s",
                        "success" if "error" not in result else "error"
                    ])

            print(f"CSV summary saved: {csv_filename}")

    def _print_summary(self, results: List[Dict[str, Any]], processing_time: float):
        """Print analysis summary"""

        print("\n" + "=" * 60)
        print("SITE ANALYSIS SUMMARY")
        print("=" * 60)

        print(f"Total sites analyzed: {len(results):,}")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Average time per site: {processing_time/len(results):.2f}s" if results else "N/A")

        print(f"\nMETHOD DISTRIBUTION:")
        print(f"  HTTP Suitable: {self.stats['http_suitable']:,} ({self.stats['http_suitable']/len(results)*100:.1f}%)")
        print(f"  Apify Required: {self.stats['apify_required']:,} ({self.stats['apify_required']/len(results)*100:.1f}%)")
        print(f"  Hybrid Approach: {self.stats['hybrid_approach']:,} ({self.stats['hybrid_approach']/len(results)*100:.1f}%)")

        print(f"\nCOST ANALYSIS:")
        print(f"  Estimated total cost: ${self.stats['total_cost_estimate']:.3f}")
        print(f"  Average cost per site: ${self.stats['total_cost_estimate']/len(results):.4f}" if results else "N/A")

        # Error analysis
        errors = [r for r in results if "error" in r]
        if errors:
            print(f"\nERRORS: {len(errors)} sites failed")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  {error['url']}: {error['error']}")

        print("=" * 60)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function for testing"""

    print("=" * 60)
    print(f"SITE ANALYZER v{SCRIPT_STATS['version']}")
    print("=" * 60)

    # Sample websites for testing
    test_websites = [
        "https://www.altitudestrategies.ca",
        "https://www.stryvemarketing.com",
        "http://www.workparty.ca",
        "http://www.theog.co",
        "http://www.involvedmedia.ca"
    ]

    analyzer = SiteAnalyzer()
    results = await analyzer.analyze_sites(test_websites)

    print(f"\nAnalysis completed: {len(results)} results generated")

    return results

if __name__ == "__main__":
    asyncio.run(main())