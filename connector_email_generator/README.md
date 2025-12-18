# Connector Email Generator

Generate high-status connector-style cold emails using AI based on SSM SOP methodology.

## Features

- **4 Deduplicated Prompts** - Company-Based, Market Conversations, Daily Spine, Deal-Flow Movement
- **Rotation Framework** - 5 opener variations to avoid market fatigue
- **Auto-detect CSV Fields** - Smart column mapping with fallback patterns
- **Variable Extraction** - Automatically extracts dreamICP, painTheySolve, etc.
- **Email Assembly** - Prefix + AI output + Suffix with customizable structure
- **Follow-up Generation** - Automatic Follow-Up #1 and #2 from SOP
- **Validation** - Corporate speak detection (optimize, solutions, leverage, etc.)
- **Batch Processing** - Process multiple leads with retry logic
- **Streamlit UI** - Interactive web interface for easy configuration

## Installation

### 1. Install Dependencies

```bash
pip install openai pandas python-dotenv streamlit
```

### 2. Configure OpenAI API Key

Create `.env` file in project root:

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Prepare CSV File

Place your leads CSV in `data/input/leads.csv`

**Supported column names (auto-detected):**
- FirstName, First Name, first_name, fname
- Company, CompanyName, company
- Title, Job Title, Position
- Description, Company Description
- Industry, Vertical, Sector
- Company Size, Employees, Size
- Revenue, Annual Revenue, ARR

## Usage

### Method 1: Streamlit UI (Recommended)

```bash
cd connector_email_generator
streamlit run streamlit_app.py
```

**Streamlit features:**
- Upload CSV directly
- Visual prompt selection
- Live field mapping preview
- Rotation opener selection
- Custom email prefix/suffix
- Download results instantly

### Method 2: Python Script

```bash
cd connector_email_generator
python scripts/generator.py
```

**Configure in `scripts/generator.py`:**

```python
CONFIG = {
    "INPUT_CSV": "data/input/leads.csv",
    "PROMPT_ID": 3,  # 1-4
    "ROTATION_KEY": "curating_matches",  # Optional for Prompt 3
    "EMAIL_STRUCTURE": {
        "prefix": "Hey {first_name}—\n\n",
        "use_ai_output": True,
        "suffix": "\n\nWorth intro'eing you?\n\nBest,",
    },
    "EXTRACT_VARIABLES": True,
    "GENERATE_FOLLOWUPS": True,
    "OPENAI_MODEL": "gpt-4o",
    "SKIP_ROWS": 0,
    "LIMIT_ROWS": None,  # None = all rows
    "DRY_RUN": False,
}
```

## Prompts Overview

### Prompt 1: Company-Based Connector Insight
**Output format:**
```
Noticed [company] helps [job_titles] at [company_type] — I know a few who [pain_description].
```

**Example:**
```
Noticed Summit Capital helps CEOs and CFOs at mid-market manufacturing companies — I know a few who can't find buyers when they're ready to exit.
```

**Variables extracted:**
- clean_company_name
- job_titles
- company_type
- pain_description

---

### Prompt 2: Market Conversations Insight
**Output format:**
```
Figured I'd reach out — I talk to a lot of [dreamICP] and they keep saying they [painTheySolve].
Thought you two should connect.
```

**Example:**
```
Figured I'd reach out — I talk to a lot of CEOs in mid-market manufacturing and they keep saying they can't find buyers who actually understand their space.
Thought you two should connect.
```

**Variables extracted:**
- dreamICP
- painTheySolve

---

### Prompt 3: Daily Spine (with Rotation)
**Output format:**
```
Figured I'd reach out — I'm around [dreamICP] daily and they keep saying they [painTheySolve].
```

**Example:**
```
Figured I'd reach out — I'm around CEOs in mid-market manufacturing daily and they keep saying they can't find buyers who actually understand their space.
```

**Rotation Openers:**
- `been_mapping` - "Been mapping some signals lately —"
- `saw_movement` - "Saw some movement on my side —"
- `name_came_up` - "Your name came up on my end —"
- `curating_matches` - "Been curating a few matches this week —"
- `got_signal` - "Got a signal that fits you —"

**Usage:**
```python
"PROMPT_ID": 3,
"ROTATION_KEY": "curating_matches",  # Optional
```

**Variables extracted:**
- dreamICP
- painTheySolve

---

### Prompt 4: Deal-Flow Movement
**Output format:**
```
Saw some movement on my side —
Figured I'd reach out — I'm around [dreamICP] daily and they keep saying they [painTheySolve].
Can plug you into the deal flow if you want.
```

**Example:**
```
Saw some movement on my side —
Figured I'd reach out — I'm around CEOs in mid-market manufacturing daily and they keep saying they can't find buyers who actually understand their operations.
Can plug you into the deal flow if you want.
```

**Variables extracted:**
- dreamICP
- painTheySolve

---

## Output Structure

Generated CSV includes:

| Column | Description |
|--------|-------------|
| `AI_Icebreaker` | Raw AI output (icebreaker only) |
| `Final_Email` | Assembled email (prefix + AI + suffix) |
| `dreamICP` | Extracted ICP group (e.g., "CEOs in SaaS") |
| `painTheySolve` | Extracted pain point |
| `clean_company_name` | Company name without LLC/Inc |
| `job_titles` | Extracted job titles |
| `company_type` | Company type description |
| `pain_description` | Pain description |
| `FollowUp_1` | "Hey {first_name}, worth intro'ing you?" |
| `FollowUp_2` | Final follow-up |
| `Is_Valid` | Boolean validation flag |
| `Issues` | Validation issues (corporate speak, etc.) |
| `Tokens_Used` | OpenAI tokens consumed |

## Rotation Framework

**Purpose:** Avoid market fatigue by rotating opener lines while keeping core message identical.

**How it works:**
1. Select Prompt 3 (Daily Spine)
2. Choose rotation opener (or use default)
3. Core spine remains same: "I'm around [dreamICP] daily and they keep saying..."
4. Only opener rotates for variety

**Rotation frequency recommendations:**
- Change every 500-1000 emails
- Track market response rates
- A/B test different openers

## Validation Rules

**Automatic checks:**
- Corporate speak detection (optimize, solutions, leverage, streamline, platform, synergy)
- Insufficient data detection (when AI returns "INSUFFICIENT_DATA")
- Output format validation

**If validation fails:**
- `Is_Valid` = False
- `Issues` column shows specific problems
- Email still generated (review manually)

## Advanced Configuration

### Custom Field Mapping

Add custom column names to `FIELD_MAPPING` in `generator.py`:

```python
"FIELD_MAPPING": {
    "first_name": ["FirstName", "First Name", "fname", "YourCustomColumn"],
    "company_name": ["Company", "CompanyName", "CustomCompanyField"],
    # Add more...
}
```

### Custom Email Structure

**Minimal (AI only):**
```python
"EMAIL_STRUCTURE": {
    "prefix": "",
    "use_ai_output": True,
    "suffix": "",
}
```

**Full template:**
```python
"EMAIL_STRUCTURE": {
    "prefix": "Hey {first_name}—\n\nQuick note:\n\n",
    "use_ai_output": True,
    "suffix": "\n\nWorth intro'eing you?\n\nBest,\nYour Name",
}
```

### Batch Processing Options

```python
"SKIP_ROWS": 100,      # Start from row 100
"LIMIT_ROWS": 50,      # Process only 50 rows
"BATCH_SIZE": 5,       # API calls per batch
"RETRY_ATTEMPTS": 3,   # Retry failed API calls
"DRY_RUN": True,       # Test without API calls
```

## Follow-Ups

**Follow-Up #1** (minimal, high-status):
```
Hey {first_name}, worth intro'ing you?
```

**Follow-Up #2** (clean exit):
```
Hey {first_name}, maybe this isn't something you're interested in — wishing you the best.
```

**Usage:**
- Send Follow-Up #1 after 3-5 days
- Send Follow-Up #2 after 7-10 days
- Never send more than 2 follow-ups

## Troubleshooting

### Error: OPENAI_API_KEY not found
```bash
# Add to .env file
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Error: Input file not found
```bash
# Place CSV in correct location
cp your-leads.csv connector_email_generator/data/input/leads.csv
```

### Error: Column not found
- Check CSV column names
- Add custom column to `FIELD_MAPPING`
- Use Streamlit UI to preview field mapping

### Corporate speak detected
- Review AI output in `Issues` column
- Adjust prompt or input data
- Forbidden words: optimize, solution, leverage, streamline, platform, synergy

### Insufficient data
- AI couldn't generate from input data
- Check Description, Industry, Title fields
- Add more context to CSV

## File Structure

```
connector_email_generator/
├── data/
│   └── input/              # Place CSV files here
│       └── leads.csv
├── results/                # Generated outputs
│   └── connector_emails_*.csv
├── scripts/
│   └── generator.py        # Main processing script
├── prompts.py              # Prompt library
├── streamlit_app.py        # Web UI
└── README.md               # This file
```

## Best Practices

1. **Test with small batches first** - Use `LIMIT_ROWS: 10` for testing
2. **Review validation flags** - Check `Is_Valid` and `Issues` columns
3. **Rotate openers regularly** - Avoid market fatigue
4. **Monitor corporate speak** - Adjust prompts if frequently detected
5. **Use DRY_RUN** - Test configuration without API costs
6. **A/B test prompts** - Track response rates by prompt type
7. **Clean your data** - Better inputs = better outputs

## Cost Estimation

**GPT-4o pricing (as of Jan 2025):**
- ~500-1000 tokens per email
- ~$0.005-$0.01 per email
- 1000 emails ≈ $5-$10

**Tips to reduce costs:**
- Use `gpt-3.5-turbo` for testing
- Set `MAX_TOKENS: 1000` (lower limit)
- Use `DRY_RUN` for configuration testing
- Process in batches to monitor costs

## Support

For issues or questions:
1. Check Troubleshooting section
2. Review CLAUDE.md guidelines
3. Check OpenAI API status
4. Review generated logs in console

## Version History

**v1.0.0** (2025-01-19)
- Initial release
- 4 deduplicated prompts
- Rotation framework
- Streamlit UI
- Variable extraction
- Follow-up generation
