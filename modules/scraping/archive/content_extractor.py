#!/usr/bin/env python3
"""
=== CONTENT EXTRACTOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Mass website content extraction with intelligent page prioritization

FEATURES:
- Parallel content extraction from websites
- Smart page discovery and prioritization
- Content cleaning and structuring
- Contact information extraction
- Technology stack detection

USAGE:
1. Configure target websites in CONFIG
2. Run: python content_extractor.py

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import re
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log

CONFIG = {
    "SCRAPING": {
        "CONCURRENCY": 40,
        "TIMEOUT": 30,
        "USER_AGENT": "Mozilla/5.0 (compatible; ContentExtractor/1.0)"
    },
    "EXTRACTION": {
        "MAX_PAGES_PER_SITE": 5,
        "PRIORITY_PAGES": ["/about", "/team", "/contact", "/services"],
        "EXTRACT_EMAILS": True,
        "EXTRACT_PHONES": True
    },
    "OUTPUT": {
        "SAVE_JSON": True,
        "RESULTS_DIR": "results"
    }
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "sites_processed": 0,
    "pages_extracted": 0
}

class ContentExtractor:
    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    @auto_log("content_extractor")
    async def extract_content(self, websites: List[str]) -> List[Dict[str, Any]]:
        print(f"Extracting content from {len(websites)} websites")

        async with aiohttp.ClientSession() as session:
            self.session = session
            results = await self._extract_websites_parallel(websites)

        await self._save_results(results)
        return results

    async def _extract_websites_parallel(self, websites: List[str]) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(self.config["SCRAPING"]["CONCURRENCY"])

        async def extract_with_semaphore(website):
            async with semaphore:
                return await self._extract_single_website(website)

        tasks = [extract_with_semaphore(site) for site in websites]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _extract_single_website(self, website: str) -> Dict[str, Any]:
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        result = {
            "website": website,
            "extracted_at": datetime.now().isoformat(),
            "pages": [],
            "emails": [],
            "phones": [],
            "technologies": []
        }

        try:
            # Extract main page
            main_content = await self._extract_page_content(website)
            if main_content:
                result["pages"].append(main_content)
                self._extract_contact_info(main_content, result)

            # Extract priority pages
            for page_path in self.config["EXTRACTION"]["PRIORITY_PAGES"]:
                page_url = website.rstrip('/') + page_path
                page_content = await self._extract_page_content(page_url)
                if page_content:
                    result["pages"].append(page_content)
                    self._extract_contact_info(page_content, result)

        except Exception as e:
            result["error"] = str(e)

        return result

    async def _extract_page_content(self, url: str) -> Dict[str, Any]:
        try:
            headers = {"User-Agent": self.config["SCRAPING"]["USER_AGENT"]}
            timeout = aiohttp.ClientTimeout(total=self.config["SCRAPING"]["TIMEOUT"])

            async with self.session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remove scripts and styles
                    for script in soup(["script", "style"]):
                        script.decompose()

                    return {
                        "url": url,
                        "title": soup.title.string if soup.title else "",
                        "text": soup.get_text(),
                        "headings": [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
                    }
        except Exception as e:
            print(f"Failed to extract {url}: {e}")

        return None

    def _extract_contact_info(self, content: Dict[str, Any], result: Dict[str, Any]):
        text = content.get("text", "")

        if self.config["EXTRACTION"]["EXTRACT_EMAILS"]:
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            result["emails"].extend(emails)

        if self.config["EXTRACTION"]["EXTRACT_PHONES"]:
            phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
            result["phones"].extend(phones)

    async def _save_results(self, results: List[Dict[str, Any]]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_sites": len(results)
            },
            "results": results
        }

        filename = f"content_extraction_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"Content extraction saved: {filename}")

async def main():
    extractor = ContentExtractor()
    sample_sites = ["example.com", "google.com"]
    await extractor.extract_content(sample_sites)

if __name__ == "__main__":
    asyncio.run(main())