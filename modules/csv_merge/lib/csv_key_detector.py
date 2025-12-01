"""
CSV Key Detector - Atomic module for detecting possible merge keys
"""
import re
from typing import List, Dict


EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
URL_PATTERN = re.compile(r'^https?://|www\.|\.com|\.org|\.net')


def is_email_column(column_name: str) -> bool:
    """Check if column name suggests email field"""
    email_keywords = ['email', 'e-mail', 'mail', 'contact']
    return any(keyword in column_name.lower() for keyword in email_keywords)


def is_website_column(column_name: str) -> bool:
    """Check if column name suggests website/domain field"""
    website_keywords = ['website', 'site', 'url', 'domain', 'link']
    return any(keyword in column_name.lower() for keyword in website_keywords)


def detect_key_columns(columns: List[str]) -> Dict[str, List[str]]:
    """
    Detect potential merge key columns by name

    Args:
        columns: List of column names

    Returns:
        Dict with categorized columns: {'email': [...], 'website': [...], 'other': [...]}
    """
    result = {
        'email': [],
        'website': [],
        'other': []
    }

    for col in columns:
        if is_email_column(col):
            result['email'].append(col)
        elif is_website_column(col):
            result['website'].append(col)
        else:
            result['other'].append(col)

    return result


def suggest_primary_key(columns: List[str]) -> str:
    """
    Suggest best primary key column

    Args:
        columns: List of column names

    Returns:
        Suggested column name (default: first email column or first column)
    """
    detected = detect_key_columns(columns)

    # Prefer email columns
    if detected['email']:
        return detected['email'][0]

    # Then website columns
    if detected['website']:
        return detected['website'][0]

    # Fallback to first column
    return columns[0] if columns else 'id'
