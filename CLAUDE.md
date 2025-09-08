# Cold Outreach Automation Platform - Claude Coding Guidelines

# Core Principles

## Simplicity First
- Always prefer simple solutions over complex ones
- Avoid over-engineering or premature optimization
- Choose straightforward implementations that are easy to understand and maintain

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

## Service Organization
- Each service in `services/[service-name]/` with scripts/, outputs/, prompts/ folders
- No files in project root except .env, CHANGELOG.md, CLAUDE.md
- Use centralized .env for all API keys and configuration

### Project Structure:
```
├── leads/                # DATA MANAGEMENT by processing status
│   ├── raw/             # Original CSVs (Lumid verification Canada.csv)
│   ├── processed/       # Company names cleaned
│   ├── enriched/        # + website intelligence added  
│   └── ready/           # Final campaign-ready data
├── core/                # SHARED TOOLS & UTILITIES
│   ├── processors/      # company_name_cleaner_analytics.py
│   └── prompts/         # company_name_shortener.txt (dialogue-style)
├── services/            # EXTERNAL SERVICE INTEGRATIONS
│   ├── website-intel/   # Website scraping & content analysis
│   │   ├── scripts/     # intelligent scraping, page prioritization  
│   │   ├── outputs/     # website data, prioritized content
│   │   └── prompts/     # page_prioritizer.txt
│   ├── apollo/          # Lead generation via Apollo API
│   └── instantly/       # Email campaign management
```

### Path Configuration Rules:
- Core tools use: `../../.env` for root config
- Service scripts use: `../../../.env` for root config  
- Core prompts: `../prompts/[prompt-name].txt`
- Service prompts: `../prompts/[prompt-name].txt` 
- Lead data flows: raw → processed → enriched → ready
