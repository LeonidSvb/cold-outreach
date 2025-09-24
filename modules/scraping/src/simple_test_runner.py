#!/usr/bin/env python3
"""
=== SIMPLE TEST RUNNER ===
Version: 1.0.0 | Created: 2025-09-25

PURPOSE:
Simplified test runner for 100 Canadian domains - focuses on working components only

FEATURES:
- Site analysis (HTTP vs JavaScript detection)
- Website scraping (text-only content extraction)
- Real Canadian company data testing
- Performance metrics and validation
"""

import asyncio
import json
import time
import os
import csv
import sys
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# Import working modules
from site_analyzer import SiteAnalyzer
from website_scraper import WebsiteScraper

class SimpleTestRunner:
    """Simplified test runner focusing on working components"""

    def __init__(self):
        self.results_dir = Path(__file__).parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.stats = {"start_time": 0, "domains_tested": 0}

    @auto_log("simple_test_runner")
    async def run_simple_test(self, max_domains: int = 100):
        """Run simplified test on Canadian domains"""

        print("=" * 80)
        print(f"SIMPLIFIED SCRAPING TEST - {max_domains} DOMAINS")
        print("=" * 80)

        self.stats["start_time"] = time.time()

        try:
            # Load Canadian domains
            domains = await self._load_canadian_domains(max_domains)
            self.stats["domains_tested"] = len(domains)
            print(f"Loaded {len(domains)} Canadian domains")

            # Stage 1: Site Analysis
            print(f"\n{'='*50}")
            print("STAGE 1: SITE ANALYSIS")
            print(f"{'='*50}")
            analyzer = SiteAnalyzer()
            site_results = await analyzer.analyze_sites(domains)

            # Stage 2: Website Scraping
            print(f"\n{'='*50}")
            print("STAGE 2: WEBSITE SCRAPING")
            print(f"{'='*50}")
            scraper = WebsiteScraper()
            scrape_results = await scraper.scrape_websites(domains)

            # Save combined results
            await self._save_combined_results(site_results, scrape_results)

            # Print final summary
            self._print_final_summary(site_results, scrape_results)

            return {"site_results": site_results, "scrape_results": scrape_results}

        except Exception as e:
            print(f"Test failed: {e}")
            return {"error": str(e)}

    async def _load_canadian_domains(self, max_domains: int):
        """Load Canadian domains from CSV"""

        data_file = Path(__file__).parent.parent / "../../data/master-leads/test_clean_canadian.csv"

        if not data_file.exists():
            print(f"Canadian data file not found at {data_file}")
            # Return sample domains
            return [
                "https://www.altitudestrategies.ca",
                "https://www.stryvemarketing.com",
                "http://www.bigfishcreative.ca",
                "http://www.workparty.ca",
                "http://www.theog.co",
                "http://www.involvedmedia.ca",
                "http://www.nimiopere.com"
            ]

        domains = []
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    website = row.get('website', '').strip()
                    if website and len(domains) < max_domains:
                        domains.append(website)

            return domains[:max_domains]

        except Exception as e:
            print(f"Error loading Canadian data: {e}")
            return []

    async def _save_combined_results(self, site_results, scrape_results):
        """Save combined results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Combine results
        combined_results = {
            "metadata": {
                "timestamp": timestamp,
                "domains_tested": self.stats["domains_tested"],
                "total_processing_time": time.time() - self.stats["start_time"],
                "test_type": "simplified_canadian_test"
            },
            "site_analysis": {
                "total_analyzed": len(site_results),
                "successful": len([r for r in site_results if "error" not in r]),
                "results": site_results
            },
            "website_scraping": {
                "total_scraped": len(scrape_results),
                "successful": len([r for r in scrape_results if "error" not in r]),
                "total_pages": sum(len(r.get("pages", [])) for r in scrape_results),
                "results": scrape_results
            }
        }

        # Save JSON
        json_filename = f"simple_test_results_{timestamp}.json"
        json_filepath = self.results_dir / json_filename

        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)

        print(f"Results saved: {json_filename}")

        # Save CSV summary
        csv_filename = f"simple_test_summary_{timestamp}.csv"
        csv_filepath = self.results_dir / csv_filename

        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Domain', 'Site_Analysis_Method', 'Site_Analysis_Confidence',
                'Scraping_Success', 'Pages_Scraped', 'Total_Content_Length'
            ])

            # Create lookup dict for site analysis
            site_lookup = {}
            for result in site_results:
                url = result.get("url", "")
                site_lookup[url] = result

            for scrape_result in scrape_results:
                domain = scrape_result.get("domain", "")
                site_data = site_lookup.get(domain, {})

                writer.writerow([
                    domain,
                    site_data.get("recommendation", {}).get("method", "unknown"),
                    f"{site_data.get('recommendation', {}).get('confidence', 0):.2f}",
                    "success" if "error" not in scrape_result else "failed",
                    len(scrape_result.get("pages", [])),
                    scrape_result.get("metadata", {}).get("total_content_length", 0)
                ])

        print(f"CSV summary saved: {csv_filename}")

    def _print_final_summary(self, site_results, scrape_results):
        """Print final comprehensive summary"""

        processing_time = time.time() - self.stats["start_time"]

        print("\n" + "=" * 80)
        print("SIMPLIFIED TEST RESULTS SUMMARY")
        print("=" * 80)

        # Overall metrics
        print(f"Total domains tested: {self.stats['domains_tested']}")
        print(f"Total processing time: {processing_time:.2f}s ({processing_time/60:.1f} minutes)")
        print(f"Avg time per domain: {processing_time/self.stats['domains_tested']:.2f}s")

        # Site analysis results
        site_successful = len([r for r in site_results if "error" not in r])
        print(f"\nSITE ANALYSIS:")
        print(f"  Successful: {site_successful}/{len(site_results)} ({site_successful/len(site_results)*100:.1f}%)")

        # Method distribution
        method_counts = {}
        for result in site_results:
            if "error" not in result:
                method = result.get("recommendation", {}).get("method", "unknown")
                method_counts[method] = method_counts.get(method, 0) + 1

        print(f"  Method distribution:")
        for method, count in method_counts.items():
            percentage = (count / site_successful * 100) if site_successful > 0 else 0
            print(f"    {method}: {count} ({percentage:.1f}%)")

        # Scraping results
        scrape_successful = len([r for r in scrape_results if "error" not in r])
        total_pages = sum(len(r.get("pages", [])) for r in scrape_results if "error" not in r)
        total_content = sum(
            r.get("metadata", {}).get("total_content_length", 0)
            for r in scrape_results if "error" not in r
        )

        print(f"\nWEBSITE SCRAPING:")
        print(f"  Successful: {scrape_successful}/{len(scrape_results)} ({scrape_successful/len(scrape_results)*100:.1f}%)")
        print(f"  Total pages scraped: {total_pages}")
        print(f"  Avg pages per domain: {total_pages/scrape_successful:.1f}" if scrape_successful > 0 else "N/A")
        print(f"  Total content extracted: {total_content:,} characters")
        print(f"  Avg content per page: {total_content/total_pages:,.0f} chars" if total_pages > 0 else "N/A")

        # Performance assessment
        domains_per_minute = (self.stats['domains_tested'] / processing_time) * 60 if processing_time > 0 else 0
        print(f"\nPERFORMANCE:")
        print(f"  Domains per minute: {domains_per_minute:.1f}")
        print(f"  Pages per minute: {(total_pages / processing_time) * 60:.1f}" if processing_time > 0 else "N/A")

        # Success criteria check
        overall_success = (site_successful + scrape_successful) / (len(site_results) + len(scrape_results)) * 100
        print(f"\nOVERALL ASSESSMENT:")
        print(f"  Combined success rate: {overall_success:.1f}%")

        if overall_success >= 80 and domains_per_minute >= 4:
            print("  EXCELLENT - Ready for production scaling")
        elif overall_success >= 70 and domains_per_minute >= 3:
            print("  GOOD - Minor optimizations recommended")
        else:
            print("  NEEDS IMPROVEMENT - Review failed domains")

        print("=" * 80)

async def main():
    """Main execution"""

    runner = SimpleTestRunner()
    results = await runner.run_simple_test(max_domains=100)

    if "error" not in results:
        print("\n🎉 Simplified test completed successfully!")
    else:
        print(f"\n❌ Test failed: {results['error']}")

    return results

if __name__ == "__main__":
    asyncio.run(main())