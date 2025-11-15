# Instantly Module

Integration with Instantly.ai for cold email outreach automation.

## Overview

This module provides tools to upload leads from CSV files to Instantly campaigns via API, with full support for custom variables and multi-step sequences.

## Directory Structure

```
modules/instantly/
├── scripts/              # Executable Python scripts
│   ├── upload_csv_to_campaign.py       # Main upload script
│   ├── test_instantly_connection.py    # API connection tester
│   ├── upload_to_instantly.bat         # Windows quick launcher
│   └── test_connection.bat             # Windows test launcher
├── docs/                 # Documentation
│   ├── CSV_UPLOAD_GUIDE.md             # Detailed upload guide (EN)
│   └── QUICK_START_RU.md               # Quick start guide (RU)
├── results/              # Upload results (JSON)
└── requirements.txt      # Python dependencies
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r modules/instantly/requirements.txt
```

### 2. Get API Credentials

**API Key:**
- Go to Instantly.ai → Settings → API
- Copy your API key

**Campaign ID:**
- Open your campaign in Instantly
- Get ID from URL: `https://app.instantly.ai/app/campaigns/[CAMPAIGN_ID]`

### 3. Test Connection (Recommended)

**Option A - Windows:**
Double-click: `modules/instantly/scripts/test_connection.bat`

**Option B - Python:**
```bash
python modules/instantly/scripts/test_instantly_connection.py
```

Edit the script first to add your API key.

### 4. Upload CSV

**Option A - Windows:**
1. Edit `upload_csv_to_campaign.py` - add API key and Campaign ID
2. Double-click: `upload_to_instantly.bat`

**Option B - Python:**
```bash
python modules/instantly/scripts/upload_csv_to_campaign.py
```

## Scripts

### upload_csv_to_campaign.py

Main script for uploading CSV leads to Instantly campaign.

**Features:**
- Reads CSV with custom structure
- Maps all columns to Instantly custom variables
- Cleans email addresses (removes artifacts)
- Validates email format
- Bulk upload via API
- Saves results to JSON

**Configuration:**
```python
CONFIG = {
    "API": {
        "api_key": "your-api-key",
    },
    "CAMPAIGN": {
        "campaign_id": "your-campaign-id",
    },
    "INPUT": {
        "csv_path": r"path\to\your\file.csv",
    }
}
```

**CSV Structure:**
- Required: `email` column
- Optional standard fields: `name`, `website`, `phone`, etc.
- Custom variables: Any other columns become `{{Custom_Variables}}`

**Output:**
Results saved to: `modules/instantly/results/upload_campaign_YYYYMMDD_HHMMSS.json`

### test_instantly_connection.py

Quick tester to verify API credentials and campaign access.

**Tests:**
1. API key validity
2. Campaign access (if ID provided)
3. Lists all available campaigns

**Usage:**
1. Set `API_KEY` in the script
2. Optional: Set `CAMPAIGN_ID`
3. Run script
4. Check output for campaign list

## CSV Format

### Required Column
- `email` - Email address (must be first column)

### Standard Fields (Optional)
- `name` - Lead/company name
- `website` - Website URL
- `phone` - Phone number
- `location` - Location/city
- `company_name` - Company name
- `first_name` - First name
- `last_name` - Last name
- `job_title` - Job title

### Custom Variables (Optional)
Any additional columns become custom variables in Instantly.

Example custom columns:
- `subject_line` - Email subject
- `email_1` - Step 1 email body
- `email_2` - Step 2 email body
- `email_3` - Step 3 email body
- `language` - Email language
- `icebreaker` - Personalization line
- `industry` - Industry
- `company_size` - Company size

**Important:**
- Column names: Start with capital letter, max 20 chars
- No spaces in names: Use `Company_Name` not `Company Name`
- Max 50 custom variables per campaign
- UTF-8 encoding required

### Example CSV

```csv
email,name,website,subject_line,email_1,email_2,email_3,language
john@acme.com,Acme Corp,acme.com,Quick question,Hey John...,Following up...,Final touch...,en
marie@example.fr,Example SA,example.fr,Question rapide,Bonjour Marie...,Relance...,Dernier message...,fr
```

## Using Variables in Instantly

After upload, use custom variables in sequence steps:

### Step 1
- Subject: `{{Subject_Line}}`
- Body: `{{Email_1}}`
- Wait: 0 days

### Step 2
- Subject: (empty - continues thread)
- Body: `{{Email_2}}`
- Wait: 3 days

### Step 3
- Subject: (empty - continues thread)
- Body: `{{Email_3}}`
- Wait: 3 days

## Features

### Email Cleaning
Automatically removes common artifacts:
- `info@remove-this.museum.com` → `info@museum.com`
- `contact@museum.nliban` → `contact@museum.nl`

### Email Validation
Validates all emails before upload:
- Checks format: `user@domain.com`
- Skips invalid emails
- Reports skipped emails in results

### Multiline Support
Preserves line breaks in email content:
```
Hey {{Name}},

I noticed your recent expansion.

Best,
Leo
```

### Duplicate Handling
- `skip_if_in_workspace`: Skip if email exists anywhere in workspace
- `skip_if_in_campaign`: Skip if email already in this campaign

## API Endpoints Used

- `POST /v2/leads/bulk` - Bulk upload leads
- `GET /v2/workspace` - Get workspace info
- `GET /v2/campaign/{id}` - Get campaign details
- `GET /v2/campaign/list` - List all campaigns

## Results

Upload results saved as JSON:

```json
{
  "timestamp": "2025-11-15T15:30:00",
  "stats": {
    "total_processed": 100,
    "successful_uploads": 95,
    "skipped_invalid": 5,
    "execution_time": 3.45
  },
  "api_response": {...},
  "uploaded_leads": [...]
}
```

## Error Handling

### Common Errors

**"API key not configured"**
→ Set API key in script config

**"Campaign ID not configured"**
→ Set campaign ID in script config

**"401 Unauthorized"**
→ Invalid API key - get new one from Instantly

**"404 Not Found"**
→ Campaign ID incorrect - check URL

**"No valid leads to upload"**
→ CSV has no valid emails in `email` column

### Debugging

1. Check terminal output for errors
2. Review results JSON file for details
3. Run test_instantly_connection.py first
4. Verify CSV encoding (UTF-8)
5. Check logs in universal logger output

## Best Practices

### Before Upload
1. ✅ Test with 5-10 leads first
2. ✅ Verify CSV encoding (UTF-8)
3. ✅ Check email column is named `email`
4. ✅ Validate email addresses
5. ✅ Test API connection first

### Campaign Setup
1. 📧 One campaign per language
2. 🎯 Use descriptive variable names
3. 📝 Preserve line breaks in emails
4. 🔄 Use subsequences for segmentation
5. 📊 Monitor results in Instantly

### CSV Preparation
1. Remove duplicate emails
2. Clean email addresses
3. Validate all required fields
4. Use consistent column naming
5. Test with small batch first

## Documentation

- **Quick Start (Russian):** `docs/QUICK_START_RU.md`
- **Full Guide (English):** `docs/CSV_UPLOAD_GUIDE.md`

## Dependencies

- `requests` - HTTP requests to Instantly API
- `pandas` - CSV processing
- `python-dotenv` - Environment variables
- Custom: `universal_logger` - Structured logging

## Support

For issues:
1. Check script output and error messages
2. Review results JSON file
3. Verify API credentials
4. Check CSV format and encoding
5. Run connection test first

## License

Internal use only - Part of Cold Outreach Automation Platform
