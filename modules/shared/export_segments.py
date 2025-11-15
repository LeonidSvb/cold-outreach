#!/usr/bin/env python3
"""
=== EXPORT SEGMENTS FOR MANUAL ICEBREAKERS ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Export Soviet Boots leads into 3 segmented CSV files for manual icebreaker writing

SEGMENTS:
1. museums.csv - 891 leads
2. militaria_stores.csv - 376 leads
3. other_mixed.csv - 143 leads (collectors, reenactment, historical_society, etc.)

USAGE:
python modules/shared/export_segments.py

OUTPUTS:
data/exports/soviet_boots_museums.csv
data/exports/soviet_boots_militaria_stores.csv
data/exports/soviet_boots_other_mixed.csv
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.shared.parquet_manager import ParquetManager

def create_insights_column(df):
    """
    Combine personalization fields into single insights column
    """
    def format_insights(row):
        parts = []

        if pd.notna(row.get('personalization_hooks')):
            parts.append(f"HOOKS: {row['personalization_hooks']}")

        focus_parts = []
        if pd.notna(row.get('focus_wars')):
            focus_parts.append(f"Wars: {row['focus_wars']}")
        if pd.notna(row.get('focus_periods')):
            focus_parts.append(f"Periods: {row['focus_periods']}")
        if pd.notna(row.get('focus_topics')):
            focus_parts.append(f"Topics: {row['focus_topics']}")

        if focus_parts:
            parts.append("FOCUS: " + " | ".join(focus_parts))

        if pd.notna(row.get('summary')):
            parts.append(f"SUMMARY: {row['summary']}")

        return "\n\n".join(parts) if parts else ""

    df['insights_for_personalization'] = df.apply(format_insights, axis=1)
    return df

def main():
    print("=== EXPORTING SEGMENTED CSVs ===\n")

    # Load data
    manager = ParquetManager(project='soviet_boots_europe')
    df = manager.load()

    print(f"Total leads: {len(df):,}")

    # Filter only leads with emails
    df_with_emails = df[
        (df['emails'].notna()) &
        (df['emails'] != '')
    ].copy()

    print(f"Leads with emails: {len(df_with_emails):,}\n")

    # Select columns for export
    export_columns = [
        'name',
        'type',
        'emails',
        'website',
        'phone',
        'focus_wars',
        'focus_periods',
        'focus_topics',
        'personalization_hooks',
        'summary',
        'relevance_score',
        'relevance_reasoning',
        'contact_status',
        'insights_for_personalization'
    ]

    # Create insights column
    df_with_emails = create_insights_column(df_with_emails)

    # Export directory
    export_dir = Path('data/exports')
    export_dir.mkdir(exist_ok=True)

    # Segment 1: Museums
    museums = df_with_emails[df_with_emails['type'] == 'museum'].copy()
    museums_file = export_dir / 'soviet_boots_museums.csv'
    museums[export_columns].to_csv(museums_file, index=False, encoding='utf-8-sig')
    print(f"[OK] Museums: {len(museums):,} leads -> {museums_file}")

    # Segment 2: Militaria Stores
    stores = df_with_emails[df_with_emails['type'] == 'militaria_store'].copy()
    stores_file = export_dir / 'soviet_boots_militaria_stores.csv'
    stores[export_columns].to_csv(stores_file, index=False, encoding='utf-8-sig')
    print(f"[OK] Militaria Stores: {len(stores):,} leads -> {stores_file}")

    # Segment 3: Other Mixed
    other = df_with_emails[
        ~df_with_emails['type'].isin(['museum', 'militaria_store'])
    ].copy()
    other_file = export_dir / 'soviet_boots_other_mixed.csv'
    other[export_columns].to_csv(other_file, index=False, encoding='utf-8-sig')
    print(f"[OK] Other Mixed: {len(other):,} leads -> {other_file}")

    print(f"\n[OK] Total exported: {len(museums) + len(stores) + len(other):,} leads")
    print(f"\nFiles saved to: {export_dir.absolute()}")

    # Show type breakdown for other_mixed
    print("\nOther Mixed breakdown:")
    print(other['type'].value_counts().to_string())

if __name__ == "__main__":
    main()
