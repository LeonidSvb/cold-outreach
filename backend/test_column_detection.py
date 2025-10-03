"""
Test script for enhanced CSV column detection
Tests the detection system on real CSV file
"""

import pandas as pd
from lib.column_detector import detect_all_columns

# Test CSV file path
CSV_PATH = r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders (1).csv"

def test_detection():
    """Test column detection on real CSV"""
    print("=" * 80)
    print("CSV Column Detection Test")
    print("=" * 80)

    # Read CSV
    print(f"\nReading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)

    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    print(f"\nColumns: {list(df.columns)}")

    # Prepare sample data
    sample_size = 10
    sample_data = {}
    for col in df.columns:
        sample_data[col] = df[col].head(sample_size).tolist()

    # Detect column types
    print(f"\n{'='*80}")
    print("Detecting column types...")
    print(f"{'='*80}\n")

    detected = detect_all_columns(
        columns=df.columns.tolist(),
        sample_data=sample_data,
        sample_size=sample_size
    )

    # Print results
    print(f"{'Column Name':<30} {'Detected Type':<20} {'Confidence':<12} {'Method':<20} {'Matches'}")
    print("-" * 110)

    for col, result in detected.items():
        confidence = result.get('confidence', 0)
        detected_type = result.get('detected_type', 'UNKNOWN')
        method = result.get('method', 'N/A')
        matches = result.get('sample_matches', 'N/A')

        print(f"{col:<30} {detected_type:<20} {confidence:<12.2f} {method:<20} {matches}")

    # Summary
    print("\n" + "=" * 80)
    print("Detection Summary")
    print("=" * 80)

    type_counts = {}
    for result in detected.values():
        dtype = result['detected_type']
        type_counts[dtype] = type_counts.get(dtype, 0) + 1

    for dtype, count in sorted(type_counts.items()):
        print(f"{dtype:<30} {count} columns")

    # Validation checks
    print("\n" + "=" * 80)
    print("Validation Checks")
    print("=" * 80)

    checks = {
        "email column detected as EMAIL": detected.get('email', {}).get('detected_type') == 'EMAIL',
        "phone_number detected correctly": detected.get('phone_number', {}).get('detected_type') in ['PHONE', 'TEXT'],
        "company_url detected as WEBSITE": detected.get('company_url', {}).get('detected_type') == 'WEBSITE',
        "linkedin_url detected correctly": 'LINKEDIN' in detected.get('linkedin_url', {}).get('detected_type', ''),
        "company_linkedin_url detected correctly": 'LINKEDIN' in detected.get('company_linkedin_url', {}).get('detected_type', ''),
        "first_name detected correctly": detected.get('first_name', {}).get('detected_type') == 'FIRST_NAME',
        "last_name detected correctly": detected.get('last_name', {}).get('detected_type') == 'LAST_NAME',
        "company_name detected correctly": detected.get('company_name', {}).get('detected_type') == 'COMPANY_NAME',
    }

    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {check}")

    passed_count = sum(checks.values())
    total_count = len(checks)
    print(f"\nPassed: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")

    return detected

if __name__ == "__main__":
    results = test_detection()
