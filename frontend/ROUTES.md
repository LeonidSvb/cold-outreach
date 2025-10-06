# Frontend Routes Map

**Last Updated:** 2025-10-06 | **Version:** 14.0.0

Complete map of all pages, API routes, and components in the Cold Outreach Platform frontend.

---

## 📄 Pages (User-Facing Routes)

### ✅ Active Pages

| Route | Page File | Purpose | Status | Components Used |
|-------|-----------|---------|--------|----------------|
| `/` | `app/page.tsx` | **Home / Dashboard** - Main navigation hub with module cards | ✅ Active | Button, Link |
| `/leads` | `app/leads/page.tsx` | **Leads Database** - View/manage Supabase leads, CSV upload | ✅ Active | LeadsPreview, UploadHistoryDrawer, FileUpload |
| `/dashboard` | `app/dashboard/page.tsx` | **Instantly Analytics** - Campaign metrics, charts, performance | ✅ Active | Card, Select, Badge, LineChart, BarChart |
| `/instantly-sync` | `app/instantly-sync/page.tsx` | **Instantly Sync** - Sync campaigns/analytics from Instantly API | ✅ Active | Button, Card, Alert, Progress |
| `/script-runner` | `app/script-runner/page.tsx` | **Script Runner** - Execute Python scripts with file uploads | ✅ Active | FileUpload, CsvPreview, ConfigForm, JobStatus |
| `/components-test` | `app/components-test/page.tsx` | **UI Components Test** - Test/showcase shadcn/ui components | ✅ Active | All shadcn/ui components |

### ❌ Planned (Not Implemented)

These routes appear on home page but **do not exist** yet:

| Route | Status | Shown on Home | Should Implement? |
|-------|--------|---------------|------------------|
| `/apollo` | ❌ Not created | Yes (dev status) | **🤔 REVIEW NEEDED** |
| `/openai` | ❌ Not created | Yes (dev status) | **🤔 REVIEW NEEDED** |
| `/scraping` | ❌ Not created | Yes (planned) | **🤔 REVIEW NEEDED** |
| `/sheets` | ❌ Not created | Yes (planned) | **🤔 REVIEW NEEDED** |

**Action Required:** Delete from home page OR create these routes

---

## 🔌 API Routes (Backend Endpoints)

### ✅ Active API Routes

| Endpoint | File | Purpose | Used By | Status |
|----------|------|---------|---------|--------|
| `POST /api/csv-upload` | `app/api/csv-upload/route.ts` | Upload CSV to Supabase leads table | `/leads` page | ✅ Active |
| `GET /api/leads` | `app/api/leads/route.ts` | Fetch leads from Supabase | LeadsPreview component | ✅ Active |
| `GET /api/upload-history` | `app/api/upload-history/route.ts` | Get upload batch history | UploadHistoryDrawer | ✅ Active |
| `GET /api/scripts` | `app/api/scripts/route.ts` | List available Python scripts | `/script-runner` | ✅ Active |
| `POST /api/run-script` | `app/api/run-script/route.ts` | Execute Python script with config | `/script-runner` | ✅ Active |
| `POST /api/upload` | `app/api/upload/route.ts` | Upload file to backend storage | `/script-runner` | ✅ Active |
| `GET /api/files/[fileId]/preview` | `app/api/files/[fileId]/preview/route.ts` | Preview uploaded file data | CsvPreview component | ✅ Active |

### ⚠️ Potentially Unused Routes

**None identified** - all API routes are actively used

---

## 🧩 Components

### 📦 Business Components

| Component | File | Purpose | Used In | Status |
|-----------|------|---------|---------|--------|
| **LeadsPreview** | `components/LeadsPreview.tsx` | Main leads table with column selection, AI transform toolbar | `/leads` | ✅ Active |
| **UploadHistoryDrawer** | `components/UploadHistoryDrawer.tsx` | Side drawer with upload batch history | `/leads` | ✅ Active |
| **ColumnVisibilityDropdown** | `components/ColumnVisibilityDropdown.tsx` | Multi-select column visibility control | LeadsPreview | ✅ Active |
| **FileUpload** | `components/FileUpload.tsx` | Drag-and-drop file upload with validation | `/leads`, `/script-runner` | ✅ Active |
| **CsvPreview** | `components/CsvPreview.tsx` | Preview CSV file data in table | `/script-runner` | ✅ Active |
| **ConfigForm** | `components/ConfigForm.tsx` | Dynamic form for script configuration | `/script-runner` | ✅ Active |
| **JobStatus** | `components/JobStatus.tsx` | Real-time script execution status | `/script-runner` | ✅ Active |

### 🗑️ Obsolete Components (Candidates for Deletion)

| Component | File | Reason | Replaced By | Action |
|-----------|------|--------|-------------|--------|
| **UploadHistory** | `components/UploadHistory.tsx` | Old sidebar version | UploadHistoryDrawer (drawer version) | **🗑️ DELETE** |
| **FilePreview** | `components/FilePreview.tsx` | Not used anywhere | CsvPreview (better version) | **🗑️ DELETE** |

### 🎨 UI Components (shadcn/ui)

All located in `components/ui/`:

- ✅ alert.tsx
- ✅ badge.tsx
- ✅ button.tsx
- ✅ card.tsx
- ✅ checkbox.tsx
- ✅ dialog.tsx
- ✅ dropdown-menu.tsx
- ✅ input.tsx
- ✅ progress.tsx
- ✅ select.tsx
- ✅ sheet.tsx
- ✅ sonner.tsx (toast notifications)
- ✅ table.tsx

---

## 🏗️ Architecture Overview

### Current Flow

```
User Visits Homepage (/)
  ↓
Selects Module Card
  ↓
Routes to Specific Page:
  - /leads → Manage leads from Supabase
  - /dashboard → View Instantly analytics
  - /instantly-sync → Sync data from Instantly
  - /script-runner → Execute Python scripts
  - /components-test → Test UI components
```

### Data Flow (Leads Page Example)

```
/leads page
  ↓
[Upload CSV] → POST /api/csv-upload → Supabase
  ↓
[View Leads] → GET /api/leads → LeadsPreview component
  ↓
[Upload History] → GET /api/upload-history → UploadHistoryDrawer
  ↓
[Select Columns] → ColumnVisibilityDropdown → Transform with AI (WIP)
```

---

## 🔥 Cleanup Actions Required

### 1. Delete Obsolete Components

```bash
# Delete old sidebar component (replaced by drawer)
rm frontend/src/components/UploadHistory.tsx

# Delete unused preview component (replaced by CsvPreview)
rm frontend/src/components/FilePreview.tsx
```

### 2. Fix Home Page

**Issue:** Home page shows 4 unimplemented routes as "Development" or "Planned"

**Options:**
- **A) Remove cards** for `/apollo`, `/openai`, `/scraping`, `/sheets`
- **B) Create placeholder pages** for these routes
- **C) Move to future roadmap section**

**Recommendation:** Remove from home page, add to README roadmap section

### 3. Version Sync

**Issue:** Version mismatch
- Home page shows: `v7.2.0`
- CHANGELOG shows: `v14.0.0`

**Fix:** Update home page stats card to show `v14.0.0`

---

## 📊 Statistics

- **Total Pages:** 6 active, 4 planned (not implemented)
- **Total API Routes:** 7 active
- **Total Business Components:** 7 active, 2 obsolete
- **Total UI Components:** 12 (shadcn/ui)
- **Lines of Code (TSX):** ~3,500 (estimated)

---

## 🎯 Next Steps

1. **Review this document** and decide on cleanup actions
2. **Delete obsolete components** (UploadHistory.tsx, FilePreview.tsx)
3. **Update home page** (remove unimplemented routes OR create them)
4. **Fix version number** (v7.2.0 → v14.0.0)
5. **Create routes.ts constants** (avoid hardcoded URLs)
6. **Update README.md** with frontend section

---

## 📝 Notes

- All components use TypeScript
- Desktop-first design (not mobile-optimized)
- Server Components by default (Client Components marked with 'use client')
- Styling: Tailwind CSS only (no CSS files)
- State: Local useState, no global state management
