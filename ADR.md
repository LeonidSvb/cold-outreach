# Architecture Decision Log

## Index

| ID   | Title                                                        | Date       | Status   |
| ---- | ------------------------------------------------------------ | ---------- | -------- |
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
