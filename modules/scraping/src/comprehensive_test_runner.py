#!/usr/bin/env python3
"""
=== COMPREHENSIVE SCRAPING TEST RUNNER ===
Version: 1.0.0 | Created: 2025-09-25

PURPOSE:
Complete test runner for all 4 scraping components - tests full pipeline on real Canadian domains

FEATURES:
- Site analysis (HTTP vs JavaScript detection)
- Website scraping (ultra-parallel content extraction)
- Page prioritization (AI-powered intelligence analysis)
- Apify scraping (JavaScript-heavy sites fallback)
- Comprehensive performance metrics and cost analysis
- Detailed results with CSV summaries and JSON exports

USAGE:
1. Configure test parameters in CONFIG section
2. Ensure all API keys in .env (OPENAI_API_KEY, APIFY_API_KEY)
3. Run: python comprehensive_test_runner.py
4. Results saved to ../results/ with timestamp
"""

import asyncio
import json
import time
import os
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# Import all scraping modules
from site_analyzer import SiteAnalyzer
from website_scraper import WebsiteScraper
from page_prioritizer import PagePrioritizer
from apify_scraper import ApifyScraper

# ============================================================================
# CONFIG SECTION
# ============================================================================

CONFIG = {
    "TESTING": {
        "MAX_DOMAINS": 100,
        "ENABLE_SITE_ANALYSIS": True,
        "ENABLE_WEBSITE_SCRAPING": True,
        "ENABLE_PAGE_PRIORITIZATION": True,
        "ENABLE_APIFY_SCRAPING": True,
        "DETAILED_LOGGING": True
    },

    "PERFORMANCE": {
        "PARALLEL_LIMIT": 20,
        "REQUEST_DELAY": 0.1,
        "TIMEOUT_SECONDS": 30,
        "MAX_RETRIES": 3
    },

    "OUTPUT": {
        "SAVE_DETAILED_JSON": True,
        "SAVE_CSV_SUMMARY": True,
        "SAVE_PERFORMANCE_METRICS": True,
        "RESULTS_DIR": "../results"
    }
}

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

class ComprehensiveTestRunner:
    """Complete test runner for all scraping components"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.stats = {
            "start_time": 0,
            "domains_tested": 0,
            "total_processing_time": 0,
            "component_stats": {}
        }

    @auto_log("comprehensive_test_runner")
    async def run_comprehensive_test(self):
        """Run complete test pipeline on Canadian domains"""

        print("=" * 80)
        print(f"COMPREHENSIVE SCRAPING TEST - ALL 4 COMPONENTS")
        print("=" * 80)

        self.stats["start_time"] = time.time()

        try:
            # Load Canadian domains
            domains = await self._load_canadian_domains()
            self.stats["domains_tested"] = len(domains)
            print(f"Loaded {len(domains)} Canadian domains for testing")

            results = {}

            # Stage 1: Site Analysis
            if self.config["TESTING"]["ENABLE_SITE_ANALYSIS"]:
                print(f"\n{'='*60}")
                print("STAGE 1: SITE ANALYSIS")
                print(f"{'='*60}")
                results["site_analysis"] = await self._run_site_analysis(domains)

            # Stage 2: Website Scraping
            if self.config["TESTING"]["ENABLE_WEBSITE_SCRAPING"]:
                print(f"\n{'='*60}")
                print("STAGE 2: WEBSITE SCRAPING")
                print(f"{'='*60}")
                results["website_scraping"] = await self._run_website_scraping(domains)

            # Stage 3: Page Prioritization
            if self.config["TESTING"]["ENABLE_PAGE_PRIORITIZATION"] and "website_scraping" in results:
                print(f"\n{'='*60}")
                print("STAGE 3: PAGE PRIORITIZATION (AI)")
                print(f"{'='*60}")
                results["page_prioritization"] = await self._run_page_prioritization(results["website_scraping"])

            # Stage 4: Apify Scraping (selective)
            if self.config["TESTING"]["ENABLE_APIFY_SCRAPING"] and "site_analysis" in results:
                print(f"\n{'='*60}")
                print("STAGE 4: APIFY SCRAPING (JavaScript Sites)")
                print(f"{'='*60}")
                results["apify_scraping"] = await self._run_apify_scraping(domains, results["site_analysis"])

            # Calculate final stats
            self.stats["total_processing_time"] = time.time() - self.stats["start_time"]

            # Save comprehensive results
            await self._save_comprehensive_results(results)

            # Print final summary
            self._print_comprehensive_summary(results)

            return results

        except Exception as e:
            print(f"Comprehensive test failed: {e}")
            return {"error": str(e)}

    async def _load_canadian_domains(self) -> List[str]:
        """Load Canadian domains from CSV"""

        data_file = Path(__file__).parent.parent / "../../data/master-leads/test_clean_canadian.csv"

        if not data_file.exists():
            print(f"Canadian data file not found at {data_file}")
            # Return sample domains for testing
            return [
                "https://www.altitudestrategies.ca",
                "https://www.stryvemarketing.com",
                "http://www.bigfishcreative.ca",
                "http://www.workparty.ca",
                "http://www.theog.co",
                "http://www.involvedmedia.ca",
                "http://www.nimiopere.com",
                "https://www.cossette.com",
                "https://www.rethinkfirst.com",
                "https://www.john-st.com"
            ]

        domains = []
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    website = row.get('website', '').strip()
                    if website and len(domains) < self.config["TESTING"]["MAX_DOMAINS"]:
                        domains.append(website)

            return domains[:self.config["TESTING"]["MAX_DOMAINS"]]

        except Exception as e:
            print(f"Error loading Canadian data: {e}")
            return []

    async def _run_site_analysis(self, domains: List[str]) -> Dict[str, Any]:
        """Run site analysis component"""

        stage_start = time.time()
        analyzer = SiteAnalyzer()

        try:
            results = await analyzer.analyze_sites(domains)
            processing_time = time.time() - stage_start

            # Calculate stats
            successful = len([r for r in results if "error" not in r])

            stage_stats = {
                "total_domains": len(domains),
                "successful_analyses": successful,
                "failed_analyses": len(results) - successful,
                "success_rate": (successful / len(results) * 100) if results else 0,
                "processing_time": processing_time,
                "domains_per_minute": (len(domains) / processing_time * 60) if processing_time > 0 else 0,
                "results": results
            }

            self.stats["component_stats"]["site_analysis"] = stage_stats
            print(f"Site Analysis: {successful}/{len(results)} success ({successful/len(results)*100:.1f}%)")

            return stage_stats

        except Exception as e:
            print(f"Site analysis failed: {e}")
            return {"error": str(e), "results": []}

    async def _run_website_scraping(self, domains: List[str]) -> Dict[str, Any]:
        """Run website scraping component"""

        stage_start = time.time()
        scraper = WebsiteScraper()

        try:
            results = await scraper.scrape_websites(domains)
            processing_time = time.time() - stage_start

            # Calculate stats
            successful = len([r for r in results if "error" not in r])
            total_pages = sum(len(r.get("pages", [])) for r in results if "error" not in r)
            total_content = sum(
                r.get("metadata", {}).get("total_content_length", 0)
                for r in results if "error" not in r
            )

            stage_stats = {
                "total_domains": len(domains),
                "successful_scrapes": successful,
                "failed_scrapes": len(results) - successful,
                "success_rate": (successful / len(results) * 100) if results else 0,
                "total_pages_scraped": total_pages,
                "total_content_extracted": total_content,
                "avg_pages_per_domain": total_pages / successful if successful > 0 else 0,
                "processing_time": processing_time,
                "pages_per_minute": (total_pages / processing_time * 60) if processing_time > 0 else 0,
                "results": results
            }

            self.stats["component_stats"]["website_scraping"] = stage_stats
            print(f"Website Scraping: {successful}/{len(results)} success, {total_pages} pages scraped")

            return stage_stats

        except Exception as e:
            print(f"Website scraping failed: {e}")
            return {"error": str(e), "results": []}

    async def _run_page_prioritization(self, scraping_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run page prioritization component"""

        stage_start = time.time()

        # Extract pages from scraping results
        all_pages = []
        for result in scraping_results.get("results", []):
            if "error" not in result:
                pages = result.get("pages", [])
                for page in pages:
                    # Add domain info
                    page["domain"] = result.get("domain", "")
                    all_pages.append(page)

        if not all_pages:
            print("No pages available for prioritization")
            return {"error": "No pages to analyze", "results": []}

        # Limit pages for cost control (sample from each domain)
        sample_pages = self._sample_pages_per_domain(all_pages, max_per_domain=3, max_total=50)

        print(f"Analyzing {len(sample_pages)} pages (sampled from {len(all_pages)} total)")

        try:
            prioritizer = PagePrioritizer()
            results = await prioritizer.analyze_pages(sample_pages)
            processing_time = time.time() - stage_start

            # Calculate stats
            successful = len([r for r in results if "error" not in r])
            high_value_pages = len([
                r for r in results
                if "error" not in r and r.get("analysis", {}).get("classification", {}).get("score", 0) >= 8
            ])

            total_cost = sum(
                r.get("processing", {}).get("cost_estimate_usd", 0)
                for r in results if "error" not in r
            )

            stage_stats = {
                "total_pages_analyzed": len(sample_pages),
                "successful_analyses": successful,
                "failed_analyses": len(results) - successful,
                "success_rate": (successful / len(results) * 100) if results else 0,
                "high_value_pages_found": high_value_pages,
                "total_ai_cost_usd": total_cost,
                "avg_cost_per_page": total_cost / len(results) if results else 0,
                "processing_time": processing_time,
                "pages_per_minute": (len(sample_pages) / processing_time * 60) if processing_time > 0 else 0,
                "results": results
            }

            self.stats["component_stats"]["page_prioritization"] = stage_stats
            print(f"Page Prioritization: {successful}/{len(results)} success, ${total_cost:.3f} AI cost")

            return stage_stats

        except Exception as e:
            print(f"Page prioritization failed: {e}")
            return {"error": str(e), "results": []}

    async def _run_apify_scraping(self, domains: List[str], site_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Run Apify scraping for JavaScript-heavy sites"""

        stage_start = time.time()

        # Filter domains that need Apify based on site analysis
        apify_domains = []
        analysis_results = site_analysis.get("results", [])

        for result in analysis_results:
            if "error" not in result:
                recommendation = result.get("recommendation", {})
                if recommendation.get("method") in ["APIFY_REQUIRED", "HYBRID_APPROACH"]:
                    apify_domains.append(result.get("url", ""))

        # Limit Apify domains for cost control
        apify_domains = apify_domains[:10]  # Max 10 domains for testing

        if not apify_domains:
            print("No domains require Apify scraping based on site analysis")
            return {"total_domains": 0, "results": []}

        print(f"Running Apify scraping on {len(apify_domains)} JavaScript-heavy domains")

        try:
            scraper = ApifyScraper()
            results = await scraper.scrape_domains(apify_domains, analysis_results)
            processing_time = time.time() - stage_start

            # Calculate stats
            successful = len([r for r in results if "error" not in r])
            total_pages = sum(len(r.get("pages", [])) for r in results if "error" not in r)
            total_cost = sum(
                r.get("metadata", {}).get("cost_estimate_usd", 0)
                for r in results if "error" not in r
            )

            stage_stats = {
                "total_domains": len(apify_domains),
                "successful_scrapes": successful,
                "failed_scrapes": len(results) - successful,
                "success_rate": (successful / len(results) * 100) if results else 0,
                "total_pages_scraped": total_pages,
                "total_apify_cost_usd": total_cost,
                "avg_cost_per_domain": total_cost / len(apify_domains) if apify_domains else 0,
                "processing_time": processing_time,
                "results": results
            }

            self.stats["component_stats"]["apify_scraping"] = stage_stats
            print(f"Apify Scraping: {successful}/{len(results)} success, ${total_cost:.3f} cost")

            return stage_stats

        except Exception as e:
            print(f"Apify scraping failed: {e}")
            return {"error": str(e), "results": []}

    def _sample_pages_per_domain(self, pages: List[Dict], max_per_domain: int = 3, max_total: int = 50) -> List[Dict]:
        """Sample pages intelligently per domain for cost control"""

        # Group by domain
        domain_pages = {}
        for page in pages:
            domain = page.get("domain", "unknown")
            if domain not in domain_pages:
                domain_pages[domain] = []
            domain_pages[domain].append(page)

        # Sample pages from each domain
        sampled_pages = []

        for domain, domain_page_list in domain_pages.items():
            # Sort by likely importance (homepage first, then about, services, etc.)
            priority_keywords = ["home", "index", "about", "team", "services", "case", "news"]

            def page_priority(page):
                url = page.get("url", "").lower()
                for i, keyword in enumerate(priority_keywords):
                    if keyword in url:
                        return i
                return len(priority_keywords)

            sorted_pages = sorted(domain_page_list, key=page_priority)
            sampled_pages.extend(sorted_pages[:max_per_domain])

            if len(sampled_pages) >= max_total:
                break

        return sampled_pages[:max_total]

    async def _save_comprehensive_results(self, results: Dict[str, Any]):
        """Save all results with comprehensive metadata"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Comprehensive results
        comprehensive_results = {
            "metadata": {
                "timestamp": timestamp,
                "test_type": "comprehensive_scraping_pipeline",
                "domains_tested": self.stats["domains_tested"],
                "total_processing_time": self.stats["total_processing_time"],
                "components_tested": list(self.stats["component_stats"].keys()),
                "configuration": self.config
            },
            "component_results": results,
            "performance_summary": self.stats["component_stats"],
            "overall_metrics": self._calculate_overall_metrics(results)
        }

        # Save detailed JSON
        if self.config["OUTPUT"]["SAVE_DETAILED_JSON"]:
            json_filename = f"comprehensive_test_results_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)

            print(f"Comprehensive results saved: {json_filename}")

        # Save CSV summary
        if self.config["OUTPUT"]["SAVE_CSV_SUMMARY"]:
            await self._save_csv_summary(results, timestamp)

    async def _save_csv_summary(self, results: Dict[str, Any], timestamp: str):
        """Save CSV summary of all components"""

        csv_filename = f"comprehensive_test_summary_{timestamp}.csv"
        csv_filepath = self.results_dir / csv_filename

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Domain', 'Site_Analysis_Method', 'Site_Analysis_Confidence',
                'Scraping_Success', 'Pages_Scraped', 'Content_Length',
                'AI_Analysis_Success', 'Priority_Score', 'AI_Cost_USD',
                'Apify_Used', 'Apify_Cost_USD', 'Total_Cost_USD'
            ])

            # Create lookup dictionaries
            site_lookup = {}
            if "site_analysis" in results:
                for result in results["site_analysis"].get("results", []):
                    url = result.get("url", "")
                    site_lookup[url] = result

            scraping_lookup = {}
            if "website_scraping" in results:
                for result in results["website_scraping"].get("results", []):
                    domain = result.get("domain", "")
                    scraping_lookup[domain] = result

            prioritization_lookup = {}
            if "page_prioritization" in results:
                for result in results["page_prioritization"].get("results", []):
                    domain = result.get("page_data", {}).get("domain", "")
                    if domain not in prioritization_lookup:
                        prioritization_lookup[domain] = []
                    prioritization_lookup[domain].append(result)

            apify_lookup = {}
            if "apify_scraping" in results:
                for result in results["apify_scraping"].get("results", []):
                    domain = result.get("domain", "")
                    apify_lookup[domain] = result

            # Write domain data
            all_domains = set()
            for component_results in results.values():
                if "results" in component_results:
                    for result in component_results["results"]:
                        domain = result.get("domain", "") or result.get("url", "")
                        if domain:
                            all_domains.add(domain)

            for domain in sorted(all_domains):
                site_data = site_lookup.get(domain, {})
                scraping_data = scraping_lookup.get(domain, {})
                priority_data = prioritization_lookup.get(domain, [])
                apify_data = apify_lookup.get(domain, {})

                # Aggregate priority data
                avg_priority_score = 0
                total_ai_cost = 0
                ai_success = False

                if priority_data:
                    scores = [p.get("analysis", {}).get("classification", {}).get("score", 0) for p in priority_data if "error" not in p]
                    costs = [p.get("processing", {}).get("cost_estimate_usd", 0) for p in priority_data if "error" not in p]

                    if scores:
                        avg_priority_score = sum(scores) / len(scores)
                        total_ai_cost = sum(costs)
                        ai_success = True

                writer.writerow([
                    domain,
                    site_data.get("recommendation", {}).get("method", "unknown"),
                    f"{site_data.get('recommendation', {}).get('confidence', 0):.2f}",
                    "success" if "error" not in scraping_data else "failed",
                    len(scraping_data.get("pages", [])),
                    scraping_data.get("metadata", {}).get("total_content_length", 0),
                    "success" if ai_success else "failed",
                    f"{avg_priority_score:.1f}" if ai_success else "0.0",
                    f"{total_ai_cost:.4f}",
                    "yes" if "error" not in apify_data else "no",
                    f"{apify_data.get('metadata', {}).get('cost_estimate_usd', 0):.4f}",
                    f"{total_ai_cost + apify_data.get('metadata', {}).get('cost_estimate_usd', 0):.4f}"
                ])

        print(f"CSV summary saved: {csv_filename}")

    def _calculate_overall_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall pipeline metrics"""

        total_cost = 0
        total_domains = self.stats["domains_tested"]

        # Sum costs from all components
        for component_stats in self.stats["component_stats"].values():
            total_cost += component_stats.get("total_ai_cost_usd", 0)
            total_cost += component_stats.get("total_apify_cost_usd", 0)

        return {
            "overall_success_rate": self._calculate_overall_success_rate(results),
            "total_pipeline_cost_usd": total_cost,
            "cost_per_domain": total_cost / total_domains if total_domains > 0 else 0,
            "total_processing_time": self.stats["total_processing_time"],
            "domains_per_minute": (total_domains / self.stats["total_processing_time"] * 60) if self.stats["total_processing_time"] > 0 else 0,
            "pipeline_efficiency": "excellent" if total_cost / total_domains < 0.05 else "good" if total_cost / total_domains < 0.10 else "needs_optimization"
        }

    def _calculate_overall_success_rate(self, results: Dict[str, Any]) -> float:
        """Calculate overall pipeline success rate"""

        total_success = 0
        total_attempts = 0

        for component_stats in self.stats["component_stats"].values():
            if "success_rate" in component_stats:
                success_count = component_stats.get("successful_analyses", 0) or component_stats.get("successful_scrapes", 0)
                total_count = success_count + component_stats.get("failed_analyses", 0) + component_stats.get("failed_scrapes", 0)

                total_success += success_count
                total_attempts += total_count

        return (total_success / total_attempts * 100) if total_attempts > 0 else 0

    def _print_comprehensive_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""

        print("\n" + "=" * 80)
        print("COMPREHENSIVE SCRAPING TEST SUMMARY")
        print("=" * 80)

        overall_metrics = self._calculate_overall_metrics(results)

        print(f"Total domains tested: {self.stats['domains_tested']}")
        print(f"Total processing time: {self.stats['total_processing_time']:.2f}s ({self.stats['total_processing_time']/60:.1f} minutes)")
        print(f"Overall success rate: {overall_metrics['overall_success_rate']:.1f}%")
        print(f"Domains per minute: {overall_metrics['domains_per_minute']:.1f}")

        # Component breakdown
        print(f"\nCOMPONENT PERFORMANCE:")
        for component, stats in self.stats["component_stats"].items():
            success_rate = stats.get("success_rate", 0)
            processing_time = stats.get("processing_time", 0)

            print(f"  {component.upper()}:")
            print(f"    Success rate: {success_rate:.1f}%")
            print(f"    Processing time: {processing_time:.2f}s")

            if "total_pages_scraped" in stats:
                print(f"    Pages scraped: {stats['total_pages_scraped']:,}")

            cost = stats.get("total_ai_cost_usd", 0) + stats.get("total_apify_cost_usd", 0)
            if cost > 0:
                print(f"    Cost: ${cost:.3f}")

        # Cost analysis
        total_cost = overall_metrics["total_pipeline_cost_usd"]
        print(f"\nCOST ANALYSIS:")
        print(f"  Total pipeline cost: ${total_cost:.3f}")
        print(f"  Cost per domain: ${overall_metrics['cost_per_domain']:.4f}")
        print(f"  Efficiency rating: {overall_metrics['pipeline_efficiency']}")

        # Final assessment
        print(f"\nFINAL ASSESSMENT:")
        if overall_metrics["overall_success_rate"] >= 85 and overall_metrics["cost_per_domain"] <= 0.05:
            print("  EXCELLENT - Production ready pipeline")
        elif overall_metrics["overall_success_rate"] >= 75 and overall_metrics["cost_per_domain"] <= 0.10:
            print("  GOOD - Minor optimizations recommended")
        else:
            print("  NEEDS IMPROVEMENT - Review failed components")

        print("=" * 80)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""

    runner = ComprehensiveTestRunner()
    results = await runner.run_comprehensive_test()

    if "error" not in results:
        print(f"\nComprehensive test completed successfully!")
    else:
        print(f"\nTest failed: {results['error']}")

    return results

if __name__ == "__main__":
    asyncio.run(main())