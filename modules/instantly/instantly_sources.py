#!/usr/bin/env python3
"""
Instantly JSON Data Sources
Loads data from JSON files (raw_data or dashboard_data)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_from_json(file_path: str) -> Dict[str, Any]:
    """
    Load Instantly data from JSON file

    Args:
        file_path: Path to JSON file (raw_data or dashboard_data)

    Returns:
        Dict with parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "success": True,
            "data": data,
            "file_path": str(file_path),
            "data_type": detect_data_type(data)
        }

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def detect_data_type(data: Dict) -> str:
    """
    Detect if JSON is raw_data or dashboard_data format

    Args:
        data: Parsed JSON data

    Returns:
        'raw_data' or 'dashboard_data'
    """
    # Dashboard data has 'metadata' and 'campaigns' keys
    if 'metadata' in data and 'campaigns' in data:
        return 'dashboard_data'

    # Raw data has direct keys like 'campaigns_overview'
    if 'campaigns_overview' in data:
        return 'raw_data'

    return 'unknown'

def extract_campaigns(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract campaigns from JSON (handles both formats)

    Args:
        data: Parsed JSON data

    Returns:
        List of campaign dictionaries
    """
    data_type = detect_data_type(data)

    if data_type == 'dashboard_data':
        return data.get('campaigns', [])
    elif data_type == 'raw_data':
        # Use campaigns_detailed if available, else campaigns_overview
        return data.get('campaigns_detailed', data.get('campaigns_overview', []))

    return []

def extract_accounts(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract email accounts from JSON

    Args:
        data: Parsed JSON data

    Returns:
        List of account dictionaries
    """
    accounts_data = data.get('accounts', {})

    # Accounts might be in 'items' array
    if isinstance(accounts_data, dict):
        return accounts_data.get('items', [])

    # Or directly as array
    if isinstance(accounts_data, list):
        return accounts_data

    return []

def extract_daily_analytics(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract daily analytics from JSON

    Args:
        data: Parsed JSON data

    Returns:
        List of daily analytics dictionaries
    """
    # Dashboard format
    if 'daily_trends' in data:
        return data['daily_trends']

    # Raw format
    if 'daily_analytics_all' in data:
        return data['daily_analytics_all']

    return []

def get_file_stats(file_path: str) -> Dict[str, Any]:
    """
    Get statistics about JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Dict with file stats
    """
    result = load_from_json(file_path)
    data = result['data']

    campaigns = extract_campaigns(data)
    accounts = extract_accounts(data)
    daily = extract_daily_analytics(data)

    return {
        "file_path": file_path,
        "data_type": result['data_type'],
        "campaigns_count": len(campaigns),
        "accounts_count": len(accounts),
        "daily_records": len(daily)
    }

# Test function
if __name__ == "__main__":
    # Test with real file
    test_file = "results/raw_data_20250921_125555.json"

    if Path(test_file).exists():
        stats = get_file_stats(test_file)
        print(f"File stats: {stats}")
    else:
        print(f"Test file not found: {test_file}")
