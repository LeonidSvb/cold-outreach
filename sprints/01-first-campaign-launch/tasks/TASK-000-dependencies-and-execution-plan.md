# TASK-000: Dependencies Analysis & Parallel Execution Plan

---

## Purpose

This document analyzes all tasks in Sprint 01 and identifies:
1. Which tasks can run in parallel
2. Which tasks have dependencies and must wait
3. Optimal execution order for maximum speed
4. Critical path through the sprint

**Last Updated:** 2025-10-03

---

## All Tasks Overview

### CSV Upload Flow (TASK-001 to TASK-005)
- **TASK-001**: MCP Supabase Setup & Testing
- **TASK-002**: CSV Column Detection System
- **TASK-003**: Supabase Upload Backend Logic
- **TASK-004**: Frontend Upload Button & UI
- **TASK-005**: E2E Testing & Documentation

### Instantly Sync Flow (TASK-006 to TASK-010)
- **TASK-006**: Supabase Client Library Setup
- **TASK-007**: Instantly JSON Sources Module
- **TASK-008**: Data Transformation for RAW Tables
- **TASK-009**: Instantly Sync Service (Orchestration)
- **TASK-010**: Frontend Sync Page & API Endpoints

---

## Dependency Graph

```
TASK-000 (This doc - no dependencies)
    |
    |
    |--- PARALLEL GROUP A: Infrastructure Setup (Day 1 - Morning) ---
    |    |
    |    ├─ TASK-001 (MCP Supabase) [INDEPENDENT] - 1h
    |    |
    |    └─ TASK-006 (Supabase Client) [INDEPENDENT] - 1h
    |
    |
    |--- PARALLEL GROUP B: Data Processing (Day 1 - Afternoon) ---
    |    |
    |    ├─ CSV Branch:
    |    |  TASK-002 (CSV Detection) [Depends: TASK-001] - 1.5h
    |    |     |
    |    |     └─ TASK-003 (CSV Backend) [Depends: TASK-002, TASK-006] - 2h
    |    |           |
    |    |           └─ TASK-004 (CSV Frontend) [Depends: TASK-003] - 2h
    |    |
    |    └─ Instantly Branch:
    |       TASK-007 (Instantly Sources) [Depends: TASK-006] - 1.5h
    |          |
    |          └─ TASK-008 (Transform) [Depends: TASK-007] - 2h
    |                |
    |                └─ TASK-009 (Sync Service) [Depends: TASK-008] - 2h
    |                      |
    |                      └─ TASK-010 (Frontend) [Depends: TASK-009] - 2h
    |
    |
    └─ TASK-005 (E2E Testing) [Depends: TASK-004, TASK-010] - 1.5h
```

---

## Execution Strategy

### Phase 1: Infrastructure (Parallel - Day 1 Morning)

**Can run simultaneously:**
- ✅ TASK-001: MCP Supabase Setup (1 hour)
- ✅ TASK-006: Supabase Client Library (1 hour)

**Why parallel?**
- TASK-001 = Setup MCP connection (infrastructure config)
- TASK-006 = Create Python library (`backend/lib/supabase_client.py`)
- Zero overlap, different files, different systems

**Time estimate:** 1 hour total (both run in parallel)

---

### Phase 2: Data Modules (Parallel - Day 1 Afternoon)

**After Phase 1 completes, can run simultaneously:**
- ✅ TASK-002: CSV Column Detection [needs TASK-001] - 1.5h
- ✅ TASK-007: Instantly JSON Sources [needs TASK-006] - 1.5h

**Why parallel?**
- TASK-002 = CSV-specific logic (`modules/csv/`)
- TASK-007 = Instantly-specific logic (`modules/instantly/instantly_sources.py`)
- Different data sources, different files, independent logic

**Sequential dependencies within each branch:**
```
CSV Branch:
TASK-002 (Detection) → TASK-003 (Backend) → TASK-004 (Frontend)

Instantly Branch:
TASK-007 (Sources) → TASK-008 (Transform) → TASK-009 (Service) → TASK-010 (Frontend)
```

**Time estimate:** 1.5 hours (parallel execution)

---

### Phase 3: Backend Services (Parallel - Day 2)

**CSV Branch (Sequential within branch):**
```
TASK-003 (CSV Upload Backend) [2h]
    ↓
TASK-004 (CSV Frontend UI) [2h]
```

**Instantly Branch (Sequential within branch):**
```
TASK-008 (Data Transform) [2h]
    ↓
TASK-009 (Sync Service) [2h]
    ↓
TASK-010 (Instantly Frontend) [2h]
```

**Can these branches run parallel?**
- ✅ YES! CSV branch and Instantly branch are completely independent
- Developer can work on TASK-003 + TASK-004 while TASK-008 + TASK-009 + TASK-010 execute
- Different files, different modules, no shared dependencies

**Time estimate:**
- CSV Branch: 4 hours (2h + 2h sequential)
- Instantly Branch: 6 hours (2h + 2h + 2h sequential)
- **With parallelization:** 6 hours total (Instantly is critical path)

---

### Phase 4: Integration Testing (Sequential - Day 3)

**Must wait for:**
- TASK-004 (CSV Frontend) - complete
- TASK-010 (Instantly Frontend) - complete

**Then run:**
- TASK-005 (E2E Testing) - tests both flows end-to-end

**Time estimate:** 1.5 hours

---

## Critical Path Analysis

### Longest Sequential Chain (Instantly Flow):

```
START
  ↓
TASK-006 (Supabase Client) [1h]
  ↓
TASK-007 (Instantly Sources) [1.5h]
  ↓
TASK-008 (Data Transform) [2h]
  ↓
TASK-009 (Sync Service) [2h]
  ↓
TASK-010 (Frontend) [2h]
  ↓
TASK-005 (E2E Testing) [1.5h]
  ↓
DONE
```

**Total critical path:** 10 hours

**With perfect parallelization:** ~10 hours (critical path unchanged, but CSV branch completes earlier)

---

## Optimal Execution Order

### Recommended Sprint Timeline

**DAY 1: Infrastructure + Modules (3.5 hours)**
```
Morning (1 hour):
├─ PARALLEL: TASK-001 (MCP Setup) [1h]
└─ PARALLEL: TASK-006 (Supabase Client) [1h]

Afternoon (2.5 hours):
├─ PARALLEL: TASK-002 (CSV Detection) [1.5h]
└─ PARALLEL: TASK-007 (Instantly Sources) [1.5h]

// Optional: Start TASK-003 or TASK-008 if time permits
```

**DAY 2: Backend + Frontend (7-8 hours)**
```
Morning (4 hours):
├─ PARALLEL: TASK-003 (CSV Backend) [2h] → TASK-004 (CSV Frontend) [2h]
└─ PARALLEL: TASK-008 (Transform) [2h] → Start TASK-009 [partial]

Afternoon (4 hours):
├─ CSV Branch: TASK-004 may finish early
└─ Instantly: TASK-009 (Sync Service) [2h] → TASK-010 (Frontend) [2h]
```

**DAY 3: Testing & Docs (1.5-2 hours)**
```
Morning (2 hours):
└─ SEQUENTIAL: TASK-005 (E2E Testing + Documentation)
```

**Total sprint time:** ~12-13 hours of work across 3 days
**Without parallelization:** ~20+ hours (almost double!)

---

## Task Dependencies Table

| Task | Depends On | Blocks | Can Start After | Estimated Time |
|------|-----------|--------|----------------|----------------|
| TASK-001 | None | TASK-002 | Immediately | 1h |
| TASK-002 | TASK-001 | TASK-003 | 1h | 1.5h |
| TASK-003 | TASK-002, TASK-006 | TASK-004 | 2.5h | 2h |
| TASK-004 | TASK-003 | TASK-005 | 4.5h | 2h |
| TASK-005 | TASK-004, TASK-010 | None (Sprint Done) | 10h | 1.5h |
| TASK-006 | None | TASK-003, TASK-007 | Immediately | 1h |
| TASK-007 | TASK-006 | TASK-008 | 1h | 1.5h |
| TASK-008 | TASK-007 | TASK-009 | 2.5h | 2h |
| TASK-009 | TASK-008 | TASK-010 | 4.5h | 2h |
| TASK-010 | TASK-009 | TASK-005 | 6.5h | 2h |

---

## Parallel Execution Matrix

### What CAN run in parallel:

| Time Slot | Task A | Task B | Why Safe? |
|-----------|--------|--------|-----------|
| Hour 0-1 | TASK-001 (MCP) | TASK-006 (Client) | Different files, different systems |
| Hour 1-2.5 | TASK-002 (CSV) | TASK-007 (Instantly) | Different modules, no overlap |
| Hour 2.5-4.5 | TASK-003 (CSV Backend) | TASK-008 (Transform) | Different data sources |
| Hour 4.5-6.5 | TASK-004 (CSV UI) | TASK-009 (Sync Service) | Frontend vs Backend |
| Hour 6.5-8.5 | Done (CSV complete) | TASK-010 (Instantly UI) | CSV already done |

### What CANNOT run in parallel:

| Task A | Task B | Why Not? |
|--------|--------|----------|
| TASK-006 | TASK-007 | TASK-007 needs TASK-006 client library |
| TASK-007 | TASK-008 | TASK-008 needs TASK-007 sources output |
| TASK-008 | TASK-009 | TASK-009 needs TASK-008 transform functions |
| TASK-009 | TASK-010 | TASK-010 needs TASK-009 service endpoints |
| TASK-004 | TASK-005 | TASK-005 needs TASK-004 frontend complete |
| TASK-010 | TASK-005 | TASK-005 needs TASK-010 frontend complete |

---

## Risk Analysis

### High-Risk Blockers (Must succeed)

**TASK-006 (Supabase Client):**
- ⚠️ **Blocks:** TASK-003, TASK-007 (entire Instantly flow + CSV backend)
- **Impact:** If fails, blocks 7 other tasks
- **Mitigation:** Start Day 1, validate connection immediately with test query
- **Fallback:** Use direct `supabase-py` SDK if custom wrapper has issues

**TASK-001 (MCP Setup):**
- ⚠️ **Blocks:** TASK-002 (CSV detection needs DB schema)
- **Impact:** Medium - only blocks CSV branch
- **Mitigation:** OAuth might require manual browser intervention
- **Fallback:** Skip MCP, use Python Supabase SDK directly for queries

### Medium-Risk Dependencies

**TASK-008 (Data Transform):**
- ⚠️ **Blocks:** TASK-009, TASK-010
- **Risk:** Complex JSON → SQL transformation logic
- **Mitigation:** Use real data (`raw_data_20250921_125555.json`) for testing
- **Fallback:** Implement simplified transform (campaigns only, skip accounts/daily)

**TASK-009 (Sync Service):**
- ⚠️ **Blocks:** TASK-010 (Frontend)
- **Risk:** Orchestration complexity (3 modules integration)
- **Mitigation:** Test each helper function independently
- **Fallback:** Start with campaigns-only sync, add accounts later

---

## Parallel Execution Tips

### When to parallelize:
1. ✅ Different file paths (no edit conflicts)
2. ✅ Different modules (csv vs instantly)
3. ✅ Independent data sources
4. ✅ No shared dependencies
5. ✅ Frontend + Backend work (can split if needed)

### When NOT to parallelize:
1. ❌ Same file being edited
2. ❌ Sequential data flow (sources → transform → sync)
3. ❌ Shared configuration files (.env, main.py)
4. ❌ Testing phases (need complete system running)

### Example Parallel Sessions:

**Session 1 (Morning - 1h):**
```
Terminal 1: Work on TASK-001 (MCP Setup)
Terminal 2: Work on TASK-006 (Supabase Client)
Both complete at same time
```

**Session 2 (Afternoon - 1.5h):**
```
Terminal 1: Work on TASK-002 (CSV Detection)
Terminal 2: Work on TASK-007 (Instantly Sources)
Both complete at same time
```

**Session 3 (Day 2 - 6h):**
```
Branch A: TASK-003 → TASK-004 (CSV flow, 4h total)
Branch B: TASK-008 → TASK-009 → TASK-010 (Instantly flow, 6h total)
Work on both branches simultaneously
```

---

## Success Criteria

**Sprint considered complete when:**

- [ ] All 10 tasks (TASK-001 to TASK-010) status = "done"
- [ ] CSV upload flow: CSV file → Supabase → visible in DB
- [ ] Instantly sync flow: JSON file → RAW tables → data persisted
- [ ] E2E tests passing (TASK-005)
- [ ] Documentation complete for both flows

**Minimum Viable Success (MVP):**
- [ ] TASK-006 (Supabase Client) - working connection
- [ ] TASK-009 (Instantly Sync) - campaigns sync functional
- [ ] TASK-010 (Frontend) - can upload JSON and see results
- [ ] At least one end-to-end flow complete (Instantly OR CSV)

**Nice to Have:**
- [ ] Both flows complete (Instantly AND CSV)
- [ ] Daily analytics sync working
- [ ] API sync mode (placeholder implemented)

---

## Quick Start Guide for AI Agent

### Before starting ANY task:

1. **Check dependencies:**
   ```
   Read TASK-XXX.md → Look at "dependencies" field
   If empty [] → Can start immediately
   If has items → Check those tasks are "done" first
   ```

2. **Verify prerequisites:**
   ```
   Read "Plan Konteksta" → "V nachale" section
   All files listed must exist before starting
   ```

3. **Identify parallel opportunities:**
   ```
   Check TASK-000 (this file) → Parallel Execution Matrix
   If another task can run parallel → mention it to user
   ```

### Execution checklist:

- [ ] Read full task .md file
- [ ] Confirm all dependencies complete
- [ ] Check all "V nachale" files exist
- [ ] Execute each step in "Poshagovyy Plan"
- [ ] Run tests in "Strategiya Testirovaniya"
- [ ] Verify all "Kriterii Priyomki" checked
- [ ] Mark task as complete

---

## Visual Sprint Timeline

```
DAY 1 (3.5 hours)
========================================================
Hour 0-1    | TASK-001 MCP Setup         | [PARALLEL]
            | TASK-006 Supabase Client   |
--------------------------------------------------------
Hour 1-2.5  | TASK-002 CSV Detection     | [PARALLEL]
            | TASK-007 Instantly Sources |
========================================================

DAY 2 (7-8 hours)
========================================================
Hour 0-2    | TASK-003 CSV Backend       | [PARALLEL]
            | TASK-008 Transform         |
--------------------------------------------------------
Hour 2-4    | TASK-004 CSV Frontend      | [PARALLEL]
            | TASK-009 Sync Service      |
--------------------------------------------------------
Hour 4-6    | (CSV Done - Can rest)      | [PARALLEL]
            | TASK-010 Instantly Frontend|
========================================================

DAY 3 (1.5 hours)
========================================================
Hour 0-1.5  | TASK-005 E2E Testing       | [SEQUENTIAL]
========================================================

TOTAL: 12-13 hours of focused work
```

---

**Document Version:** 2.0 (Updated with all 10 tasks)
**Sprint:** First Campaign Launch
**Status:** Analysis Complete - Ready for Execution
**Critical Path:** 10 hours (TASK-006 → TASK-007 → TASK-008 → TASK-009 → TASK-010 → TASK-005)
