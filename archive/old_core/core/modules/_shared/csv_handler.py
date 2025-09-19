#!/usr/bin/env python3
"""
=== FLEXIBLE CSV HANDLER ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Universal CSV operations for modular functions - auto-detect columns, flexible processing

FEATURES:
- Auto-detect relevant columns in any CSV structure
- Safe column updates without data loss
- Backup creation before modifications  
- Progress tracking for large files
- UTF-8 handling for international data
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class FlexibleCSVHandler:
    """Universal CSV handler for modular workflow"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.column_mapping = {}
        self.backup_created = False
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
        self._load_csv()
        self._analyze_columns()
    
    def _load_csv(self):
        """Load CSV with proper encoding detection"""
        try:
            # Try UTF-8 first
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                # Fallback to CP1251 for Russian data
                self.df = pd.read_csv(self.csv_path, encoding='cp1251')
            except:
                # Last resort - ignore errors
                self.df = pd.read_csv(self.csv_path, encoding='utf-8', errors='ignore')
    
    def _analyze_columns(self):
        """Auto-detect column types and suggest mappings"""
        columns = self.df.columns.tolist()
        
        # Common column patterns
        patterns = {
            'website': ['website', 'url', 'domain', 'site', 'web', 'компания_сайт'],
            'company': ['company', 'name', 'компания', 'название', 'firm', 'business'],
            'email': ['email', 'mail', 'contact', 'почта', '@'],
            'phone': ['phone', 'tel', 'телефон', 'номер'],
            'links': ['links', 'urls', 'pages', 'ссылки'],
            'content': ['content', 'data', 'text', 'контент', 'данные'],
            'summary': ['summary', 'description', 'about', 'описание', 'резюме']
        }
        
        detected = {}
        for col in columns:
            col_lower = col.lower()
            for field, keywords in patterns.items():
                if any(keyword in col_lower for keyword in keywords):
                    detected[field] = col
                    break
        
        self.column_mapping = detected
        print(f"Auto-detected columns: {detected}")
    
    def set_column_mapping(self, mapping: Dict[str, str]):
        """Override auto-detected column mapping"""
        self.column_mapping.update(mapping)
    
    def get_column_mapping(self) -> Dict[str, str]:
        """Get current column mapping"""
        return self.column_mapping
    
    def create_backup(self):
        """Create backup of original CSV"""
        if not self.backup_created:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.csv_path.parent / f"{self.csv_path.stem}_backup_{timestamp}.csv"
            self.df.to_csv(backup_path, index=False, encoding='utf-8')
            self.backup_created = True
            print(f"Backup created: {backup_path}")
    
    def update_column(self, field: str, row_index: int, value: Any):
        """Update single cell safely"""
        if field not in self.column_mapping:
            # Create new column if it doesn't exist
            column_name = field
            self.column_mapping[field] = column_name
            self.df[column_name] = None
        else:
            column_name = self.column_mapping[field]
        
        self.df.at[row_index, column_name] = value
    
    def update_column_bulk(self, field: str, values: List[Any]):
        """Update entire column with list of values"""
        if len(values) != len(self.df):
            raise ValueError(f"Values count ({len(values)}) doesn't match rows count ({len(self.df)})")
        
        if field not in self.column_mapping:
            column_name = field
            self.column_mapping[field] = column_name
        else:
            column_name = self.column_mapping[field]
        
        self.df[column_name] = values
    
    def get_rows_for_processing(self, field: str, filter_empty: bool = True) -> List[Tuple[int, Any]]:
        """Get rows that need processing for specific field"""
        if field not in self.column_mapping:
            # All rows need processing
            target_column = self.column_mapping.get('website', self.df.columns[0])
            return [(i, row[target_column]) for i, row in self.df.iterrows()]
        
        column_name = self.column_mapping[field]
        
        if filter_empty:
            # Only rows where target field is empty
            mask = self.df[column_name].isna() | (self.df[column_name] == '')
            filtered_df = self.df[mask]
        else:
            # All rows
            filtered_df = self.df
        
        # Return (index, source_value) pairs
        source_field = self.column_mapping.get('website', self.df.columns[0])
        return [(i, row[source_field]) for i, row in filtered_df.iterrows()]
    
    def save(self, output_path: Optional[str] = None):
        """Save CSV with modifications"""
        save_path = Path(output_path) if output_path else self.csv_path
        self.df.to_csv(save_path, index=False, encoding='utf-8')
        print(f"CSV saved: {save_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get CSV statistics"""
        return {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "detected_fields": list(self.column_mapping.keys()),
            "column_mapping": self.column_mapping,
            "file_path": str(self.csv_path),
            "encoding": "utf-8"
        }
    
    def preview(self, rows: int = 5) -> str:
        """Get preview of CSV data"""
        return self.df.head(rows).to_string()

# Export main class
__all__ = ['FlexibleCSVHandler']