# Outreach Service Integration Instructions

## ⚠️ CRITICAL SERVICE ORGANIZATION RULES

**NEVER create files outside designated service structure. You MUST:**

1. **For ANY file creation:**
   - Determine which service it belongs to (instantly, apollo, airtable, n8n, firecrawl, apify)
   - Place in appropriate service folder with correct subfolder (scripts/outputs/docs)
   - Explain WHY this specific file is needed for that service
   - Get explicit approval before creating

2. **For cross-service functionality:**
   - Use centralized .env file for configuration
   - No hard-coded API keys or service-specific paths
   - Scripts must be portable between environments
   - Document dependencies clearly in service docs

**No exceptions. Service isolation is mandatory.**

## 🗂️ MANDATORY SERVICE ORGANIZATION

**EACH SERVICE MUST FOLLOW THIS STRUCTURE - NO EXCEPTIONS:**

```
services/
├── [service-name]/
│   ├── scripts/     # Executable Python/batch scripts
│   ├── outputs/     # Generated data, reports, logs
│   └── docs/        # Service-specific documentation
```

❌ **FORBIDDEN:**
- Files in project root (except .env, CHANGELOG.md, CLAUDE.md)
- Cross-service file dependencies
- Hard-coded paths or API keys
- Service-specific configs outside service folder

✅ **REQUIRED PATHS:**
- **Instantly**: `services/instantly/scripts/`, `services/instantly/outputs/`
- **Apollo**: `services/apollo/scripts/`, `services/apollo/outputs/`
- **Airtable**: `services/airtable/scripts/`, `services/airtable/outputs/`
- **N8N**: `services/n8n/scripts/`, `services/n8n/outputs/`
- **Firecrawl**: `services/firecrawl/scripts/`, `services/firecrawl/outputs/`
- **Apify**: `services/apify/scripts/`, `services/apify/outputs/`

## ⚠️ CONFIGURATION MANAGEMENT RULES

**All services MUST use centralized configuration:**

1. **API Keys**: Read from root `.env` file only
2. **Service URLs**: No hardcoded endpoints in scripts
3. **Output Paths**: Relative to service folder structure
4. **Dependencies**: Minimal external libraries, prefer built-in Python modules

**Configuration Pattern:**
```python
# Load from centralized .env
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
api_key = load_from_env('SERVICE_API_KEY')
```

## ⚠️ SCRIPT DEVELOPMENT STANDARDS

**When creating service scripts, you MUST:**

1. **Self-contained execution** - script runs independently
2. **Error handling** - comprehensive try/catch with meaningful messages
3. **Output management** - save results to service outputs folder
4. **Progress reporting** - user feedback during execution
5. **Flexible authentication** - test multiple methods if one fails
6. **No external dependencies** - use built-in Python libraries when possible

**Script Template Pattern:**
```python
#!/usr/bin/env python3
"""Service Script - Brief Description"""

import os
import json
from datetime import datetime

def load_api_key():
    """Load API key from centralized .env"""
    
def make_api_request(endpoint, method='GET', data=None):
    """Make API request with error handling"""
    
def save_output(data, filename):
    """Save to service outputs folder"""
    
def main():
    """Main execution with progress reporting"""

if __name__ == "__main__":
    main()
```

## Architecture & Service Integration

**Outreach Process Flow:**
1. **Lead Generation** → Apollo API retrieves prospect data
2. **Data Enrichment** → Airtable stores and organizes prospect information  
3. **Content Research** → Firecrawl/Apify gather company intelligence
4. **Campaign Setup** → Instantly API manages email sequences
5. **Automation** → N8N orchestrates workflow triggers
6. **Analytics** → Cross-service reporting and optimization

## Project Context

**What this is:**
- Multi-service outreach automation platform
- API-first integration approach with major outreach tools
- Modular architecture allowing service swapping/upgrades
- Centralized configuration with isolated service execution

**What this is NOT:**
- Single-service dependency system
- Monolithic application architecture
- Hard-coded service implementation
- Manual configuration management

## Service-Specific Guidelines

**Instantly Service:**
- Email campaign management and delivery
- Lead list uploads and segmentation
- Performance analytics and reporting
- Template management and A/B testing

**Apollo Service:**
- Prospect discovery and contact information
- Company intelligence gathering
- Lead scoring and qualification
- Data export for campaign use

**Airtable Service:**
- Centralized prospect database management
- Campaign tracking and status updates
- Custom field management for personalization
- Integration hub for other services

**N8N Service:**
- Workflow automation and triggers
- Cross-service data synchronization
- Campaign scheduling and management
- Error handling and notifications

**Firecrawl/Apify Services:**
- Website content extraction for personalization
- Company research and intelligence gathering
- Social media and news monitoring
- Competitive analysis data collection

## Development Standards

**API Integration:**
- Always test authentication methods comprehensively
- Implement retry logic with exponential backoff
- Log all API responses for debugging
- Handle rate limits gracefully

**Error Handling:**
- Specific error messages for different failure modes
- Graceful degradation when services unavailable
- User-friendly progress reporting
- Detailed logs in service outputs folder

**Data Management:**
- Timestamped output files for version tracking
- JSON format for structured data
- CSV format for tabular data exchange
- Automatic backup of important data

**Security:**
- No API keys in source code
- Environment variable validation
- Secure credential storage
- Access logging for audit trails

## Quality Control Standards

**Service Integration Quality:**
- Each service operates independently
- Cross-service data flow is documented
- API failures don't break entire workflow
- Configuration changes don't require code updates

**Code Quality:**
- Self-documenting variable and function names
- Comprehensive error handling
- Progress indicators for long-running operations
- Clean separation of concerns

**Documentation Quality:**
- Each service has clear setup instructions
- API usage examples and troubleshooting
- Common error scenarios and solutions
- Integration patterns with other services