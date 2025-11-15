# CSV Upload to Instantly Campaign - Guide

## Overview

Upload leads from CSV file to Instantly campaign with all custom variables mapped automatically.

## Quick Start

### 1. Get Your API Credentials

**Get API Key:**
1. Go to Instantly.ai → Settings → API
2. Copy your API key

**Get Campaign ID:**
1. Open your campaign in Instantly
2. Look at URL: `https://app.instantly.ai/app/campaigns/[CAMPAIGN_ID]`
3. Copy the campaign ID from URL

### 2. Configure the Script

Open `modules/instantly/scripts/upload_csv_to_campaign.py` and set:

```python
CONFIG = {
    "API": {
        "api_key": "your-api-key-here",  # Your Instantly API key
    },
    "CAMPAIGN": {
        "campaign_id": "your-campaign-id-here",  # Your campaign ID
    },
    "INPUT": {
        "csv_path": r"path\to\your\file.csv",  # Path to your CSV
    }
}
```

### 3. Run the Script

```bash
python modules/instantly/scripts/upload_csv_to_campaign.py
```

## CSV Structure

The script expects CSV with these columns:

### Required:
- `email` - Email address (REQUIRED)

### Standard fields:
- `name` - Lead name
- `website` - Website URL

### Custom variables (all optional):
- `short_museum_name` - Short name for personalization
- `specific_section` - Specific section/department
- `subject_line` - Email subject line
- `email_1` - Text for Step 1
- `email_2` - Text for Step 2
- `email_3` - Text for Step 3
- `language` - Email language
- `summary` - Organization summary
- `focus_wars` - Focus area
- `focus_periods` - Time periods

## How It Works

### Step 1: Script reads your CSV
```
name,email,website,subject_line,email_1,email_2,email_3
Museum A,info@museum.com,museum.com,Quick question,Hey...,Follow up...,Final...
```

### Step 2: Maps to Instantly format
```json
{
  "email": "info@museum.com",
  "name": "Museum A",
  "website": "museum.com",
  "custom_variables": {
    "Subject_Line": "Quick question",
    "Email_1": "Hey...",
    "Email_2": "Follow up...",
    "Email_3": "Final..."
  }
}
```

### Step 3: Uploads via API
All leads uploaded to your campaign with custom variables.

### Step 4: Use in Instantly UI

Create your sequence steps in Instantly:

**Step 1:**
- Subject: `{{Subject_Line}}`
- Body: `{{Email_1}}`

**Step 2:**
- Subject: (leave empty to continue thread)
- Body: `{{Email_2}}`

**Step 3:**
- Subject: (leave empty to continue thread)
- Body: `{{Email_3}}`

## Features

### Email Cleaning
Script automatically removes common artifacts:
- `info@remove-this.museum.com` → `info@museum.com`
- `contact@museum.nliban` → `contact@museum.nl`

### Email Validation
Validates all emails before upload - invalid emails are skipped.

### Multiline Support
Preserves line breaks in email content.

### Custom Variables
All CSV columns become available as `{{Variables}}` in Instantly.

## Output

Results saved to: `modules/instantly/results/upload_campaign_YYYYMMDD_HHMMSS.json`

Example output:
```json
{
  "timestamp": "2025-11-15T15:30:00",
  "stats": {
    "total_processed": 10,
    "successful_uploads": 9,
    "skipped_invalid": 1
  },
  "api_response": {...},
  "uploaded_leads": [...]
}
```

## Configuration Options

### API Settings
```python
"API": {
    "base_url": "https://api.instantly.ai/api/v2",
    "api_key": "",  # Your API key
    "timeout": 60   # Request timeout in seconds
}
```

### Campaign Settings
```python
"CAMPAIGN": {
    "campaign_id": "",  # Your campaign ID
    "skip_if_in_workspace": False,  # Skip if lead exists in workspace
    "skip_if_in_campaign": True     # Skip if lead exists in this campaign
}
```

### Processing Settings
```python
"PROCESSING": {
    "clean_emails": True,      # Remove email artifacts
    "validate_emails": True,   # Validate email format
    "batch_size": 100          # Leads per batch
}
```

## Troubleshooting

### Error: "API key not configured"
→ Set your API key in `CONFIG["API"]["api_key"]`

### Error: "Campaign ID not configured"
→ Set your campaign ID in `CONFIG["CAMPAIGN"]["campaign_id"]`

### Error: "No valid leads to upload"
→ Check your CSV has valid email addresses in the `email` column

### Error: "401 Unauthorized"
→ Your API key is invalid - get a new one from Instantly settings

### Error: "404 Not Found"
→ Campaign ID is wrong - check the campaign URL

## Examples

### Example 1: Basic Upload
```python
CONFIG = {
    "API": {"api_key": "xyz123"},
    "CAMPAIGN": {"campaign_id": "abc456"},
    "INPUT": {"csv_path": "leads.csv"}
}
```

### Example 2: Multiple Languages
CSV with language-specific content:
```csv
email,language,email_1,email_2,email_3
us@example.com,en,Hey there...,Following up...,Final touch...
fr@example.com,fr,Bonjour...,Je reviens vers vous...,Dernier message...
de@example.com,de,Hallo...,Nachfassen...,Letzte Nachricht...
```

Upload to ONE campaign, use `{{Email_1}}`, `{{Email_2}}`, `{{Email_3}}` in sequence steps.

### Example 3: Segmentation by Custom Variable
After upload, use Instantly's filtering:
- Filter by `{{Language}}` = "en" → Move to English subsequence
- Filter by `{{Language}}` = "fr" → Move to French subsequence

## Best Practices

1. **Test with small batch first** - Upload 5-10 leads to test
2. **One campaign per language** - Create separate campaigns for different languages
3. **Use descriptive variable names** - Clear names like `Icebreaker`, not `var1`
4. **Preserve line breaks** - They make emails more readable
5. **Validate before upload** - Script validates, but check your CSV first

## Next Steps After Upload

1. ✅ Leads uploaded with all custom variables
2. 📧 Create sequence steps in Instantly UI
3. 🎯 Use `{{Variable_Name}}` placeholders in email templates
4. 🚀 Launch campaign
5. 📊 Monitor results in Instantly analytics

## Support

For issues:
1. Check logs in terminal output
2. Check results JSON file for details
3. Verify API key and campaign ID
4. Check CSV encoding (should be UTF-8)
