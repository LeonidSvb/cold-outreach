# Website Intelligence Extractor

Automated system for extracting personalization data from company websites for cold outreach campaigns.

## Features

- **HTTP-Only Scraping**: Pure Python HTTP requests, no external services
- **Smart Page Discovery**: Finds pages via sitemaps and internal linking
- **Content Prioritization**: Focuses on About, Company, Team pages
- **AI-Powered Analysis**: Uses OpenAI to extract personalization insights
- **Batch Processing**: Handles large CSV files in manageable chunks
- **Error Resilience**: Continues processing even when individual sites fail

## Usage

### Quick Test (5 domains)
```bash
cd scripts
test_extraction.bat
```

### Custom Batch Processing
```bash
cd scripts
python run_extraction.py [batch_size] [start_index] [csv_filename]

# Examples:
python run_extraction.py 10 0 "Lumid - verification - Canada.csv"    # First 10 domains
python run_extraction.py 10 10 "Lumid - verification - Canada.csv"   # Next 10 domains  
python run_extraction.py 50 0 "large_file.csv"                       # 50 domains from large file
```

### Large File Processing
For 1000+ domain files, process in batches:

```bash
# Process in batches of 25
python run_extraction.py 25 0    # Domains 1-25
python run_extraction.py 25 25   # Domains 26-50  
python run_extraction.py 25 50   # Domains 51-75
# ... continue until complete
```

## Output Format

Results are saved to `outputs/website_intelligence_[batch]_[timestamp].json`:

```json
{
  "total_processed": 10,
  "successful": 8,
  "failed": 2,
  "processed_at": "2024-01-15T10:30:00",
  "results": [
    {
      "domain": "example.com",
      "company_name": "Example Corp",
      "success": true,
      "pages_found": 15,
      "pages_processed": 3,
      "ai_analysis": {
        "company_focus": "B2B SaaS solutions for small businesses",
        "company_values": "Innovation, customer success, transparency",
        "recent_developments": "Launched new AI-powered analytics platform",
        "team_info": "25+ employees, founded by tech veterans",
        "unique_differentiators": "First to market with real-time insights",
        "personalization_hooks": [
          "Recently raised Series A funding",
          "Focus on helping small businesses scale",
          "Strong emphasis on customer support"
        ]
      }
    }
  ]
}
```

## Configuration

API keys are loaded from project root `.env` file:
```
OPENAI_API_KEY=your_openai_key_here
```

## CSV Requirements

The script expects CSV with these columns:
- `company_domain`: Website domain (required)
- `company_name`: Company name for context (optional but recommended)

## Error Handling

- **Network Issues**: Retries with different protocols (HTTPS → HTTP)
- **SSL Problems**: Uses permissive SSL context
- **Content Issues**: Falls back to raw text if HTML parsing fails  
- **API Failures**: Saves partial results and continues processing
- **Large Files**: Processes in chunks to avoid memory issues

## Performance Tips

- **Batch Size**: 10-25 domains per batch for optimal performance
- **Rate Limiting**: Built-in delays prevent site blocking
- **Progress Saving**: Results saved after each domain (no data loss)
- **Resource Usage**: Minimal memory footprint, scales to large files

## Troubleshooting

### Common Issues

**"No pages discovered"**
- Domain might be inactive or blocking requests
- Try different protocols (HTTP vs HTTPS)

**"OpenAI API error"**  
- Check API key in .env file
- Verify API credits/limits
- Content might be too long (automatically truncated)

**"SSL Certificate error"**
- Script uses permissive SSL context
- Some corporate sites may still block requests

### Monitoring Progress

Each domain shows processing steps:
```
Processing example.com (Example Corp)...
  Discovering pages...
  Prioritizing 12 pages...  
    Extracting content from https://example.com/about
    Extracting content from https://example.com/team
  Analyzing content with OpenAI...
  ✓ Successfully processed example.com
```

## Integration

Results can be used with:
- **Instantly**: Email personalization data
- **Airtable**: Enriched company records  
- **N8N**: Automated workflow triggers
- **Custom Scripts**: JSON format for easy parsing