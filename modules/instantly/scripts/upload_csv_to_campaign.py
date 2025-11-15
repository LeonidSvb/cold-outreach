#!/usr/bin/env python3
"""
=== INSTANTLY CSV TO CAMPAIGN UPLOADER ===
Version: 1.0.0 | Created: 2025-11-15

PURPOSE:
Upload leads from CSV file to Instantly campaign via API with custom variables

FEATURES:
- Reads CSV with email sequences (email_1, email_2, email_3)
- Maps all columns to custom variables in Instantly
- Cleans email addresses (removes 'remove-this' artifacts)
- Handles multiline email content
- Bulk upload via Instantly API v2

USAGE:
1. Configure CONFIG section below
2. Run: python upload_csv_to_campaign.py
3. Results saved to modules/instantly/results/

CSV STRUCTURE EXPECTED:
- name, email, website, short_museum_name, specific_section
- subject_line, email_1, email_2, email_3, language
- summary, focus_wars, focus_periods

HOW TO USE IN INSTANTLY:
After upload, create sequence steps in Instantly UI:
- Step 1 subject: {{Subject_line}}
- Step 1 body: {{Email_1}}
- Step 2 body: {{Email_2}}
- Step 3 body: {{Email_3}}

IMPROVEMENTS:
v1.0.0 - Initial version with full CSV mapping
"""

import sys
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "API": {
        "base_url": "https://api.instantly.ai/api/v2",
        "api_key": "",  # SET YOUR API KEY HERE or via environment
        "timeout": 60
    },
    "CAMPAIGN": {
        "campaign_id": "",  # SET YOUR CAMPAIGN ID HERE
        "skip_if_in_workspace": False,
        "skip_if_in_campaign": True
    },
    "INPUT": {
        "csv_path": r"C:\Users\79818\Desktop\Outreach - new\modules\openai\results\museum_emails_20251115_153331.csv",
        "encoding": "utf-8-sig"  # Handles BOM in CSV
    },
    "MAPPING": {
        # Map CSV columns to Instantly fields
        "email_field": "email",
        "standard_fields": ["name", "website"],
        "custom_variables": [
            "short_museum_name",
            "specific_section",
            "subject_line",
            "email_1",
            "email_2",
            "email_3",
            "language",
            "summary",
            "focus_wars",
            "focus_periods"
        ]
    },
    "PROCESSING": {
        "clean_emails": True,  # Remove 'remove-this' and similar artifacts
        "validate_emails": True,
        "batch_size": 100  # Instantly supports bulk upload
    },
    "OUTPUT": {
        "save_results": True,
        "results_dir": "modules/instantly/results"
    }
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_processed": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "skipped_invalid": 0,
    "execution_time": 0
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_email(email: str) -> Optional[str]:
    """
    Clean email address from common artifacts

    Args:
        email: Raw email address

    Returns:
        Cleaned email or None if invalid
    """
    if not email or pd.isna(email):
        return None

    email = str(email).strip().lower()

    # Remove common artifacts
    email = email.replace("remove-this.", "")
    email = email.replace("-remove-this", "")
    email = email.replace("removethis", "")

    # Fix common typos
    email = re.sub(r'\.nl[a-z]+$', '.nl', email)  # Fix .nliban -> .nl
    email = re.sub(r'\.com[a-z]+$', '.com', email)

    return email if email else None


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid email format
    """
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def read_csv(csv_path: str, encoding: str = "utf-8-sig") -> pd.DataFrame:
    """
    Read CSV file with proper handling of multiline fields

    Args:
        csv_path: Path to CSV file
        encoding: File encoding

    Returns:
        DataFrame with CSV data
    """
    logger.info("Reading CSV file", path=csv_path)

    try:
        df = pd.read_csv(csv_path, encoding=encoding)
        logger.info("CSV loaded successfully", rows=len(df), columns=list(df.columns))
        return df
    except Exception as e:
        logger.error("Failed to read CSV", error=str(e))
        raise


def map_row_to_lead(row: pd.Series, config: Dict) -> Optional[Dict[str, Any]]:
    """
    Map CSV row to Instantly lead format

    Args:
        row: DataFrame row
        config: Configuration dict

    Returns:
        Lead dict in Instantly API format or None if invalid
    """
    # Extract and clean email
    email = clean_email(row.get(config["MAPPING"]["email_field"]))

    if not email:
        logger.warning("Missing email", row_data=row.to_dict())
        return None

    if config["PROCESSING"]["validate_emails"] and not validate_email(email):
        logger.warning("Invalid email format", email=email)
        return None

    # Build lead object
    lead = {
        "email": email
    }

    # Add standard fields (first_name, last_name, company_name, etc.)
    for field in config["MAPPING"]["standard_fields"]:
        value = row.get(field)
        if pd.notna(value):
            lead[field] = str(value).strip()

    # Add custom variables
    custom_vars = {}
    for var in config["MAPPING"]["custom_variables"]:
        value = row.get(var)
        if pd.notna(value):
            # Convert to string and preserve formatting
            str_value = str(value).strip()
            if str_value:
                # Normalize field name for Instantly (capitalize first letter, no spaces)
                var_name = var.replace("_", " ").title().replace(" ", "_")
                custom_vars[var_name] = str_value

    if custom_vars:
        lead["custom_variables"] = custom_vars

    return lead


def upload_leads_to_instantly(
    leads: List[Dict[str, Any]],
    config: Dict
) -> Dict[str, Any]:
    """
    Upload leads to Instantly campaign via API

    Args:
        leads: List of lead dicts
        config: Configuration dict

    Returns:
        API response dict
    """
    api_key = config["API"]["api_key"]
    campaign_id = config["CAMPAIGN"]["campaign_id"]

    if not api_key:
        raise ValueError("API key not configured. Set CONFIG['API']['api_key']")

    if not campaign_id:
        raise ValueError("Campaign ID not configured. Set CONFIG['CAMPAIGN']['campaign_id']")

    url = f"{config['API']['base_url']}/leads/bulk"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "campaign_id": campaign_id,
        "skip_if_in_workspace": config["CAMPAIGN"]["skip_if_in_workspace"],
        "skip_if_in_campaign": config["CAMPAIGN"]["skip_if_in_campaign"],
        "leads": leads
    }

    logger.info(
        "Uploading leads to Instantly",
        campaign_id=campaign_id,
        lead_count=len(leads)
    )

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=config["API"]["timeout"]
        )

        response.raise_for_status()

        result = response.json()
        logger.info("Upload successful", response=result)
        return result

    except requests.exceptions.RequestException as e:
        logger.error("API request failed", error=str(e))
        if hasattr(e.response, 'text'):
            logger.error("Response details", response_text=e.response.text)
        raise


def save_results(results: Dict[str, Any], config: Dict) -> str:
    """
    Save upload results to JSON file

    Args:
        results: Results dict to save
        config: Configuration dict

    Returns:
        Path to saved file
    """
    if not config["OUTPUT"]["save_results"]:
        return ""

    # Create results directory
    results_dir = Path(config["OUTPUT"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"upload_campaign_{timestamp}.json"
    filepath = results_dir / filename

    # Save to file
    import json
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Results saved", path=str(filepath))
    return str(filepath)


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main execution function"""
    start_time = datetime.now()
    logger.info("Starting CSV to Instantly campaign upload", config=CONFIG)

    try:
        # Step 1: Read CSV
        df = read_csv(CONFIG["INPUT"]["csv_path"], CONFIG["INPUT"]["encoding"])
        SCRIPT_STATS["total_processed"] = len(df)

        # Step 2: Map rows to leads
        leads = []
        for idx, row in df.iterrows():
            lead = map_row_to_lead(row, CONFIG)
            if lead:
                leads.append(lead)
            else:
                SCRIPT_STATS["skipped_invalid"] += 1

        logger.info(
            "Lead mapping complete",
            total_rows=len(df),
            valid_leads=len(leads),
            skipped=SCRIPT_STATS["skipped_invalid"]
        )

        if not leads:
            logger.error("No valid leads to upload")
            return

        # Step 3: Upload to Instantly
        api_response = upload_leads_to_instantly(leads, CONFIG)
        SCRIPT_STATS["successful_uploads"] = len(leads)

        # Step 4: Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "stats": SCRIPT_STATS,
            "config": {
                "campaign_id": CONFIG["CAMPAIGN"]["campaign_id"],
                "csv_path": CONFIG["INPUT"]["csv_path"]
            },
            "api_response": api_response,
            "uploaded_leads": leads
        }

        SCRIPT_STATS["execution_time"] = (datetime.now() - start_time).total_seconds()
        results["stats"]["execution_time"] = SCRIPT_STATS["execution_time"]

        saved_path = save_results(results, CONFIG)

        # Final summary
        logger.info(
            "Upload completed successfully",
            total_leads=len(leads),
            execution_time=f"{SCRIPT_STATS['execution_time']:.2f}s",
            results_file=saved_path
        )

        print("\n" + "="*60)
        print("UPLOAD SUMMARY")
        print("="*60)
        print(f"Total rows processed: {SCRIPT_STATS['total_processed']}")
        print(f"Valid leads uploaded: {SCRIPT_STATS['successful_uploads']}")
        print(f"Skipped (invalid): {SCRIPT_STATS['skipped_invalid']}")
        print(f"Execution time: {SCRIPT_STATS['execution_time']:.2f}s")
        print(f"Results saved to: {saved_path}")
        print("="*60)
        print("\nNEXT STEPS:")
        print("1. Go to your Instantly campaign")
        print("2. Create sequence steps:")
        print("   - Step 1 Subject: {{Subject_Line}}")
        print("   - Step 1 Body: {{Email_1}}")
        print("   - Step 2 Body: {{Email_2}}")
        print("   - Step 3 Body: {{Email_3}}")
        print("3. All other custom variables are available: {{Language}}, {{Summary}}, etc.")
        print("="*60 + "\n")

    except Exception as e:
        logger.error("Script failed", error=str(e), stats=SCRIPT_STATS)
        raise


if __name__ == "__main__":
    main()
