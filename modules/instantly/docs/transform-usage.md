# Instantly Transform Module - Usage Guide

## Overview
Module for transforming Instantly JSON data to Supabase RAW tables format.

## Functions

### `transform_campaigns(campaigns: List[Dict]) -> List[Dict]`
Transforms campaign data for `instantly_campaigns_raw` table.

**Input:** List of campaign dictionaries from Instantly API
**Output:** List of rows ready for Supabase insert

**Example:**
```python
from instantly_sources import load_from_json, extract_campaigns
from instantly_transform import transform_campaigns

# Load data
result = load_from_json('results/raw_data.json')
campaigns = extract_campaigns(result['data'])

# Transform
transformed = transform_campaigns(campaigns)

# Result ready for Supabase insert
# Each row has: instantly_campaign_id, campaign_name, campaign_status, leads_count, etc.
```

### `transform_accounts(accounts: List[Dict]) -> List[Dict]`
Transforms account data for `instantly_accounts_raw` table.

**Input:** List of account dictionaries from Instantly API
**Output:** List of rows ready for Supabase insert

### `transform_daily_analytics(daily: List[Dict], campaign_id: str = None) -> List[Dict]`
Transforms daily analytics for `instantly_daily_analytics_raw` table.

**Input:**
- `daily` - List of daily analytics dictionaries
- `campaign_id` - Optional campaign ID to link records to specific campaign

**Output:** List of rows ready for Supabase insert

### `validate_transformed_data(table: str, rows: List[Dict]) -> Dict`
Validates transformed data before upload to Supabase.

**Input:**
- `table` - Table name (e.g., 'instantly_campaigns_raw')
- `rows` - Transformed rows

**Output:** Dict with validation result
```python
{
    "valid": True,
    "rows_validated": 10
}
```

## Complete Example

```python
from instantly_sources import load_from_json, extract_campaigns, extract_accounts, extract_daily_analytics
from instantly_transform import transform_campaigns, transform_accounts, transform_daily_analytics, validate_transformed_data

# Load JSON
result = load_from_json('results/raw_data_20250921_125555.json')

# Extract data
campaigns = extract_campaigns(result['data'])
accounts = extract_accounts(result['data'])
daily = extract_daily_analytics(result['data'])

# Transform
campaigns_transformed = transform_campaigns(campaigns)
accounts_transformed = transform_accounts(accounts)
daily_transformed = transform_daily_analytics(daily)

# Validate before upload
campaigns_valid = validate_transformed_data('instantly_campaigns_raw', campaigns_transformed)
accounts_valid = validate_transformed_data('instantly_accounts_raw', accounts_transformed)
daily_valid = validate_transformed_data('instantly_daily_analytics_raw', daily_transformed)

# Now ready for Supabase insert via MCP tools
```

## Testing

Run unit test:
```bash
cd modules/instantly
python instantly_transform.py
```

Run integration test with real data:
```bash
cd modules/instantly
python test_transform_integration.py
```

## Next Steps
After transformation, use Supabase MCP tools to insert data:
- `mcp__supabase__execute_sql` for insert queries
- Or use proper sync service (TASK-009)
