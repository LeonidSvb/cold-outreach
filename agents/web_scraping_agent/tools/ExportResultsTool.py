from agency_swarm.tools import BaseTool
from pydantic import Field
import sys
from pathlib import Path
from typing import Literal
import pandas as pd
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class ExportResultsTool(BaseTool):
    """
    Export scraping results to various formats with statistics report.

    Converts scraped data to different output formats (CSV, JSON, Excel)
    with optional statistics summary.
    """

    input_file: str = Field(
        ...,
        description="Path to input CSV file with scraping results",
        examples=["results/scraped_data.csv"]
    )

    output_format: Literal["csv", "json", "excel", "all"] = Field(
        default="csv",
        description="Output format: csv, json, excel, or 'all' for all formats"
    )

    output_path: str = Field(
        ...,
        description="Base path for output file(s). Extension will be added automatically",
        examples=["exports/final_results", "C:/Users/user/output"]
    )

    include_stats: bool = Field(
        default=True,
        description="Whether to include a statistics summary file"
    )

    email_only: bool = Field(
        default=False,
        description="If True, only export rows that have extracted emails"
    )

    def run(self) -> str:
        """
        Export results to specified format(s).

        Returns:
            JSON string with:
            - Paths to created files
            - Export statistics
            - Data summary
        """
        try:
            # Read input file
            df = pd.read_csv(self.input_file)

            # Filter email-only if requested
            if self.email_only and 'extracted_emails' in df.columns:
                df = df[df['extracted_emails'].notna() & (df['extracted_emails'] != '')]

            output_files = []

            # Export to CSV
            if self.output_format in ["csv", "all"]:
                csv_path = f"{self.output_path}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                output_files.append(csv_path)

            # Export to JSON
            if self.output_format in ["json", "all"]:
                json_path = f"{self.output_path}.json"
                df.to_json(json_path, orient='records', indent=2, force_ascii=False)
                output_files.append(json_path)

            # Export to Excel
            if self.output_format in ["excel", "all"]:
                excel_path = f"{self.output_path}.xlsx"
                df.to_excel(excel_path, index=False, engine='openpyxl')
                output_files.append(excel_path)

            # Calculate statistics
            stats = {
                "total_rows": len(df),
                "timestamp": datetime.now().isoformat()
            }

            if 'extracted_emails' in df.columns:
                rows_with_emails = df['extracted_emails'].notna().sum()
                stats["rows_with_emails"] = int(rows_with_emails)
                stats["email_rate"] = f"{(rows_with_emails/len(df)*100):.1f}%"

            if 'extracted_phones' in df.columns:
                rows_with_phones = df['extracted_phones'].notna().sum()
                stats["rows_with_phones"] = int(rows_with_phones)
                stats["phone_rate"] = f"{(rows_with_phones/len(df)*100):.1f}%"

            if 'scraping_success' in df.columns:
                successful = df['scraping_success'].sum()
                stats["successful_scrapes"] = int(successful)
                stats["success_rate"] = f"{(successful/len(df)*100):.1f}%"

            # Create statistics file if requested
            if self.include_stats:
                stats_path = f"{self.output_path}_statistics.json"
                with open(stats_path, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2)
                output_files.append(stats_path)

            return json.dumps({
                "status": "completed",
                "output_files": output_files,
                "statistics": stats,
                "message": f"Successfully exported {len(df)} rows to {len(output_files)} file(s)"
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "message": "Failed to export results. Check file paths and permissions."
            }, indent=2)


if __name__ == "__main__":
    # Test the tool
    tool = ExportResultsTool(
        input_file="test_results.csv",
        output_format="all",
        output_path="exports/final",
        include_stats=True
    )
    print(tool.run())
