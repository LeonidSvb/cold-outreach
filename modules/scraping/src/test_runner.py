#!/usr/bin/env python3
"""
=== SCRAPING TEST RUNNER ===
Version: 2.0.0 | Created: 2025-09-25

PURPOSE:
Complete testing pipeline for the scraping module using 100+ Canadian domains.
Orchestrates all 4 scraping scripts in logical sequence with comprehensive validation.

FEATURES:
- Full 4-script pipeline orchestration
- Site analysis → Website scraping → Page prioritization → Apify fallback
- Real Canadian company data testing (100+ domains)
- Performance metrics tracking across all stages
- Cost analysis and optimization recommendations
- Success rate validation and error analysis
- Comprehensive reporting with actionable insights

USAGE:
1. Ensure all dependencies are configured (.env with API keys)
2. Run: python test_runner.py
3. Monitor progress through all 4 pipeline stages
4. Review comprehensive results and recommendations

IMPROVEMENTS:
v2.0.0 - Initial comprehensive test runner implementation
"""

import asyncio
import json
import time
import os
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# Import our scraping modules
from site_analyzer import SiteAnalyzer
from website_scraper import WebsiteScraper
from page_prioritizer import PagePrioritizer
from apify_scraper import ApifyScraper

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # TEST SETTINGS
    "TEST": {
        "MAX_DOMAINS": 100,
        "USE_REAL_DATA": True,
        "CANADIAN_DATA_FILE": "../../data/master-leads/test_clean_canadian.csv",
        "ENABLE_ALL_STAGES": True,
        "PARALLEL_PROCESSING": True
    },

    # PIPELINE CONTROL
    "PIPELINE": {
        "ENABLE_SITE_ANALYSIS": True,
        "ENABLE_WEBSITE_SCRAPING": True,
        "ENABLE_PAGE_PRIORITIZATION": True,
        "ENABLE_APIFY_FALLBACK": True,
        "STOP_ON_ERRORS": False,
        "MAX_ERRORS_PER_STAGE": 10
    },

    # PERFORMANCE TARGETS
    "TARGETS": {
        "MAX_PROCESSING_TIME": 1200,  # 20 minutes for 100 domains
        "MIN_SUCCESS_RATE": 80,       # 80% success rate
        "MAX_COST_USD": 2.0,          # $2 total cost
        "MIN_PAGES_PER_DOMAIN": 2,    # At least 2 pages per domain
        "MAX_COST_PER_DOMAIN": 0.02   # $0.02 per domain max
    },

    # VALIDATION THRESHOLDS
    "VALIDATION": {
        "MIN_CONTENT_LENGTH": 500,
        "MIN_HIGH_VALUE_PAGES": 10,   # At least 10 high-value pages
        "MAX_HTTP_FAILURES": 20,      # Max 20% HTTP failures
        "MIN_APIFY_SUCCESS": 70,      # 70% Apify success rate
        "REQUIRED_PAGE_TYPES": ["about", "services", "contact"]
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_COMPREHENSIVE_REPORT": True,
        "SAVE_PERFORMANCE_METRICS": True,
        "SAVE_ERROR_ANALYSIS": True,
        "RESULTS_DIR": "../results",
        "CREATE_SUMMARY_CSV": True
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_test_runs": 0,
    "last_test_run": None,
    "best_performance": {
        "processing_time": float('inf'),
        "success_rate": 0,
        "cost_efficiency": float('inf')
    }
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class ScrapingTestRunner:
    """Comprehensive test runner for scraping module pipeline"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)

        # Pipeline stages
        self.stages = {
            "site_analysis": {"enabled": self.config["PIPELINE"]["ENABLE_SITE_ANALYSIS"], "results": []},
            "website_scraping": {"enabled": self.config["PIPELINE"]["ENABLE_WEBSITE_SCRAPING"], "results": []},
            "page_prioritization": {"enabled": self.config["PIPELINE"]["ENABLE_PAGE_PRIORITIZATION"], "results": []},
            "apify_scraping": {"enabled": self.config["PIPELINE"]["ENABLE_APIFY_FALLBACK"], "results": []}
        }

        # Test metrics
        self.metrics = {
            "start_time": 0,
            "total_processing_time": 0,
            "domains_processed": 0,
            "total_cost": 0.0,
            "success_rates": {},
            "performance_data": {},
            "errors": []
        }

    @auto_log("test_runner")
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run complete scraping pipeline test"""

        print("=" * 80)
        print(f"SCRAPING MODULE COMPREHENSIVE TEST v{SCRIPT_STATS['version']}")
        print("=" * 80)
        print(f"Target domains: {self.config['TEST']['MAX_DOMAINS']}")
        print(f"Performance target: {self.config['TARGETS']['MAX_PROCESSING_TIME']/60:.1f} minutes")
        print(f"Cost target: ${self.config['TARGETS']['MAX_COST_USD']:.2f}")
        print(f"Success rate target: {self.config['TARGETS']['MIN_SUCCESS_RATE']}%")
        print("=" * 80)

        self.metrics["start_time"] = time.time()

        try:
            # Stage 1: Load test data
            domains = await self._load_test_domains()
            if not domains:
                raise Exception("No test domains loaded")

            self.metrics["domains_processed"] = len(domains)
            print(f"\nLoaded {len(domains)} test domains")

            # Stage 2: Site Analysis
            if self.stages["site_analysis"]["enabled"]:
                print(f"\n{'='*50}")
                print("STAGE 1: SITE ANALYSIS")
                print(f"{'='*50}")
                site_analysis_results = await self._run_site_analysis(domains)
                self.stages["site_analysis"]["results"] = site_analysis_results

            # Stage 3: Website Scraping
            if self.stages["website_scraping"]["enabled"]:
                print(f"\n{'='*50}")
                print("STAGE 2: WEBSITE SCRAPING")
                print(f"{'='*50}")
                scraping_results = await self._run_website_scraping(domains)
                self.stages["website_scraping"]["results"] = scraping_results

            # Stage 4: Page Prioritization
            if self.stages["page_prioritization"]["enabled"]:
                print(f"\n{'='*50}")
                print("STAGE 3: PAGE PRIORITIZATION")
                print(f"{'='*50}")
                prioritization_results = await self._run_page_prioritization()
                self.stages["page_prioritization"]["results"] = prioritization_results

            # Stage 5: Apify Fallback
            if self.stages["apify_scraping"]["enabled"]:
                print(f"\n{'='*50}")
                print("STAGE 4: APIFY FALLBACK")
                print(f"{'='*50}")
                apify_results = await self._run_apify_scraping(domains)
                self.stages["apify_scraping"]["results"] = apify_results

            # Calculate final metrics
            self.metrics["total_processing_time"] = time.time() - self.metrics["start_time"]

            # Generate comprehensive analysis
            analysis_results = await self._analyze_pipeline_results()

            # Save all results
            await self._save_comprehensive_results(analysis_results)

            # Print final summary
            self._print_comprehensive_summary(analysis_results)

            return analysis_results

        except Exception as e:
            print(f"\nCRITICAL ERROR: {e}")
            print(traceback.format_exc())
            return {"error": str(e), "traceback": traceback.format_exc()}

    async def _load_test_domains(self) -> List[str]:
        """Load test domains from Canadian company data"""

        try:
            data_file = Path(__file__).parent.parent / self.config["TEST"]["CANADIAN_DATA_FILE"]
            if not data_file.exists():
                print(f"Warning: Canadian data file not found at {data_file}")
                # Fallback to sample domains
                return self._get_sample_domains()

            domains = []
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    website = row.get('website', '').strip()
                    if website and len(domains) < self.config["TEST"]["MAX_DOMAINS"]:
                        domains.append(website)

            print(f"Loaded {len(domains)} domains from Canadian data")
            return domains[:self.config["TEST"]["MAX_DOMAINS"]]

        except Exception as e:
            print(f"Error loading Canadian data: {e}")
            return self._get_sample_domains()

    def _get_sample_domains(self) -> List[str]:
        """Get sample domains for testing if real data unavailable"""

        return [
            "https://www.altitudestrategies.ca",
            "https://www.stryvemarketing.com",
            "http://www.bigfishcreative.ca",
            "http://www.workparty.ca",
            "http://www.theog.co",
            "http://www.involvedmedia.ca",
            "http://www.nimiopere.com",
            "https://example.com",
            "https://google.com",
            "https://github.com"
        ]

    async def _run_site_analysis(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Run site analysis stage"""

        try:
            stage_start = time.time()

            analyzer = SiteAnalyzer()
            results = await analyzer.analyze_sites(domains)

            stage_time = time.time() - stage_start

            # Calculate stage metrics
            successful = len([r for r in results if "error" not in r])
            success_rate = (successful / len(results)) * 100 if results else 0

            self.metrics["performance_data"]["site_analysis"] = {
                "processing_time": stage_time,
                "domains_analyzed": len(results),
                "success_rate": success_rate,
                "successful_analyses": successful,
                "avg_time_per_domain": stage_time / len(results) if results else 0
            }

            print(f"Site Analysis Complete:")
            print(f"  Domains analyzed: {len(results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Processing time: {stage_time:.2f}s")

            # Analyze method recommendations
            method_counts = {}
            for result in results:
                if "error" not in result:
                    method = result.get("recommendation", {}).get("method", "unknown")
                    method_counts[method] = method_counts.get(method, 0) + 1

            print(f"  Method distribution:")
            for method, count in method_counts.items():
                print(f"    {method}: {count} ({count/successful*100:.1f}%)")

            self.stages["site_analysis"]["success_rate"] = success_rate
            return results

        except Exception as e:
            print(f"Site Analysis Stage Failed: {e}")
            self.metrics["errors"].append({"stage": "site_analysis", "error": str(e)})
            return []

    async def _run_website_scraping(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Run website scraping stage"""

        try:
            stage_start = time.time()

            scraper = WebsiteScraper()
            results = await scraper.scrape_websites(domains)

            stage_time = time.time() - stage_start

            # Calculate stage metrics
            successful = len([r for r in results if "error" not in r])
            success_rate = (successful / len(results)) * 100 if results else 0
            total_pages = sum(len(r.get("pages", [])) for r in results)

            self.metrics["performance_data"]["website_scraping"] = {
                "processing_time": stage_time,
                "domains_scraped": len(results),
                "success_rate": success_rate,
                "successful_domains": successful,
                "total_pages_scraped": total_pages,
                "avg_pages_per_domain": total_pages / successful if successful else 0,
                "avg_time_per_domain": stage_time / len(results) if results else 0
            }

            print(f"Website Scraping Complete:")
            print(f"  Domains processed: {len(results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Total pages scraped: {total_pages}")
            print(f"  Avg pages per domain: {total_pages/successful:.1f}" if successful else "N/A")
            print(f"  Processing time: {stage_time:.2f}s")

            # Content quality analysis
            total_content = sum(
                sum(page.get("content_length", 0) for page in r.get("pages", []))
                for r in results if "error" not in r
            )

            print(f"  Total content extracted: {total_content:,} characters")
            print(f"  Avg content per page: {total_content/total_pages:,.0f} chars" if total_pages > 0 else "N/A")

            self.stages["website_scraping"]["success_rate"] = success_rate
            return results

        except Exception as e:
            print(f"Website Scraping Stage Failed: {e}")
            self.metrics["errors"].append({"stage": "website_scraping", "error": str(e)})
            return []

    async def _run_page_prioritization(self) -> List[Dict[str, Any]]:
        """Run page prioritization stage"""

        try:
            stage_start = time.time()

            # Collect all pages from scraping results
            all_pages = []
            scraping_results = self.stages["website_scraping"]["results"]

            for domain_result in scraping_results:
                if "error" not in domain_result:
                    pages = domain_result.get("pages", [])
                    for page in pages:
                        # Add domain context to page
                        page["source_domain"] = domain_result.get("domain", "")
                        all_pages.append(page)

            if not all_pages:
                print("No pages available for prioritization")
                return []

            print(f"Analyzing {len(all_pages)} pages for outreach intelligence...")

            prioritizer = PagePrioritizer()
            results = await prioritizer.analyze_pages(all_pages)

            stage_time = time.time() - stage_start

            # Calculate stage metrics
            successful = len([r for r in results if "error" not in r])
            success_rate = (successful / len(results)) * 100 if results else 0

            # Analyze priority distribution
            priority_distribution = {"high": 0, "medium": 0, "low": 0}
            total_cost = 0.0

            for result in results:
                if "error" not in result:
                    score = result.get("analysis", {}).get("classification", {}).get("score", 0)
                    if score >= 8:
                        priority_distribution["high"] += 1
                    elif score >= 5:
                        priority_distribution["medium"] += 1
                    else:
                        priority_distribution["low"] += 1

                    cost = result.get("processing", {}).get("cost_estimate_usd", 0)
                    total_cost += cost

            self.metrics["performance_data"]["page_prioritization"] = {
                "processing_time": stage_time,
                "pages_analyzed": len(results),
                "success_rate": success_rate,
                "successful_analyses": successful,
                "priority_distribution": priority_distribution,
                "total_cost_usd": total_cost,
                "avg_cost_per_page": total_cost / len(results) if results else 0,
                "avg_time_per_page": stage_time / len(results) if results else 0
            }

            self.metrics["total_cost"] += total_cost

            print(f"Page Prioritization Complete:")
            print(f"  Pages analyzed: {len(results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  High-value pages: {priority_distribution['high']} ({priority_distribution['high']/successful*100:.1f}%)" if successful else "N/A")
            print(f"  Medium-value pages: {priority_distribution['medium']} ({priority_distribution['medium']/successful*100:.1f}%)" if successful else "N/A")
            print(f"  Low-value pages: {priority_distribution['low']} ({priority_distribution['low']/successful*100:.1f}%)" if successful else "N/A")
            print(f"  Total cost: ${total_cost:.4f}")
            print(f"  Processing time: {stage_time:.2f}s")

            self.stages["page_prioritization"]["success_rate"] = success_rate
            return results

        except Exception as e:
            print(f"Page Prioritization Stage Failed: {e}")
            self.metrics["errors"].append({"stage": "page_prioritization", "error": str(e)})
            return []

    async def _run_apify_scraping(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Run Apify scraping stage"""

        try:
            stage_start = time.time()

            # Filter domains that need Apify based on site analysis
            site_analysis = self.stages["site_analysis"]["results"]

            scraper = ApifyScraper()
            results = await scraper.scrape_domains(domains, site_analysis)

            stage_time = time.time() - stage_start

            # Calculate stage metrics
            successful = len([r for r in results if "error" not in r])
            success_rate = (successful / len(results)) * 100 if results else 0
            total_pages = sum(len(r.get("pages", [])) for r in results if "error" not in r)
            total_cost = sum(r.get("cost_estimate_usd", 0) for r in results)

            self.metrics["performance_data"]["apify_scraping"] = {
                "processing_time": stage_time,
                "domains_processed": len(results),
                "success_rate": success_rate,
                "successful_domains": successful,
                "total_pages_scraped": total_pages,
                "total_cost_usd": total_cost,
                "avg_cost_per_domain": total_cost / len(results) if results else 0,
                "avg_time_per_domain": stage_time / len(results) if results else 0
            }

            self.metrics["total_cost"] += total_cost

            print(f"Apify Scraping Complete:")
            print(f"  Domains processed: {len(results)}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Total pages scraped: {total_pages}")
            print(f"  Total cost: ${total_cost:.4f}")
            print(f"  Processing time: {stage_time:.2f}s")

            self.stages["apify_scraping"]["success_rate"] = success_rate
            return results

        except Exception as e:
            print(f"Apify Scraping Stage Failed: {e}")
            self.metrics["errors"].append({"stage": "apify_scraping", "error": str(e)})
            return []

    async def _analyze_pipeline_results(self) -> Dict[str, Any]:
        """Analyze complete pipeline results"""

        analysis = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "script_version": SCRIPT_STATS["version"],
                "test_duration": self.metrics["total_processing_time"],
                "domains_tested": self.metrics["domains_processed"],
                "total_cost_usd": self.metrics["total_cost"]
            },
            "pipeline_performance": {},
            "success_metrics": {},
            "cost_analysis": {},
            "quality_assessment": {},
            "recommendations": [],
            "stage_results": self.stages
        }

        # Performance analysis
        total_time = self.metrics["total_processing_time"]
        target_time = self.config["TARGETS"]["MAX_PROCESSING_TIME"]

        analysis["pipeline_performance"] = {
            "total_processing_time": total_time,
            "target_processing_time": target_time,
            "performance_rating": "excellent" if total_time < target_time * 0.8 else "good" if total_time < target_time else "needs_improvement",
            "domains_per_minute": (self.metrics["domains_processed"] / total_time) * 60 if total_time > 0 else 0,
            "stage_breakdown": self.metrics["performance_data"]
        }

        # Success rate analysis
        overall_success_rates = {}
        for stage_name, stage_data in self.stages.items():
            if stage_data["enabled"] and "success_rate" in stage_data:
                overall_success_rates[stage_name] = stage_data["success_rate"]

        analysis["success_metrics"] = {
            "stage_success_rates": overall_success_rates,
            "overall_success_rate": sum(overall_success_rates.values()) / len(overall_success_rates) if overall_success_rates else 0,
            "target_success_rate": self.config["TARGETS"]["MIN_SUCCESS_RATE"],
            "meets_target": all(rate >= self.config["TARGETS"]["MIN_SUCCESS_RATE"] for rate in overall_success_rates.values())
        }

        # Cost analysis
        cost_per_domain = self.metrics["total_cost"] / self.metrics["domains_processed"] if self.metrics["domains_processed"] > 0 else 0
        target_cost = self.config["TARGETS"]["MAX_COST_USD"]

        analysis["cost_analysis"] = {
            "total_cost_usd": self.metrics["total_cost"],
            "cost_per_domain": cost_per_domain,
            "target_total_cost": target_cost,
            "target_cost_per_domain": self.config["TARGETS"]["MAX_COST_PER_DOMAIN"],
            "cost_efficiency": "excellent" if self.metrics["total_cost"] < target_cost * 0.8 else "good" if self.metrics["total_cost"] < target_cost else "over_budget",
            "cost_breakdown": {
                stage: data.get("total_cost_usd", 0)
                for stage, data in self.metrics["performance_data"].items()
            }
        }

        # Quality assessment
        quality_metrics = self._assess_content_quality()
        analysis["quality_assessment"] = quality_metrics

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)
        analysis["recommendations"] = recommendations

        return analysis

    def _assess_content_quality(self) -> Dict[str, Any]:
        """Assess overall content quality from scraping results"""

        quality_metrics = {
            "total_pages_scraped": 0,
            "total_content_characters": 0,
            "avg_content_per_page": 0,
            "high_value_pages_found": 0,
            "page_type_distribution": {},
            "content_quality_rating": "unknown"
        }

        # Analyze website scraping results
        scraping_results = self.stages["website_scraping"]["results"]
        total_pages = 0
        total_content = 0

        for result in scraping_results:
            if "error" not in result:
                pages = result.get("pages", [])
                total_pages += len(pages)

                for page in pages:
                    content_length = page.get("content_length", 0)
                    total_content += content_length

                    # Track page types
                    page_type = page.get("page_type", "unknown")
                    quality_metrics["page_type_distribution"][page_type] = quality_metrics["page_type_distribution"].get(page_type, 0) + 1

        # Analyze prioritization results
        prioritization_results = self.stages["page_prioritization"]["results"]
        high_value_count = 0

        for result in prioritization_results:
            if "error" not in result:
                score = result.get("analysis", {}).get("classification", {}).get("score", 0)
                if score >= 8:
                    high_value_count += 1

        quality_metrics.update({
            "total_pages_scraped": total_pages,
            "total_content_characters": total_content,
            "avg_content_per_page": total_content / total_pages if total_pages > 0 else 0,
            "high_value_pages_found": high_value_count
        })

        # Determine quality rating
        if (quality_metrics["avg_content_per_page"] >= 2000 and
            quality_metrics["high_value_pages_found"] >= self.config["VALIDATION"]["MIN_HIGH_VALUE_PAGES"]):
            quality_metrics["content_quality_rating"] = "excellent"
        elif quality_metrics["avg_content_per_page"] >= 1000:
            quality_metrics["content_quality_rating"] = "good"
        else:
            quality_metrics["content_quality_rating"] = "needs_improvement"

        return quality_metrics

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on test results"""

        recommendations = []

        # Performance recommendations
        performance = analysis["pipeline_performance"]
        if performance["performance_rating"] == "needs_improvement":
            recommendations.append({
                "category": "performance",
                "priority": "high",
                "issue": f"Processing time {performance['total_processing_time']:.1f}s exceeds target {performance['target_processing_time']}s",
                "recommendation": "Increase concurrent requests or optimize scraping parameters",
                "expected_improvement": "20-40% faster processing"
            })

        # Success rate recommendations
        success_metrics = analysis["success_metrics"]
        for stage, rate in success_metrics["stage_success_rates"].items():
            if rate < self.config["TARGETS"]["MIN_SUCCESS_RATE"]:
                recommendations.append({
                    "category": "reliability",
                    "priority": "high",
                    "issue": f"{stage} success rate {rate:.1f}% below target {self.config['TARGETS']['MIN_SUCCESS_RATE']}%",
                    "recommendation": f"Improve error handling and retry logic for {stage}",
                    "expected_improvement": f"Increase {stage} success rate to 85%+"
                })

        # Cost recommendations
        cost_analysis = analysis["cost_analysis"]
        if cost_analysis["cost_efficiency"] == "over_budget":
            recommendations.append({
                "category": "cost",
                "priority": "medium",
                "issue": f"Total cost ${cost_analysis['total_cost_usd']:.3f} exceeds target ${cost_analysis['target_total_cost']:.2f}",
                "recommendation": "Optimize Apify usage and reduce page limits for initial discovery",
                "expected_improvement": "30-50% cost reduction"
            })

        # Quality recommendations
        quality = analysis["quality_assessment"]
        if quality["content_quality_rating"] == "needs_improvement":
            recommendations.append({
                "category": "quality",
                "priority": "medium",
                "issue": f"Average content per page {quality['avg_content_per_page']:.0f} chars is low",
                "recommendation": "Improve content extraction filters and target higher-quality pages",
                "expected_improvement": "2x increase in actionable content"
            })

        if not recommendations:
            recommendations.append({
                "category": "success",
                "priority": "info",
                "issue": "All metrics meet or exceed targets",
                "recommendation": "Current configuration is optimal for production use",
                "expected_improvement": "Ready for scaling to 1000+ domains"
            })

        return recommendations

    async def _save_comprehensive_results(self, analysis: Dict[str, Any]):
        """Save comprehensive test results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main analysis report
        if self.config["OUTPUT"]["SAVE_COMPREHENSIVE_REPORT"]:
            report_filename = f"scraping_test_report_{timestamp}.json"
            report_filepath = self.results_dir / report_filename

            with open(report_filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)

            print(f"Comprehensive report saved: {report_filename}")

        # Save CSV summary
        if self.config["OUTPUT"]["CREATE_SUMMARY_CSV"]:
            csv_filename = f"test_summary_{timestamp}.csv"
            csv_filepath = self.results_dir / csv_filename

            with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Stage', 'Enabled', 'Success_Rate', 'Processing_Time',
                    'Items_Processed', 'Cost_USD', 'Rating'
                ])

                for stage_name, stage_data in self.stages.items():
                    if stage_name in self.metrics["performance_data"]:
                        perf_data = self.metrics["performance_data"][stage_name]
                        writer.writerow([
                            stage_name,
                            'Yes' if stage_data["enabled"] else 'No',
                            f"{stage_data.get('success_rate', 0):.1f}%",
                            f"{perf_data.get('processing_time', 0):.2f}s",
                            perf_data.get('domains_processed', perf_data.get('domains_analyzed', perf_data.get('pages_analyzed', 0))),
                            f"{perf_data.get('total_cost_usd', 0):.4f}",
                            "✓" if stage_data.get('success_rate', 0) >= self.config['TARGETS']['MIN_SUCCESS_RATE'] else "✗"
                        ])

            print(f"CSV summary saved: {csv_filename}")

        # Update global statistics
        global SCRIPT_STATS
        SCRIPT_STATS["total_test_runs"] += 1
        SCRIPT_STATS["last_test_run"] = datetime.now().isoformat()

        # Update best performance if this run was better
        overall_success = analysis["success_metrics"]["overall_success_rate"]
        processing_time = analysis["test_metadata"]["test_duration"]
        cost_efficiency = analysis["cost_analysis"]["cost_per_domain"]

        if (overall_success >= SCRIPT_STATS["best_performance"]["success_rate"] and
            processing_time < SCRIPT_STATS["best_performance"]["processing_time"]):
            SCRIPT_STATS["best_performance"] = {
                "processing_time": processing_time,
                "success_rate": overall_success,
                "cost_efficiency": cost_efficiency
            }

    def _print_comprehensive_summary(self, analysis: Dict[str, Any]):
        """Print comprehensive test summary"""

        print("\n" + "=" * 80)
        print("COMPREHENSIVE SCRAPING TEST RESULTS")
        print("=" * 80)

        # Overall metrics
        metadata = analysis["test_metadata"]
        performance = analysis["pipeline_performance"]
        success_metrics = analysis["success_metrics"]
        cost_analysis = analysis["cost_analysis"]

        print(f"Test Duration: {metadata['test_duration']:.2f}s ({metadata['test_duration']/60:.1f} minutes)")
        print(f"Domains Tested: {metadata['domains_tested']}")
        print(f"Total Cost: ${metadata['total_cost_usd']:.4f}")

        # Performance summary
        print(f"\nPERFORMANCE SUMMARY:")
        print(f"  Overall Rating: {performance['performance_rating'].title()}")
        print(f"  Processing Speed: {performance['domains_per_minute']:.1f} domains/minute")
        print(f"  Target Speed: {self.config['TARGETS']['MAX_DOMAINS']/self.config['TARGETS']['MAX_PROCESSING_TIME']*60:.1f} domains/minute")

        # Success rates
        print(f"\nSUCCESS RATES:")
        for stage, rate in success_metrics["stage_success_rates"].items():
            status = "✓" if rate >= self.config["TARGETS"]["MIN_SUCCESS_RATE"] else "✗"
            print(f"  {stage.replace('_', ' ').title()}: {rate:.1f}% {status}")

        overall_rate = success_metrics["overall_success_rate"]
        overall_status = "✓" if overall_rate >= self.config["TARGETS"]["MIN_SUCCESS_RATE"] else "✗"
        print(f"  Overall Success Rate: {overall_rate:.1f}% {overall_status}")

        # Cost breakdown
        print(f"\nCOST ANALYSIS:")
        print(f"  Total Cost: ${cost_analysis['total_cost_usd']:.4f}")
        print(f"  Cost per Domain: ${cost_analysis['cost_per_domain']:.4f}")
        print(f"  Target Cost: ${cost_analysis['target_total_cost']:.2f}")
        print(f"  Cost Efficiency: {cost_analysis['cost_efficiency'].title()}")

        # Quality assessment
        quality = analysis["quality_assessment"]
        print(f"\nCONTENT QUALITY:")
        print(f"  Pages Scraped: {quality['total_pages_scraped']:,}")
        print(f"  Content Extracted: {quality['total_content_characters']:,} characters")
        print(f"  Avg Content/Page: {quality['avg_content_per_page']:,.0f} characters")
        print(f"  High-Value Pages: {quality['high_value_pages_found']}")
        print(f"  Quality Rating: {quality['content_quality_rating'].title()}")

        # Recommendations
        recommendations = analysis["recommendations"]
        if recommendations:
            print(f"\nRECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                print(f"  {i}. [{rec['priority'].upper()}] {rec['recommendation']}")

        # Overall assessment
        print(f"\n{'='*80}")
        if (success_metrics["overall_success_rate"] >= self.config["TARGETS"]["MIN_SUCCESS_RATE"] and
            cost_analysis["cost_efficiency"] in ["excellent", "good"] and
            performance["performance_rating"] in ["excellent", "good"]):
            print("✅ SCRAPING MODULE READY FOR PRODUCTION")
            print("   All targets met - ready for scaling to 1000+ domains")
        else:
            print("⚠️  SCRAPING MODULE NEEDS OPTIMIZATION")
            print("   Review recommendations before production deployment")

        print("=" * 80)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""

    print("Starting Comprehensive Scraping Module Test...")

    runner = ScrapingTestRunner()
    results = await runner.run_comprehensive_test()

    if "error" not in results:
        print("\n🎉 Test completed successfully!")
        print("Review the comprehensive report for detailed insights.")
    else:
        print(f"\n❌ Test failed: {results['error']}")

    return results

if __name__ == "__main__":
    asyncio.run(main())