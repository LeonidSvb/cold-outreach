# Homepage Email Scraper (Unified v4.0.0)

Fast homepage scraping with multi-page fallback - extracts emails and content from websites with enhanced UI and flexibility.

## ✨ Features

### Core Scraping
- **Homepage + multi-page fallback** (up to 10 pages configurable)
- **Email extraction** with 3 output formats
- **Full text content extraction** (15k chars max)
- **Site type detection** (static/dynamic/SPA)
- **URL validation** before processing
- **Deduplication** by email (automatic)
- **Preserves ALL original CSV columns**

### UI/UX
- **Real-time progress tracking** from subprocess
- **Live logs** with expandable viewer
- **Auto-detect URL/name columns** or manual selection
- **Rich configuration sidebar** (12+ options)
- **Historical results browsing**
- **Detailed JSON analytics**
- **Session state** for immediate results
- **Custom CSS styling** (gradients, metrics)

### Flexibility
- **2 scraping modes**: Homepage Only | Deep Search
- **Email toggle**: Can disable email extraction
- **3 email formats**:
  - Separate row per email (default)
  - All emails in one cell (comma-separated)
  - Primary email only (first found)
- **Flexible columns**: Works with any column names
- **Processing limit**: Test on first N rows

## 📂 Structure

```
homepage_email_scraper/
├── app.py              ← Streamlit UI v4.0.0 (unified)
├── scraper.py          ← Backend v2.1.0 (enhanced)
├── results/            ← Output folders (scraped_YYYYMMDD_HHMMSS/)
│   └── scraped_*/
│       ├── success_emails.csv       (deduplicated)
│       ├── failed_static.csv
│       ├── failed_dynamic.csv
│       ├── failed_other.csv
│       └── scraping_analytics.json
└── README.md           ← This file
```

## 🚀 Usage

### Option 1: Streamlit UI (Recommended)

```bash
streamlit run modules/scraping/homepage_email_scraper/app.py
# or
py -m streamlit run modules/scraping/homepage_email_scraper/app.py
```

**UI Features:**
- Upload CSV (auto-validates URLs)
- Configure all options in sidebar
- Watch real-time progress
- Browse historical results
- Download split output files
- View detailed analytics

### Option 2: CLI (Advanced)

```bash
python modules/scraping/homepage_email_scraper/scraper.py \
  --input input.csv \
  --website-column "Website" \
  --name-column "Company Name" \
  --workers 50 \
  --max-pages 5 \
  --scraping-mode deep_search \
  --email-format separate \
  --limit 100
```

**CLI Options:**
- `--input` - Input CSV path (required)
- `--website-column` - URL column name (default: 'website')
- `--name-column` - Name column (default: 'name', auto-generated if missing)
- `--workers` - Parallel workers (default: 50)
- `--max-pages` - Max pages to search (default: 5)
- `--scraping-mode` - `homepage_only` | `deep_search` (default: deep_search)
- `--email-format` - `separate` | `all` | `primary` (default: separate)
- `--no-emails` - Disable email extraction (content only)
- `--limit` - Process first N rows (testing)
- `--output` - Custom output directory

## 📊 Output Files

### 1. success_emails.csv
- Websites with emails found
- **Deduplicated** by email (keeps first)
- All original columns preserved + new columns:
  - `email` - Found email(s)
  - `homepage_content` - Cleaned text (15k max)
  - `site_type` - static | dynamic
  - `scrape_status` - success
  - `email_source` - homepage | deep_search
  - `error_message` - (empty)

### 2. failed_static.csv
- Static HTML sites without emails
- Includes full homepage content for manual review

### 3. failed_dynamic.csv
- Dynamic sites (React/Vue/Angular/etc) without emails
- May need browser-based scraping

### 4. failed_other.csv
- Connection errors, timeouts, invalid responses
- Check error_message column for details

### 5. scraping_analytics.json
```json
{
  "summary": {
    "total_sites": 1000,
    "success_rate": "73.74%",
    "duration_minutes": 3.5,
    "sites_per_second": 7.6
  },
  "results": {
    "success": {
      "count": 737,
      "total_emails": 1245,
      "from_homepage": 980,
      "from_deep_search": 265
    },
    "failed": {
      "static_no_email": 156,
      "dynamic_no_email": 89,
      "other_errors": 18
    }
  },
  "site_types": {
    "static": 893,
    "dynamic": 107
  }
}
```

## ⚡ Performance

- **Speed**: ~5-10 sites/second (depends on network/website speed)
- **Success Rate**: 70-75% (on quality lead lists)
- **Parallel Workers**: Up to 100 concurrent requests
- **No Cost**: Pure HTTP scraping, no AI APIs
- **Memory**: ~200MB for 10k sites

## 🔧 Dependencies

### Required
- `pandas` - CSV processing
- `streamlit` - Web UI
- Python 3.8+ (tested on 3.12)

### Shared Libraries (internal)
- `modules/scraping/lib/http_utils.py` - HTTP client with retry
- `modules/scraping/lib/text_utils.py` - Email extraction & cleaning
- `modules/scraping/lib/sitemap_utils.py` - Smart page discovery
- `modules/logging/shared/universal_logger.py` - Structured logging

## 📝 Version History

### v4.0.0 (2025-11-19) - Unified Release
- ✅ Merged best features from v1.0.0 and v3.0.0
- ✅ Live progress tracking via subprocess
- ✅ URL validation before processing
- ✅ Flexible column selection
- ✅ 3 email output formats
- ✅ Email extraction toggle
- ✅ Preserves all original columns
- ✅ Enhanced CLI with all options
- ✅ Automatic deduplication

### v2.0.0 (2025-11-18) - Multi-page Fallback
- Added deep search (contact/about/team pages)
- 4 split output files
- JSON analytics
- Site type detection

### v1.0.0 (2025-11-18) - Initial Release
- Basic homepage scraping
- Email extraction
- Simple Streamlit UI
