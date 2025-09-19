# Cold Outreach Automation Platform

## Modular Website Intelligence System

### Quick Start:
```bash
# Preview any CSV structure
py core/processor/flexible_csv.py companies.csv --workflow extract_links --preview

# Full workflow: extract → filter → scrape → summarize  
py core/processor/flexible_csv.py companies.csv --workflow extract_links filter_links scrape_content summarize_content

# Single modules
py core/modules/link_extractor/function.py "https://example.com" --depth=2
py core/modules/content_scraper/function.py links.json --output content.json
```

### Architecture:
```
├── core/
│   ├── modules/              # Independent modular functions
│   │   ├── link_extractor/   # Extract all site links
│   │   ├── link_filter/      # Filter relevant pages  
│   │   ├── content_scraper/  # Scrape → clean JSON
│   │   └── content_summarizer/ # Extract personalization hooks
│   ├── processor/            # Flexible CSV workflow engine
│   └── prompts/              # Editable AI prompts
├── data/
│   ├── input/               # Source CSV files
│   ├── output/              # Processed results
│   └── logs/                # Auto-generated logs
├── leads/                   # Lead data management
└── legacy/                  # Archived old code
```

### Features:
- ✅ **Auto-detect** any CSV column structure
- ✅ **Modular functions** - use separately or combined
- ✅ **HTTP-only scraping** - no external dependencies
- ✅ **Auto-logging** with performance tracking
- ✅ **Flexible workflows** - combine functions like n8n nodes
- ✅ **Editable prompts** - modify AI behavior without code changes