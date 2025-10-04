# Logging Usage Examples

Comprehensive examples for different scenarios

## Basic Logging

### Simple Script

```python
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Script started")

    # Process data
    logger.debug("Loading CSV", filename="leads.csv")
    leads = load_csv("leads.csv")

    logger.info("CSV loaded", row_count=len(leads))

if __name__ == "__main__":
    main()
```

## Error Handling

### With Exception Details

```python
try:
    response = requests.get(api_url)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(
        "API request failed",
        error=e,
        url=api_url,
        status_code=getattr(e.response, 'status_code', None)
    )
    raise
```

### Custom Error Context

```python
if not api_key:
    logger.error(
        "Missing API key",
        config_file=".env",
        required_var="APOLLO_API_KEY"
    )
    sys.exit(1)
```

## Performance Tracking

### Function Decorator

```python
from modules.logging.shared.universal_logger import auto_log

@auto_log
def process_batch(leads):
    """This function will be automatically logged"""
    # Processing logic
    return results
```

**Logs:**
```json
{"module":"apollo","level":"DEBUG","message":"process_batch started"}
{"module":"apollo","level":"INFO","message":"process_batch completed","duration_seconds":2.34}
```

### Async Functions

```python
@auto_log
async def fetch_data(url):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

## API Integration Logging

### FastAPI Endpoint

```python
from fastapi import APIRouter
from modules.logging.shared.universal_logger import get_logger

router = APIRouter()
logger = get_logger("api")

@router.post("/api/upload")
async def upload_csv(file: UploadFile):
    logger.info("CSV upload started", filename=file.filename)

    try:
        content = await file.read()
        result = process_csv(content)

        logger.info(
            "CSV upload successful",
            filename=file.filename,
            rows_processed=result['count']
        )

        return {"success": True, "data": result}

    except Exception as e:
        logger.error(
            "CSV upload failed",
            error=e,
            filename=file.filename
        )
        raise
```

## Batch Processing

### CSV Processing with Progress

```python
logger.info("Batch processing started", total_batches=10)

for batch_num, batch in enumerate(batches, 1):
    logger.debug(
        "Processing batch",
        batch_number=batch_num,
        batch_size=len(batch)
    )

    try:
        results = process_batch(batch)
        logger.info(
            "Batch completed",
            batch_number=batch_num,
            success_count=results['success'],
            error_count=results['errors']
        )
    except Exception as e:
        logger.error(
            "Batch failed",
            error=e,
            batch_number=batch_num
        )

logger.info("All batches completed", total_processed=total_count)
```

## API Cost Tracking

### OpenAI API Calls

```python
import openai

logger.info(
    "OpenAI API call started",
    model="gpt-3.5-turbo",
    prompt_length=len(prompt)
)

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)

logger.info(
    "OpenAI API call completed",
    tokens_used=response.usage.total_tokens,
    cost_usd=response.usage.total_tokens * 0.000002
)
```

## Frontend Logging (via Backend)

### React Component Error

```typescript
// Frontend sends log to backend
const logger = {
  error: (message: string, data: any) => {
    fetch('/api/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level: 'ERROR',
        message,
        data,
        timestamp: new Date().toISOString(),
        url: window.location.href
      })
    });
  }
};

// Usage
try {
  await uploadFile(file);
} catch (error) {
  logger.error('File upload failed', {
    filename: file.name,
    size: file.size,
    error: error.message
  });
}
```

### Backend Receives Frontend Logs

```python
from pydantic import BaseModel
from modules.logging.shared.universal_logger import get_logger

logger = get_logger("frontend")

class FrontendLogEntry(BaseModel):
    level: str
    message: str
    data: dict
    timestamp: str
    url: str

@router.post("/api/logs")
async def receive_frontend_log(entry: FrontendLogEntry):
    log_method = getattr(logger, entry.level.lower())
    log_method(
        entry.message,
        url=entry.url,
        **entry.data
    )
    return {"success": True}
```

## Production Patterns

### Rate Limit Warnings

```python
if remaining_calls < 10:
    logger.warning(
        "API rate limit approaching",
        remaining_calls=remaining_calls,
        limit=rate_limit,
        reset_time=reset_time
    )
```

### Configuration Validation

```python
if not validate_config():
    logger.error(
        "Invalid configuration",
        config_file=".env",
        missing_keys=missing_keys
    )
    sys.exit(1)
```

### Startup Logging

```python
def main():
    logger.info(
        "Application started",
        version="10.0.0",
        environment="production",
        python_version=sys.version
    )

    # Initialize systems
    logger.info("Database connected", host=db_host)
    logger.info("API keys validated", services=["apollo", "instantly"])

    # Start processing
    logger.info("Ready to process requests")
```

## Analyzing Logs

### Find All Errors Today

```bash
cat modules/logging/logs/errors/2025-10-04.log
```

### Search for Specific Error

```bash
grep "API call failed" modules/logging/logs/2025-10-04.log
```

### Count Errors by Module

```bash
grep "ERROR" modules/logging/logs/2025-10-04.log | \
jq -r '.module' | sort | uniq -c
```

### Extract API Costs

```bash
grep "cost_usd" modules/logging/logs/2025-10-04.log | \
jq -r '.cost_usd' | \
awk '{sum+=$1} END {print sum}'
```
