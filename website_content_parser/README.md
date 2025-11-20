# Website Content Parser (OpenAI)

Extract business variables from website content using GPT-4o-mini.

## Features

- AI-powered content parsing with OpenAI GPT
- Parallel processing (up to 100 workers)
- Real-time progress tracking with ETA
- Customizable variables extraction
- Results history with analytics
- Cost estimation before running
- Auto-detection of content columns
- Batch processing with session state

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Access at:** http://localhost:8501

### Streamlit Cloud Deployment

1. **Push to GitHub:**
   ```bash
   git add website_content_parser/
   git commit -m "feat(parser): Add Website Content Parser deployment"
   git push
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Set main file path: `website_content_parser/app.py`
   - Add secret: `OPENAI_API_KEY` = your-api-key
   - Click "Deploy"

## Usage

### 1. Upload & Process Tab

1. **Upload CSV** with website content (from Homepage Scraper)
2. **Select columns:**
   - Content column (auto-detected by average length)
   - Company name column
3. **Customize variables** to extract (default 16 variables)
4. **Adjust settings:**
   - Model: `gpt-4o-mini` (recommended), `gpt-4o`, `gpt-3.5-turbo`
   - Workers: 1-100 (default 50)
   - Sample size or process all rows
5. **Review cost estimate**
6. **Click "Start Processing"**
7. **Download results** when complete

### 2. View Results Tab

- Browse all historical processing runs
- View analytics (duration, success rate, cost)
- Download previous results
- See settings used for each run

## CSV Format

Your CSV should have:
- **Company name column** (e.g., "name", "company")
- **Website content column** (e.g., "homepage_content", "website_content")

Recommended: Use Homepage Email Scraper first to collect website content.

## Default Variables Extracted

1. `owner_first_name` - Owner or founder's first name
2. `tagline` - Company tagline or slogan
3. `value_proposition` - Main value proposition
4. `guarantees` - Service guarantees offered
5. `certifications` - Certifications or licenses
6. `awards_badges` - Awards or badges displayed
7. `special_offers` - Special offers or promotions
8. `is_hiring` - Whether company is hiring
9. `hiring_roles` - Open positions if hiring
10. `is_family_owned` - Family-owned business indicator
11. `emergency_24_7` - 24/7 emergency service availability
12. `free_estimate` - Free estimate offering
13. `license_number` - License number if shown
14. `testimonial_snippet` - Short testimonial quote
15. `corporate_clients` - Corporate client mentions
16. `creative_insights` - Unique creative insights

All variables are fully customizable in the UI.

## Cost & Performance

- **Model:** GPT-4o-mini (~$0.002 per site)
- **Speed:** ~2 sites/second with 50 workers
- **Example:** 1000 sites = ~$2.00, ~8-10 minutes

## Results Storage

Results are saved in `results/` folder:

```
results/
├── parsed_20250120_143022/
│   ├── parsed_content.csv
│   └── analytics.json
├── parsed_20250120_145533/
│   ├── parsed_content.csv
│   └── analytics.json
```

Each run includes:
- **CSV:** Enriched data with extracted variables
- **Analytics:** Metadata (duration, success rate, cost, settings)

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)

## Tech Stack

- **UI:** Streamlit
- **AI:** OpenAI GPT-4o-mini
- **Data:** Pandas
- **Async:** ThreadPoolExecutor

## Version

**Version:** 2.0.0
**Last Updated:** 2025-11-20

## License

Private - Internal Tool
