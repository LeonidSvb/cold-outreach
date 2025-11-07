# Cold Outreach AI Automation Platform

AI-powered cold outreach automation with 10K-30K leads/month capacity. Modular system for CSV lead processing, AI normalization, icebreaker generation, and Instantly campaign management.

**🌐 Live Demo:** [cold-outreach-khaki.vercel.app](https://cold-outreach-khaki.vercel.app/)

---

## Overview

This platform automates the complete cold outreach pipeline:

```
CSV Upload → AI Normalization → Icebreaker Generation → Batch Processing → Instantly Campaign Launch
```

**Current Focus:** First campaign launch with 1500 leads using offer-based A/B testing.

---

## Tech Stack

- **Backend:** Python (FastAPI), OpenAI GPT-4o-mini, Supabase (PostgreSQL + Storage)
- **Frontend:** Next.js 15 (App Router, RSC), TypeScript, shadcn/ui, Tailwind CSS
- **Integrations:** Instantly API, Apollo API, Google Sheets API

---

## Features

### ✅ Implemented
- **Leads Database** - Supabase-powered lead management with CSV upload
- **Column Selection** - Airtable-style multi-select for AI transformations
- **Instantly Sync** - Automated campaign and analytics synchronization
- **Analytics Dashboard** - Real-time campaign performance visualizations
- **Script Runner** - Execute Python modules with file uploads
- **Universal Logging** - Centralized logging across Python, FastAPI, Next.js
- **AI Processing** - Mass parallel OpenAI transformations

### 🔄 In Progress
- AI column transformation modal (test mode + custom prompts)
- Website scraping for enhanced icebreakers
- Advanced lead segmentation

### 📋 Planned
- Email sequence builder with A/B testing
- Multi-user authentication
- Apollo API integration page

---

## Current Status

**Version:** 14.0.0 (2025-10-06)

**Latest Updates:**
- Airtable-style column selection for AI transformations
- Leads database UI with Supabase integration
- Universal logging system across platform
- Instantly campaign sync and analytics dashboard

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## For AI: Quick Module Reference

**Production Scripts by Module:**
- **Instantly** → [modules/instantly/README.md](modules/instantly/README.md) - Campaign management, data collection, lead upload
- **CSV Transformer** → [modules/csv_transformer/README.md](modules/csv_transformer/README.md) - AI-powered CSV column transformation
- **OpenAI** → [modules/openai/README.md](modules/openai/README.md) - Mass parallel AI processing
- **Apollo** → [modules/apollo/README.md](modules/apollo/README.md) - Lead collection from Apollo API
- **Scraping** → [modules/scraping/README.md](modules/scraping/README.md) - Website content extraction
- **Sheets** → [modules/sheets/README.md](modules/sheets/README.md) - Google Sheets operations
- **Logging** → [modules/logging/README.md](modules/logging/README.md) - Centralized logging system (Python, FastAPI, Next.js)
- **Shared** → [modules/shared/README.md](modules/shared/README.md) - Common utilities (Google Sheets client)

**By Feature:**
- CSV Processing → modules/csv_transformer/
- Lead Collection → modules/apollo/, modules/scraping/
- Campaign Management → modules/instantly/
- AI Processing → modules/openai/

**Architecture:** See [docs/ADR.md](docs/ADR.md) for architectural decisions

---

## Documentation

### Core Documents
- **[docs/PRD.md](docs/PRD.md)** - Product requirements and vision
- **[CHANGELOG.md](CHANGELOG.md)** - Version history (Keep a Changelog format)
- **[CLAUDE.md](CLAUDE.md)** - Coding guidelines (Python + Next.js)
- **[docs/ADR.md](docs/ADR.md)** - Architecture decision records

### Sprint Documents
- **[docs/sprints/](docs/sprints/)** - Sprint-specific implementation plans
- **Current:** [2025-10-02_first-campaign-launch.md](docs/sprints/2025-10-02_first-campaign-launch.md)

---

## Project Structure

```
├── backend/             # Python FastAPI API
├── frontend/            # Next.js application
│   ├── src/app/         # Next.js App Router pages
│   │   ├── page.tsx           # Home page
│   │   ├── leads/             # Leads database page
│   │   ├── dashboard/         # Instantly analytics
│   │   ├── instantly-sync/    # Campaign sync
│   │   └── script-runner/     # Python script executor
│   ├── src/components/  # React components
│   └── ROUTES.md        # Frontend route documentation
├── modules/             # Processing scripts
│   ├── apollo/          # Apollo API integration
│   ├── instantly/       # Instantly API integration
│   ├── openai/          # AI processing
│   ├── logging/         # Universal logging system
│   ├── scraping/        # Web scraping
│   └── sheets/          # Google Sheets
├── data/                # CSV files and processing results
├── docs/                # Documentation
│   ├── PRD.md           # Product requirements
│   ├── ADR.md           # Architecture decisions
│   └── sprints/         # Sprint plans
└── archive/             # Legacy code
```

### Frontend Pages

See **[frontend/ROUTES.md](frontend/ROUTES.md)** for complete route documentation.

**Active Pages (5):**
- `/` - Home page with navigation
- `/leads` - Leads database with AI column selection
- `/dashboard` - Instantly campaign analytics
- `/instantly-sync` - Campaign synchronization
- `/script-runner` - Python script execution

**API Routes (7):**
- `POST /api/csv-upload` - Upload CSV to Supabase
- `GET /api/leads` - Fetch leads from database
- `GET /api/upload-history` - Upload batch history
- `POST /api/run-script` - Execute Python scripts
- And more (see [frontend/ROUTES.md](frontend/ROUTES.md))

---

## Success Metrics

**Primary Goals:**
- High reply rate and positive responses leading to booked calls
- Scalable processing of 10K-30K leads/month (target: 30K/month by Q2 2025)

**Current Performance:**
- 1.5K leads/campaign with A/B testing capability
- Full pipeline from CSV upload to Instantly campaign operational
- Multi-offer tracking for conversion optimization

---

## Development Approach

**Agentic Coding:** This project is developed using Claude Code (AI-powered development).

**Key Conventions:**
- Python: Functional programming, `snake_case`, embedded configs, no emojis
- Next.js: Server Components first, TypeScript, desktop-first design
- All comments in English, icebreakers in English (or target language)
- Real data only - no mocks in production

See [CLAUDE.md](CLAUDE.md) for complete coding guidelines.

---

## License

**Private Project** - All rights reserved

---

## Links

- **Live Application:** [cold-outreach-khaki.vercel.app](https://cold-outreach-khaki.vercel.app/)
- **GitHub:** [LeonidSvb/cold-outreach](https://github.com/LeonidSvb/cold-outreach)
- **Author:** Leonid Svibunov

---

**Last Updated:** 2025-10-06 (v14.0.0)
