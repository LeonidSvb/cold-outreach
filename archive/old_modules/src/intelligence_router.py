#!/usr/bin/env python3
"""
=== WEBSITE INTELLIGENCE ROUTER ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
Main orchestrator for website intelligence extraction pipeline.
Automatically routes domains through HTTP or Apify based on complexity analysis.

FEATURES:
- Automatic domain complexity analysis
- Smart routing (HTTP vs Apify)
- Parallel processing with optimal resource allocation
- AI-powered content summarization
- Comprehensive result aggregation

USAGE:
1. Configure domains list in config.json
2. Set API keys in .env
3. Run: python intelligence_router.py
4. Results saved to results/ with timestamped files

IMPROVEMENTS:
v1.0.0 - Initial implementation with full pipeline
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures

# Add parent directory to path for shared modules
sys.path.append(str(Path(__file__).parent.parent.parent))
from modules.shared.logger import auto_log

# Import local components
from site_analyzer import SiteAnalyzer
from http_scraper import HTTPScraper
from content_processor import ContentProcessor

# ============================================================================
# CONFIG SECTION
# ============================================================================

CONFIG = {
    "PROCESSING": {
        "max_concurrent_domains": 20,
        "http_batch_size": 50,
        "apify_batch_size": 10,
        "ai_batch_size": 5,
        "timeout_seconds": 30,
        "retry_attempts": 2
    },

    "ROUTING": {
        "http_confidence_threshold": 0.7,
        "javascript_risk_threshold": 50,
        "force_apify_patterns": [
            "react", "angular", "vue", "spa",
            "single-page", "javascript-required"
        ]
    },

    "OUTPUT": {
        "save_raw_data": True,
        "save_analysis_results": True,
        "save_ai_summaries": True,
        "export_csv": True,
        "results_dir": "results"
    },

    "AI_PROCESSING": {
        "summarization_enabled": True,
        "personalization_enabled": True,
        "contact_extraction": True,
        "company_analysis": True
    }
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "domains_processed": 0,
    "http_success_rate": 0.0,
    "apify_success_rate": 0.0,
    "avg_processing_time": 0.0
}

# ============================================================================
# MAIN ROUTER CLASS
# ============================================================================

class WebsiteIntelligenceRouter:
    """Main orchestrator for website intelligence extraction"""

    def __init__(self):
        self.config = CONFIG
        self.session_id = f"intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()

        # Initialize components
        self.site_analyzer = SiteAnalyzer()
        self.http_scraper = HTTPScraper()
        self.content_processor = ContentProcessor()

        # Results storage
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["results_dir"]
        self.results_dir.mkdir(exist_ok=True)

        # Processing stats
        self.stats = {
            "domains_analyzed": 0,
            "http_processed": 0,
            "apify_processed": 0,
            "ai_summarized": 0,
            "errors": [],
            "processing_times": {}
        }

    @auto_log("website_intelligence")
    async def process_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Main processing pipeline for domain list"""

        print(f"Starting Website Intelligence Pipeline")
        print(f"Session ID: {self.session_id}")
        print(f"Total domains: {len(domains):,}")
        print(f"Configuration: {self.config['PROCESSING']}")

        # Phase 1: Analyze all domains for routing
        print(f"\n=== PHASE 1: DOMAIN ANALYSIS ===")
        routing_results = await self._analyze_domains_for_routing(domains)

        # Phase 2: Process domains based on routing
        print(f"\n=== PHASE 2: CONTENT EXTRACTION ===")
        extraction_results = await self._process_routed_domains(routing_results)

        # Phase 3: AI processing and summarization
        print(f"\n=== PHASE 3: AI SUMMARIZATION ===")
        final_results = await self._process_ai_summarization(extraction_results)

        # Phase 4: Save and export results
        print(f"\n=== PHASE 4: RESULTS EXPORT ===")
        await self._save_final_results(final_results)

        # Update stats and return summary
        total_time = time.time() - self.start_time
        self._update_script_stats(len(domains), total_time)

        summary = self._generate_processing_summary(final_results, total_time)
        print(f"\n{summary}")

        return final_results

    async def _analyze_domains_for_routing(self, domains: List[str]) -> Dict[str, Any]:
        """Phase 1: Analyze domains to determine routing strategy"""

        routing_results = {
            "http_domains": [],
            "apify_domains": [],
            "analysis_details": {},
            "routing_stats": {"total": len(domains), "http": 0, "apify": 0, "errors": 0}
        }

        print(f"Analyzing {len(domains)} domains for optimal routing...")

        # Process domains in batches for analysis
        batch_size = 20
        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            batch_results = await self._analyze_domain_batch(batch)

            # Categorize results
            for domain, analysis in batch_results.items():
                if analysis.get("error"):
                    routing_results["routing_stats"]["errors"] += 1
                    continue

                routing_results["analysis_details"][domain] = analysis

                # Routing decision logic
                if self._should_use_http(analysis):
                    routing_results["http_domains"].append(domain)
                    routing_results["routing_stats"]["http"] += 1
                else:
                    routing_results["apify_domains"].append(domain)
                    routing_results["routing_stats"]["apify"] += 1

            # Progress update
            progress = min(i + batch_size, len(domains))
            print(f"Analysis progress: {progress}/{len(domains)} ({progress/len(domains)*100:.1f}%)")

        # Print routing summary
        stats = routing_results["routing_stats"]
        print(f"Routing completed:")
        print(f"  HTTP domains: {stats['http']} ({stats['http']/stats['total']*100:.1f}%)")
        print(f"  Apify domains: {stats['apify']} ({stats['apify']/stats['total']*100:.1f}%)")
        print(f"  Errors: {stats['errors']}")

        return routing_results

    async def _analyze_domain_batch(self, domains: List[str]) -> Dict[str, Dict]:
        """Analyze a batch of domains"""

        results = {}

        # Use ThreadPoolExecutor for concurrent analysis
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {
                executor.submit(self.site_analyzer.analyze_site, domain): domain
                for domain in domains
            }

            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    analysis = future.result(timeout=30)
                    results[domain] = analysis
                except Exception as e:
                    results[domain] = {"error": str(e), "scraping_method": "apify"}

        return results

    def _should_use_http(self, analysis: Dict) -> bool:
        """Determine if domain should use HTTP scraping"""

        # Check confidence score
        confidence = analysis.get("confidence", 0)
        if confidence >= self.config["ROUTING"]["http_confidence_threshold"]:
            return True

        # Check JavaScript risk
        js_indicators = analysis.get("js_indicators", {})
        risk_score = js_indicators.get("risk_score", 100)
        if risk_score >= self.config["ROUTING"]["javascript_risk_threshold"]:
            return False

        # Check for protection
        if js_indicators.get("protection_detected", False):
            return False

        # Check explicit recommendation
        scraping_method = analysis.get("scraping_method", "apify")
        return scraping_method == "http"

    async def _process_routed_domains(self, routing_results: Dict) -> Dict[str, Any]:
        """Phase 2: Process domains based on routing results"""

        extraction_results = {
            "http_results": {},
            "apify_results": {},
            "processing_stats": {
                "http_success": 0,
                "http_failures": 0,
                "apify_success": 0,
                "apify_failures": 0
            }
        }

        # Process HTTP domains
        if routing_results["http_domains"]:
            print(f"Processing {len(routing_results['http_domains'])} domains via HTTP...")
            http_results = await self._process_http_domains(routing_results["http_domains"])
            extraction_results["http_results"] = http_results

            # Update stats
            for result in http_results.values():
                if result.get("success", False):
                    extraction_results["processing_stats"]["http_success"] += 1
                else:
                    extraction_results["processing_stats"]["http_failures"] += 1

        # Process Apify domains
        if routing_results["apify_domains"]:
            print(f"Processing {len(routing_results['apify_domains'])} domains via Apify...")
            apify_results = await self._process_apify_domains(routing_results["apify_domains"])
            extraction_results["apify_results"] = apify_results

            # Update stats
            for result in apify_results.values():
                if result.get("success", False):
                    extraction_results["processing_stats"]["apify_success"] += 1
                else:
                    extraction_results["processing_stats"]["apify_failures"] += 1

        return extraction_results

    async def _process_http_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Process domains using HTTP scraper"""

        results = {}

        # Use HTTP scraper with high concurrency
        http_results = await self.http_scraper.scrape_domains_parallel(
            domains,
            max_workers=self.config["PROCESSING"]["http_batch_size"]
        )

        for domain, result in http_results.items():
            results[domain] = {
                "method": "http",
                "success": bool(result.get("pages")),
                "pages_extracted": len(result.get("pages", [])),
                "total_text_length": sum(len(p.get("text", "")) for p in result.get("pages", [])),
                "processing_time": result.get("processing_time", 0),
                "raw_data": result
            }

        return results

    async def _process_apify_domains(self, domains: List[str]) -> Dict[str, Any]:
        """Process domains using Apify"""

        results = {}

        # TODO: Implement Apify router
        print(f"Apify processing not yet implemented. Marking {len(domains)} domains as pending.")

        for domain in domains:
            results[domain] = {
                "method": "apify",
                "success": False,
                "error": "Apify integration not yet implemented",
                "pages_extracted": 0,
                "total_text_length": 0,
                "processing_time": 0,
                "raw_data": {}
            }

        return results

    async def _process_ai_summarization(self, extraction_results: Dict) -> Dict[str, Any]:
        """Phase 3: AI summarization of extracted content"""

        if not self.config["AI_PROCESSING"]["summarization_enabled"]:
            print("AI summarization disabled in config")
            return extraction_results

        print(f"Starting AI summarization...")

        # Combine all successful extractions
        all_extractions = {}
        all_extractions.update(extraction_results.get("http_results", {}))
        all_extractions.update(extraction_results.get("apify_results", {}))

        # Filter successful extractions
        successful_extractions = {
            domain: result for domain, result in all_extractions.items()
            if result.get("success", False) and result.get("total_text_length", 0) > 100
        }

        if not successful_extractions:
            print("No successful extractions found for AI processing")
            return extraction_results

        print(f"Processing {len(successful_extractions)} domains with AI...")

        # Process in batches for optimal token usage
        ai_results = await self.content_processor.process_domains_batch(
            successful_extractions,
            batch_size=self.config["PROCESSING"]["ai_batch_size"]
        )

        # Merge AI results back
        final_results = extraction_results.copy()
        final_results["ai_summaries"] = ai_results

        return final_results

    async def _save_final_results(self, results: Dict[str, Any]):
        """Phase 4: Save all results to files"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save comprehensive results JSON
        results_file = self.results_dir / f"website_intelligence_{timestamp}.json"

        # Prepare metadata
        results_data = {
            "metadata": {
                "session_id": self.session_id,
                "timestamp": timestamp,
                "processing_time": time.time() - self.start_time,
                "config_used": self.config,
                "script_version": SCRIPT_STATS["version"],
                "stats": self.stats
            },
            "results": results
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"Results saved: {results_file.name}")

        # Export CSV summary if enabled
        if self.config["OUTPUT"]["export_csv"]:
            await self._export_csv_summary(results, timestamp)

    async def _export_csv_summary(self, results: Dict, timestamp: str):
        """Export CSV summary of results"""

        import pandas as pd

        # Flatten results for CSV
        csv_data = []

        # Process HTTP results
        for domain, result in results.get("http_results", {}).items():
            csv_data.append({
                "domain": domain,
                "method": "http",
                "success": result.get("success", False),
                "pages_extracted": result.get("pages_extracted", 0),
                "text_length": result.get("total_text_length", 0),
                "processing_time": result.get("processing_time", 0),
                "ai_processed": domain in results.get("ai_summaries", {})
            })

        # Process Apify results
        for domain, result in results.get("apify_results", {}).items():
            csv_data.append({
                "domain": domain,
                "method": "apify",
                "success": result.get("success", False),
                "pages_extracted": result.get("pages_extracted", 0),
                "text_length": result.get("total_text_length", 0),
                "processing_time": result.get("processing_time", 0),
                "ai_processed": domain in results.get("ai_summaries", {})
            })

        if csv_data:
            df = pd.DataFrame(csv_data)
            csv_file = self.results_dir / f"website_intelligence_summary_{timestamp}.csv"
            df.to_csv(csv_file, index=False)
            print(f"CSV summary saved: {csv_file.name}")

    def _generate_processing_summary(self, results: Dict, total_time: float) -> str:
        """Generate processing summary"""

        http_count = len(results.get("http_results", {}))
        apify_count = len(results.get("apify_results", {}))
        ai_count = len(results.get("ai_summaries", {}))

        http_success = results.get("processing_stats", {}).get("http_success", 0)
        apify_success = results.get("processing_stats", {}).get("apify_success", 0)

        summary = f"""
=== WEBSITE INTELLIGENCE PIPELINE COMPLETE ===
Session: {self.session_id}
Total Time: {total_time:.2f}s

PROCESSING RESULTS:
  HTTP Domains: {http_count} (Success: {http_success})
  Apify Domains: {apify_count} (Success: {apify_success})
  AI Summaries: {ai_count}

PERFORMANCE:
  Avg Time per Domain: {total_time/(http_count + apify_count):.2f}s
  Success Rate: {(http_success + apify_success)/(http_count + apify_count)*100:.1f}%

RESULTS SAVED:
  Location: {self.results_dir}
  Files: JSON, CSV summaries available
"""
        return summary

    def _update_script_stats(self, domains_count: int, processing_time: float):
        """Update global script statistics"""
        global SCRIPT_STATS

        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["domains_processed"] += domains_count
        SCRIPT_STATS["avg_processing_time"] = processing_time

# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main execution function"""

    print("=" * 60)
    print("WEBSITE INTELLIGENCE ROUTER v1.0.0")
    print("=" * 60)

    # Sample domains for testing
    test_domains = [
        "https://example.com",
        "https://google.com",
        "https://github.com",
        "https://stackoverflow.com",
        "https://reddit.com"
    ]

    # Initialize router
    router = WebsiteIntelligenceRouter()

    # Process domains
    results = await router.process_domains(test_domains)

    print("=" * 60)
    print("PROCESSING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())