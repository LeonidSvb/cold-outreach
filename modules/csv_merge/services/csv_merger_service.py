"""
CSV Merger Service - Merge multiple CSV files with conflict resolution
"""
import pandas as pd
from typing import List, Dict, Optional, Literal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.csv_merge.lib.csv_loader import load_csv, get_all_columns
from modules.csv_merge.lib.csv_normalizer import normalize_key_column, deduplicate_by_key


class CSVMergerService:
    """Service for merging multiple CSV files with intelligent conflict resolution"""

    def __init__(
        self,
        key_column: str,
        key_type: Literal['email', 'website', 'generic'] = 'email',
        normalize: bool = True
    ):
        """
        Initialize CSV Merger Service

        Args:
            key_column: Column name to use as merge key
            key_type: Type of key normalization
            normalize: Whether to normalize key column
        """
        self.key_column = key_column
        self.key_type = key_type
        self.normalize = normalize
        self.dataframes: List[pd.DataFrame] = []

    def add_csv(self, file_path: str) -> None:
        """
        Add CSV file to merge queue

        Args:
            file_path: Path to CSV file
        """
        df = load_csv(file_path)

        # Normalize key column if requested
        if self.normalize and self.key_column in df.columns:
            df = normalize_key_column(df, self.key_column, self.key_type)

        self.dataframes.append(df)

    def merge(self) -> pd.DataFrame:
        """
        Merge all loaded DataFrames

        Returns:
            Merged DataFrame with conflict resolution

        Raises:
            ValueError: If no DataFrames loaded or key column missing
        """
        if not self.dataframes:
            raise ValueError("No DataFrames to merge")

        # Start with first DataFrame
        result = self.dataframes[0].copy()

        # Merge each subsequent DataFrame
        for df in self.dataframes[1:]:
            result = self._merge_two(result, df)

        # Final deduplication
        result = deduplicate_by_key(result, self.key_column)

        return result

    def _merge_two(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Merge two DataFrames with conflict resolution

        Conflict resolution strategy:
        - If column exists in both: df2 value overwrites df1 if not null
        - If column only in one: keep that value

        Args:
            df1: First DataFrame
            df2: Second DataFrame

        Returns:
            Merged DataFrame
        """
        # Ensure key column exists in both
        if self.key_column not in df1.columns:
            raise ValueError(f"Key column '{self.key_column}' not in first DataFrame")
        if self.key_column not in df2.columns:
            raise ValueError(f"Key column '{self.key_column}' not in second DataFrame")

        # Outer merge on key column
        merged = pd.merge(
            df1,
            df2,
            on=self.key_column,
            how='outer',
            suffixes=('_old', '_new')
        )

        # Resolve conflicts: prefer new non-null values
        for col in df1.columns:
            if col == self.key_column:
                continue

            old_col = f"{col}_old"
            new_col = f"{col}_new"

            if old_col in merged.columns and new_col in merged.columns:
                # Prefer new value if not null, otherwise keep old
                merged[col] = merged[new_col].combine_first(merged[old_col])
                # Drop temp columns
                merged = merged.drop(columns=[old_col, new_col])
            elif old_col in merged.columns:
                # Only old exists (col not in df2)
                merged = merged.rename(columns={old_col: col})
            elif new_col in merged.columns:
                # Only new exists (col not in df1)
                merged = merged.rename(columns={new_col: col})

        return merged

    def get_stats(self, merged_df: pd.DataFrame) -> Dict[str, any]:
        """
        Get merge statistics

        Args:
            merged_df: Merged DataFrame

        Returns:
            Dictionary with statistics
        """
        return {
            'total_files': len(self.dataframes),
            'unique_keys': merged_df[self.key_column].nunique(),
            'total_rows': len(merged_df),
            'total_columns': len(merged_df.columns),
            'columns': list(merged_df.columns)
        }
