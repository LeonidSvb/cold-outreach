"""
Test backend API integration with enhanced column detection
"""

from main import analyze_csv_file_enhanced

CSV_PATH = r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders (1).csv"

def test_api_integration():
    """Test analyze_csv_file function with enhanced detection"""
    print("=" * 80)
    print("Testing Backend API Integration")
    print("=" * 80)

    result = analyze_csv_file_enhanced(CSV_PATH)

    print(f"\nFile Analysis Results:")
    print(f"Total Rows: {result['rows']}")
    print(f"Total Columns: {len(result['columns'])}")

    print(f"\n{'='*80}")
    print("Enhanced Column Detection Results")
    print(f"{'='*80}\n")

    detected = result['detected_columns']

    print(f"{'Column Name':<30} {'Detected Type':<20} {'Confidence':<12} {'Method'}")
    print("-" * 90)

    for col, info in detected.items():
        detected_type = info.get('detected_type', 'UNKNOWN')
        confidence = info.get('confidence', 0.0)
        method = info.get('method', 'N/A')

        print(f"{col:<30} {detected_type:<20} {confidence:<12.2f} {method}")

    # Critical columns check
    print(f"\n{'='*80}")
    print("Critical Columns Validation")
    print(f"{'='*80}")

    critical_checks = {
        "email": "EMAIL",
        "company_url": "WEBSITE",
        "linkedin_url": "LINKEDIN_PROFILE",
        "company_linkedin_url": "LINKEDIN_COMPANY",
        "first_name": "FIRST_NAME",
        "last_name": "LAST_NAME",
    }

    all_passed = True
    for col, expected_type in critical_checks.items():
        actual = detected.get(col, {}).get('detected_type', 'UNKNOWN')
        passed = expected_type in actual or actual == expected_type
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {col}: expected {expected_type}, got {actual}")

        if not passed:
            all_passed = False

    print(f"\n{'='*80}")
    if all_passed:
        print("SUCCESS: All critical columns detected correctly!")
    else:
        print("WARNING: Some critical columns not detected properly")
    print(f"{'='*80}")

    return result

if __name__ == "__main__":
    test_api_integration()
