---
description: Architectural Decision Records
globs:
alwaysApply: false
---

# Architecture Decision Log

<!--
ADR_AGENT_PROTOCOL v1.0

You (the agent) manage this file as the single source of truth for all ADRs.

INVARIANTS
- Keep this exact file structure and headings.
- All ADR entries use H2 headings: "## ADR-XXXX — <Title>" (4-digit zero-padded ID).
- Allowed Status values: Proposed | Accepted | Superseded
- Date format: YYYY-MM-DD
- New entries must be appended to the END of the file.
- The Index table between the INDEX markers must always reflect the latest state and be sorted by ID desc (newest on top).
- Each ADR MUST contain: Date, Status, Owner, Context, Decision, Consequences.
- Each ADR must include an explicit anchor `<a id="adr-XXXX"></a>` so links remain stable.

HOW TO ADD A NEW ADR
1) Read the whole file.
2) Compute next ID:
   - Scan for headings matching: ^## ADR-(\d{4}) — .+$
   - next_id = (max captured number) + 1, left-pad to 4 digits.
3) Create a new ADR section using the "New ADR Entry Template" below.
   - Place it AFTER the last ADR section in the file.
   - Add an `<a id="adr-XXXX"></a>` line immediately below the heading.
4) Update the Index (between the INDEX markers):
   - Insert/replace the row for this ADR keeping the table sorted by ID descending.
   - Title in the Index MUST link to the anchor: [<Title>](#adr-XXXX)
   - If this ADR supersedes another: set "Supersedes" in this row, and update that older ADR:
       a) Change its Status to "Superseded"
       b) Add "Superseded by: ADR-XXXX" in its Consequences block
       c) Update the older ADR's Index row "Superseded by" column to ADR-XXXX
5) Validate before saving:
   - Exactly one heading exists for ADR-XXXX
   - All required fields are present and non-empty
   - Index contains a row for ADR-XXXX and remains properly sorted
6) Concurrency resolution:
   - If a merge conflict or duplicate ID is detected after reading: recompute next_id from the current file state, rename your heading, anchor, and Index row accordingly, and retry once.

COMMIT MESSAGE SUGGESTION
- "ADR-XXXX: <Short Title> — <Status>"

END ADR_AGENT_PROTOCOL
-->

## Index

<!-- BEGIN:ADR_INDEX -->

| ID   | Title                                                        | Date       | Status   | Supersedes | Superseded by |
| ---- | ------------------------------------------------------------ | ---------- | -------- | ---------- | ------------- |
| 0005 | [AI-Powered Page Prioritization with OpenAI](#adr-0005) | 2025-01-08 | Accepted | —          | —             |
| 0004 | [Parallel Processing for Website Intelligence](#adr-0004) | 2025-01-08 | Accepted | —          | —             |
| 0003 | [HTTP-Only Website Content Extraction](#adr-0003) | 2025-01-08 | Accepted | —          | —             |
| 0002 | [Dialogue-Style Prompting System](#adr-0002) | 2025-01-08 | Accepted | —          | —             |
| 0001 | [Service-Based Modular Architecture](#adr-0001) | 2025-01-08 | Accepted | —          | —             |

<!-- END:ADR_INDEX -->

---

## New ADR Entry Template (copy for each new decision)

> Replace placeholders, keep section headers. Keep prose concise.

```

## ADR-XXXX — \<Short, specific title>

<a id="adr-XXXX"></a>
**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded
**Owner**: <Name>

### Context

<1–3 sentences: what changed or what forces drive this decision now>

### Alternatives

<Quick bullet list of alternatives considered, and why they were rejected.>

### Decision

\<Single clear decision in active voice; make it testable/verifiable>

### Consequences

* **Pros**: \<benefit 1>, \<benefit 2>
* **Cons / risks**: \<cost 1>, \<risk 1>
* **Supersedes**: ADR-NNNN (if any)
* **Superseded by**: ADR-MMMM (filled later if replaced)

### (Optional) Compliance / Verification

\<How we'll check this is honored: tests, checks, fitness functions, runbooks>

```

---

## ADR-0001 — Service-Based Modular Architecture

<a id="adr-0001"></a>
**Date**: 2025-01-08
**Status**: Accepted  
**Owner**: Cold Outreach Platform Team

### Context

The cold outreach platform needs to integrate multiple external services (Instantly, Apollo, Airtable, N8N, Firecrawl, Apify) while maintaining maintainability and allowing for service swapping. A monolithic approach would create tight coupling and make the system fragile to API changes.

### Alternatives

- **Monolithic Architecture**: Single application with all services embedded - rejected due to tight coupling and maintenance complexity
- **Microservices with Docker**: Full containerization - rejected as overkill for current scale and adds deployment complexity
- **Plugin System**: Dynamic loading of service modules - rejected due to configuration complexity and debugging difficulty

### Decision

Implement a service-based modular architecture where each external service integration is isolated in its own directory structure under `services/[service-name]/` with standardized subfolders: `scripts/`, `outputs/`, `docs/`, and `prompts/`.

### Consequences

- **Pros**: Clear separation of concerns, easy service swapping, isolated testing, standardized structure
- **Cons / risks**: Potential code duplication between services, need for centralized configuration management
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

Each service must follow the mandatory directory structure defined in CLAUDE.md. All API keys must be stored in centralized .env file. Cross-service dependencies are forbidden.

---

## ADR-0002 — Dialogue-Style Prompting System

<a id="adr-0002"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: AI Integration Team

### Context

AI-powered features require reliable and predictable outputs for business automation. Traditional zero-shot prompting produces inconsistent results that are unsuitable for production outreach campaigns where quality directly impacts client success.

### Alternatives

- **Zero-Shot Prompting**: Simple instructions without examples - rejected due to unpredictable outputs
- **Few-Shot Prompting**: Basic examples in single message - rejected as less reliable than dialogue approach
- **Fine-Tuned Models**: Custom model training - rejected due to cost and maintenance overhead

### Decision

Implement dialogue-style prompting using OpenAI Chat Completions API with system role, user instructions, and multiple user/assistant example pairs that demonstrate expected input/output format before providing real data.

### Consequences

- **Pros**: Predictable outputs, easily editable prompts, follows prompting knowledge base best practices
- **Cons / risks**: Higher token usage, more complex prompt management, requires example maintenance
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

All AI prompts must be stored in dedicated `prompts/` folders as .txt files with dialogue examples. Prompts must achieve >90% accuracy on test datasets before production use.

---

## ADR-0003 — HTTP-Only Website Content Extraction

<a id="adr-0003"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Website Intelligence Team

### Context

The platform needs to extract company intelligence from websites for cold outreach personalization. External scraping services add cost, latency, and external dependencies. Many services have usage limits or reliability issues.

### Alternatives

- **Firecrawl API**: External service for web scraping - rejected due to API costs and external dependency
- **Apify Actors**: Managed scraping infrastructure - rejected due to complex setup and costs
- **Browser Automation**: Selenium/Playwright - rejected due to resource overhead and detection issues

### Decision

Implement HTTP-only content extraction using Python's built-in urllib and html.parser modules for direct website scraping with custom HTML content cleaning and text extraction.

### Consequences

- **Pros**: No external dependencies, cost-free, full control over extraction logic, fast processing
- **Cons / risks**: May be blocked by some sites, no JavaScript rendering, requires SSL handling
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

All content extraction must respect robots.txt. Rate limiting must be implemented. SSL certificate verification must handle common issues gracefully.

---

## ADR-0004 — Parallel Processing for Website Intelligence

<a id="adr-0004"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Performance Optimization Team

### Context

Sequential processing of website content extraction is too slow for batch operations on hundreds of domains. Users need faster processing to handle large CSV files efficiently for outreach campaigns.

### Alternatives

- **Sequential Processing**: One domain at a time - rejected due to poor performance (tested at 38s per domain)
- **Asyncio**: Asynchronous I/O processing - rejected due to complexity and debugging difficulty
- **Multiprocessing**: Full process isolation - rejected due to memory overhead and IPC complexity

### Decision

Implement parallel processing using ThreadPoolExecutor with 3 concurrent threads for website content extraction, allowing multiple domains to be processed simultaneously while maintaining safety limits.

### Consequences

- **Pros**: 5x faster processing, configurable worker count, maintains error isolation per domain
- **Cons / risks**: Potential rate limiting by target sites, higher memory usage, more complex error handling
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

Thread pool size must be configurable and default to 3 workers. Each domain must be processed independently with isolated error handling. Performance must be measured and logged.

---

## ADR-0005 — AI-Powered Page Prioritization with OpenAI

<a id="adr-0005"></a>
**Date**: 2025-01-08
**Status**: Accepted
**Owner**: Content Intelligence Team

### Context

Website content extraction finds many pages but not all are valuable for outreach intelligence. Manually prioritizing pages is not scalable. The system needs to automatically identify high-value pages like careers, blog posts, and company information while skipping legal/policy pages.

### Alternatives

- **Rule-Based Filtering**: Hardcoded URL patterns - rejected as inflexible and language-dependent
- **Machine Learning Classification**: Custom trained model - rejected due to training data requirements and maintenance
- **Simple Scoring**: Basic keyword matching - rejected as too simplistic for nuanced content

### Decision

Implement AI-powered page prioritization using OpenAI with dialogue-style prompts to classify discovered pages into high/medium/low priority categories based on outreach intelligence value, with editable prompts for easy customization.

### Consequences

- **Pros**: Intelligent prioritization, adaptable to different industries, reduces unnecessary scraping, improves content relevance
- **Cons / risks**: OpenAI API costs, requires API key management, dependent on external service availability
- **Supersedes**: —
- **Superseded by**: —

### Compliance / Verification

Page prioritization must use dialogue-style prompts stored in prompts/ directory. Classification accuracy must be manually validated on test datasets. Priority categories must be clearly defined and consistently applied.

---

<!-- ADD MORE ADR ENTRIES HERE FOLLOWING THE SAME TEMPLATE PATTERN -->

---