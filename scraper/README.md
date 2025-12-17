# Simple Web Scraper with AI Summary

**Stupid simple scraper**: Homepage → Markdown → OpenAI Summary → CSV

Maximum flexibility, minimum complexity.

---

## Quick Start (3 Steps)

### 1. Prepare Input CSV

Place your CSV file in `scraper/input/` folder.

**Requirements:**
- Must have a `website` column with URLs
- URLs can be with or without `https://` prefix

**Example CSV:**
```csv
company_name,website,industry
Acme Corp,acme.com,SaaS
TechStart,https://techstart.io,AI
```

### 2. Configure (Optional)

Edit `scraper.py` CONFIG section if needed:

```python
CONFIG = {
    "INPUT_FILE": "scraper/input/input.csv",  # Your input file
    "TEST_MODE": True,  # Process only 10 rows (testing)
    "HOMEPAGE_ONLY": True,  # Only scrape homepage
    "AI_PROCESSING": True,  # Generate AI summaries
    "OPENAI_MODEL": "gpt-4o-mini",  # Cheap and fast
    "AI_PROMPT": "Your custom prompt here...",  # Customize analysis
}
```

**Default Settings (No Config Needed):**
- ✅ Test mode: 10 rows
- ✅ Homepage only (fast)
- ✅ AI summaries enabled
- ✅ Markdown text extraction
- ✅ 6000 words limit (fits in GPT context)

### 3. Run Scraper

```bash
python scraper/scraper.py
```

**Output:**
- Saved to `scraper/results/scraped_YYYYMMDD_HHMMSS.csv`
- Includes original columns + `ai_summary` column

---

## Features

### 🚀 Super Simple
- **No CLI arguments** - just edit CONFIG and run
- **No external config files** - everything embedded
- **Automatic URL normalization** - works with or without `https://`

### 📝 Smart Text Extraction
- **Markdown format** - preserves structure (headers, lists, links)
- **Auto-cleanup** - removes scripts, styles, nav, footer
- **Token limit** - truncates to 6000 words (~8K tokens for GPT)

### 🤖 Flexible AI Summaries
- **Customizable prompt** - edit `AI_PROMPT` in CONFIG
- **No structured output** - pure text summaries
- **Maximum flexibility** - analyze any website aspect you need

### ⚡ Performance
- **Fast model** - `gpt-4o-mini` (cheap and quick)
- **Rate limiting** - respects API limits
- **Progress tracking** - see status in real-time
- **Error handling** - continues on failures

---

## Configuration Options

### Input/Output
```python
"INPUT_FILE": "scraper/input/input.csv",
"WEBSITE_COLUMN": "website",  # Column with URLs
"OUTPUT_DIR": "scraper/results",
```

### Scraping
```python
"TEST_MODE": True,  # Only process 10 rows
"TEST_ROWS": 10,
"HOMEPAGE_ONLY": True,  # No deep search
"TIMEOUT": 10,  # Request timeout (seconds)
```

### Text Extraction
```python
"TEXT_FORMAT": "markdown",  # or "plain_text"
"MAX_WORDS": 6000,  # Truncate long pages
```

### AI Processing
```python
"AI_PROCESSING": True,  # Enable AI summaries
"OPENAI_MODEL": "gpt-4o-mini",  # Model to use
"AI_PROMPT": """Your custom prompt here...""",
```

### Rate Limiting
```python
"DELAY_BETWEEN_REQUESTS": 0.5,  # Scraping delay
"DELAY_BETWEEN_AI_CALLS": 0.2,  # OpenAI API delay
```

### Output Columns
```python
"ADD_SUMMARY_COLUMN": True,  # Include 'ai_summary' column
"ADD_CONTENT_COLUMN": False,  # Include 'scraped_content' (large!)
```

---

## Custom AI Prompts

### Example 1: Competitor Analysis
```python
"AI_PROMPT": """Analyze this competitor's website.

Focus on:
- Their main products/services
- Pricing strategy (if visible)
- Target audience
- Unique selling points
- Technology stack used

Be concise but thorough."""
```

### Example 2: Lead Qualification
```python
"AI_PROMPT": """Determine if this company is a good sales lead.

Evaluate:
- Company size indicators
- Industry and market
- Technology sophistication
- Budget indicators
- Decision maker contact info

Output: Qualified/Not Qualified + reasoning."""
```

### Example 3: Content Extraction
```python
"AI_PROMPT": """Extract key facts from this website.

Find and list:
- Company description
- Main products/services
- Target customers
- Contact information
- Key personnel mentioned

Format as bullet points."""
```

---

## Output Format

**Original columns preserved** + new columns:

| Column | Description |
|--------|-------------|
| `ai_summary` | AI-generated summary (always included) |
| `scrape_status` | Status: `success`, `scrape_failed`, `ai_failed`, `no_url` |
| `scraped_content` | Full markdown text (optional, set `ADD_CONTENT_COLUMN: True`) |

**Example output:**
```csv
company_name,website,ai_summary,scrape_status
Acme Corp,acme.com,"Acme is a SaaS platform for...",success
TechStart,techstart.io,"TechStart provides AI solutions...",success
```

---

## Troubleshooting

### Error: "OPENAI_API_KEY not found"
**Solution:** Add OpenAI API key to `.env` file in project root:
```bash
OPENAI_API_KEY=sk-proj-...
```

### Error: "Column 'website' not found"
**Solution:** Either:
1. Rename your column to `website`, OR
2. Update CONFIG: `"WEBSITE_COLUMN": "your_column_name"`

### Error: "Timeout scraping URL"
**Solution:** Increase timeout in CONFIG:
```python
"TIMEOUT": 30,  # Increase to 30 seconds
```

### Too expensive OpenAI costs?
**Solution 1:** Use test mode (10 rows only):
```python
"TEST_MODE": True,
```

**Solution 2:** Disable AI processing (scrape only):
```python
"AI_PROCESSING": False,
```

---

## Production Mode

When ready for full processing:

1. **Disable test mode:**
```python
"TEST_MODE": False,
```

2. **Run full dataset:**
```bash
python scraper/scraper.py
```

3. **Monitor progress:**
- Watch console output for real-time status
- Check `data/logs/` for detailed logs

---

## Dependencies

**Required packages:**
```bash
pip install requests beautifulsoup4 html2text openai pandas python-dotenv
```

**Already installed** if using this project's environment.

---

## Performance Estimates

**Test Mode (10 rows):**
- Scraping: ~5-10 seconds
- AI Processing: ~10-20 seconds
- **Total:** ~30 seconds
- **Cost:** ~$0.01 (gpt-4o-mini)

**Production (1000 rows):**
- Scraping: ~8-15 minutes
- AI Processing: ~15-30 minutes
- **Total:** ~30-45 minutes
- **Cost:** ~$1.00 (gpt-4o-mini)

---

## Advanced Usage

### Disable AI Summaries (Scrape Only)
```python
"AI_PROCESSING": False,
```

### Keep Full Content for Manual Review
```python
"ADD_CONTENT_COLUMN": True,
```

### Use More Powerful Model
```python
"OPENAI_MODEL": "gpt-4-turbo",  # Better quality, higher cost
```

### Process Specific Rows
Edit your input CSV to include only desired rows before running.

---

## File Structure

```
scraper/
├── scraper.py          # Main script
├── input/              # Place your CSV files here
│   └── input.csv       # Your input file
├── results/            # Output CSVs saved here
│   └── scraped_YYYYMMDD_HHMMSS.csv
└── README.md           # This file
```

---

## Tips

✅ **Start with test mode** - verify prompt works before full run
✅ **Customize the prompt** - tailor analysis to your specific needs
✅ **Monitor costs** - gpt-4o-mini is cheap but costs add up at scale
✅ **Check scrape_status** - filter successful rows for analysis
✅ **Iterate on prompts** - run small batches to refine your prompt

---

## Support

**Issues?**
1. Check `.env` file has `OPENAI_API_KEY`
2. Verify input CSV has `website` column
3. Check logs in `data/logs/` folder
4. Try test mode first (10 rows)

**Questions?**
Read the CONFIG section comments in `scraper.py` - everything is documented!

---

**Built with ❤️ for maximum simplicity and flexibility**
