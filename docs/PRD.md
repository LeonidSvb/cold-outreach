# Cold Outreach AI Automation Platform - Product Requirements

Modular AI-powered system for processing 10K-30K leads/month with intelligent personalization and multi-channel outreach.

---

## 1. Vision & Users

### Primary User
Solo entrepreneur running AI automation/lead generation services

### Jobs-to-be-done (JTBD)
- When I have raw CSV leads from various sources, I want to enrich them with AI-powered insights, so I can create highly personalized outreach that converts.
- When I need to scale outreach to 10K+ leads/month, I want modular functions that work independently, so I can mix-match processing based on available data.

---

## 2. Success Metrics

### Primary Goals
- **High reply rate** and positive response rate leading to booked calls
- **Scalable processing** of 10K-30K leads/month (target: 30K/month by Q2 2025)

### Current Status (as of v8.4.0)
- **1.5K leads/campaign** with A/B testing framework
- **CSV upload + normalization** pipeline operational
- **Instantly integration** for cold email campaigns

For detailed changelog see: [CHANGELOG.md](../CHANGELOG.md)

---

## 3. Tech Stack

### Backend
- **Python 3.11+** - Core processing pipeline
- **FastAPI** - REST API endpoints
- **OpenAI GPT-4o-mini** - Icebreaker generation and content analysis
- **Supabase** - PostgreSQL database + Storage for CSV files

### Frontend
- **Next.js 15** - App Router, React Server Components
- **TypeScript** - Type safety
- **shadcn/ui** - UI component library
- **Tailwind CSS** - Styling

### Integrations
- **Instantly API** - Cold email campaign management
- **Apollo API** - Lead enrichment and company data
- **Google Sheets API** - Data export and management

### Data Processing
- **Pandas** - CSV manipulation and transformation
- **ThreadPoolExecutor** - Parallel processing for large batches

---

## 4. Core Architecture

### High-Level Pipeline

```
CSV Upload → Column Detection → Normalization → Enrichment → Icebreaker Generation → Batch Splitting → Upload to Instantly
```

### System Components

**Backend (Python FastAPI)**
- API endpoints for CSV processing
- AI-powered normalization scripts (company names, cities)
- Icebreaker generation engine
- Batch processing and splitting
- Instantly API integration

**Frontend (Next.js)**
- Wizard UI for lead processing workflow
- Offers management interface
- Dashboard for campaign analytics
- File upload and preview system

**Database (Supabase PostgreSQL)**
- Users, Offers, Leads, Batches tables
- Campaigns and Events (Instantly sync)
- Email Accounts tracking
- Multi-user foundation (prepared for future)

**Integrations**
- Instantly: Campaign creation, lead upload, event sync
- Apollo: Lead enrichment (planned)
- Google Sheets: Data export (planned)

---

## 5. Current Status

### ✅ Implemented (from CHANGELOG v8.4.0)

**Infrastructure:**
- Unified CLAUDE.md coding guidelines (Python + Next.js)
- Backend/Frontend separation with monorepo structure
- Supabase Storage integration for CSV files
- Multi-user database foundation (default user_id='1')

**Core Features:**
- CSV Column Transformer with auto-detection
- File upload and metadata tracking
- Instantly campaign analytics integration
- Modular architecture with clean separation

### 🔄 In Progress

**Current Sprint:** [First Campaign Launch](sprints/2025-10-02_first-campaign-launch.md)
- Database schema setup (users, offers, leads, batches, campaigns, events)
- CSV parsing and column mapping
- Company name + city normalization (OpenAI)
- Icebreaker generation (CSV data only, no scraping)
- Batch splitting (200-300 leads per batch)
- Instantly upload with offer tracking
- Event sync from Instantly (bonus)

### 📋 Planned (Future Sprints)

**Enrichment:**
- Website scraping for enhanced icebreakers
- LinkedIn data processing
- Advanced segmentation (seniority, industry)

**Platform:**
- Multi-user authentication + Row Level Security
- Dashboard analytics visualizations
- Email sequence builder
- A/B testing framework

**Optimization:**
- Smart batching and rate limiting
- Cost optimization and performance tuning
- Advanced error recovery mechanisms

---

## 6. Scope Definition

### Must-Have (Current Sprint)
- ✅ CSV upload with flexible field mapping
- ✅ AI-powered normalization (company names, cities)
- ✅ Icebreaker generation using CSV data
- ✅ Batch processing and splitting
- ✅ Instantly campaign upload
- ✅ Offer-based A/B testing

### Nice-to-Have (Next Sprints)
- Website intelligence extraction
- Advanced offer copywriting
- Email sequence generation
- Template performance analytics
- Google Sheets auto-export

### Explicitly Out (Not Planned)
- CRM integrations (Salesforce, HubSpot)
- Real-time notifications
- Complex workflow automation
- Natural language orchestration
- Multi-channel outreach (SMS, LinkedIn)

---

## 7. Quality Standards

### Code Quality
- Self-documenting scripts with embedded analytics
- Comprehensive error handling with detailed logging
- Performance optimization for 30K+ lead processing
- Modular design enabling function reusability

### Data Quality
- Input validation and data cleaning
- Duplicate detection and handling
- Output verification before upload
- Cost tracking and budget monitoring

### User Experience
- Wizard-based UI for step-by-step workflow
- Real-time progress tracking
- Clear error messages and resolution guidance
- Automated analytics and improvement suggestions

---

## 8. Active Sprint

**Current Sprint:** [First Campaign Launch](sprints/2025-10-02_first-campaign-launch.md)

**Timeline:** 2-3 days (2025-10-02)

**Goal:** Launch first real campaign with 1500 leads through complete pipeline

See sprint documentation for:
- Detailed implementation plan
- Database schema
- API endpoints
- Technical decisions
- Timeline and risks

---

## 9. Documentation

### Core Documents
- **[CHANGELOG.md](../CHANGELOG.md)** - Detailed version history
- **[CLAUDE.md](../CLAUDE.md)** - Coding guidelines (Python + Next.js)
- **[ADR.md](ADR.md)** - Architecture decision records

### Sprint Documents
- **[docs/sprints/](sprints/)** - Sprint-specific implementation plans

---

## Notes

- This PRD contains **high-level vision only** - no file paths, no specific implementations
- For detailed technical decisions see: [ADR.md](ADR.md)
- For version history see: [CHANGELOG.md](../CHANGELOG.md)
- For current sprint details see: [Active Sprint](sprints/2025-10-02_first-campaign-launch.md)
- Updated: 2025-10-02 (v8.4.0)
