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
- CSV upload with auto-column detection
- AI-powered normalization (company names, cities)
- Icebreaker generation from CSV data
- Batch processing (200-300 leads per batch)
- Instantly campaign integration
- Offer management for A/B testing

### 🔄 In Progress
- Database schema setup (users, offers, leads, batches, campaigns, events)
- Full wizard UI for lead processing workflow
- Event sync from Instantly to Supabase

### 📋 Planned
- Website scraping for enhanced icebreakers
- Advanced segmentation (seniority, industry, company size)
- Email sequence builder
- Dashboard analytics with performance visualizations
- Multi-user authentication

---

## Current Status

**Version:** 8.4.0 (2025-10-02)

**Current Focus:**
- Launch first real campaign with 1500 leads
- Complete CSV → normalization → icebreakers → batch splitting → Instantly upload pipeline
- Implement offer tracking for A/B testing

See [docs/sprints/](docs/sprints/) for detailed sprint documentation.

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
├── modules/             # Processing scripts
│   ├── apollo/          # Apollo API integration
│   ├── instantly/       # Instantly API integration
│   ├── openai/          # AI processing
│   ├── scraping/        # Web scraping
│   └── sheets/          # Google Sheets
├── data/                # CSV files and processing results
├── docs/                # Documentation
│   ├── PRD.md           # Product requirements
│   ├── ADR.md           # Architecture decisions
│   └── sprints/         # Sprint plans
└── archive/             # Legacy code
```

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

**Last Updated:** 2025-10-02 (v8.4.0)
