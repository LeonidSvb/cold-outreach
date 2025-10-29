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

## Execution Tracking (NEW)

### Full Script Tracking with Metrics

```python
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

def main():
    with logger.track_execution("apollo-lead-collector") as tracker:
        # Fetch leads from Apollo API
        logger.info("Fetching leads from Apollo API")
        leads = fetch_apollo_leads(limit=1000)
        tracker.add_metric("leads_fetched", len(leads))

        # Process and enrich leads
        logger.info("Processing and enriching leads")
        enriched = enrich_leads(leads)
        tracker.add_metric("leads_enriched", len(enriched))

        # Save to CSV
        output_file = save_to_csv(enriched)
        tracker.add_metric("output_file", output_file)

        # Track API costs
        tracker.add_metrics(
            api_calls=10,
            api_cost_usd=0.05
        )

if __name__ == "__main__":
    main()
```

**Logs generated:**
```json
{"timestamp":"2025-10-29T10:00:00","module":"apollo","level":"INFO","message":"apollo-lead-collector started","script":"apollo-lead-collector"}
{"timestamp":"2025-10-29T10:00:05","module":"apollo","level":"INFO","message":"apollo-lead-collector completed successfully","script":"apollo-lead-collector","duration_seconds":45.23,"leads_fetched":1000,"leads_enriched":950,"output_file":"leads_20251029.csv","api_calls":10,"api_cost_usd":0.05}
```

### Execution Tracking with Error Handling

```python
with logger.track_execution("instantly-sync") as tracker:
    try:
        # Fetch campaigns
        campaigns = instantly_client.get_campaigns()
        tracker.add_metric("campaigns_fetched", len(campaigns))

        # Process each campaign
        for campaign in campaigns:
            emails = process_campaign(campaign)
            tracker.add_metric(f"emails_{campaign['id']}", len(emails))

    except Exception as e:
        # Error automatically logged with all metrics collected so far
        raise
```

**On error:**
```json
{"timestamp":"2025-10-29T10:05:00","module":"instantly","level":"ERROR","message":"instantly-sync failed","script":"instantly-sync","duration_seconds":12.45,"error_type":"APIError","error_details":"Rate limit exceeded","campaigns_fetched":5}
```

### Multiple Metrics at Once

```python
with logger.track_execution("openai-enrichment") as tracker:
    total_cost = 0
    total_tokens = 0

    for lead in leads:
        result = enrich_with_openai(lead)
        total_cost += result['cost']
        total_tokens += result['tokens']

    # Add all metrics at end
    tracker.add_metrics(
        leads_processed=len(leads),
        total_cost_usd=round(total_cost, 4),
        total_tokens=total_tokens,
        avg_tokens_per_lead=round(total_tokens / len(leads), 2)
    )
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
