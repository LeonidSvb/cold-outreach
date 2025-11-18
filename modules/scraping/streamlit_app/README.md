# Homepage Scraper - Streamlit UI

Simple minimalist interface for running homepage email scraper.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

## Features

- Upload CSV with websites
- Configure scraping parameters (workers, max pages)
- View results & analytics
- Download cleaned CSV files

## Requirements

- Python 3.8+
- Streamlit 1.28+
- Pandas 2.0+

## Usage

1. **Upload CSV** - Must have `name` and `website` columns
2. **Configure** - Set workers (default: 50), max pages (default: 5)
3. **Run** - Click "Start Scraping" and monitor terminal
4. **Results** - View analytics and download CSV files

## File Outputs

- `success_emails.csv` - Unique emails with content
- `failed_static.csv` - Static sites without email
- `failed_dynamic.csv` - Dynamic sites without email
- `failed_other.csv` - Connection errors
- `scraping_analytics.json` - Detailed metrics

## Notes

- Scraper runs in background (check terminal for progress)
- Auto-deduplication by email
- Auto-clean (remove webmaster, NPS generic emails)
- Auto-fix truncated emails (.co → .com)
