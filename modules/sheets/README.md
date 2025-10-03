# Sheets Module

**Priority:** Low
**Status:** Production Ready (not used in current sprint)
**Used In:** Google Sheets operations (on-demand)

---

## Quick Info

**Purpose:** Advanced Google Sheets batch operations and data processing

**Scripts:** 2 production scripts
**Dependencies:** Google Sheets API credentials

---

## Scripts

### sheets_mass_updater.py
**Purpose:** Advanced Google Sheets batch operations
**Features:**
- 50+ concurrent operations
- Batch read/write optimization
- Backup creation before updates
- Error recovery and retry logic
- Real-time progress tracking

**Usage:**
```bash
cd modules/sheets
python sheets_mass_updater.py
```

**Configuration:** Edit CONFIG section in script
```python
CONFIG = {
    "CONCURRENT_OPERATIONS": 50,
    "BATCH_SIZE": 100,
    "CREATE_BACKUP": True
}
```

**Output:** Updated Google Sheets + backup copy

---

### sheets_data_processor.py
**Purpose:** Process data from/to Google Sheets
**Features:**
- Data validation and cleaning
- Format conversion
- Batch processing
- Integration with other modules

**Usage:**
```bash
python sheets_data_processor.py
```

**Output:** Processed data in Google Sheets

---

## Data Structure

```
modules/sheets/
├── sheets_mass_updater.py      # Batch operations
├── sheets_data_processor.py    # Data processing
└── results/                    # Operation logs (timestamped)
```

---

## Configuration

**Required Credentials:**
- Google Sheets API credentials (JSON file)
- OAuth 2.0 authentication

**Location:** Root directory (credentials.json)

**Shared Utilities:**
- modules/shared/google_sheets.py - Core Sheets client

---

## Performance Metrics

**Processing Speed:**
- 50+ concurrent operations
- Batch optimization for large sheets
- Efficient API quota usage

**Use Cases:**
- Data export from Sheets to CSV
- Bulk updates to existing sheets
- Integration with lead pipelines

---

## Integration

**Used By:**
- Data import/export operations
- Backup and recovery systems
- Alternative to CSV uploads

**Compatible With:**
- modules/csv_transformer/ - Data transformation
- modules/instantly/ - Lead export
- data/ - CSV pipeline

---

## Documentation

**Related ADRs:**
- None yet (established functionality)

**Sprint Docs:**
- Not in current sprint (low priority)

**Shared Utilities:**
- modules/shared/google_sheets.py - Core client

---

**Last Updated:** 2025-10-03
