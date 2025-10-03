#!/usr/bin/env python3
"""
Quick verification script to check uploaded data in Supabase
"""

from lib.supabase_client import get_supabase

def verify_upload():
    """Verify CSV upload results in Supabase"""
    print("=" * 80)
    print("Verifying CSV Upload in Supabase")
    print("=" * 80)

    supabase = get_supabase()

    # Check companies
    print("\n[COMPANIES]")
    companies = supabase.table('companies')\
        .select('*')\
        .eq('source_type', 'csv_upload')\
        .execute()

    print(f"Total companies: {len(companies.data)}")

    if companies.data:
        # Count unique domains
        domains = set()
        with_domain = 0
        without_domain = 0

        for company in companies.data:
            if company.get('company_domain'):
                domains.add(company['company_domain'])
                with_domain += 1
            else:
                without_domain += 1

        print(f"Unique domains: {len(domains)}")
        print(f"Companies with domain: {with_domain}")
        print(f"Companies without domain: {without_domain}")

        print("\nFirst 3 companies:")
        for i, company in enumerate(companies.data[:3], 1):
            print(f"  {i}. {company.get('company_name')} - {company.get('company_domain')}")

    # Check leads
    print("\n[LEADS]")
    leads = supabase.table('leads')\
        .select('*')\
        .eq('source_type', 'csv_upload')\
        .execute()

    print(f"Total leads: {len(leads.data)}")

    if leads.data:
        # Count unique emails
        emails = set(lead['email'] for lead in leads.data if lead.get('email'))
        print(f"Unique emails: {len(emails)}")

        print("\nFirst 3 leads:")
        for i, lead in enumerate(leads.data[:3], 1):
            print(f"  {i}. {lead.get('first_name')} {lead.get('last_name')} - {lead.get('email')}")

    # Check imports
    print("\n[CSV IMPORTS]")
    imports = supabase.table('csv_imports_raw')\
        .select('id, file_name, total_rows, processed_rows, failed_rows, import_status, uploaded_at')\
        .order('uploaded_at', desc=True)\
        .limit(1)\
        .execute()

    if imports.data:
        imp = imports.data[0]
        print(f"Latest import: {imp['file_name']}")
        print(f"Import ID: {imp['id']}")
        print(f"Status: {imp['import_status']}")
        print(f"Total rows: {imp['total_rows']}")
        print(f"Processed: {imp['processed_rows']}")
        print(f"Failed: {imp['failed_rows']}")
        print(f"Uploaded at: {imp['uploaded_at']}")

    print("\n" + "=" * 80)
    print("[SUCCESS] Verification complete!")
    print("=" * 80)

if __name__ == "__main__":
    verify_upload()
