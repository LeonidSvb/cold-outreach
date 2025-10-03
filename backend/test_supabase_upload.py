#!/usr/bin/env python3
"""
Test script for CSV to Supabase upload
Tests the full upload flow with real CSV file
"""

import pandas as pd
from services.csv_to_supabase import upload_csv_to_supabase
from lib.column_detector import detect_all_columns

# Test CSV file
CSV_PATH = "uploads/test_small.csv"  # 50 rows for quick test

def test_upload():
    """Test CSV upload to Supabase"""
    print("=" * 80)
    print("Testing CSV to Supabase Upload")
    print("=" * 80)

    # Read CSV
    print(f"\nReading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    # Detect columns
    print("\nDetecting column types...")
    sample_data = {}
    for col in df.columns:
        sample_data[col] = df[col].head(10).tolist()

    detected_columns = detect_all_columns(
        columns=df.columns.tolist(),
        sample_data=sample_data,
        sample_size=10
    )

    print("\nDetected columns:")
    for col, info in detected_columns.items():
        print(f"  {col}: {info['detected_type']} (confidence: {info['confidence']})")

    # Upload to Supabase
    print("\n" + "=" * 80)
    print("Uploading to Supabase...")
    print("=" * 80)

    results = upload_csv_to_supabase(
        file_path=CSV_PATH,
        detected_columns=detected_columns,
        user_id='ce8ac78e-1bb6-4a89-83ee-3cbac618ad25',
        batch_size=500
    )

    # Print results
    print("\n" + "=" * 80)
    print("Upload Results")
    print("=" * 80)

    print(f"\nSuccess: {results['success']}")
    print(f"Import ID: {results['import_id']}")
    print(f"Total rows processed: {results['total_rows']}")
    print(f"Companies created: {results['companies_created']}")
    print(f"Companies merged: {results['companies_merged']}")
    print(f"Leads created: {results['leads_created']}")
    print(f"Leads updated: {results['leads_updated']}")

    if results['errors']:
        print(f"\nErrors encountered: {len(results['errors'])}")
        print("\nFirst 5 errors:")
        for error in results['errors'][:5]:
            print(f"  - {error}")
    else:
        print("\nNo errors!")

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)

    if results['success']:
        print("[SUCCESS] Upload completed successfully!")
        print(f"[SUCCESS] Uploaded {results['leads_created']} leads")
        print(f"[SUCCESS] Created {results['companies_created']} company entries")

        if results['errors']:
            print(f"[WARNING] {len(results['errors'])} rows had errors")
    else:
        print("[FAILED] Upload failed")

    return results

if __name__ == "__main__":
    test_upload()
