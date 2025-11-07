# Architecture Decision Log

## Index

| ID   | Title                                                        | Date       | Status   |
| ---- | ------------------------------------------------------------ | ---------- | -------- |
| 0013 | [Project Structure Simplification - Ultra-Clean Architecture](#adr-0013) | 2025-11-07 | Accepted |
| 0012 | [Universal Logging System for Platform Observability](#adr-0012) | 2025-10-04 | Accepted |
| 0011 | [Hierarchical README Pattern for AI-First Development](#adr-0011) | 2025-10-03 | Accepted |
| 0010 | [Backend/Frontend Separation & Monorepo Management](#adr-0010) | 2025-10-02 | Accepted |
| 0009 | [Module-Centric Data Architecture & Massive Cleanup](#adr-0009) | 2025-09-23 | Accepted |
| 0008 | [Data-Centric Architecture with Core Tool Separation](#adr-0008) | 2025-09-08 | Superseded |
| 0007 | [Session Continuity and Context Preservation](#adr-0007) | 2025-09-08 | Accepted |
| 0006 | [Production Readiness Validation Framework](#adr-0006) | 2025-09-08 | Accepted |
| 0005 | [AI-Powered Page Prioritization with OpenAI](#adr-0005) | 2025-01-08 | Accepted |
| 0004 | [Parallel Processing for Website Intelligence](#adr-0004) | 2025-01-08 | Accepted |
| 0003 | [HTTP-Only Website Content Extraction](#adr-0003) | 2025-01-08 | Accepted |
| 0002 | [Dialogue-Style Prompting System](#adr-0002) | 2025-01-08 | Accepted |
| 0001 | [Service-Based Modular Architecture](#adr-0001) | 2025-01-08 | Superseded |

---

## ADR-0012 — Universal Logging System for Platform Observability

<a id="adr-0012"></a>
**Date**: 2025-10-04
**Status**: Accepted
**Owner**: Platform Infrastructure Team

### Context

Platform had no centralized logging system. Python scripts used print statements, FastAPI had no request/response logging, and frontend errors were only visible in browser console. Debugging production issues required manual code inspection with no audit trail of system operations.

### Decision

Implement Universal Logging System with:
- Centralized logging module (modules/logging/) with singleton UniversalLogger class
- Daily log rotation with automatic file creation (YYYY-MM-DD.log)
- JSON structured logging for machine readability
- Separate error logs (logs/errors/) for quick access
- FastAPI middleware for automatic API request/response logging
- Frontend TypeScript logger forwarding logs to backend
- @auto_log decorator for function performance tracking
- Zero maintenance (no manual file management required)

### Technical Implementation

**Log Structure:**
- Location: modules/logging/logs/
- Format: Single-line JSON per entry
- Levels: ERROR, WARNING, INFO, DEBUG
- Fields: timestamp, module, level, message, context data

**Integration Points:**
- Python scripts: `from modules.logging.shared.universal_logger import get_logger`
- FastAPI: Middleware in backend/middleware/logging_middleware.py
- Next.js: Frontend logger in frontend/src/lib/logger.ts
- All scripts: Mandatory logger in main() with try/except error handling

### Consequences

- **Pros**: Complete system observability, automatic audit trail, fast error diagnosis, zero maintenance overhead, industry-standard JSON format, modular architecture (logs inside logging module), production-ready from day one
- **Cons**: Additional 2-3 lines of boilerplate per script, slight performance overhead (negligible with async writes), log files grow over time (mitigated by daily rotation)

### Metrics

- **Files Created**: 5 new files (universal_logger.py, logging_middleware.py, logs.py, logger.ts, test_full_system.py)
- **Files Updated**: 15 files (all Python scripts, CLAUDE.md, README.md)
- **Test Coverage**: 100% (ALL TESTS PASSED)
- **Log Storage**: ~6KB/day for current load

---

## ADR-0011 — Hierarchical README Pattern for AI-First Development

<a id="adr-0011"></a>
**Date**: 2025-10-03
**Status**: Accepted
**Owner**: Documentation Team

### Context

The project had a 579-line SCRIPTS_INVENTORY.md file that AI agents read first, consuming excessive context tokens (74K/200K). This created documentation maintenance burden as the file required updates for every script change and duplicated information already in code. For AI-first (agentic coding) projects, documentation must be optimized for AI consumption while remaining human-readable.

### Decision

Implement Hierarchical README Pattern with module-level documentation:
- Enhanced Root README.md with "For AI: Quick Module Reference" section linking to all modules
- Created README.md for each module (instantly, csv_transformer, openai, apollo, scraping, sheets, shared)
- Each module README includes: Priority (High/Medium/Low), Status, Usage, Scripts, Configuration, Performance Metrics
- Removed 579-line SCRIPTS_INVENTORY.md in favor of distributed documentation
- Standardized README format across all modules (50-70 lines each)

### Consequences

- **Pros**: Token-efficient AI navigation (AI reads only needed module ~50 lines vs 579 lines all at once), localized documentation (updates near code), industry-standard pattern (common in modular projects), reduced maintenance (changes scoped to affected module only), better human readability (each module self-contained)
- **Cons**: More files to maintain (7 module READMEs vs 1 inventory), requires discipline to keep READMEs updated, slight learning curve for new contributors

### Metrics

- **Before**: 579 lines in SCRIPTS_INVENTORY.md (100% read by AI on every session)
- **After**: Root README ~150 lines + module READMEs ~50 lines each (AI reads root + 1-2 modules = ~150-250 lines)
- **Token Savings**: ~50-60% reduction in documentation tokens consumed per session

---

## ADR-0010 — Backend/Frontend Separation & Monorepo Management

<a id="adr-0010"></a>
**Date**: 2025-10-02
**Status**: Accepted
**Owner**: Platform Architecture Team

### Context

The project had unclear separation between Python FastAPI backend (in `api/`) and Next.js frontend API routes (in `frontend/src/app/api/`), causing confusion about which API to use. Additionally, running backend and frontend required two separate terminal commands, complicating development workflow.

### Decision

Rename `api/` to `backend/` for clear separation from Next.js API routes, implement root `package.json` with monorepo management using `concurrently` to run both backend and frontend with single `npm run dev` command, and prepare database for multi-user mode by adding `user_id` column with default '1'.

### Consequences

- **Pros**: Clear backend/frontend separation, simplified development workflow, future-ready for multi-user mode, clean project structure
- **Cons**: Required migration of existing references, developers need to learn new structure

---

## ADR-0009 — Module-Centric Data Architecture & Massive Cleanup

<a id="adr-0009"></a>
**Date**: 2025-09-23
**Status**: Accepted
**Owner**: Platform Architecture Team

### Context

The data-centric architecture had scattered test files, duplicate scripts, and unclear data boundaries. With 12 test files in instantly module, backup files throughout, and mixed data responsibilities, the system needed radical cleanup and proper module-centric data organization for maintainability.

### Decision

Implement module-centric data architecture where each module contains its own data/ subfolder with input/, templates/, campaigns/ as needed. Remove all test scripts, backup files, and duplicate functionality. Establish clean separation: modules/ (automation), app/ (web application), data/ (shared cross-module data only).

### Consequences

- **Pros**: Self-contained modules, eliminated test clutter, clear data ownership, minimal root directory, improved navigation
- **Cons**: Required massive cleanup effort, some data duplication between modules
- **Supersedes**: ADR-0008

---

## ADR-0007 — Session Continuity and Context Preservation

<a id="adr-0007"></a>
**Date**: 2025-09-08
**Status**: Accepted
**Owner**: Development Workflow Team

### Context

Complex development sessions often hit context limits or require continuation across multiple sessions. Critical technical decisions, file locations, architectural patterns, and implementation details need to be preserved to maintain development momentum and avoid rework.

### Decision

Implement structured session continuity framework with chronological analysis, technical context tracking, architectural decision preservation, and comprehensive state documentation to enable seamless session continuation.

### Consequences

- **Pros**: Enables seamless development continuation, preserves technical context, reduces rework, maintains architectural consistency
- **Cons**: Requires structured documentation approach, additional overhead during development

---

## ADR-0006 — Production Readiness Validation Framework

<a id="adr-0006"></a>
**Date**: 2025-09-08
**Status**: Accepted
**Owner**: Production Deployment Team

### Context

The cold outreach platform has reached a mature state with multiple services and AI integrations. Before production deployment, all system components need comprehensive validation to ensure reliability, performance, and compliance with architectural standards.

### Decision

Implement a comprehensive production readiness validation framework that systematically verifies all system components including file structure, service organization, API integrations, analytics capabilities, and architectural compliance before deployment.

### Consequences

- **Pros**: Ensures system reliability, validates architectural compliance, prevents production issues, provides deployment confidence
- **Cons**: Requires systematic validation time, may reveal additional issues requiring fixes

---

## ADR-0005 — AI-Powered Page Prioritization with OpenAI

<a id="adr-0005"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Content Intelligence Team

### Context

Website content extraction finds many pages but not all are valuable for outreach intelligence. The system needs to automatically identify high-value pages like careers, blog posts, and company information while skipping legal/policy pages.

### Decision

Implement AI-powered page prioritization using OpenAI with dialogue-style prompts to classify discovered pages into high/medium/low priority categories based on outreach intelligence value, with editable prompts for easy customization.

### Consequences

- **Pros**: Intelligent prioritization, adaptable to different industries, reduces unnecessary scraping, improves content relevance
- **Cons**: OpenAI API costs, requires API key management, dependent on external service availability

---

## ADR-0004 — Parallel Processing for Website Intelligence

<a id="adr-0004"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Performance Optimization Team

### Context

Sequential processing of website content extraction is too slow for batch operations on hundreds of domains. Users need faster processing to handle large CSV files efficiently for outreach campaigns.

### Decision

Implement parallel processing using ThreadPoolExecutor with 3 concurrent threads for website content extraction, allowing multiple domains to be processed simultaneously while maintaining safety limits.

### Consequences

- **Pros**: 5x faster processing, configurable worker count, maintains error isolation per domain
- **Cons**: Potential rate limiting by target sites, higher memory usage, more complex error handling

---

## ADR-0003 — HTTP-Only Website Content Extraction

<a id="adr-0003"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Website Intelligence Team

### Context

The platform needs to extract company intelligence from websites for cold outreach personalization. External scraping services add cost, latency, and external dependencies.

### Decision

Implement HTTP-only content extraction using Python's built-in urllib and html.parser modules for direct website scraping with custom HTML content cleaning and text extraction.

### Consequences

- **Pros**: No external dependencies, cost-free, full control over extraction logic, fast processing
- **Cons**: May be blocked by some sites, no JavaScript rendering, requires SSL handling

---

## ADR-0002 — Dialogue-Style Prompting System

<a id="adr-0002"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: AI Integration Team

### Context

AI-powered features require reliable and predictable outputs for business automation. Traditional zero-shot prompting produces inconsistent results that are unsuitable for production outreach campaigns.

### Decision

Implement dialogue-style prompting using OpenAI Chat Completions API with system role, user instructions, and multiple user/assistant example pairs that demonstrate expected input/output format before providing real data.

### Consequences

- **Pros**: Predictable outputs, easily editable prompts, follows prompting knowledge base best practices
- **Cons**: Higher token usage, more complex prompt management, requires example maintenance

---

## ADR-0013 — Project Structure Simplification - Ultra-Clean Architecture

<a id="adr-0013"></a>
**Date**: 2025-11-07
**Status**: Accepted
**Owner**: Leo (Project Lead)

### Context

The "Outreach - new" project grew organically over 68 commits, accumulating multiple modules, a full-stack architecture (FastAPI backend + Next.js frontend), and scattered results across 7+ module directories. The project became bloated with 83 Python files across modules (apollo, instantly, openai, scraping, sheets, csv_transformer), 97 JSON result files scattered in different module results/ folders, and a backend that was built for Supabase UI but is not needed for current workflow. Current needs are simple: (1) Process CSV/JSON files through OpenAI API, (2) Scrape websites for content and emails, (3) Store all results in one place. The existing modular architecture was over-engineered for these requirements.

### Alternatives

- **Keep full modular architecture**: Rejected due to excessive complexity for 2 primary use cases
- **Start completely new project from scratch**: Rejected because it would lose 3 weeks of work including Universal Logger, Supabase setup, CLAUDE.md conventions, and all existing working scripts
- **Hybrid cleanup (archive frontend, keep modules)**: Rejected because it still maintains unnecessary folder nesting and doesn't solve scattered results problem

### Decision

Reorganize project into ULTRA-CLEAN flat structure with maximum simplicity. Create scripts/ directory containing ALL scripts with naming pattern {module}_{script}.py (e.g., openai_mass_processor.py, scraping_website_scraper.py). Centralize ALL results into results/ directory with subdirectories for each category (openai/, scraping/, raw/, processed/). Move logger from modules/logging/shared/ to logger/universal_logger.py. DELETE unused modules: apollo/ (never used), instantly/ (incomplete WIP), csv_transformer/ (not used), sheets/ (deprecated). DELETE backend/ (FastAPI not needed). PRESERVE frontend/ completely (all packages, node_modules, components) for future refactoring.

### Consequences

- **Pros**: 10x simpler structure, centralized results in one place, easier navigation (ls scripts/ shows all tools), naming clarity with prefixes, preserved infrastructure (Universal Logger, Git history, CLAUDE.md), frontend preserved for future refactoring, faster onboarding, no quality loss
- **Cons**: One-time migration effort (~30-60 minutes), import path updates needed, git history fragmentation from file moves, convention change for naming pattern
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

Verification checks: (1) All scripts from modules/openai/ exist in scripts/ with openai_ prefix, (2) All scripts from modules/scraping/ exist in scripts/ with scraping_ prefix, (3) All results from modules/*/results/ moved to results/{category}/, (4) logger/universal_logger.py accessible and functional, (5) Frontend runs without errors, (6) No orphaned files in deleted modules/, (7) .gitignore updated to ignore results/**/*.json and results/**/*.csv.

Testing commands:
```bash
# Verify scripts work
python scripts/openai_mass_processor.py --help
python scripts/scraping_website_scraper.py --help

# Verify logger import
python -c "from logger.universal_logger import get_logger; print('OK')"

# Verify frontend
cd frontend && npm run dev
```

Success criteria: Project size reduced from 3000+ files to ~50-100 essential files, all 2 primary use cases work (OpenAI processing, website scraping), results easily found in results/ with clear organization.

---
