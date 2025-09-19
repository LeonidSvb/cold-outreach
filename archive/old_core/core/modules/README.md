# Modular Website Intelligence Functions

## Available Modules:

### Core Functions:
- **link_extractor** - Extract all links from company website (v1.0.0)  
- **link_filter** - Filter relevant links using AI criteria (v1.0.0)
- **content_scraper** - Scrape URLs and convert to clean JSON (v1.0.0)
- **content_summarizer** - Extract key facts for personalization (v1.0.0)

### Usage Examples:

#### Standalone Usage:
```python
from core.modules.link_extractor.function import extract_all_links
from core.modules.content_scraper.function import scrape_urls_to_clean_json

# Extract all links
links = extract_all_links("https://example.com", max_depth=2)

# Scrape to clean JSON
data = scrape_urls_to_clean_json(links[:5])
```

#### CSV Workflow:
```python
from core.processor.flexible_csv import FlexibleCSVProcessor

processor = FlexibleCSVProcessor('data/input/companies.csv')
processor.set_column_mapping({
    'website': 'Company Website',
    'links': 'Extracted Links',
    'content': 'Scraped Content'
})
processor.run_workflow(['extract_links', 'filter_links', 'scrape_content'])
```

## Architecture:
- Each module is **completely independent** 
- All prompts stored in `core/prompts/`
- Auto-logging to `data/logs/`
- Statistics tracking in each module
- CSV processor handles any column structure

## Quick Start:
```bash
python -m core.modules.link_extractor.function "https://example.com"
python -m core.processor.flexible_csv companies.csv --workflow="extract,scrape,summarize"
```