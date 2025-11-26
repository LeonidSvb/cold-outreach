# CSV Tools Module

Universal CSV merging and manipulation utilities for the Cold Outreach Automation Platform.

## Features

- **Flexible CSV Merging**: Support for left, right, inner, and outer joins
- **Smart Column Mapping**: Rename and map columns between files
- **Data Filtering**: Filter rows by column values before/after merge
- **Deduplication**: Remove duplicate entries based on specified columns
- **Encoding Detection**: Automatically handles UTF-8, Latin1, CP1252 encodings
- **Normalized Matching**: Case-insensitive and whitespace-tolerant key matching
- **Logging**: Built-in logging with universal_logger integration

## Module Structure

```
csv_tools/
├── docs/
│   └── README.md          # This file
├── scripts/
│   ├── csv_merger.py      # Universal CSV merger class
│   └── merge_soviet_boots_leads.py  # Example implementation
└── results/               # Output directory for merged files
```

## Quick Start

### Basic Merge

```python
from modules.csv_tools.scripts.csv_merger import CSVMerger

merger = CSVMerger()
result = merger.merge_files(
    file1='file1.csv',
    file2='file2.csv',
    merge_on='name',
    merge_how='left'
)
merger.save_result(result, 'output.csv')
```

### Merge with Filters

```python
# Keep only verified emails (deliverable + risky)
result = merger.merge_files(
    file1='verified_emails.csv',
    file2='locations.csv',
    merge_on='name',
    merge_how='left',
    filters={'Result': ['deliverable', 'risky']}
)
```

### Advanced Options

```python
result = merger.merge_files(
    file1='primary.csv',
    file2='secondary.csv',
    merge_on=['name', 'email'],           # Multiple merge keys
    merge_how='inner',                     # Only matching rows
    normalize_merge_key=True,              # Case-insensitive match
    drop_duplicates='email',               # Remove duplicate emails
    suffixes=('', '_secondary'),           # Handle overlapping columns
    column_mapping={                       # Rename columns
        'file1': {'old_name': 'new_name'},
        'file2': {'company': 'name'}
    }
)
```

## Merge Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `left` | Keep all rows from file1, add matching data from file2 | Add extra data to primary list |
| `right` | Keep all rows from file2, add matching data from file1 | Primary data is in file2 |
| `inner` | Keep only rows that exist in both files | Only want exact matches |
| `outer` | Keep all rows from both files | Combine all data |

## CSVMerger Class

### Methods

#### `read_csv(file_path, encoding=None, columns=None)`
Read CSV file with automatic encoding detection.

**Parameters:**
- `file_path` (str): Path to CSV file
- `encoding` (str, optional): Force specific encoding
- `columns` (list, optional): Select only specific columns

**Returns:** pandas.DataFrame

#### `merge_files(...)`
Merge two CSV files with flexible options.

**Parameters:**
- `file1` (str): Path to first CSV (primary)
- `file2` (str): Path to second CSV (secondary)
- `merge_on` (str | list): Column name(s) to merge on
- `merge_how` (str): Merge strategy - 'left', 'right', 'inner', 'outer'
- `suffixes` (tuple): Suffixes for overlapping columns (default: ('', '_from_file2'))
- `filters` (dict, optional): Filter rows {column: [allowed_values]}
- `normalize_merge_key` (bool): Normalize keys (lowercase, strip) - default: True
- `drop_duplicates` (str, optional): Column to deduplicate on
- `column_mapping` (dict, optional): Rename columns {file: {old: new}}

**Returns:** pandas.DataFrame

#### `save_result(df, output_path, include_timestamp=True)`
Save merged DataFrame to CSV.

**Parameters:**
- `df` (DataFrame): DataFrame to save
- `output_path` (str): Output file path
- `include_timestamp` (bool): Add timestamp to filename - default: True

**Returns:** str (final output path)

## Examples

### Example 1: Merge Verified Leads with Location Data

```python
from modules.csv_tools.scripts.csv_merger import CSVMerger

merger = CSVMerger()

# File 1: verified_emails.csv (name, email, Result, website)
# File 2: locations.csv (name, state, phone, address)

result = merger.merge_files(
    file1='verified_emails.csv',
    file2='locations.csv',
    merge_on='name',
    merge_how='left',
    filters={'Result': ['deliverable', 'risky']},
    normalize_merge_key=True
)

output_file = merger.save_result(result, 'modules/csv_tools/results/merged_leads.csv')
print(f"Saved to: {output_file}")
```

### Example 2: Quick Merge Function

```python
from modules.csv_tools.scripts.csv_merger import quick_merge

output = quick_merge(
    file1='primary.csv',
    file2='secondary.csv',
    merge_on='email',
    output='output.csv',
    how='inner'
)
```

### Example 3: Column Mapping

```python
# Rename columns before merging
result = merger.merge_files(
    file1='apollo_leads.csv',
    file2='google_maps.csv',
    merge_on='name',
    column_mapping={
        'file1': {
            'Company Name': 'name',
            'Email Address': 'email'
        },
        'file2': {
            'Business Name': 'name',
            'Phone Number': 'phone'
        }
    }
)
```

## Command Line Usage

Run the Soviet Boots example:

```bash
python modules/csv_tools/scripts/merge_soviet_boots_leads.py
```

Create your own merge script:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger
from modules.csv_tools.scripts.csv_merger import CSVMerger

logger = get_logger(__name__)

def main():
    merger = CSVMerger()

    result = merger.merge_files(
        file1='path/to/file1.csv',
        file2='path/to/file2.csv',
        merge_on='name',
        merge_how='left'
    )

    merger.save_result(result, 'modules/csv_tools/results/output.csv')
    logger.info("Merge completed!")

if __name__ == "__main__":
    main()
```

## Best Practices

1. **Always filter data early**: Use the `filters` parameter to reduce data size before merging
2. **Normalize merge keys**: Enable `normalize_merge_key=True` for fuzzy name matching
3. **Handle duplicates**: Use `drop_duplicates` when one organization has multiple contacts
4. **Check column overlaps**: Use appropriate `suffixes` to avoid column name conflicts
5. **Use timestamped output**: Keep `include_timestamp=True` for version control
6. **Test with small samples**: Test your merge logic on small datasets first

## Troubleshooting

### Issue: "UnicodeDecodeError"
**Solution**: The auto-detection should handle this, but you can force encoding:
```python
df = merger.read_csv('file.csv', encoding='latin1')
```

### Issue: "KeyError: column not found"
**Solution**: Check column names in both files. Use column_mapping to align them.

### Issue: Merge produces too many/few rows
**Solution**:
- Check `merge_how` strategy
- Verify merge keys match between files
- Enable `normalize_merge_key=True` for fuzzy matching

### Issue: Duplicate columns (name_x, name_y)
**Solution**: Use `suffixes` parameter:
```python
suffixes=('', '_raw')  # Keep original names from file1
```

## Version History

### v1.0.0 (2025-01-25)
- Initial release
- Universal CSV merger with flexible options
- Support for multiple merge strategies
- Column mapping and filtering
- Automatic encoding detection
- Integration with universal_logger
