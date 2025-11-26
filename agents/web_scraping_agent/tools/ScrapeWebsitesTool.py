from agency_swarm.tools import BaseTool
from pydantic import Field
import sys
from pathlib import Path
from typing import List, Dict, Literal
import subprocess
import json
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ScrapeWebsitesTool(BaseTool):
    """
    Scrape websites in bulk with configurable modes and settings.

    This tool processes one or multiple website URLs using parallel scraping.
    Supports three modes: quick (detection only), standard (with email extraction),
    and full (with AI analysis).
    """

    urls: List[str] = Field(
        ...,
        description="List of website URLs to scrape. Can be single URL or multiple URLs.",
        examples=[["https://example.com"], ["https://site1.com", "https://site2.com"]]
    )

    mode: Literal["quick", "standard", "full"] = Field(
        default="standard",
        description="""Scraping mode:
        - quick: Fast detection only (~0.05 sec/site) - checks if site is static/dynamic
        - standard: Full scraping with email extraction (~0.5 sec/site) - recommended
        - full: Complete scraping with AI content analysis (~3 sec/site) - slower but detailed
        """
    )

    workers: int = Field(
        default=25,
        description="Number of parallel workers for scraping. Range: 1-50. Higher = faster but more resource intensive.",
        ge=1,
        le=50
    )

    extract_emails: bool = Field(
        default=True,
        description="Whether to extract email addresses from scraped content"
    )

    extract_phones: bool = Field(
        default=True,
        description="Whether to extract phone numbers from scraped content"
    )

    def run(self) -> str:
        """
        Execute website scraping with specified configuration.

        Returns:
            JSON string with scraping results including:
            - Scraped data for each URL
            - Extracted emails and phones
            - Success/failure status
            - Processing statistics
        """
        try:
            # Import scraping modules
            from modules.scraping.lib.http_utils import HTTPClient, get_smart_pages
            from modules.scraping.lib.text_utils import (
                clean_html_to_text,
                extract_emails_from_html,
                extract_phones
            )

            results = []
            client = HTTPClient()

            # Process each URL
            for url in self.urls:
                try:
                    result = {
                        "url": url,
                        "success": False,
                        "emails": [],
                        "phones": [],
                        "content_preview": "",
                        "site_type": "unknown"
                    }

                    # Mode: quick - just check if site loads
                    if self.mode == "quick":
                        response = client.fetch(url)
                        if response['status'] == 'success':
                            result["success"] = True
                            result["site_type"] = "accessible"

                    # Mode: standard - scrape homepage and contact page
                    elif self.mode == "standard":
                        # Scrape homepage
                        response = client.fetch(url)
                        if response['status'] == 'success':
                            html = response['content']

                            # Extract emails
                            if self.extract_emails:
                                emails = extract_emails_from_html(html)
                                result["emails"].extend(emails)

                            # Extract phones
                            if self.extract_phones:
                                phones = extract_phones(html)
                                result["phones"].extend(phones)

                            # Get content preview
                            text = clean_html_to_text(html)
                            result["content_preview"] = text[:500] + "..." if len(text) > 500 else text
                            result["success"] = True

                        # Remove duplicates
                        result["emails"] = list(set(result["emails"]))
                        result["phones"] = list(set(result["phones"]))

                    # Mode: full - complete scraping with multiple pages
                    elif self.mode == "full":
                        # Get smart page paths
                        from urllib.parse import urljoin, urlparse
                        base_url = url
                        parsed = urlparse(url)
                        base_domain = f"{parsed.scheme}://{parsed.netloc}"

                        # Get list of important page paths
                        page_paths = get_smart_pages(categories=['contact', 'about'])

                        # Build full URLs
                        pages_to_scrape = [base_url] + [urljoin(base_domain, path) for path in page_paths[:4]]

                        all_text = []
                        for page_url in pages_to_scrape:
                            try:
                                response = client.fetch(page_url)
                                if response['status'] == 'success':
                                    html = response['content']

                                    if self.extract_emails:
                                        emails = extract_emails_from_html(html)
                                        result["emails"].extend(emails)

                                    if self.extract_phones:
                                        phones = extract_phones(html)
                                        result["phones"].extend(phones)

                                    text = clean_html_to_text(html)
                                    all_text.append(text)
                            except Exception:
                                continue  # Skip failed pages

                        # Combine all text
                        full_content = " ".join(all_text)
                        result["content_preview"] = full_content[:1000] + "..." if len(full_content) > 1000 else full_content
                        result["full_content_length"] = len(full_content)

                        # Remove duplicates
                        result["emails"] = list(set(result["emails"]))
                        result["phones"] = list(set(result["phones"]))
                        result["success"] = True if result["emails"] or result["phones"] or full_content else False

                    results.append(result)

                except Exception as e:
                    results.append({
                        "url": url,
                        "success": False,
                        "error": str(e),
                        "emails": [],
                        "phones": []
                    })

            # Calculate statistics
            total = len(results)
            successful = sum(1 for r in results if r["success"])
            total_emails = sum(len(r.get("emails", [])) for r in results)
            total_phones = sum(len(r.get("phones", [])) for r in results)

            return json.dumps({
                "status": "completed",
                "statistics": {
                    "total_urls": total,
                    "successful": successful,
                    "failed": total - successful,
                    "success_rate": f"{(successful/total*100):.1f}%",
                    "total_emails_found": total_emails,
                    "total_phones_found": total_phones
                },
                "results": results
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to execute scraping. Check that all dependencies are installed."
            }, indent=2)


if __name__ == "__main__":
    # Test the tool
    tool = ScrapeWebsitesTool(
        urls=["https://example.com"],
        mode="standard",
        workers=5
    )
    print(tool.run())
