# Logging Module

Centralized logging system for Cold Outreach Automation Platform

## Overview

Universal logging module providing structured JSON logging for:
- Python scripts (modules/*)
- FastAPI backend
- Next.js frontend

All logs stored in `modules/logging/logs/` with automatic daily rotation.

## Features

- **Daily log rotation** - automatic file creation per day (YYYY-MM-DD.log)
- **Separate error logs** - errors duplicated to `logs/errors/` for quick debugging
- **JSON structured logs** - easy parsing and analysis
- **Multiple log levels** - ERROR, WARNING, INFO, DEBUG
- **Performance tracking** - @auto_log decorator for function timing
- **Zero maintenance** - no manual file management required
- **Modular architecture** - self-contained in logging module

## Quick Start

### Python Scripts

```python
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# Basic logging
logger.info("Script started", lead_count=100)
logger.warning("Rate limit approaching", remaining=5)
logger.error("API failed", error=e, status_code=500)
logger.debug("Processing batch", batch_id=3)
```

### Performance Tracking

```python
from modules.logging.shared.universal_logger import auto_log

@auto_log
def process_leads(leads):
    # Function automatically logged with duration
    return results
```

### FastAPI Backend

```python
from modules.logging.shared.universal_logger import get_logger

logger = get_logger("backend")

@app.get("/api/data")
async def get_data():
    logger.info("API request received", endpoint="/api/data")
    # Process request
    logger.info("API response sent", status=200)
```

## Log Format

Each log entry is a single-line JSON object:

```json
{
  "timestamp": "2025-10-04T17:49:12.021736",
  "module": "apollo_lead_collector",
  "level": "ERROR",
  "message": "API call failed",
  "status_code": 500,
  "endpoint": "/api/leads"
}
```

## File Structure

```
modules/logging/
├── logs/                    # All logs stored here
│   ├── 2025-10-04.log      # Daily combined log
│   └── errors/
│       └── 2025-10-04.log  # Daily errors only
├── shared/
│   └── universal_logger.py  # Main logger implementation
├── tests/
│   └── test_logger.py       # Integration tests
└── docs/
    └── usage-examples.md    # Detailed examples
```

## Viewing Logs

### VS Code
```bash
code modules/logging/logs/2025-10-04.log
```

### Search for errors
```bash
grep "ERROR" modules/logging/logs/2025-10-04.log
```

### Real-time monitoring (PowerShell)
```powershell
Get-Content modules/logging/logs/2025-10-04.log -Wait
```

## Migration from Old Logger

Old `modules/shared/logger.py` is replaced by this module.

**Before:**
```python
from modules.shared.logger import auto_log
```

**After:**
```python
from modules.logging.shared.universal_logger import auto_log, get_logger
```

## API Reference

### get_logger(module_name: str)
Get or create logger instance for a module.

### logger.info(message, **kwargs)
Log informational message with optional extra fields.

### logger.error(message, error=None, **kwargs)
Log error with optional exception and extra fields.

### logger.warning(message, **kwargs)
Log warning message.

### logger.debug(message, **kwargs)
Log debug message (for development).

### @auto_log
Decorator for automatic function performance logging.

## Version

- **Current:** 1.0.0
- **Created:** 2025-10-04
- **Status:** Production Ready
