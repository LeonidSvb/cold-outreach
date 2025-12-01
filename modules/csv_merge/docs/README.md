# CSV Merger Module

Universal CSV merging tool with intelligent key normalization and conflict resolution.

## Features

- Merge unlimited CSV files by common key
- Auto-detect merge keys (email, website, or custom)
- Intelligent normalization:
  - **Email**: lowercase, trim, remove `mailto:`, validate `@`
  - **Website**: extract clean domain (remove protocol, www, path, params)
  - **Generic**: lowercase + trim
- Smart conflict resolution (latest non-null values win)
- Deduplication by merge key
- Streamlit UI integration

## Architecture

Following **atomic modular philosophy**:

```
csv_merge/
├── lib/                              # ATOMS (pure functions)
│   ├── csv_loader.py                 # Load CSV, detect encoding
│   ├── csv_key_detector.py           # Auto-detect merge keys
│   ├── csv_cleaner.py                # Normalize email/website/generic
│   └── csv_normalizer.py             # Apply normalization to DataFrames
├── services/
│   └── csv_merger_service.py         # SERVICE (merge logic)
└── docs/
    └── README.md
```

## Usage

### Via Streamlit UI

```bash
streamlit run modules/ui/main_app.py
```

Navigate to **"CSV Merger"** tab.

### Programmatic

```python
from modules.csv_merge.services.csv_merger_service import CSVMergerService

# Initialize merger
merger = CSVMergerService(
    key_column='email',
    key_type='email',
    normalize=True
)

# Add files
merger.add_csv('file1.csv')
merger.add_csv('file2.csv')
merger.add_csv('file3.csv')

# Merge
merged_df = merger.merge()
stats = merger.get_stats(merged_df)

# Save
merged_df.to_csv('merged_output.csv', index=False)
```

## Key Types

| Type | Normalization | Example |
|------|---------------|---------|
| `email` | Lowercase, trim, remove mailto:, validate @ | `John@Example.COM` → `john@example.com` |
| `website` | Extract domain, remove www/protocol/path | `https://www.apple.com/iphone` → `apple.com` |
| `generic` | Lowercase, trim | `  New York  ` → `new york` |

## Conflict Resolution

When same key has different values in different files:

1. **Latest non-null wins**: Last file's value overwrites previous if not empty
2. **Preserve non-empty**: Empty values never overwrite existing values
3. **Union columns**: All columns from all files are included

## Example

**Input files:**

`leads1.csv`:
```csv
email,company,phone
john@apple.com,Apple,123-456
jane@google.com,Google,
```

`leads2.csv`:
```csv
email,website,phone
john@apple.com,apple.com,111-222
```

**Merged output:**
```csv
email,company,phone,website
john@apple.com,Apple,111-222,apple.com
jane@google.com,Google,,
```

## Requirements

- pandas
- python 3.10+

## Integration

CSV Merger is integrated as **4th tab** in Unified Streamlit Platform (`modules/ui/main_app.py`).

No code duplication - reuses `modules/shared/` utilities.
