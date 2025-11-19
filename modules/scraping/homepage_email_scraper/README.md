# Homepage Email Scraper

Fast homepage scraping with multi-page fallback - extracts emails and content from websites.

## Features

- Homepage + multi-page fallback (up to 5 pages)
- Email extraction from homepage and deep search
- Full text content extraction
- Site type detection (static/dynamic)
- Maximum parallel processing (50 workers)
- NO AI analysis (fast & free)
- Real-time progress tracking in Streamlit UI

## Structure

```
homepage_email_scraper/
├── app.py              ← Streamlit UI (run this)
├── scraper.py          ← SimpleHomepageScraper class (backend logic)
├── results/            ← Output files (scraped_YYYYMMDD/)
└── README.md           ← This file
```

## Usage

### Option 1: Streamlit UI (Recommended)

```bash
streamlit run modules/scraping/homepage_email_scraper/app.py
```

### Option 2: CLI

```bash
python modules/scraping/homepage_email_scraper/scraper.py --input input.csv --workers 50 --max-pages 5
```

## Output Files

1. `success_emails.csv` - Websites with emails found
2. `failed_static.csv` - Static sites without emails
3. `failed_dynamic.csv` - Dynamic sites without emails
4. `failed_other.csv` - Connection errors, timeouts, etc.
5. `scraping_analytics.json` - Performance metrics

## Performance

- **Speed**: ~5-10 sites/second (depending on website response time)
- **Success Rate**: 70-75% (on quality lists)
- **Parallel Workers**: 50 concurrent requests
- **No Cost**: Pure HTTP scraping, no AI APIs

## Dependencies

Shared libraries from `modules/scraping/lib/`:
- `http_utils.py` - HTTP client with retry logic
- `text_utils.py` - Email extraction and text cleaning
- `sitemap_utils.py` - Sitemap parsing for smart page discovery

## Version

- **v2.0.0** - Proven stable version (Nov 18, 2025)
- Based on `simple_homepage_scraper.py` with 73.74% success rate
