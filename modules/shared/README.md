# Shared Module

**Priority:** High (Foundation)
**Status:** Production Ready
**Used In:** All modules (cross-cutting utilities)

---

## Quick Info

**Purpose:** Common utilities and shared functionality across all modules

**Scripts:** 2 core utilities
**Dependencies:** None (foundation layer)

---

## Utilities

### logger.py
**Purpose:** Auto-logging decorator for all scripts
**Features:**
- @auto_log decorator for automatic logging
- Performance tracking (execution time)
- Cost calculation (API usage)
- Session analytics
- JSON log output

**Usage:**
```python
from modules.shared.logger import auto_log

@auto_log
def process_leads(csv_path):
    # Your function code
    pass
```

**Output:** `data/logs/SCRIPT_NAME_YYYYMMDD_HHMMSS.json`

**Benefits:**
- Consistent logging across all scripts
- Zero-config performance tracking
- Automatic cost monitoring
- Session history preservation

---

### google_sheets.py
**Purpose:** Google Sheets integration client
**Features:**
- Batch read/write operations
- Data validation and cleaning
- OAuth 2.0 authentication
- Error handling and retry logic
- Rate limiting compliance

**Usage:**
```python
from modules.shared.google_sheets import GoogleSheetsClient

client = GoogleSheetsClient()
data = client.read_sheet(sheet_id, range_name)
client.write_sheet(sheet_id, range_name, data)
```

**Configuration:**
- Credentials file: Root directory (credentials.json)
- API quotas: Automatic rate limiting

---

## Data Structure

```
modules/shared/
├── logger.py                   # Auto-logging decorator
├── google_sheets.py            # Sheets client
└── README.md                   # This file
```

---

## Integration

**Used By:**
- **All modules** - logger.py for performance tracking
- modules/sheets/ - google_sheets.py for operations
- backend/ - Shared utilities

**Architecture:**
- Foundation layer (Level 2)
- Zero external dependencies
- Cross-module compatibility

---

## Configuration

**Logger Configuration:**
- Automatic - no setup required
- Logs saved to: `data/logs/`
- JSON format for easy parsing

**Google Sheets Configuration:**
- credentials.json in root
- OAuth 2.0 flow on first use
- Token refresh automatic

---

## Performance Metrics

**Logger Overhead:**
- <1ms per function call
- Minimal performance impact
- JSON serialization optimized

**Sheets Client:**
- Batch operations for efficiency
- Rate limiting built-in
- Retry logic for reliability

---

## Best Practices

**Using @auto_log:**
```python
@auto_log
def your_function():
    # Automatically logs:
    # - Execution time
    # - Input parameters
    # - Output results
    # - Errors and exceptions
    pass
```

**Using Google Sheets Client:**
```python
# Batch operations
client.batch_read([sheet1, sheet2])
client.batch_write(data_dict)

# Automatic backups
client.write_with_backup(sheet_id, data)
```

---

## Documentation

**Related ADRs:**
- None (foundation utilities)

**Used In:**
- All production scripts
- Backend services
- Data processing pipelines

**Maintenance:**
- Regular updates with Python version
- API compatibility checks
- Performance optimization

---

**Last Updated:** 2025-10-03
