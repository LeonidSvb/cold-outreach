#!/usr/bin/env python3
"""
=== PARQUET MANAGER - CENTRAL DATA ACCESS LAYER ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Single Source of Truth for all project data
Provides unified interface for loading, saving, and updating Parquet files

FEATURES:
- Project-specific Parquet files
- Incremental column addition
- Automatic merging on primary key
- Efficient column-based loading
- CSV export with filtering
- Data integrity validation

USAGE:
    from modules.shared.parquet_manager import ParquetManager

    manager = ParquetManager(project='soviet_boots_europe')
    df = manager.load()
    manager.add_columns(new_data, key='place_id')
    manager.export_csv('exports/with_emails.csv', filters={'contact_status': 'with_emails'})
"""

import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
from datetime import datetime


class ParquetManager:
    """
    Central data access layer for project-specific Parquet files

    Manages single source of truth in /data/projects/{project}.parquet
    All enrichment scripts should use this instead of direct file I/O
    """

    def __init__(self, project: str):
        """
        Initialize ParquetManager for a specific project

        Args:
            project: Project name (e.g., 'soviet_boots_europe', 'hvac_usa')
        """
        self.project = project
        self.base_dir = Path(__file__).parent.parent.parent / 'data'
        self.projects_dir = self.base_dir / 'projects'
        self.exports_dir = self.base_dir / 'exports'
        self.file_path = self.projects_dir / f'{project}.parquet'
        self.metadata_path = self.projects_dir / f'{project}_metadata.json'

        # Ensure directories exist
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Check if project Parquet file exists"""
        return self.file_path.exists()

    def load(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load data with optional column filtering

        Args:
            columns: List of column names to load (None = all columns)

        Returns:
            DataFrame with requested columns

        Example:
            df = manager.load(columns=['name', 'website', 'emails'])
        """
        if not self.exists():
            raise FileNotFoundError(f"Project '{self.project}' not found at {self.file_path}")

        if columns:
            return pd.read_parquet(self.file_path, columns=columns)
        return pd.read_parquet(self.file_path)

    def save(self, df: pd.DataFrame, update_metadata: bool = True):
        """
        Save entire dataframe (overwrites existing file)

        Args:
            df: DataFrame to save
            update_metadata: Whether to update metadata file
        """
        df.to_parquet(self.file_path, compression='snappy', index=False)

        if update_metadata:
            self._update_metadata(df)

    def add_columns(self, new_data: pd.DataFrame, key: str = 'place_id',
                    update_existing: bool = True):
        """
        Add new columns to existing data (incremental enrichment)

        Args:
            new_data: DataFrame with new columns to add
            key: Column name to merge on (must exist in both DataFrames)
            update_existing: If True, update existing columns with new values
                            If False, only add new columns (keep existing values)

        Example:
            # Add scraping results
            scraping_data = pd.DataFrame({
                'place_id': [...],
                'emails': [...],
                'scraped_content': [...]
            })
            manager.add_columns(scraping_data, key='place_id')
        """
        if not self.exists():
            # First time - just save new data
            self.save(new_data)
            return

        # Load existing data
        existing = self.load()

        # Merge with new data
        merged = existing.merge(new_data, on=key, how='left', suffixes=('', '_new'))

        # Handle column updates
        for col in new_data.columns:
            if col == key:
                continue

            new_col = f'{col}_new'
            if new_col in merged.columns:
                if update_existing:
                    # Update existing values with new ones (fill NaN from existing)
                    merged[col] = merged[new_col].fillna(merged[col])
                else:
                    # Keep existing values (only fill where missing)
                    merged[col] = merged[col].fillna(merged[new_col])

                # Drop temporary column
                merged.drop(new_col, axis=1, inplace=True)

        # Save updated data
        self.save(merged)

    def export_csv(self, output: str, columns: Optional[List[str]] = None,
                   filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Export filtered data to CSV

        Args:
            output: Output filename (relative to /data/exports/ or absolute path)
            columns: Columns to include in export (None = all)
            filters: Dictionary of column filters
                    Examples:
                    - {'contact_status': 'with_emails'}
                    - {'relevance_score': '>=7'}
                    - {'has_website': True}

        Returns:
            Number of rows exported

        Example:
            # Export leads with emails and high relevance
            manager.export_csv(
                output='soviet_boots_email_outreach.csv',
                columns=['name', 'emails', 'summary', 'relevance_score'],
                filters={'contact_status': 'with_emails', 'relevance_score': '>=7'}
            )
        """
        # Load data
        df = self.load(columns=columns)

        # Apply filters
        if filters:
            for col, condition in filters.items():
                if col not in df.columns:
                    print(f"Warning: Column '{col}' not found, skipping filter")
                    continue

                if isinstance(condition, str) and condition.startswith('>='):
                    threshold = float(condition[2:])
                    df = df[df[col] >= threshold]
                elif isinstance(condition, str) and condition.startswith('<='):
                    threshold = float(condition[2:])
                    df = df[df[col] <= threshold]
                elif isinstance(condition, str) and condition.startswith('>'):
                    threshold = float(condition[1:])
                    df = df[df[col] > threshold]
                elif isinstance(condition, str) and condition.startswith('<'):
                    threshold = float(condition[1:])
                    df = df[df[col] < threshold]
                elif isinstance(condition, bool):
                    df = df[df[col] == condition]
                else:
                    df = df[df[col] == condition]

        # Determine output path
        if Path(output).is_absolute():
            output_path = Path(output)
        else:
            output_path = self.exports_dir / output

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Export
        df.to_csv(output_path, index=False, encoding='utf-8')

        return len(df)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the project data

        Returns:
            Dictionary with data statistics
        """
        if not self.exists():
            return {'error': 'Project not found'}

        df = self.load()

        stats = {
            'project': self.project,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'file_size_mb': round(self.file_path.stat().st_size / (1024 * 1024), 2),
            'missing_values': df.isnull().sum().to_dict(),
            'dtypes': df.dtypes.astype(str).to_dict()
        }

        return stats

    def _update_metadata(self, df: pd.DataFrame):
        """Update metadata file with current state"""
        metadata = {
            'project': self.project,
            'last_updated': datetime.now().isoformat(),
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': list(df.columns),
            'file_size_bytes': self.file_path.stat().st_size,
            'schema_version': '1.0.0'
        }

        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)


def list_projects() -> List[str]:
    """
    List all available projects

    Returns:
        List of project names
    """
    projects_dir = Path(__file__).parent.parent.parent / 'data' / 'projects'
    if not projects_dir.exists():
        return []

    parquet_files = list(projects_dir.glob('*.parquet'))
    return [f.stem for f in parquet_files if not f.stem.endswith('_metadata')]


if __name__ == "__main__":
    print("=== PARQUET MANAGER - Available Projects ===")
    print()

    projects = list_projects()
    if not projects:
        print("No projects found in /data/projects/")
    else:
        print(f"Found {len(projects)} projects:")
        for project in projects:
            manager = ParquetManager(project=project)
            stats = manager.get_stats()
            print(f"\n  {project}:")
            print(f"    - Rows: {stats['total_rows']}")
            print(f"    - Columns: {stats['total_columns']}")
            print(f"    - Size: {stats['file_size_mb']} MB")
