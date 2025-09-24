#!/usr/bin/env python3
"""
=== PAGE PRIORITIZER ===
Version: 2.0.0 | Created: 2025-09-25

PURPOSE:
AI-powered page classification and prioritization for B2B cold outreach intelligence value.
Uses OpenAI GPT-4o to analyze web pages and extract actionable insights for personalized outreach.

FEATURES:
- OpenAI GPT-4o integration with optimized prompting
- Dynamic prompt loading from ../prompts.md
- Outreach value scoring (0-10) with confidence assessment
- Batch processing for cost optimization
- Intelligence extraction for personalization opportunities
- Conversation starter identification
- Leadership and company insights detection
- Cost tracking and performance analytics

USAGE:
1. Configure API settings and analysis parameters in CONFIG
2. Set target pages/domains for analysis
3. Run: python page_prioritizer.py
4. Results saved with detailed intelligence insights

IMPROVEMENTS:
v2.0.0 - Complete rewrite with modular prompts, advanced intelligence extraction
v1.0.0 - Basic OpenAI integration with embedded prompts
"""

import asyncio
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import openai
from openai import OpenAI
import re

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # OPENAI API SETTINGS
    "AI": {
        "MODEL": "gpt-4o-mini",
        "TEMPERATURE": 0.1,
        "MAX_TOKENS": 2000,
        "API_TIMEOUT": 30,
        "MAX_RETRIES": 3
    },

    # ANALYSIS SETTINGS
    "ANALYSIS": {
        "BATCH_SIZE": 5,
        "MIN_CONTENT_LENGTH": 200,
        "MAX_CONTENT_LENGTH": 10000,
        "MIN_PRIORITY_SCORE": 5,
        "ENABLE_BATCH_MODE": True,
        "EXTRACT_COMPANY_INSIGHTS": True
    },

    # OUTREACH CATEGORIES
    "CATEGORIES": {
        "HIGH_VALUE": ["about", "team", "leadership", "case-studies", "news", "awards"],
        "MEDIUM_VALUE": ["services", "products", "solutions", "blog", "insights"],
        "LOW_VALUE": ["contact", "careers", "faq", "support"],
        "NO_VALUE": ["privacy", "terms", "login", "register", "error"]
    },

    # COST TRACKING
    "COSTS": {
        "GPT4O_MINI_INPUT_PER_1K": 0.00015,
        "GPT4O_MINI_OUTPUT_PER_1K": 0.0006,
        "TARGET_COST_PER_PAGE": 0.003,
        "MAX_DAILY_COST": 10.0
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "SAVE_CSV_SUMMARY": True,
        "RESULTS_DIR": "../results",
        "INCLUDE_RAW_RESPONSES": False,
        "DETAILED_LOGGING": True
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_runs": 0,
    "total_pages_analyzed": 0,
    "total_api_calls": 0,
    "total_cost_usd": 0.0,
    "avg_priority_score": 0.0,
    "high_value_pages_found": 0,
    "success_rate": 0.0,
    "last_run": None
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class PagePrioritizer:
    """AI-powered page analysis for cold outreach intelligence"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.prompts = self._load_prompts()
        self.openai_client = self._initialize_openai()
        self.stats = {
            "start_time": time.time(),
            "pages_analyzed": 0,
            "api_calls": 0,
            "total_cost": 0.0,
            "high_value_found": 0,
            "successful_analyses": 0
        }

    def _initialize_openai(self) -> OpenAI:
        """Initialize OpenAI client with API key"""

        # Load API key from .env file
        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        if not env_path.exists():
            raise FileNotFoundError("No .env file found. Please create one with OPENAI_API_KEY.")

        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    return OpenAI(api_key=api_key)

        raise ValueError("OPENAI_API_KEY not found in .env file")

    def _load_prompts(self) -> Dict[str, str]:
        """Load AI prompts from prompts.md file"""

        prompts_path = Path(__file__).parent.parent / "prompts.md"
        if not prompts_path.exists():
            raise FileNotFoundError(f"prompts.md not found at {prompts_path}")

        with open(prompts_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse prompts from markdown
        prompts = {}
        current_section = None
        current_prompt = []
        in_code_block = False

        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Only process section headers when not in code block
            if not in_code_block and line.startswith('## ') and not line.startswith('## Version') and not line.startswith('## ARCHIVE'):
                current_section = line[3:].strip()
                current_prompt = []
            elif line.strip() == '```' and current_section:
                if not in_code_block:
                    in_code_block = True
                    current_prompt = []
                else:
                    in_code_block = False
                    if current_section and current_prompt:
                        prompts[current_section] = '\n'.join(current_prompt)
            elif in_code_block and current_section:
                current_prompt.append(line)

        print(f"Loaded {len(prompts)} prompts: {list(prompts.keys())}")
        return prompts

    @auto_log("page_prioritizer")
    async def analyze_pages(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Main function to analyze pages for outreach intelligence"""

        print(f"Starting Page Prioritization v{SCRIPT_STATS['version']}")
        print(f"Pages to analyze: {len(pages_data):,}")
        print(f"AI Model: {self.config['AI']['MODEL']}")
        print(f"Batch size: {self.config['ANALYSIS']['BATCH_SIZE']}")
        print("=" * 60)

        start_time = time.time()

        # Filter pages by content length
        valid_pages = self._filter_valid_pages(pages_data)
        print(f"Valid pages for analysis: {len(valid_pages):,}")

        # Process pages
        if self.config["ANALYSIS"]["ENABLE_BATCH_MODE"] and len(valid_pages) > 1:
            results = await self._process_pages_in_batches(valid_pages)
        else:
            results = await self._process_pages_individually(valid_pages)

        # Calculate final statistics
        processing_time = time.time() - start_time
        await self._calculate_final_stats(results, processing_time)

        # Save results
        await self._save_results(results, processing_time)

        # Print summary
        self._print_summary(results, processing_time)

        return results

    def _filter_valid_pages(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter pages suitable for analysis"""

        valid_pages = []

        for page in pages_data:
            content = page.get("content", "") or page.get("text", "")
            content_length = len(content)

            if content_length < self.config["ANALYSIS"]["MIN_CONTENT_LENGTH"]:
                continue

            # Truncate if too long
            if content_length > self.config["ANALYSIS"]["MAX_CONTENT_LENGTH"]:
                content = content[:self.config["ANALYSIS"]["MAX_CONTENT_LENGTH"]] + "... [truncated]"
                page["content"] = content

            valid_pages.append(page)

        return valid_pages

    async def _process_pages_in_batches(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process pages in batches for cost optimization"""

        batch_size = self.config["ANALYSIS"]["BATCH_SIZE"]
        all_results = []

        print(f"Processing {len(pages)} pages in batches of {batch_size}")

        for i in range(0, len(pages), batch_size):
            batch = pages[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(pages) + batch_size - 1) // batch_size

            print(f"Batch {batch_number}/{total_batches}: {len(batch)} pages")

            # Process single batch
            batch_results = await self._analyze_batch(batch)
            all_results.extend(batch_results)

            # Progress update
            completed = min(i + batch_size, len(pages))
            progress = (completed / len(pages)) * 100
            print(f"Progress: {progress:.1f}% ({completed}/{len(pages)} pages)")

            # Small delay between batches
            if i + batch_size < len(pages):
                await asyncio.sleep(0.5)

        return all_results

    async def _process_pages_individually(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process pages individually for detailed analysis"""

        results = []

        for i, page in enumerate(pages):
            print(f"Analyzing page {i+1}/{len(pages)}: {page.get('url', 'Unknown URL')[:50]}...")

            result = await self._analyze_single_page(page)
            results.append(result)

            # Small delay between API calls
            await asyncio.sleep(0.2)

        return results

    async def _analyze_batch(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze a batch of pages efficiently"""

        if len(pages) == 1:
            return [await self._analyze_single_page(pages[0])]

        # For batch processing, analyze domain-level if multiple pages from same domain
        domains = {}
        for page in pages:
            domain = self._extract_domain_from_url(page.get("url", ""))
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(page)

        results = []

        # Process each domain
        for domain, domain_pages in domains.items():
            if len(domain_pages) > 1:
                # Use batch analysis for multiple pages from same domain
                domain_result = await self._analyze_domain_pages(domain, domain_pages)
                results.extend(domain_result)
            else:
                # Single page analysis
                result = await self._analyze_single_page(domain_pages[0])
                results.append(result)

        return results

    async def _analyze_single_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single page for outreach intelligence"""

        try:
            page_url = page_data.get("url", "Unknown")
            page_title = page_data.get("title", "")
            page_content = page_data.get("content", "") or page_data.get("text", "")
            content_length = len(page_content)
            domain = self._extract_domain_from_url(page_url)

            # Prepare prompt
            prompt = self.prompts.get("PAGE_CLASSIFICATION", "")
            if not prompt:
                raise ValueError("PAGE_CLASSIFICATION prompt not found")

            # Format prompt with page data
            formatted_prompt = prompt.format(
                page_url=page_url,
                page_title=page_title,
                content_length=content_length,
                domain=domain,
                page_content=page_content
            )

            # Make API call
            api_start_time = time.time()
            response = await self._make_openai_request(formatted_prompt)
            api_time = time.time() - api_start_time

            # Parse response
            analysis_result = self._parse_ai_response(response)

            # Calculate costs
            cost_estimate = self._estimate_api_cost(formatted_prompt, response)

            # Prepare final result
            result = {
                "page_data": {
                    "url": page_url,
                    "title": page_title,
                    "content_length": content_length,
                    "domain": domain
                },
                "analysis": analysis_result,
                "processing": {
                    "analyzed_at": datetime.now().isoformat(),
                    "api_processing_time": api_time,
                    "cost_estimate_usd": cost_estimate,
                    "model_used": self.config["AI"]["MODEL"]
                }
            }

            # Update stats
            self.stats["pages_analyzed"] += 1
            self.stats["api_calls"] += 1
            self.stats["total_cost"] += cost_estimate
            self.stats["successful_analyses"] += 1

            # Track high-value pages
            priority_score = analysis_result.get("classification", {}).get("score", 0)
            if priority_score >= 8:
                self.stats["high_value_found"] += 1

            return result

        except Exception as e:
            print(f"Error analyzing page {page_data.get('url', 'Unknown')}: {e}")
            return {
                "page_data": {
                    "url": page_data.get("url", "Unknown"),
                    "title": page_data.get("title", ""),
                    "content_length": len(page_data.get("content", "")),
                    "domain": self._extract_domain_from_url(page_data.get("url", ""))
                },
                "error": str(e),
                "processing": {
                    "analyzed_at": datetime.now().isoformat(),
                    "cost_estimate_usd": 0.0
                }
            }

    async def _analyze_domain_pages(self, domain: str, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze multiple pages from same domain efficiently"""

        try:
            # Prepare batch prompt
            prompt = self.prompts.get("BATCH_ANALYSIS", "")
            if not prompt:
                # Fallback to individual analysis
                results = []
                for page in pages:
                    result = await self._analyze_single_page(page)
                    results.append(result)
                return results

            # Format pages data for batch analysis
            pages_data_str = ""
            for i, page in enumerate(pages):
                pages_data_str += f"\n**PAGE {i+1}:**\n"
                pages_data_str += f"URL: {page.get('url', 'Unknown')}\n"
                pages_data_str += f"Title: {page.get('title', '')}\n"
                pages_data_str += f"Content: {page.get('content', '')[:2000]}...\n"

            formatted_prompt = prompt.format(
                domain=domain,
                page_count=len(pages),
                pages_data=pages_data_str
            )

            # Make API call
            response = await self._make_openai_request(formatted_prompt)
            batch_result = self._parse_ai_response(response)

            # Convert batch result to individual page results
            results = []
            cost_per_page = self._estimate_api_cost(formatted_prompt, response) / len(pages)

            for i, page in enumerate(pages):
                # Extract individual page analysis from batch result
                page_analysis = self._extract_page_from_batch(batch_result, i, page.get('url', ''))

                result = {
                    "page_data": {
                        "url": page.get("url", "Unknown"),
                        "title": page.get("title", ""),
                        "content_length": len(page.get("content", "")),
                        "domain": domain
                    },
                    "analysis": page_analysis,
                    "processing": {
                        "analyzed_at": datetime.now().isoformat(),
                        "cost_estimate_usd": cost_per_page,
                        "model_used": self.config["AI"]["MODEL"],
                        "batch_analysis": True
                    }
                }
                results.append(result)

            # Update stats
            self.stats["pages_analyzed"] += len(pages)
            self.stats["api_calls"] += 1
            self.stats["total_cost"] += self._estimate_api_cost(formatted_prompt, response)
            self.stats["successful_analyses"] += len(results)

            return results

        except Exception as e:
            print(f"Error in batch analysis for {domain}: {e}")
            # Fallback to individual analysis
            results = []
            for page in pages:
                result = await self._analyze_single_page(page)
                results.append(result)
            return results

    async def _make_openai_request(self, prompt: str) -> str:
        """Make request to OpenAI API with retry logic"""

        for attempt in range(self.config["AI"]["MAX_RETRIES"]):
            try:
                response = self.openai_client.chat.completions.create(
                    model=self.config["AI"]["MODEL"],
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing web pages for B2B cold outreach intelligence. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config["AI"]["TEMPERATURE"],
                    max_tokens=self.config["AI"]["MAX_TOKENS"],
                    timeout=self.config["AI"]["API_TIMEOUT"]
                )

                return response.choices[0].message.content

            except Exception as e:
                print(f"OpenAI API attempt {attempt + 1} failed: {e}")
                if attempt == self.config["AI"]["MAX_RETRIES"] - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""

        try:
            # Try to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # Fallback structure
            return {
                "classification": {
                    "category": "ANALYSIS_ERROR",
                    "score": 0,
                    "confidence": 0,
                    "reasoning": "Failed to parse AI response"
                },
                "intelligence": {
                    "personalization_opportunities": [],
                    "conversation_starters": [],
                    "key_people": [],
                    "company_insights": {}
                },
                "outreach_summary": "Analysis failed",
                "raw_response": response
            }

    def _extract_page_from_batch(self, batch_result: Dict[str, Any], page_index: int, page_url: str) -> Dict[str, Any]:
        """Extract individual page analysis from batch result"""

        # Try to extract from page_rankings if available
        page_rankings = batch_result.get("page_rankings", [])
        if page_index < len(page_rankings):
            page_data = page_rankings[page_index]

            # Convert batch format to individual format
            return {
                "classification": {
                    "category": page_data.get("value_category", "UNKNOWN"),
                    "score": page_data.get("priority_score", 0),
                    "confidence": 8,  # Default confidence for batch
                    "reasoning": "Batch analysis result"
                },
                "intelligence": {
                    "personalization_opportunities": page_data.get("key_insights", []),
                    "conversation_starters": [],
                    "key_people": [],
                    "company_insights": {}
                },
                "outreach_summary": batch_result.get("outreach_strategy", "")
            }

        # Fallback to basic classification
        return {
            "classification": {
                "category": "MEDIUM_VALUE",
                "score": 5,
                "confidence": 5,
                "reasoning": "Batch analysis fallback"
            },
            "intelligence": {
                "personalization_opportunities": [],
                "conversation_starters": [],
                "key_people": [],
                "company_insights": {}
            },
            "outreach_summary": "Page from batch analysis"
        }

    def _estimate_api_cost(self, prompt: str, response: str) -> float:
        """Estimate API cost based on token usage"""

        # Rough token estimation (1 token ≈ 4 characters for English)
        input_tokens = len(prompt) / 4
        output_tokens = len(response) / 4

        input_cost = (input_tokens / 1000) * self.config["COSTS"]["GPT4O_MINI_INPUT_PER_1K"]
        output_cost = (output_tokens / 1000) * self.config["COSTS"]["GPT4O_MINI_OUTPUT_PER_1K"]

        return input_cost + output_cost

    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""

        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or "unknown"
        except:
            return "unknown"

    async def _calculate_final_stats(self, results: List[Dict[str, Any]], processing_time: float):
        """Calculate final statistics"""

        # Calculate averages
        successful_results = [r for r in results if "error" not in r]

        if successful_results:
            priority_scores = []
            for result in successful_results:
                score = result.get("analysis", {}).get("classification", {}).get("score", 0)
                priority_scores.append(score)

            avg_priority_score = sum(priority_scores) / len(priority_scores)
        else:
            avg_priority_score = 0

        # Update global stats
        global SCRIPT_STATS
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["total_pages_analyzed"] += len(results)
        SCRIPT_STATS["total_api_calls"] += self.stats["api_calls"]
        SCRIPT_STATS["total_cost_usd"] += self.stats["total_cost"]
        SCRIPT_STATS["avg_priority_score"] = avg_priority_score
        SCRIPT_STATS["high_value_pages_found"] += self.stats["high_value_found"]
        SCRIPT_STATS["success_rate"] = (len(successful_results) / len(results) * 100) if results else 0
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()

    async def _save_results(self, results: List[Dict[str, Any]], processing_time: float):
        """Save analysis results with comprehensive metadata"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Prepare comprehensive results
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "script_version": SCRIPT_STATS["version"],
                "analysis_summary": {
                    "total_pages_analyzed": len(results),
                    "successful_analyses": len([r for r in results if "error" not in r]),
                    "failed_analyses": len([r for r in results if "error" in r]),
                    "total_processing_time": processing_time,
                    "avg_time_per_page": processing_time / len(results) if results else 0,
                    "total_api_calls": self.stats["api_calls"],
                    "total_cost_usd": self.stats["total_cost"],
                    "avg_cost_per_page": self.stats["total_cost"] / len(results) if results else 0,
                    "high_value_pages_found": self.stats["high_value_found"]
                },
                "configuration": self.config,
                "cost_breakdown": {
                    "model_used": self.config["AI"]["MODEL"],
                    "total_cost": self.stats["total_cost"],
                    "cost_per_api_call": self.stats["total_cost"] / max(1, self.stats["api_calls"]),
                    "target_cost_per_page": self.config["COSTS"]["TARGET_COST_PER_PAGE"],
                    "cost_efficiency": "within_target" if (self.stats["total_cost"] / max(1, len(results))) <= self.config["COSTS"]["TARGET_COST_PER_PAGE"] else "over_target"
                }
            },
            "results": results
        }

        # Save main JSON results
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"page_prioritization_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"Analysis results saved: {json_filename}")

        # Save CSV summary
        if self.config["OUTPUT"]["SAVE_CSV_SUMMARY"]:
            csv_filename = f"priority_analysis_summary_{timestamp}.csv"
            csv_filepath = self.results_dir / csv_filename

            import csv
            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'URL', 'Domain', 'Title', 'Category', 'Priority_Score',
                    'Confidence', 'Personalization_Opportunities', 'Cost_USD', 'Status'
                ])

                for result in results:
                    page_data = result.get("page_data", {})
                    analysis = result.get("analysis", {})
                    classification = analysis.get("classification", {})
                    intelligence = analysis.get("intelligence", {})
                    processing = result.get("processing", {})

                    writer.writerow([
                        page_data.get("url", ""),
                        page_data.get("domain", ""),
                        page_data.get("title", ""),
                        classification.get("category", ""),
                        classification.get("score", 0),
                        classification.get("confidence", 0),
                        len(intelligence.get("personalization_opportunities", [])),
                        f"{processing.get('cost_estimate_usd', 0):.4f}",
                        "success" if "error" not in result else "error"
                    ])

            print(f"CSV summary saved: {csv_filename}")

    def _print_summary(self, results: List[Dict[str, Any]], processing_time: float):
        """Print analysis summary"""

        print("\n" + "=" * 60)
        print("PAGE PRIORITIZATION SUMMARY")
        print("=" * 60)

        successful_results = [r for r in results if "error" not in r]
        failed_results = [r for r in results if "error" in r]

        print(f"Pages analyzed: {len(results):,}")
        print(f"Successful: {len(successful_results):,} ({len(successful_results)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed_results):,} ({len(failed_results)/len(results)*100:.1f}%)")

        # Priority distribution
        if successful_results:
            high_value = len([r for r in successful_results if r.get("analysis", {}).get("classification", {}).get("score", 0) >= 8])
            medium_value = len([r for r in successful_results if 5 <= r.get("analysis", {}).get("classification", {}).get("score", 0) < 8])
            low_value = len([r for r in successful_results if r.get("analysis", {}).get("classification", {}).get("score", 0) < 5])

            print(f"\nPRIORITY DISTRIBUTION:")
            print(f"  High value (8-10): {high_value:,} ({high_value/len(successful_results)*100:.1f}%)")
            print(f"  Medium value (5-7): {medium_value:,} ({medium_value/len(successful_results)*100:.1f}%)")
            print(f"  Low value (0-4): {low_value:,} ({low_value/len(successful_results)*100:.1f}%)")

        # Cost analysis
        print(f"\nCOST ANALYSIS:")
        print(f"  Total API calls: {self.stats['api_calls']:,}")
        print(f"  Total cost: ${self.stats['total_cost']:.4f}")
        print(f"  Cost per page: ${self.stats['total_cost']/len(results):.4f}" if results else "N/A")
        print(f"  Target cost per page: ${self.config['COSTS']['TARGET_COST_PER_PAGE']:.4f}")

        # Performance metrics
        print(f"\nPERFORMANCE:")
        print(f"  Total processing time: {processing_time:.2f}s")
        print(f"  Average time per page: {processing_time/len(results):.2f}s" if results else "N/A")
        print(f"  Pages per second: {len(results)/processing_time:.2f}" if processing_time > 0 else "N/A")

        print("=" * 60)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function for testing"""

    print("=" * 60)
    print(f"PAGE PRIORITIZER v{SCRIPT_STATS['version']}")
    print("=" * 60)

    # Sample page data for testing
    test_pages = [
        {
            "url": "https://www.altitudestrategies.ca/about",
            "title": "About Altitude Strategies - Marketing Agency",
            "content": "Altitude Strategies is a leading marketing agency based in Canada. Founded in 2010, we specialize in digital marketing solutions for small and medium businesses. Our team of 25 professionals includes senior marketers, creative designers, and strategic consultants. We have helped over 200 clients achieve their marketing goals through innovative campaigns and data-driven approaches. Our CEO, Marie Johnson, has over 15 years of experience in marketing and leads our strategic initiatives."
        },
        {
            "url": "https://www.stryvemarketing.com/services",
            "title": "Services - Stryve Digital Marketing",
            "content": "At Stryve Marketing, we offer comprehensive digital marketing services including SEO, PPC advertising, content marketing, and social media management. Our services are designed to help businesses grow their online presence and increase conversions. We use advanced analytics and proven methodologies to deliver measurable results for our clients."
        }
    ]

    prioritizer = PagePrioritizer()
    results = await prioritizer.analyze_pages(test_pages)

    print(f"\nAnalysis completed: {len(results)} results generated")

    return results

if __name__ == "__main__":
    asyncio.run(main())