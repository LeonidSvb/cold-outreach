#!/usr/bin/env python3
"""
=== APIFY SCRAPER ===
Version: 2.0.0 | Created: 2025-09-25

PURPOSE:
Apify RAG Web Browser integration for JavaScript-heavy websites and bot-protected sites.
Provides fallback scraping capability when HTTP methods fail or return low-quality content.

FEATURES:
- Apify RAG Web Browser actor integration
- Automatic fallback for HTTP scraping failures
- Cost optimization with $0.002 per domain targeting
- Quality content extraction from JavaScript-rendered sites
- Smart routing based on site analysis recommendations
- Batch processing for cost efficiency
- Comprehensive error handling and retry logic

USAGE:
1. Configure Apify API key in .env file (APIFY_API_TOKEN)
2. Set target domains and processing parameters in CONFIG
3. Run: python apify_scraper.py
4. Results saved with cost tracking and quality metrics

IMPROVEMENTS:
v2.0.0 - Initial implementation with RAG Web Browser integration
"""

import asyncio
import aiohttp
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path
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
    # APIFY API SETTINGS
    "APIFY": {
        "ACTOR_ID": "apify/rag-web-browser",
        "DEFAULT_ACTOR": "apify/web-scraper",
        "API_BASE_URL": "https://api.apify.com/v2",
        "TIMEOUT_SECONDS": 120,
        "MAX_RETRIES": 3,
        "WAIT_FOR_COMPLETION": True
    },

    # SCRAPING CONFIGURATION
    "SCRAPING": {
        "MAX_PAGES_PER_DOMAIN": 5,
        "MAX_CRAWL_DEPTH": 2,
        "PAGE_TIMEOUT": 30,
        "EXTRACT_TEXT": True,
        "EXTRACT_LINKS": True,
        "FOLLOW_LINKS": True,
        "SMART_RETRY": True
    },

    # COST MANAGEMENT
    "COSTS": {
        "TARGET_COST_PER_DOMAIN": 0.002,
        "MAX_COST_PER_RUN": 5.0,
        "MAX_DAILY_COST": 20.0,
        "COST_ALERT_THRESHOLD": 1.0
    },

    # ROUTING LOGIC
    "ROUTING": {
        "AUTO_FALLBACK": True,
        "HTTP_FAILURE_THRESHOLD": 3,
        "APIFY_PREFERRED_PATTERNS": [
            "react", "angular", "vue", "spa", "javascript",
            "cloudflare", "bot protection", "captcha"
        ],
        "CONFIDENCE_THRESHOLD": 0.3
    },

    # BATCH PROCESSING
    "PROCESSING": {
        "BATCH_SIZE": 10,
        "CONCURRENT_ACTORS": 3,
        "DELAY_BETWEEN_BATCHES": 2.0,
        "ENABLE_PARALLEL_PROCESSING": True
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "SAVE_DETAILED_LOGS": True,
        "RESULTS_DIR": "../results",
        "INCLUDE_RAW_DATA": False,
        "COMPRESS_RESULTS": False
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_runs": 0,
    "total_domains_processed": 0,
    "total_apify_runs": 0,
    "total_cost_usd": 0.0,
    "success_rate": 0.0,
    "avg_pages_per_domain": 0.0,
    "avg_cost_per_domain": 0.0,
    "last_run": None
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class ApifyScraper:
    """Apify integration for JavaScript-heavy website scraping"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.apify_token = self._load_apify_token()
        self.session = None
        self.stats = {
            "start_time": time.time(),
            "domains_processed": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "total_pages_extracted": 0,
            "total_cost": 0.0,
            "apify_runs_created": 0
        }

    def _load_apify_token(self) -> str:
        """Load Apify API token from environment"""

        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        if not env_path.exists():
            raise FileNotFoundError("No .env file found. Please create one with APIFY_API_KEY.")

        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('APIFY_API_KEY='):
                    return line.split('=', 1)[1].strip()

        raise ValueError("APIFY_API_KEY not found in .env file")

    @auto_log("apify_scraper")
    async def scrape_domains(self, domains: List[str], site_analysis: Optional[List[Dict]] = None) -> List[Dict[str, Any]]:
        """Main function to scrape domains using Apify"""

        print(f"Starting Apify Scraper v{SCRIPT_STATS['version']}")
        print(f"Target domains: {len(domains):,}")
        print(f"Apify Actor: {self.config['APIFY']['ACTOR_ID']}")
        print(f"Max cost per domain: ${self.config['COSTS']['TARGET_COST_PER_DOMAIN']}")
        print("=" * 60)

        start_time = time.time()

        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=self.config["APIFY"]["TIMEOUT_SECONDS"])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session

            # Filter domains that should use Apify
            apify_domains = self._filter_domains_for_apify(domains, site_analysis)
            print(f"Domains requiring Apify: {len(apify_domains):,}")

            if not apify_domains:
                print("No domains require Apify processing.")
                return []

            # Process domains in batches
            results = await self._process_domains_in_batches(apify_domains)

        # Calculate final statistics
        processing_time = time.time() - start_time
        await self._calculate_final_stats(results, processing_time)

        # Save results
        await self._save_results(results, processing_time)

        # Print summary
        self._print_summary(results, processing_time)

        return results

    def _filter_domains_for_apify(self, domains: List[str], site_analysis: Optional[List[Dict]] = None) -> List[str]:
        """Filter domains that should be processed by Apify"""

        if not site_analysis:
            # If no analysis provided, process all domains
            return domains

        apify_domains = []
        analysis_dict = {item.get("url", ""): item for item in site_analysis}

        for domain in domains:
            # Normalize domain for comparison
            normalized_domain = domain if domain.startswith(('http://', 'https://')) else f'https://{domain}'

            analysis = analysis_dict.get(normalized_domain)
            if not analysis:
                # No analysis available, include by default
                apify_domains.append(domain)
                continue

            recommendation = analysis.get("recommendation", {})
            method = recommendation.get("method", "")
            confidence = recommendation.get("confidence", 0)

            # Include if recommended for Apify or low confidence in HTTP
            if method == "APIFY_REQUIRED" or (method == "HTTP_SUITABLE" and confidence < self.config["ROUTING"]["CONFIDENCE_THRESHOLD"]):
                apify_domains.append(domain)

        return apify_domains

    async def _process_domains_in_batches(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Process domains in optimized batches"""

        batch_size = self.config["PROCESSING"]["BATCH_SIZE"]
        all_results = []

        print(f"Processing {len(domains)} domains in batches of {batch_size}...")

        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(domains) + batch_size - 1) // batch_size

            print(f"\nBatch {batch_number}/{total_batches}: Processing {len(batch)} domains")

            # Check cost limits before processing
            if self.stats["total_cost"] >= self.config["COSTS"]["MAX_COST_PER_RUN"]:
                print(f"Cost limit reached: ${self.stats['total_cost']:.3f}")
                break

            # Process batch
            batch_results = await self._process_single_batch(batch)
            all_results.extend([r for r in batch_results if r is not None])

            # Progress update
            completed = min(i + batch_size, len(domains))
            progress = (completed / len(domains)) * 100
            print(f"Overall progress: {progress:.1f}% ({completed}/{len(domains)} domains)")
            print(f"Current cost: ${self.stats['total_cost']:.3f}")

            # Delay between batches
            if i + batch_size < len(domains):
                await asyncio.sleep(self.config["PROCESSING"]["DELAY_BETWEEN_BATCHES"])

        return all_results

    async def _process_single_batch(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of domains"""

        if self.config["PROCESSING"]["ENABLE_PARALLEL_PROCESSING"] and len(domains) > 1:
            # Parallel processing with controlled concurrency
            semaphore = asyncio.Semaphore(self.config["PROCESSING"]["CONCURRENT_ACTORS"])

            async def scrape_with_semaphore(domain):
                async with semaphore:
                    return await self._scrape_single_domain(domain)

            tasks = [scrape_with_semaphore(domain) for domain in domains]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Sequential processing
            results = []
            for domain in domains:
                result = await self._scrape_single_domain(domain)
                results.append(result)
                # Small delay between sequential runs
                await asyncio.sleep(1.0)
            return results

    async def _scrape_single_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Scrape a single domain using Apify"""

        try:
            # Normalize domain
            if not domain.startswith(('http://', 'https://')):
                domain = 'https://' + domain

            print(f"  Starting Apify run for: {domain}")

            # Prepare Apify run input
            run_input = self._prepare_apify_input(domain)

            # Create Apify run
            run_data = await self._create_apify_run(run_input)
            if not run_data:
                return self._create_error_result(domain, "Failed to create Apify run")

            run_id = run_data.get("id")
            print(f"  Apify run created: {run_id}")

            # Wait for completion if configured
            if self.config["APIFY"]["WAIT_FOR_COMPLETION"]:
                final_run_data = await self._wait_for_run_completion(run_id)
                if not final_run_data:
                    return self._create_error_result(domain, "Run failed or timed out")

                # Get run results
                results = await self._get_run_results(run_id)
                if not results:
                    return self._create_error_result(domain, "No results retrieved")

                # Process and format results
                formatted_result = self._format_apify_results(domain, results, final_run_data)

                # Update statistics
                self.stats["domains_processed"] += 1
                self.stats["successful_runs"] += 1
                self.stats["apify_runs_created"] += 1

                # Estimate cost
                cost_estimate = self.config["COSTS"]["TARGET_COST_PER_DOMAIN"]
                self.stats["total_cost"] += cost_estimate
                formatted_result["cost_estimate_usd"] = cost_estimate

                return formatted_result
            else:
                # Return run info without waiting
                return {
                    "domain": domain,
                    "apify_run_id": run_id,
                    "status": "started",
                    "message": "Run started, not waiting for completion",
                    "scraped_at": datetime.now().isoformat()
                }

        except Exception as e:
            print(f"  Error scraping {domain}: {e}")
            self.stats["failed_runs"] += 1
            return self._create_error_result(domain, str(e))

    def _prepare_apify_input(self, domain: str) -> Dict[str, Any]:
        """Prepare input configuration for Apify actor"""

        return {
            "startUrls": [{"url": domain}],
            "maxCrawlPages": self.config["SCRAPING"]["MAX_PAGES_PER_DOMAIN"],
            "maxCrawlDepth": self.config["SCRAPING"]["MAX_CRAWL_DEPTH"],
            "pageTimeoutSecs": self.config["SCRAPING"]["PAGE_TIMEOUT"],
            "extractText": self.config["SCRAPING"]["EXTRACT_TEXT"],
            "extractLinks": self.config["SCRAPING"]["EXTRACT_LINKS"],
            "followLinks": self.config["SCRAPING"]["FOLLOW_LINKS"],
            "waitForSelector": "body",
            "maxResults": self.config["SCRAPING"]["MAX_PAGES_PER_DOMAIN"] * 2,
            "outputFormat": "json"
        }

    async def _create_apify_run(self, run_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new Apify run"""

        url = f"{self.config['APIFY']['API_BASE_URL']}/acts/{self.config['APIFY']['ACTOR_ID']}/runs"
        headers = {
            "Authorization": f"Bearer {self.apify_token}",
            "Content-Type": "application/json"
        }

        try:
            async with self.session.post(url, json=run_input, headers=headers) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    print(f"  Failed to create run: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"  Error creating Apify run: {e}")
            return None

    async def _wait_for_run_completion(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Wait for Apify run to complete"""

        url = f"{self.config['APIFY']['API_BASE_URL']}/actor-runs/{run_id}"
        headers = {"Authorization": f"Bearer {self.apify_token}"}

        max_wait_time = self.config["APIFY"]["TIMEOUT_SECONDS"]
        check_interval = 5  # Check every 5 seconds
        waited_time = 0

        while waited_time < max_wait_time:
            try:
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        run_data = await response.json()
                        status = run_data.get("status")

                        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                            print(f"  Run completed with status: {status}")
                            return run_data

                        # Still running, wait more
                        await asyncio.sleep(check_interval)
                        waited_time += check_interval
                    else:
                        print(f"  Error checking run status: HTTP {response.status}")
                        break
            except Exception as e:
                print(f"  Error waiting for run: {e}")
                break

        print(f"  Run timeout after {waited_time}s")
        return None

    async def _get_run_results(self, run_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get results from completed Apify run"""

        url = f"{self.config['APIFY']['API_BASE_URL']}/actor-runs/{run_id}/dataset/items"
        headers = {"Authorization": f"Bearer {self.apify_token}"}

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    results = await response.json()
                    print(f"  Retrieved {len(results)} result items")
                    return results
                else:
                    print(f"  Failed to get results: HTTP {response.status}")
                    return None
        except Exception as e:
            print(f"  Error getting run results: {e}")
            return None

    def _format_apify_results(self, domain: str, results: List[Dict[str, Any]], run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Apify results into standardized structure"""

        pages = []
        total_content_length = 0

        for item in results:
            page_data = {
                "url": item.get("url", ""),
                "title": item.get("title", ""),
                "content": item.get("text", "") or item.get("content", ""),
                "content_length": len(item.get("text", "") or item.get("content", "")),
                "scraped_at": datetime.now().isoformat(),
                "scraping_method": "apify"
            }

            # Add metadata if available
            if "metadata" in item:
                page_data["metadata"] = item["metadata"]

            pages.append(page_data)
            total_content_length += page_data["content_length"]

        # Update global page count
        self.stats["total_pages_extracted"] += len(pages)

        return {
            "domain": domain,
            "scraped_at": datetime.now().isoformat(),
            "apify_run_id": run_data.get("id"),
            "apify_status": run_data.get("status"),
            "pages": pages,
            "summary": {
                "total_pages": len(pages),
                "total_content_length": total_content_length,
                "avg_content_per_page": total_content_length / len(pages) if pages else 0,
                "scraping_duration": run_data.get("stats", {}).get("runTimeSecs", 0),
                "data_transfer": run_data.get("stats", {}).get("dataSizeBytes", 0)
            },
            "apify_stats": run_data.get("stats", {}),
            "scraping_method": "apify"
        }

    def _create_error_result(self, domain: str, error_message: str) -> Dict[str, Any]:
        """Create error result structure"""

        return {
            "domain": domain,
            "error": error_message,
            "scraped_at": datetime.now().isoformat(),
            "pages": [],
            "scraping_method": "apify",
            "cost_estimate_usd": 0.0
        }

    async def _calculate_final_stats(self, results: List[Dict[str, Any]], processing_time: float):
        """Calculate final statistics"""

        successful_results = [r for r in results if "error" not in r]
        total_domains = len(results)

        # Update global script stats
        global SCRIPT_STATS
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["total_domains_processed"] += total_domains
        SCRIPT_STATS["total_apify_runs"] += self.stats["apify_runs_created"]
        SCRIPT_STATS["total_cost_usd"] += self.stats["total_cost"]
        SCRIPT_STATS["success_rate"] = (len(successful_results) / total_domains * 100) if total_domains > 0 else 0

        if successful_results:
            total_pages = sum(len(r.get("pages", [])) for r in successful_results)
            SCRIPT_STATS["avg_pages_per_domain"] = total_pages / len(successful_results)
            SCRIPT_STATS["avg_cost_per_domain"] = self.stats["total_cost"] / len(successful_results)

        SCRIPT_STATS["last_run"] = datetime.now().isoformat()

    async def _save_results(self, results: List[Dict[str, Any]], processing_time: float):
        """Save scraping results with comprehensive metadata"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Prepare results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "script_version": SCRIPT_STATS["version"],
                "processing_summary": {
                    "total_domains": len(results),
                    "successful_domains": len([r for r in results if "error" not in r]),
                    "failed_domains": len([r for r in results if "error" in r]),
                    "total_apify_runs": self.stats["apify_runs_created"],
                    "total_pages_extracted": self.stats["total_pages_extracted"],
                    "total_processing_time": processing_time,
                    "avg_time_per_domain": processing_time / len(results) if results else 0
                },
                "cost_analysis": {
                    "total_cost_usd": self.stats["total_cost"],
                    "avg_cost_per_domain": self.stats["total_cost"] / len(results) if results else 0,
                    "target_cost_per_domain": self.config["COSTS"]["TARGET_COST_PER_DOMAIN"],
                    "cost_efficiency": "within_target" if (self.stats["total_cost"] / max(1, len(results))) <= self.config["COSTS"]["TARGET_COST_PER_DOMAIN"] else "over_target"
                },
                "configuration": self.config,
                "apify_settings": {
                    "actor_id": self.config["APIFY"]["ACTOR_ID"],
                    "max_pages_per_domain": self.config["SCRAPING"]["MAX_PAGES_PER_DOMAIN"],
                    "timeout_seconds": self.config["APIFY"]["TIMEOUT_SECONDS"]
                }
            },
            "results": results
        }

        # Save JSON results
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"apify_scraping_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"Apify results saved: {json_filename}")

        # Save detailed logs if enabled
        if self.config["OUTPUT"]["SAVE_DETAILED_LOGS"]:
            log_filename = f"apify_detailed_log_{timestamp}.txt"
            log_filepath = self.results_dir / log_filename

            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Apify Scraping Session - {timestamp}\n")
                f.write("=" * 50 + "\n\n")

                for result in results:
                    domain = result.get("domain", "Unknown")
                    status = "SUCCESS" if "error" not in result else "FAILED"
                    pages_count = len(result.get("pages", []))

                    f.write(f"Domain: {domain}\n")
                    f.write(f"Status: {status}\n")
                    f.write(f"Pages: {pages_count}\n")

                    if "error" in result:
                        f.write(f"Error: {result['error']}\n")
                    else:
                        f.write(f"Apify Run ID: {result.get('apify_run_id', 'N/A')}\n")
                        f.write(f"Cost: ${result.get('cost_estimate_usd', 0):.4f}\n")

                    f.write("-" * 30 + "\n\n")

            print(f"Detailed log saved: {log_filename}")

    def _print_summary(self, results: List[Dict[str, Any]], processing_time: float):
        """Print comprehensive scraping summary"""

        print("\n" + "=" * 60)
        print("APIFY SCRAPING SUMMARY")
        print("=" * 60)

        successful_results = [r for r in results if "error" not in r]
        failed_results = [r for r in results if "error" in r]
        total_pages = sum(len(r.get("pages", [])) for r in successful_results)

        print(f"Domains processed: {len(results):,}")
        print(f"Successful: {len(successful_results):,} ({len(successful_results)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed_results):,} ({len(failed_results)/len(results)*100:.1f}%)")
        print(f"Total pages extracted: {total_pages:,}")
        print(f"Avg pages per domain: {total_pages/len(successful_results):.1f}" if successful_results else "N/A")

        # Apify-specific metrics
        print(f"\nAPIFY METRICS:")
        print(f"Total Apify runs created: {self.stats['apify_runs_created']:,}")
        print(f"Successful runs: {self.stats['successful_runs']:,}")
        print(f"Failed runs: {self.stats['failed_runs']:,}")

        # Cost analysis
        print(f"\nCOST ANALYSIS:")
        print(f"Total cost: ${self.stats['total_cost']:.4f}")
        print(f"Cost per domain: ${self.stats['total_cost']/len(results):.4f}" if results else "N/A")
        print(f"Target cost per domain: ${self.config['COSTS']['TARGET_COST_PER_DOMAIN']:.4f}")
        print(f"Cost efficiency: {'✓ Within target' if (self.stats['total_cost']/max(1, len(results))) <= self.config['COSTS']['TARGET_COST_PER_DOMAIN'] else '✗ Over target'}")

        # Performance metrics
        print(f"\nPERFORMANCE:")
        print(f"Total processing time: {processing_time:.2f}s")
        print(f"Average time per domain: {processing_time/len(results):.2f}s" if results else "N/A")

        # Content statistics
        if successful_results:
            total_chars = sum(
                sum(page.get("content_length", 0) for page in result.get("pages", []))
                for result in successful_results
            )
            print(f"\nCONTENT STATISTICS:")
            print(f"Total content extracted: {total_chars:,} characters")
            print(f"Average content per page: {total_chars/total_pages:,.0f} chars" if total_pages > 0 else "N/A")

        # Error summary
        if failed_results:
            print(f"\nERRORS: {len(failed_results)} domains failed")
            for i, error_result in enumerate(failed_results[:3]):  # Show first 3 errors
                print(f"  {i+1}. {error_result['domain']}: {error_result['error']}")
            if len(failed_results) > 3:
                print(f"  ... and {len(failed_results) - 3} more errors")

        print("=" * 60)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function for testing"""

    print("=" * 60)
    print(f"APIFY SCRAPER v{SCRIPT_STATS['version']}")
    print("=" * 60)

    # Sample domains for testing (JavaScript-heavy sites)
    test_domains = [
        "https://react-app-example.com",
        "https://angular-demo.com",
        "https://vue-showcase.com"
    ]

    # Sample site analysis (domains requiring Apify)
    sample_analysis = [
        {
            "url": "https://react-app-example.com",
            "recommendation": {
                "method": "APIFY_REQUIRED",
                "confidence": 0.9
            }
        }
    ]

    scraper = ApifyScraper()
    results = await scraper.scrape_domains(test_domains, sample_analysis)

    print(f"\nApify scraping completed: {len(results)} results generated")

    return results

if __name__ == "__main__":
    asyncio.run(main())