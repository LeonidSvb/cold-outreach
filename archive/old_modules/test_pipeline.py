#!/usr/bin/env python3
"""
=== WEBSITE INTELLIGENCE PIPELINE TEST ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
Test script for validating website intelligence pipeline functionality.
Tests individual components and full pipeline integration.

USAGE:
python test_pipeline.py
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

try:
    from site_analyzer import SiteAnalyzer
    from http_scraper import HTTPScraper
    from content_processor import ContentProcessor
    from intelligence_router import WebsiteIntelligenceRouter
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all components are in the src/ directory")
    sys.exit(1)

async def test_site_analyzer():
    """Test site analyzer component"""
    print("\n=== TESTING SITE ANALYZER ===")

    analyzer = SiteAnalyzer()
    test_urls = [
        "https://example.com",
        "https://github.com",
        "https://stackoverflow.com"
    ]

    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        try:
            result = analyzer.analyze_site(url)
            print(f"  Method: {result.get('scraping_method', 'unknown')}")
            print(f"  Confidence: {result.get('confidence', 0):.2f}")
            print(f"  Quality: {result.get('content_quality', 'unknown')}")
            print(f"  JS Risk: {result.get('js_indicators', {}).get('risk_score', 0)}")
            print(f"  Time: {result.get('analysis_time', 0):.2f}s")

            if result.get('error'):
                print(f"  Error: {result['error']}")

        except Exception as e:
            print(f"  Exception: {e}")

async def test_http_scraper():
    """Test HTTP scraper component"""
    print("\n\n=== TESTING HTTP SCRAPER ===")

    scraper = HTTPScraper()
    test_domains = [
        "example.com",
        "github.com"
    ]

    try:
        results = await scraper.scrape_domains_parallel(test_domains)

        for domain, result in results.items():
            print(f"\nDomain: {domain}")
            print(f"  Success: {result.get('success', False)}")
            print(f"  Pages: {len(result.get('pages', []))}")
            print(f"  Text Length: {result.get('total_text_length', 0):,}")
            print(f"  Processing Time: {result.get('processing_time', 0):.2f}s")

            if result.get('error'):
                print(f"  Error: {result['error']}")

    except Exception as e:
        print(f"HTTP Scraper error: {e}")

async def test_content_processor():
    """Test content processor component"""
    print("\n\n=== TESTING CONTENT PROCESSOR ===")

    processor = ContentProcessor()

    if not processor.ai_enabled:
        print("AI processing disabled - skipping content processor test")
        return

    # Mock extraction data
    test_data = {
        "example.com": {
            "success": True,
            "total_text_length": 500,
            "pages": [
                {
                    "url": "https://example.com",
                    "text": "Example Domain. This domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission. More information about Example Domain can be found at the IANA website."
                }
            ]
        }
    }

    try:
        results = await processor.process_domains_batch(test_data)

        for domain, analysis in results.items():
            print(f"\nDomain: {domain}")
            print(f"  Analysis available: {bool(analysis)}")
            if analysis:
                print(f"  Tokens used: {analysis.get('tokens_used', 0)}")
                print(f"  Cost: ${analysis.get('cost', 0):.4f}")
                print(f"  Processing time: {analysis.get('processing_time', 0):.2f}s")

    except Exception as e:
        print(f"Content Processor error: {e}")

async def test_full_pipeline():
    """Test complete pipeline integration"""
    print("\n\n=== TESTING FULL PIPELINE ===")

    try:
        router = WebsiteIntelligenceRouter()

        test_domains = [
            "example.com",
            "github.com"
        ]

        print(f"Running full pipeline on {len(test_domains)} domains...")
        results = await router.process_domains(test_domains)

        print(f"\nPipeline Results:")
        print(f"  HTTP results: {len(results.get('http_results', {}))}")
        print(f"  Apify results: {len(results.get('apify_results', {}))}")
        print(f"  AI summaries: {len(results.get('ai_summaries', {}))}")

        # Print detailed results
        for method in ['http_results', 'apify_results']:
            if method in results:
                print(f"\n{method.upper()}:")
                for domain, result in results[method].items():
                    print(f"  {domain}: Success={result.get('success', False)}, "
                          f"Pages={result.get('pages_extracted', 0)}")

    except Exception as e:
        print(f"Full Pipeline error: {e}")

async def test_configuration():
    """Test configuration loading"""
    print("\n\n=== TESTING CONFIGURATION ===")

    config_file = Path(__file__).parent / "config.json"

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"Configuration loaded successfully")
            print(f"  Module: {config.get('module_info', {}).get('name', 'Unknown')}")
            print(f"  Version: {config.get('module_info', {}).get('version', 'Unknown')}")
            print(f"  HTTP workers: {config.get('scraping', {}).get('http', {}).get('max_workers', 0)}")
            print(f"  AI enabled: {config.get('ai_processing', {}).get('enabled', False)}")
        except Exception as e:
            print(f"Configuration error: {e}")
    else:
        print("Configuration file not found")

def check_dependencies():
    """Check required dependencies"""
    print("=== CHECKING DEPENDENCIES ===")

    dependencies = [
        ('aiohttp', 'aiohttp'),
        ('beautifulsoup4', 'bs4'),
        ('requests', 'requests'),
        ('openai', 'openai')
    ]

    missing = []
    for package, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    return True

async def main():
    """Main test execution"""
    print("🌐 WEBSITE INTELLIGENCE PIPELINE TESTING")
    print("=" * 60)

    # Check dependencies first
    if not check_dependencies():
        print("\nPlease install missing dependencies before testing")
        return

    # Test configuration
    await test_configuration()

    # Test individual components
    await test_site_analyzer()
    await test_http_scraper()
    await test_content_processor()

    # Test full pipeline
    await test_full_pipeline()

    print("\n" + "=" * 60)
    print("🎯 TESTING COMPLETE")
    print("\nIf you see errors above, check:")
    print("1. Internet connection for external site testing")
    print("2. OPENAI_API_KEY environment variable for AI features")
    print("3. All required dependencies are installed")
    print("4. File permissions and paths are correct")

if __name__ == "__main__":
    asyncio.run(main())