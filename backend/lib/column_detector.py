"""
Enhanced CSV Column Detection System
Detects column types using hybrid approach: keyword matching + regex validation
"""

import re
from typing import Dict, List, Any, Optional


# Regex patterns for type validation
PATTERNS = {
    "EMAIL": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "PHONE": r'^\+?[1-9]\d{7,14}$',  # International format - matches numeric strings
    "WEBSITE": r'^https?://[^\s]+',
    "LINKEDIN_PROFILE": r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9-]+',
    "LINKEDIN_COMPANY": r'^https?://(www\.)?linkedin\.com/company/[a-zA-Z0-9-]+',
    "COMPANY_DOMAIN": r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$',
}

# Keyword matching for fallback and quick detection
# Priority order matters - more specific keywords first
KEYWORDS = {
    "STATUS": ["_status", "verification", "verified"],  # Must come before EMAIL
    "PHONE": ["phone", "tel", "mobile", "contact_number", "phone_number"],
    "EMAIL": ["email", "mail", "e-mail", "e_mail"],  # After STATUS to avoid conflicts
    "WEBSITE": ["website", "url", "site", "domain", "web", "company_url"],
    "LINKEDIN_PROFILE": ["linkedin_url", "linkedin", "profile_url"],
    "LINKEDIN_COMPANY": ["company_linkedin", "linkedin_company"],
    "COMPANY_NAME": ["company", "organization", "business", "firm", "org", "company_name"],
    "FIRST_NAME": ["first_name", "firstname", "fname", "given_name"],
    "LAST_NAME": ["last_name", "lastname", "lname", "surname", "family_name"],
    "FULL_NAME": ["full_name", "name", "fullname"],
    "JOB_TITLE": ["title", "position", "role", "job", "job_title"],
    "SENIORITY": ["seniority", "level", "rank"],
    "CITY": ["city", "town"],
    "STATE": ["state", "province", "region"],
    "COUNTRY": ["country", "nation"],
}


def validate_type_by_samples(
    sample_values: List[str],
    type_name: str,
    confidence_threshold: float = 0.7
) -> bool:
    """
    Validate if sample values match the type pattern

    Args:
        sample_values: List of non-empty sample values from column
        type_name: Type to validate (EMAIL, PHONE, etc.)
        confidence_threshold: Minimum percentage of matches (0.0-1.0)

    Returns:
        True if >= threshold samples match pattern
    """
    if not sample_values or type_name not in PATTERNS:
        return False

    pattern = PATTERNS[type_name]
    matches = 0

    for val in sample_values:
        val_str = str(val).strip()

        # Special handling for PHONE - remove decimal point from floats
        if type_name == "PHONE":
            # Convert float like "13213096900.0" to "13213096900"
            try:
                val_str = str(int(float(val_str)))
            except (ValueError, TypeError):
                pass

        if re.match(pattern, val_str):
            matches += 1

    confidence = matches / len(sample_values)
    return confidence >= confidence_threshold


def detect_by_column_name(column_name: str) -> Optional[str]:
    """
    Detect type by column name using keyword matching

    Returns:
        Type name or None if no match
    """
    col_lower = column_name.lower().strip()

    # Check each type's keywords
    for type_name, keywords in KEYWORDS.items():
        if any(keyword in col_lower for keyword in keywords):
            return type_name

    return None


def detect_column_type(
    column_name: str,
    sample_values: List[str],
    sample_size: int = 10,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Detect column type using hybrid approach:
    1. Keyword matching (fast)
    2. Regex validation (accurate)

    Priority order: EMAIL > PHONE > LINKEDIN_PROFILE > LINKEDIN_COMPANY > WEBSITE

    Returns:
        {
            "detected_type": "EMAIL",
            "confidence": 0.85,
            "method": "regex_validation",
            "sample_matches": "8/10"
        }
    """
    # Filter non-empty values
    non_empty = [
        str(val).strip()
        for val in sample_values[:sample_size]
        if val and str(val).strip() and str(val).strip() != 'nan'
    ]

    if not non_empty:
        return {
            "detected_type": "UNKNOWN",
            "confidence": 0.0,
            "method": "no_data"
        }

    # Step 1: Try keyword matching first (for quick wins)
    keyword_type = detect_by_column_name(column_name)

    # Step 2: Try regex validation (priority order)
    priority_types = [
        "EMAIL",
        "PHONE",
        "LINKEDIN_PROFILE",
        "LINKEDIN_COMPANY",
        "WEBSITE",
        "COMPANY_DOMAIN"
    ]

    for type_name in priority_types:
        if validate_type_by_samples(non_empty, type_name, confidence_threshold):
            matches = sum(
                1 for val in non_empty
                if re.match(PATTERNS[type_name], str(val).strip())
            )
            confidence = matches / len(non_empty)

            return {
                "detected_type": type_name,
                "confidence": round(confidence, 2),
                "method": "regex_validation",
                "sample_matches": f"{matches}/{len(non_empty)}"
            }

    # Step 3: Fallback to keyword matching
    if keyword_type:
        return {
            "detected_type": keyword_type,
            "confidence": 0.5,
            "method": "keyword_matching"
        }

    # Step 4: Unknown type (default to TEXT)
    return {
        "detected_type": "TEXT",
        "confidence": 0.0,
        "method": "default"
    }


def detect_all_columns(
    columns: List[str],
    sample_data: Dict[str, List[Any]],
    sample_size: int = 10
) -> Dict[str, Dict[str, Any]]:
    """
    Detect types for all columns at once

    Args:
        columns: List of column names
        sample_data: Dict mapping column names to sample values
        sample_size: Number of samples to analyze per column

    Returns:
        Dict mapping column names to detection results
    """
    detected = {}

    for col in columns:
        sample_values = sample_data.get(col, [])
        detection = detect_column_type(col, sample_values, sample_size)

        detected[col] = {
            **detection,
            "original_name": col
        }

    return detected
