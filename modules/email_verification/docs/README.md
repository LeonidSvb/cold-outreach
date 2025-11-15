# Email Verification Module

## Overview

Email verification module using [mails.so](https://mails.so) API to validate email addresses before sending cold outreach campaigns.

## Features

- **CSV Processing**: Automatic detection and processing of email columns
- **Comprehensive Checks**:
  - Email syntax validation
  - Domain DNS verification
  - SMTP mailbox verification
  - Disposable email detection
  - Free provider detection
- **Rate Limiting**: Built-in delays to respect API limits
- **Error Handling**: Graceful handling of API errors and timeouts
- **Detailed Results**: All verification data saved with original CSV data

## API Integration

**Provider**: [mails.so](https://mails.so/dashboard/api)

**Verification Checks**:
- `valid`: Overall email validity
- `deliverable`: Can email be delivered
- `smtp.valid`: SMTP server accepts email
- `dns.valid`: Domain exists
- `disposable`: Temporary email service
- `free`: Free email provider (Gmail, etc.)

## Usage

### Basic Usage

```bash
python modules/email_verification/scripts/verify_emails.py
```

### Configuration

Edit `CONFIG` section in `verify_emails.py`:

```python
CONFIG = {
    "API_KEY": "your-api-key-here",
    "INPUT_FILE": "path/to/your/emails.csv",
    "EMAIL_COLUMN": "email",  # Column name with emails
    "RATE_LIMIT_DELAY": 0.5,  # Seconds between requests
}
```

### Input Format

CSV file with at least one column containing email addresses:

```csv
name,email,website
Museum A,info@museum-a.com,https://museum-a.com
Museum B,contact@museum-b.org,https://museum-b.org
```

### Output Format

Same CSV with additional verification columns:

```csv
name,email,website,verification_status,is_valid,is_deliverable,smtp_check,domain_exists,is_disposable,is_free_provider,verification_error
Museum A,info@museum-a.com,https://museum-a.com,verified,true,true,true,true,false,false,
Museum B,invalid@fake.xyz,https://museum-b.org,verified,false,false,false,false,false,false,
```

## Results

All verification results saved to: `modules/email_verification/results/verified_emails_YYYYMMDD_HHMMSS.csv`

## Error Handling

- **Missing emails**: Marked as "missing" status
- **API errors**: Marked as "error" with error message
- **Timeouts**: Automatic retry logic (configurable)
- **Invalid responses**: Logged and marked as error

## Rate Limiting

Default: 0.5 seconds between requests (120 requests/minute)

Adjust `RATE_LIMIT_DELAY` in config for different API plan limits.

## Testing

Test with single email first:

```python
# In verify_emails.py, temporarily set:
CONFIG["INPUT_FILE"] = "test_email.csv"  # CSV with 1-2 emails
```

## API Costs

Check [mails.so pricing](https://mails.so/pricing) for current rates.

Monitor usage in dashboard: https://mails.so/dashboard/api

## Troubleshooting

**API Key Invalid**:
- Verify key in mails.so dashboard
- Check key format (UUID format expected)

**Rate Limit Exceeded**:
- Increase `RATE_LIMIT_DELAY`
- Check API plan limits

**Domain Not Found**:
- Expected for invalid domains
- Check `domain_exists` field in results

## Integration with Outreach Pipeline

1. **Generate emails** (OpenAI module)
2. **Verify emails** (this module)
3. **Filter valid only** (pandas/sheets)
4. **Send campaigns** (Instantly module)

## Version History

- v1.0.0 (2025-01-15): Initial release with mails.so API integration
