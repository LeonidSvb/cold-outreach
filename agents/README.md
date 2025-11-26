# Web Scraping Agency

AI-powered web scraping agent built with Agency Swarm for bulk website processing, email extraction, and data enrichment.

## Features

- **Bulk Website Scraping**: Process single URLs or thousands from CSV files
- **Multiple Modes**:
  - Quick (0.05s/site) - Detection only
  - Standard (0.5s/site) - With email/phone extraction
  - Full (3s/site) - With AI analysis
- **Parallel Processing**: Up to 50 concurrent workers
- **Smart Extraction**: Emails, phones, and contact information
- **Multiple Exports**: CSV, JSON, Excel formats
- **Real-time Statistics**: Track progress and success rates

## Quick Start

### 1. Install Dependencies

```bash
cd agents
pip install -r requirements.txt
```

### 2. Set Up Environment

Create `.env` file in the agents directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Agency

```bash
python agency.py
```

This will start the Gradio interface where you can interact with the agent.

## Usage Examples

### Example 1: Scrape Single Website

```
You: Scrape https://example.com and extract emails

Agent: *Uses ScrapeWebsitesTool*
- Mode: standard
- Extracted 3 emails: contact@example.com, ...
- Success rate: 100%
```

### Example 2: Process CSV File

```
You: Process the file data/leads.csv with website column, extract all emails

Agent: *Uses ProcessCSVTool*
- Processed 500 URLs
- Found emails in 387 rows (77.4%)
- Saved to: data/leads_scraped_20251126.csv
```

### Example 3: Bulk Scraping with Export

```
You: Scrape all websites in websites.csv, extract emails and phones, export to Excel

Agent: *Uses ProcessCSVTool + ExportResultsTool*
1. Processed 1000 websites (standard mode)
2. Success rate: 85.3%
3. Found 643 emails, 521 phones
4. Exported to: results.xlsx
```

## Available Tools

### 1. ScrapeWebsitesTool
Scrape one or multiple websites with configurable modes.

**Parameters:**
- `urls`: List of URLs to scrape
- `mode`: quick | standard | full
- `workers`: 1-50 (default: 25)
- `extract_emails`: true/false
- `extract_phones`: true/false

### 2. ProcessCSVTool
Process bulk websites from CSV file.

**Parameters:**
- `input_file`: Path to CSV file
- `url_column`: Column name with URLs (default: "website")
- `mode`: quick | standard | full
- `workers`: 1-50 (default: 25)
- `output_file`: Optional output path
- `max_rows`: Limit rows to process

### 3. ExportResultsTool
Export results to various formats.

**Parameters:**
- `input_file`: Path to results CSV
- `output_format`: csv | json | excel | all
- `output_path`: Base path for outputs
- `include_stats`: Include statistics file
- `email_only`: Export only rows with emails

## Architecture

```
agents/
├── web_scraping_agent/
│   ├── instructions.md          # Agent role and capabilities
│   ├── web_scraping_agent.py    # Agent class
│   ├── tools/
│   │   ├── ScrapeWebsitesTool.py
│   │   ├── ProcessCSVTool.py
│   │   └── ExportResultsTool.py
│   └── files/                   # Agent working directory
├── agency.py                    # Main agency file
├── agency_manifesto.md          # Shared instructions
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Performance Benchmarks

### Quick Mode (Detection Only)
- 1000 sites: ~50 seconds
- Use case: Validate URL list

### Standard Mode (With Emails)
- 1000 sites: ~500 seconds (8 minutes)
- Use case: Regular lead scraping

### Full Mode (With AI Analysis)
- 1000 sites: ~3000 seconds (50 minutes)
- Use case: Deep analysis of high-value leads

## Best Practices

### Optimize for Speed
1. Use Quick mode for validation
2. Use Standard mode for most scraping
3. Reserve Full mode for important leads
4. Increase workers for powerful systems

### Maximize Success Rate
1. Ensure URLs are properly formatted
2. Include http:// or https:// prefix
3. Remove trailing slashes
4. Use standard mode for best results

### Data Quality
1. Always review failed scrapes
2. Validate extracted emails
3. Remove duplicates
4. Check for generic emails (info@, contact@)

## Troubleshooting

### Agent not finding emails
- Try Full mode for deeper scraping
- Check if website has contact page
- Verify website is accessible

### Slow processing
- Reduce number of workers
- Use Quick mode for testing
- Process in smaller batches

### Import errors
- Install all requirements: `pip install -r requirements.txt`
- Ensure project root is in Python path
- Check that modules/scraping exists

## Integration with Existing Scripts

This agent integrates with your existing scraping infrastructure:

**Modules Used:**
- `modules/scraping/lib/http_utils.py` - HTTP client
- `modules/scraping/lib/text_utils.py` - Email/phone extraction
- `modules/scraping/scripts/website_scraper.py` - Main scraper

**Compatible With:**
- Universal Website Scraper (v2.0.0)
- Streamlit Homepage Scraper (v3.0.0)
- OpenAI Mass Processor (v1.0.0)

## Advanced Usage

### Programmatic API

```python
from agency_swarm import Agency
from web_scraping_agent.web_scraping_agent import WebScrapingAgent

# Create agency
web_scraper = WebScrapingAgent()
agency = Agency([web_scraper])

# Send message
response = agency.get_completion(
    "Process websites.csv and extract all emails",
    message_files=["path/to/websites.csv"]
)
print(response)
```

### Custom Tool Development

Add new tools to `web_scraping_agent/tools/`:

```python
from agency_swarm.tools import BaseTool
from pydantic import Field

class CustomTool(BaseTool):
    """Your custom scraping tool"""

    param: str = Field(..., description="Parameter description")

    def run(self):
        # Your logic here
        return "Result"
```

## Support

For issues or questions:
1. Check this README
2. Review agent instructions.md
3. Test with small datasets first
4. Check logs for error details

## License

Part of the Cold Outreach Automation Platform.
