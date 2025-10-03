#!/usr/bin/env python3
"""
CSV to Supabase Upload Service
Handles normalization, deduplication, and upload of CSV data to Supabase
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import re
from pathlib import Path

from lib.supabase_client import get_supabase, upsert_rows


def extract_domain(url: str) -> Optional[str]:
    """
    Extract clean domain from URL

    Examples:
        https://www.example.com/page -> example.com
        www.example.com -> example.com
        example.com -> example.com
        http://subdomain.example.com -> subdomain.example.com

    Args:
        url: URL or domain string

    Returns:
        Clean domain or None if invalid
    """
    if not url or pd.isna(url):
        return None

    url = str(url).strip()

    if not url:
        return None

    # Add protocol if missing for urlparse
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]

        # Basic validation
        if '.' in domain and len(domain) > 3:
            return domain.lower()

        return None
    except Exception:
        return None


def normalize_empty_values(value: Any) -> Optional[Any]:
    """
    Convert empty strings and pandas NA to None (NULL in DB)

    Args:
        value: Any value from CSV

    Returns:
        None if empty/NA, otherwise original value
    """
    if pd.isna(value) or value == '' or value == 'nan':
        return None
    return value


def prepare_company_data(row: pd.Series, detected_columns: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Extract and prepare company data from CSV row

    Args:
        row: Pandas Series (CSV row)
        detected_columns: Column detection results from TASK-002

    Returns:
        Dict with company fields
    """
    company_data = {}

    # Find column mappings from detection
    column_map = {}
    for col_name, detection in detected_columns.items():
        dtype = detection.get('detected_type')
        column_map[dtype] = col_name

    # Extract company fields
    if 'COMPANY_NAME' in column_map:
        company_data['company_name'] = normalize_empty_values(row.get(column_map['COMPANY_NAME']))

    if 'WEBSITE' in column_map:
        website = normalize_empty_values(row.get(column_map['WEBSITE']))
        company_data['website'] = website
        # Extract domain for deduplication
        company_data['company_domain'] = extract_domain(website)

    if 'LINKEDIN_COMPANY' in column_map:
        company_data['company_linkedin'] = normalize_empty_values(row.get(column_map['LINKEDIN_COMPANY']))

    # Optional fields from CSV
    for csv_col in row.index:
        csv_lower = csv_col.lower()

        if 'industry' in csv_lower:
            company_data['industry'] = normalize_empty_values(row.get(csv_col))
        elif 'company_size' in csv_lower or 'employee' in csv_lower:
            company_data['company_size'] = normalize_empty_values(row.get(csv_col))
        elif 'phone' in csv_lower and 'company' in csv_lower:
            company_data['company_phone'] = normalize_empty_values(row.get(csv_col))

    # Location fields
    if 'COUNTRY' in column_map:
        company_data['country'] = normalize_empty_values(row.get(column_map['COUNTRY']))
    if 'STATE' in column_map:
        company_data['state'] = normalize_empty_values(row.get(column_map['STATE']))
    if 'CITY' in column_map:
        company_data['city'] = normalize_empty_values(row.get(column_map['CITY']))

    # Source tracking
    company_data['source_type'] = 'csv_upload'

    return company_data


def prepare_lead_data(row: pd.Series, detected_columns: Dict[str, Dict], company_id: str) -> Dict[str, Any]:
    """
    Extract and prepare lead data from CSV row

    Args:
        row: Pandas Series (CSV row)
        detected_columns: Column detection results
        company_id: UUID of associated company

    Returns:
        Dict with lead fields
    """
    lead_data = {}

    # Find column mappings
    column_map = {}
    for col_name, detection in detected_columns.items():
        dtype = detection.get('detected_type')
        column_map[dtype] = col_name

    # Required fields
    if 'EMAIL' in column_map:
        lead_data['email'] = normalize_empty_values(row.get(column_map['EMAIL']))

    if 'FIRST_NAME' in column_map:
        lead_data['first_name'] = normalize_empty_values(row.get(column_map['FIRST_NAME']))

    if 'LAST_NAME' in column_map:
        lead_data['last_name'] = normalize_empty_values(row.get(column_map['LAST_NAME']))

    # Optional fields
    if 'JOB_TITLE' in column_map:
        lead_data['job_title'] = normalize_empty_values(row.get(column_map['JOB_TITLE']))

    if 'SENIORITY' in column_map:
        lead_data['seniority'] = normalize_empty_values(row.get(column_map['SENIORITY']))

    if 'PHONE' in column_map:
        lead_data['phone'] = normalize_empty_values(row.get(column_map['PHONE']))

    if 'LINKEDIN_PROFILE' in column_map:
        # Store in raw_data as we don't have dedicated column
        linkedin_url = normalize_empty_values(row.get(column_map['LINKEDIN_PROFILE']))
        if linkedin_url:
            lead_data['raw_data'] = {'linkedin_url': linkedin_url}

    # Company association
    lead_data['company_id'] = company_id

    # Source tracking
    lead_data['source_type'] = 'csv_upload'
    lead_data['lead_status'] = 'new'

    return lead_data


def upsert_company(company_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Upsert company with MERGE strategy (update empty fields only)

    Args:
        company_data: Company fields

    Returns:
        Tuple of (company_id, error_message)
    """
    try:
        supabase = get_supabase()

        # Check if company exists by domain
        domain = company_data.get('company_domain')

        if not domain:
            # No domain - create new company without deduplication
            response = supabase.table('companies').insert(company_data).execute()
            return response.data[0]['id'], None

        # Check existing
        existing = supabase.table('companies')\
            .select('*')\
            .eq('company_domain', domain)\
            .execute()

        if existing.data:
            # Company exists - MERGE strategy
            existing_company = existing.data[0]
            company_id = existing_company['id']

            # Merge: only update fields that are NULL in DB but have value in CSV
            update_data = {}
            for key, value in company_data.items():
                if key == 'company_domain':
                    continue  # Don't update unique key
                if value is not None and existing_company.get(key) is None:
                    update_data[key] = value

            if update_data:
                supabase.table('companies')\
                    .update(update_data)\
                    .eq('id', company_id)\
                    .execute()

            return company_id, None
        else:
            # New company - insert
            response = supabase.table('companies').insert(company_data).execute()
            return response.data[0]['id'], None

    except Exception as e:
        return None, str(e)


def upsert_lead(lead_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Upsert lead with UPDATE strategy (update if exists)

    Args:
        lead_data: Lead fields

    Returns:
        Tuple of (success, error_message)
    """
    try:
        supabase = get_supabase()

        email = lead_data.get('email')
        if not email:
            return False, "Email is required"

        # Check if lead exists
        existing = supabase.table('leads')\
            .select('id')\
            .eq('email', email)\
            .execute()

        if existing.data:
            # Lead exists - UPDATE
            lead_id = existing.data[0]['id']
            supabase.table('leads')\
                .update(lead_data)\
                .eq('id', lead_id)\
                .execute()
        else:
            # New lead - INSERT
            supabase.table('leads').insert(lead_data).execute()

        return True, None

    except Exception as e:
        return False, str(e)


def save_raw_csv_to_supabase(
    file_path: str,
    df: pd.DataFrame,
    user_id: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Save raw CSV data to csv_imports_raw table for audit trail

    Args:
        file_path: Path to CSV file
        df: Pandas DataFrame
        user_id: User UUID

    Returns:
        Tuple of (import_id, error_message)
    """
    try:
        supabase = get_supabase()

        # Convert DataFrame to JSONB array (handle NaN values)
        raw_data = df.fillna('').to_dict('records')

        # Convert to JSON string to ensure proper formatting
        import json
        raw_data_json = json.dumps(raw_data)

        import_data = {
            'file_name': Path(file_path).name,
            'file_size_bytes': Path(file_path).stat().st_size,
            'uploaded_by': user_id,
            'raw_data': raw_data_json,  # Pass as JSON string
            'total_rows': len(df),
            'import_status': 'uploaded'
        }

        response = supabase.table('csv_imports_raw').insert(import_data).execute()
        return response.data[0]['id'], None

    except Exception as e:
        return None, str(e)


def upload_csv_to_supabase(
    file_path: str,
    detected_columns: Dict[str, Dict],
    user_id: str = 'ce8ac78e-1bb6-4a89-83ee-3cbac618ad25',
    batch_size: int = 500
) -> Dict[str, Any]:
    """
    Main function to upload CSV to Supabase with normalization and deduplication

    Args:
        file_path: Path to CSV file
        detected_columns: Column detection results from TASK-002
        user_id: User UUID (default: Leonid's ID)
        batch_size: Number of rows per batch

    Returns:
        Dict with upload results and statistics
    """
    results = {
        'success': False,
        'import_id': None,
        'total_rows': 0,
        'companies_created': 0,
        'companies_merged': 0,
        'leads_created': 0,
        'leads_updated': 0,
        'errors': []
    }

    try:
        # Read CSV
        df = pd.read_csv(file_path)
        results['total_rows'] = len(df)

        # Save raw CSV for audit
        import_id, error = save_raw_csv_to_supabase(file_path, df, user_id)
        if error:
            results['errors'].append(f"Failed to save raw CSV: {error}")
            return results

        results['import_id'] = import_id

        # Process in batches
        for batch_start in range(0, len(df), batch_size):
            batch_end = min(batch_start + batch_size, len(df))
            batch_df = df.iloc[batch_start:batch_end]

            for idx, row in batch_df.iterrows():
                # Prepare company data
                company_data = prepare_company_data(row, detected_columns)

                # Upsert company
                company_id, error = upsert_company(company_data)
                if error:
                    results['errors'].append(f"Row {idx}: Company error - {error}")
                    continue

                # Track company stats
                # TODO: Track if created or merged (needs API change)
                results['companies_created'] += 1

                # Prepare lead data
                lead_data = prepare_lead_data(row, detected_columns, company_id)

                # Upsert lead
                success, error = upsert_lead(lead_data)
                if error:
                    results['errors'].append(f"Row {idx}: Lead error - {error}")
                    continue

                # Track lead stats
                # TODO: Track if created or updated (needs API change)
                results['leads_created'] += 1

        # Update import status
        supabase = get_supabase()
        supabase.table('csv_imports_raw')\
            .update({
                'import_status': 'completed',
                'processed_rows': results['leads_created'],
                'failed_rows': len(results['errors'])
            })\
            .eq('id', import_id)\
            .execute()

        results['success'] = True

    except Exception as e:
        results['errors'].append(f"Fatal error: {str(e)}")

    return results
