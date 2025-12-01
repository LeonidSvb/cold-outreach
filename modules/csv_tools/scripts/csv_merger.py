#!/usr/bin/env python3
"""
=== CSV MERGER - Universal CSV Merge Tool ===
Version: 1.0.0 | Created: 2025-01-25

PURPOSE:
Flexible CSV merging utility with support for various merge strategies,
column mapping, filtering, and deduplication.

FEATURES:
- Multiple merge strategies (left, right, inner, outer)
- Column mapping and renaming
- Data filtering by column values
- Deduplication options
- Automatic encoding detection
- Preservation of all relevant columns

USAGE:
from modules.csv_tools.scripts.csv_merger import CSVMerger

merger = CSVMerger()
result = merger.merge_files(
    file1='path/to/file1.csv',
    file2='path/to/file2.csv',
    merge_on='name',
    merge_how='left',
    filters={'Result': ['deliverable', 'risky']}
)
merger.save_result(result, 'output.csv')
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.shared.logging.universal_logger import get_logger

logger = get_logger(__name__)


class CSVMerger:
    """Universal CSV merging utility with flexible configuration"""

    def __init__(self):
        self.version = "1.0.0"
        self.stats = {
            "total_merges": 0,
            "last_merge": None,
            "success_rate": 0.0
        }

    def read_csv(
        self,
        file_path: str,
        encoding: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Read CSV file with automatic encoding detection

        Args:
            file_path: Path to CSV file
            encoding: Force specific encoding (default: auto-detect)
            columns: Select only specific columns

        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Reading CSV file: {file_path}")

        encodings = [encoding] if encoding else ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                if columns:
                    missing = set(columns) - set(df.columns)
                    if missing:
                        logger.warning(f"Missing columns: {missing}")
                    df = df[[col for col in columns if col in df.columns]]

                logger.info(f"Successfully read {len(df)} rows with encoding: {enc}")
                return df
            except (UnicodeDecodeError, Exception) as e:
                if enc == encodings[-1]:
                    logger.error(f"Failed to read CSV with all encodings", error=e)
                    raise
                continue

    def merge_files(
        self,
        file1: str,
        file2: str,
        merge_on: Union[str, List[str]],
        merge_how: str = 'left',
        suffixes: tuple = ('', '_from_file2'),
        filters: Optional[Dict[str, List[Any]]] = None,
        normalize_merge_key: bool = True,
        drop_duplicates: Optional[str] = None,
        column_mapping: Optional[Dict[str, Dict[str, str]]] = None
    ) -> pd.DataFrame:
        """
        Merge two CSV files with flexible options

        Args:
            file1: Path to first CSV (primary)
            file2: Path to second CSV (secondary)
            merge_on: Column name(s) to merge on
            merge_how: Merge strategy - 'left', 'right', 'inner', 'outer'
            suffixes: Suffixes for overlapping columns
            filters: Dict of column filters {column: [allowed_values]}
            normalize_merge_key: Normalize merge key (lowercase, strip)
            drop_duplicates: Column to deduplicate on (None = no dedup)
            column_mapping: Rename columns {file: {old: new}}

        Returns:
            Merged DataFrame
        """
        logger.info(f"Starting merge operation: {merge_how} join")

        try:
            # Read files
            df1 = self.read_csv(file1)
            df2 = self.read_csv(file2)

            logger.info(f"File 1: {len(df1)} rows, {len(df1.columns)} columns")
            logger.info(f"File 2: {len(df2)} rows, {len(df2.columns)} columns")

            # Apply column mapping if provided
            if column_mapping:
                if 'file1' in column_mapping:
                    df1 = df1.rename(columns=column_mapping['file1'])
                if 'file2' in column_mapping:
                    df2 = df2.rename(columns=column_mapping['file2'])

            # Normalize merge keys
            merge_keys = [merge_on] if isinstance(merge_on, str) else merge_on

            if normalize_merge_key:
                for key in merge_keys:
                    if key in df1.columns:
                        df1[f'{key}_normalized'] = df1[key].astype(str).str.lower().str.strip()
                    if key in df2.columns:
                        df2[f'{key}_normalized'] = df2[key].astype(str).str.lower().str.strip()
                merge_keys_norm = [f'{k}_normalized' for k in merge_keys]
            else:
                merge_keys_norm = merge_keys

            # Apply filters before merge
            if filters:
                for col, values in filters.items():
                    if col in df1.columns:
                        before = len(df1)
                        df1 = df1[df1[col].isin(values)]
                        logger.info(f"Filtered df1 by {col}: {before} -> {len(df1)} rows")

            # Perform merge
            result = pd.merge(
                df1,
                df2,
                left_on=merge_keys_norm,
                right_on=merge_keys_norm,
                how=merge_how,
                suffixes=suffixes
            )

            logger.info(f"Merge result: {len(result)} rows")

            # Remove normalized columns if they were created
            if normalize_merge_key:
                cols_to_drop = [col for col in result.columns if col.endswith('_normalized')]
                result = result.drop(columns=cols_to_drop)

            # Deduplicate if requested
            if drop_duplicates:
                before = len(result)
                result = result.drop_duplicates(subset=[drop_duplicates], keep='first')
                logger.info(f"Deduplicated by {drop_duplicates}: {before} -> {len(result)} rows")

            # Update stats
            self.stats['total_merges'] += 1
            self.stats['last_merge'] = datetime.now().isoformat()

            logger.info(f"Merge completed successfully")
            return result

        except Exception as e:
            logger.error(f"Merge operation failed", error=e)
            raise

    def save_result(
        self,
        df: pd.DataFrame,
        output_path: str,
        include_timestamp: bool = True
    ) -> str:
        """
        Save merged DataFrame to CSV

        Args:
            df: DataFrame to save
            output_path: Output file path
            include_timestamp: Add timestamp to filename

        Returns:
            Final output path
        """
        try:
            if include_timestamp:
                path = Path(output_path)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = str(path.parent / f"{path.stem}_{timestamp}{path.suffix}")

            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"Saved {len(df)} rows to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to save CSV", error=e)
            raise

    def get_stats(self) -> Dict:
        """Get merger statistics"""
        return self.stats


def quick_merge(
    file1: str,
    file2: str,
    merge_on: str,
    output: str,
    how: str = 'left',
    filters: Optional[Dict] = None
) -> str:
    """
    Quick merge utility function

    Args:
        file1: Primary CSV file
        file2: Secondary CSV file
        merge_on: Column to merge on
        output: Output file path
        how: Merge strategy
        filters: Optional filters

    Returns:
        Output file path
    """
    merger = CSVMerger()
    result = merger.merge_files(
        file1=file1,
        file2=file2,
        merge_on=merge_on,
        merge_how=how,
        filters=filters
    )
    return merger.save_result(result, output)


if __name__ == "__main__":
    # Example usage
    logger.info("CSV Merger Module - Ready for use")
    logger.info("Import this module to use: from modules.csv_tools.scripts.csv_merger import CSVMerger")
