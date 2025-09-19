# Cold Outreach Automation Platform - Claude Coding Guidelines

# Core Principles

## Simplicity First
- Always prefer simple solutions over complex ones
- Avoid over-engineering or premature optimization
- Choose straightforward implementations that are easy to understand and maintain
- **CRITICAL: NEVER use emojis in Python scripts, console output, or any code files due to Windows encoding issues**
- **MANDATORY: Always escape JSON placeholders in prompts using double braces before .format() calls**

## DRY (Don't Repeat Yourself)
- Avoid duplication of code whenever possible
- Before writing new functionality, check for similar existing code in the codebase
- Refactor common patterns into reusable utilities or components
- Share logic across components rather than duplicating it

## Environment Awareness
- Write code that works consistently across different environments: dev, test, and prod
- Use environment variables for configuration differences
- Avoid hardcoding values that might differ between environments
- Test code behavior in all target environments

## Focused Changes
- Only make changes that are requested or directly related to the task at hand
- Be confident that changes are well understood and necessary
- Avoid scope creep or tangential improvements unless explicitly requested

## Conservative Technology Choices
- When fixing issues or bugs, exhaust all options within the existing implementation first
- Avoid introducing new patterns or technologies without strong justification
- If new patterns are introduced, ensure old implementations are properly removed to prevent duplicate logic
- Maintain consistency with existing codebase patterns

# Code Organization

## Clean Codebase
- Keep the codebase very clean and organized
- Follow existing file structure and naming conventions
- Group related functionality together
- Remove unused code and imports

## File Management
- Avoid writing one-time scripts directly in files
- If scripts are needed, create them in appropriate directories (e.g., `services/[service]/scripts/`)
- Consider whether a script will be reused before embedding it in the codebase

## File Size Limits
- Keep files under 200-300 lines of code
- Refactor larger files by splitting them into smaller, focused modules
- Break down complex components into smaller, composable pieces

## Naming Conventions
- Use descriptive, self-documenting names for variables, functions, and files
- Follow Python naming conventions (snake_case for functions/variables, PascalCase for classes)
- Avoid abbreviations unless they're industry standard
- Use consistent naming patterns across the project

### NEW: File Naming Standards (January 2025)
**Scripts:** `{purpose}.py`
- Examples: `apollo_lead_collector.py`, `openai_mass_processor.py`
- Simple, descriptive names without dates

**Results:** `{script_name}_{YYYYMMDD_HHMMSS}.json`
- Examples: `apollo_leads_20250119_143022.json`, `openai_analysis_20250119_143515.json`
- Timestamp ensures uniqueness and chronological order

**Module Organization:**
- Each module contains related functionality only
- All scripts have embedded configs (no external config files)
- Results stored in module-specific results/ folders

# Data and Testing

## No Fake Data in Production
- Mocking data is only acceptable for tests
- Never add stubbing or fake data patterns that affect dev or prod environments
- Use real data sources and proper error handling for development and production

## Environment Files
- Never overwrite `.env` files without explicit permission and confirmation
- Always ask before modifying environment configuration
- Back up existing environment files when changes are necessary

# Git and Version Control

## Commit Standards
- Write clear, descriptive commit messages: "fix user login bug", not "fix"
- Make atomic commits - one commit = one feature/fix
- Review changes before committing via git diff
- Never commit secrets, .env files, or temporary files

## Branch Management
- Use descriptive branch names: feature/add-auth, fix/login-crash
- One branch = one task, don't mix different features
- Delete merged branches to keep repository clean
- For solo projects can work in main, but make frequent commits

# Code Quality

## Error Handling
- Always wrap API calls in try-catch blocks
- Write meaningful error messages: "Failed to save user data", not "Error 500"
- Don't swallow errors - log them or show to user
- Fail fast and clearly - don't let app hang in unknown state

## Performance Considerations
- Optimize for readability first, performance second
- Don't add libraries without necessity - each one adds weight
- Profile before optimizing, don't guess at bottlenecks
- For small projects: readability > performance

# Batch Processing Optimization

Where possible, make massive batches first. See what needs to be changed, then change everything massively to make it as fast as possible.

- Plan changes in advance - what needs to be changed across all files
- Make massive changes in one batch, not file by file
- Use find/replace, regex for mass edits
- Commit batches of changes, not each file separately

# Project-Specific Requirements

## HTTP-Only Scraping
- Never use external services like Firecrawl
- Use only built-in Python libraries (urllib, requests)
- Implement proper error handling for network requests

## Self-Documenting Scripts
- Embed statistics, changelogs, and run history directly in script files
- Track version, total runs, success rates within SCRIPT_STATS dictionary
- Include PURPOSE, IMPROVEMENTS, USAGE sections in script headers

### NEW: Script Structure Standard (January 2025)
All scripts must follow this structure:
```python
#!/usr/bin/env python3
"""
=== SCRIPT NAME ===
Version: 1.0.0 | Created: YYYY-MM-DD

PURPOSE:
Brief description of what the script does

FEATURES:
- Key capabilities
- Main features

USAGE:
1. Configure CONFIG section below
2. Run: python script_name.py
3. Results saved to results/

IMPROVEMENTS:
v1.0.0 - Initial version
"""

# CONFIG SECTION - All settings here
CONFIG = {
    "API_SETTINGS": {...},
    "PROCESSING": {...},
    "OUTPUT": {...}
}

# SCRIPT STATISTICS - Auto-updated
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0
}

# MAIN LOGIC
class MainClass:
    @auto_log("module_name")
    def main_function(self):
        pass

if __name__ == "__main__":
    main()
```

## Service Organization
- Each service in `services/[service-name]/` with scripts/, outputs/, prompts/ folders
- No files in project root except .env, CHANGELOG.md, CLAUDE.md
- Use centralized .env for all API keys and configuration

### Project Structure (Updated January 2025):
```
├── modules/             # MODULAR ARCHITECTURE
│   ├── shared/          # Common utilities
│   │   ├── logger.py    # Auto-logging system
│   │   └── google_sheets.py  # Google Sheets integration
│   ├── apollo/          # Apollo API integration
│   │   ├── apollo_lead_collector.py
│   │   ├── apollo_mass_processor.py
│   │   └── results/     # Timestamped JSON results
│   ├── openai/          # OpenAI processing
│   │   ├── openai_content_analyzer.py
│   │   ├── openai_mass_processor.py
│   │   └── results/
│   ├── scraping/        # Web scraping
│   │   ├── domain_analyzer.py
│   │   ├── content_extractor.py
│   │   └── results/
│   ├── sheets/          # Google Sheets operations
│   │   ├── sheets_mass_updater.py
│   │   ├── sheets_data_processor.py
│   │   └── results/
│   └── instantly/       # Instantly API
│       ├── instantly_campaign_optimizer.py
│       └── results/
├── data/                # DATA MANAGEMENT
│   ├── raw/            # Original CSVs
│   ├── processed/      # Final processed data
│   └── logs/           # Auto-logger outputs
├── archive/             # ARCHIVED FILES
│   ├── old_scripts/    # Old root scripts
│   ├── old_services/   # Old services folder
│   └── old_core/       # Old core folder
├── dashboard/           # AUTO-GENERATED ANALYTICS
│   ├── index.html      # Interactive dashboard
│   └── README.md       # Usage instructions
```

### Path Configuration Rules:
- Core tools use: `../../.env` for root config
- Service scripts use: `../../../.env` for root config  
- Core prompts: `../prompts/[prompt-name].txt`
- Service prompts: `../prompts/[prompt-name].txt` 
- Lead data flows: raw → processed (simplified 2-stage pipeline)
- File naming: raw files use YYYYMMDD, processed files use YYYYMMDD format (local Bali time zone)
- Dashboard integration: All processors automatically update `dashboard/index.html` with session data

## Smart Analytics Dashboard

### Dashboard System
- **Auto-Generation**: Every script run automatically updates HTML dashboard with embedded data
- **Intelligent Detail Levels**: Recent 5 sessions show maximum detail, older sessions show brief summary
- **Autonomous Operation**: Self-contained HTML file with no server dependencies or external resources
- **Real-Time Updates**: 30-second auto-refresh in browser, manual refresh with F5

### Session Data Management
- **Comprehensive Logging**: All processors log detailed session data including performance metrics, API costs, timing breakdown
- **Historical Preservation**: Session history preserved indefinitely with intelligent data compression for older entries
- **Aggregated Analytics**: Automatic calculation of trends, success rates, cost efficiency across all script types
- **Interactive Access**: Click-through details for recent sessions, tabular overview for historical data

### Integration Requirements
- All new processors must integrate `dashboard_manager.save_session_data()` and `dashboard_generator.generate_dashboard_now()`
- Session data must include: performance_metrics, processing_results, api_calls, timing_details, quality_metrics
- Dashboard updates are automatic and require no manual intervention
- All icebreakers and emails are written in English or any other language you need, not Russian.
- When you create scripts, never use emojis. And all comments should be in English.