from agency_swarm.tools import BaseTool
from pydantic import Field
import sys
from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ProcessCSVTool(BaseTool):
    """
    Process a CSV file containing website URLs in bulk.

    Reads URLs from CSV, processes them with specified mode,
    and saves results to a new CSV file with all extracted data.
    """

    input_file: str = Field(
        ...,
        description="Path to input CSV file containing URLs. Must have a column with website URLs.",
        examples=["data/websites.csv", "C:/Users/user/leads.csv"]
    )

    url_column: str = Field(
        default="website",
        description="Name of the column containing website URLs in the CSV file"
    )

    mode: Literal["quick", "standard", "full"] = Field(
        default="standard",
        description="Scraping mode: quick (detection only), standard (with emails), or full (with AI analysis)"
    )

    workers: int = Field(
        default=25,
        description="Number of parallel workers for processing. Range: 1-50",
        ge=1,
        le=50
    )

    output_file: Optional[str] = Field(
        default=None,
        description="Path for output CSV file. If not specified, auto-generated with timestamp"
    )

    max_rows: Optional[int] = Field(
        default=None,
        description="Maximum number of rows to process. Leave None to process all rows"
    )

    def run(self) -> str:
        """
        Process CSV file with websites and return results.

        Returns:
            JSON string with:
            - Processing statistics
            - Output file path
            - Summary of results
        """
        try:
            # Read CSV
            df = pd.read_csv(self.input_file)

            if self.url_column not in df.columns:
                return json.dumps({
                    "status": "error",
                    "error": f"Column '{self.url_column}' not found in CSV",
                    "available_columns": list(df.columns)
                }, indent=2)

            # Limit rows if specified
            if self.max_rows:
                df = df.head(self.max_rows)

            urls = df[self.url_column].dropna().tolist()

            if not urls:
                return json.dumps({
                    "status": "error",
                    "error": "No valid URLs found in the specified column"
                }, indent=2)

            # Import scraping modules
            from modules.scraping.lib.http_utils import HTTPClient, get_smart_pages
            from modules.scraping.lib.text_utils import (
                clean_html_to_text,
                extract_emails_from_html,
                extract_phones
            )
            from concurrent.futures import ThreadPoolExecutor, as_completed

            results = []
            client = HTTPClient()

            def process_single_url(url):
                """Process single URL"""
                try:
                    result = {
                        "url": url,
                        "success": False,
                        "emails": [],
                        "phones": [],
                        "content_preview": ""
                    }

                    if self.mode == "quick":
                        response = client.get(url, timeout=5)
                        if response and response.status_code == 200:
                            result["success"] = True

                    elif self.mode in ["standard", "full"]:
                        pages = get_smart_pages(url, mode="homepage_only" if self.mode == "standard" else "smart")
                        pages_to_check = pages[:3] if self.mode == "standard" else pages[:5]

                        for page_url in pages_to_check:
                            response = client.get(page_url, timeout=10)
                            if response and response.status_code == 200:
                                html = response.text
                                result["emails"].extend(extract_emails_from_html(html))
                                result["phones"].extend(extract_phones(html))

                                if not result["content_preview"]:
                                    text = clean_html_to_text(html)
                                    result["content_preview"] = text[:300]

                        result["emails"] = list(set(result["emails"]))
                        result["phones"] = list(set(result["phones"]))
                        result["success"] = True

                    return result

                except Exception as e:
                    return {
                        "url": url,
                        "success": False,
                        "error": str(e),
                        "emails": [],
                        "phones": []
                    }

            # Process URLs in parallel
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = [executor.submit(process_single_url, url) for url in urls]
                for future in as_completed(futures):
                    results.append(future.result())

            # Create output DataFrame
            output_df = df.copy()

            # Add results to original DataFrame
            url_to_result = {r["url"]: r for r in results}

            output_df["scraping_success"] = output_df[self.url_column].map(
                lambda x: url_to_result.get(x, {}).get("success", False)
            )

            output_df["extracted_emails"] = output_df[self.url_column].map(
                lambda x: ", ".join(url_to_result.get(x, {}).get("emails", []))
            )

            output_df["extracted_phones"] = output_df[self.url_column].map(
                lambda x: ", ".join(url_to_result.get(x, {}).get("phones", []))
            )

            output_df["content_preview"] = output_df[self.url_column].map(
                lambda x: url_to_result.get(x, {}).get("content_preview", "")
            )

            # Generate output filename if not specified
            if not self.output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                input_path = Path(self.input_file)
                self.output_file = str(input_path.parent / f"{input_path.stem}_scraped_{timestamp}.csv")

            # Save results
            output_df.to_csv(self.output_file, index=False, encoding='utf-8-sig')

            # Calculate statistics
            total = len(results)
            successful = sum(1 for r in results if r["success"])
            total_emails = sum(len(r.get("emails", [])) for r in results)
            total_phones = sum(len(r.get("phones", [])) for r in results)
            rows_with_emails = sum(1 for r in results if r.get("emails"))

            return json.dumps({
                "status": "completed",
                "output_file": self.output_file,
                "statistics": {
                    "total_urls_processed": total,
                    "successful_scrapes": successful,
                    "failed_scrapes": total - successful,
                    "success_rate": f"{(successful/total*100):.1f}%",
                    "total_emails_found": total_emails,
                    "total_phones_found": total_phones,
                    "rows_with_emails": rows_with_emails,
                    "email_find_rate": f"{(rows_with_emails/total*100):.1f}%"
                },
                "message": f"Successfully processed {total} URLs. Results saved to {self.output_file}"
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to process CSV file. Check file path and format."
            }, indent=2)


if __name__ == "__main__":
    # Test the tool
    tool = ProcessCSVTool(
        input_file="test_websites.csv",
        url_column="website",
        mode="standard",
        workers=10,
        max_rows=5
    )
    print(tool.run())
