#!/usr/bin/env python3
"""
=== INSTANTLY DATA COLLECTOR ===
Version: 1.0.0 | Created: 2025-11-01

PURPOSE:
Collect all raw data from Instantly API v2 and store in SQLite

FEATURES:
- Collects from all Instantly API v2 endpoints
- Uses curl to bypass Cloudflare protection
- Stores raw JSON + extracted fields in SQLite
- Handles upserts (updates existing records)
- Shows real-time progress

USAGE:
1. Ensure database initialized: python init_database.py
2. Run: python collect_data.py
3. Data saved to: data/instantly.db

API ENDPOINTS COVERED:
1. /api/v2/campaigns/analytics - Campaign analytics
2. /api/v2/leads/list - Lead data (per campaign)
3. /api/v2/campaigns/analytics/steps - Step analytics
4. /api/v2/accounts - Email accounts
5. /api/v2/emails - Email details
6. /api/v2/campaigns/analytics/daily - Daily metrics
7. /api/v2/campaigns/analytics/overview - Account overview
"""

import sqlite3
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Load environment variables
load_dotenv()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "instantly.db"
API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"

# Stats tracking
STATS = {
    "campaigns": 0,
    "leads": 0,
    "steps": 0,
    "accounts": 0,
    "emails": 0,
    "daily_records": 0,
    "overview": 0,
    "errors": 0
}

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_step(text):
    """Print step indicator"""
    print(f"\n>>> {text}")

def print_success(text):
    """Print success message"""
    print(f"  [OK] {text}")

def print_error(text):
    """Print error message"""
    print(f"  [ERROR] {text}")
    STATS["errors"] += 1

def call_api(endpoint, method="GET", data=None):
    """
    Call Instantly API using curl to bypass Cloudflare

    Args:
        endpoint: API endpoint path (e.g., /campaigns/analytics)
        method: HTTP method (GET or POST)
        data: JSON data for POST requests

    Returns:
        dict: Parsed JSON response or None on error
    """
    url = f"{BASE_URL}{endpoint}"

    # Build curl command
    cmd = [
        "curl",
        "-s",  # Silent mode
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json"
    ]

    if method == "POST":
        cmd.extend(["-X", "POST"])
        if data:
            cmd.extend(["-d", json.dumps(data)])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print_error(f"Curl failed: {result.stderr}")
            return None

        if not result.stdout:
            print_error("Empty response from API")
            return None

        # Parse JSON
        response = json.loads(result.stdout)
        return response

    except subprocess.TimeoutExpired:
        print_error("Request timeout (30s)")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response: {e}")
        return None
    except Exception as e:
        print_error(f"API call failed: {e}")
        return None

def collect_campaigns(conn):
    """Collect campaign analytics"""
    print_step("Collecting campaigns...")

    response = call_api("/campaigns/analytics")
    if not response:
        return

    cursor = conn.cursor()

    # Response is array of campaigns
    campaigns = response if isinstance(response, list) else [response]

    for campaign in campaigns:
        campaign_id = campaign.get('campaign_id')
        if not campaign_id:
            continue

        cursor.execute("""
            INSERT INTO instantly_campaigns_raw (
                instantly_campaign_id, campaign_name, campaign_status,
                leads_count, contacted_count, open_count, reply_count,
                bounced_count, emails_sent_count, total_opportunities,
                total_opportunity_value, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(instantly_campaign_id) DO UPDATE SET
                campaign_name = excluded.campaign_name,
                campaign_status = excluded.campaign_status,
                leads_count = excluded.leads_count,
                contacted_count = excluded.contacted_count,
                open_count = excluded.open_count,
                reply_count = excluded.reply_count,
                bounced_count = excluded.bounced_count,
                emails_sent_count = excluded.emails_sent_count,
                total_opportunities = excluded.total_opportunities,
                total_opportunity_value = excluded.total_opportunity_value,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at,
                updated_at = datetime('now')
        """, (
            campaign_id,
            campaign.get('campaign_name'),
            campaign.get('campaign_status'),
            campaign.get('leads_count', 0),
            campaign.get('contacted_count', 0),
            campaign.get('open_count', 0),
            campaign.get('reply_count', 0),
            campaign.get('bounced_count', 0),
            campaign.get('emails_sent_count', 0),
            campaign.get('total_opportunities', 0),
            campaign.get('total_opportunity_value', 0.0),
            json.dumps(campaign)
        ))

        STATS["campaigns"] += 1

    conn.commit()
    print_success(f"Campaigns collected: {STATS['campaigns']}")

    return [c.get('campaign_id') for c in campaigns if c.get('campaign_id')]

def collect_leads(conn, campaign_ids):
    """Collect leads for each campaign"""
    print_step(f"Collecting leads for {len(campaign_ids)} campaigns...")

    cursor = conn.cursor()

    for campaign_id in campaign_ids:
        # POST request to get leads
        response = call_api("/leads/list", method="POST", data={
            "campaign_id": campaign_id,
            "limit": 1000  # Adjust as needed
        })

        if not response:
            continue

        leads = response.get('leads', []) if isinstance(response, dict) else response

        for lead in leads:
            email = lead.get('email')
            if not email:
                continue

            cursor.execute("""
                INSERT INTO instantly_leads_raw (
                    instantly_lead_id, instantly_campaign_id,
                    email, first_name, last_name, company_name,
                    lead_status, raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(instantly_lead_id) DO UPDATE SET
                    email = excluded.email,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    company_name = excluded.company_name,
                    lead_status = excluded.lead_status,
                    raw_json = excluded.raw_json,
                    synced_at = excluded.synced_at,
                    updated_at = datetime('now')
            """, (
                lead.get('id') or f"{email}_{campaign_id}",
                campaign_id,
                email,
                lead.get('first_name'),
                lead.get('last_name'),
                lead.get('company_name'),
                lead.get('status'),
                json.dumps(lead)
            ))

            STATS["leads"] += 1

        conn.commit()

    print_success(f"Leads collected: {STATS['leads']}")

def collect_steps(conn, campaign_ids):
    """Collect step analytics for each campaign"""
    print_step(f"Collecting steps for {len(campaign_ids)} campaigns...")

    cursor = conn.cursor()

    for campaign_id in campaign_ids:
        response = call_api(f"/campaigns/analytics/steps?campaign_id={campaign_id}")

        if not response:
            continue

        steps = response if isinstance(response, list) else [response]

        for step in steps:
            step_number = step.get('step_number') or step.get('step')

            cursor.execute("""
                INSERT INTO instantly_steps_raw (
                    instantly_campaign_id, step_number, step_name, step_type,
                    emails_sent, emails_opened, emails_replied,
                    emails_bounced, emails_clicked,
                    raw_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(instantly_campaign_id, step_number) DO UPDATE SET
                    step_name = excluded.step_name,
                    step_type = excluded.step_type,
                    emails_sent = excluded.emails_sent,
                    emails_opened = excluded.emails_opened,
                    emails_replied = excluded.emails_replied,
                    emails_bounced = excluded.emails_bounced,
                    emails_clicked = excluded.emails_clicked,
                    raw_json = excluded.raw_json,
                    synced_at = excluded.synced_at,
                    updated_at = datetime('now')
            """, (
                campaign_id,
                step_number,
                step.get('step_name'),
                step.get('type'),
                step.get('sent', 0),
                step.get('opened', 0),
                step.get('replied', 0),
                step.get('bounced', 0),
                step.get('clicked', 0),
                json.dumps(step)
            ))

            STATS["steps"] += 1

        conn.commit()

    print_success(f"Steps collected: {STATS['steps']}")

def collect_accounts(conn):
    """Collect email accounts"""
    print_step("Collecting accounts...")

    response = call_api("/accounts")
    if not response:
        return

    cursor = conn.cursor()
    accounts = response.get('items', []) if isinstance(response, dict) else response

    for account in accounts:
        email = account.get('email')
        if not email:
            continue

        cursor.execute("""
            INSERT INTO instantly_accounts_raw (
                email, organization, status, warmup_status,
                stat_warmup_score, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(email) DO UPDATE SET
                organization = excluded.organization,
                status = excluded.status,
                warmup_status = excluded.warmup_status,
                stat_warmup_score = excluded.stat_warmup_score,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at,
                updated_at = datetime('now')
        """, (
            email,
            account.get('organization'),
            account.get('status'),
            account.get('warmup_status'),
            account.get('stat_warmup_score'),
            json.dumps(account)
        ))

        STATS["accounts"] += 1

    conn.commit()
    print_success(f"Accounts collected: {STATS['accounts']}")

def collect_emails(conn):
    """Collect detailed emails"""
    print_step("Collecting emails...")

    response = call_api("/emails?limit=500")
    if not response:
        return

    cursor = conn.cursor()
    emails = response if isinstance(response, list) else [response]

    for email_data in emails:
        email_id = email_data.get('id')
        if not email_id:
            continue

        cursor.execute("""
            INSERT INTO instantly_emails_raw (
                instantly_email_id, instantly_campaign_id,
                recipient_email, subject, email_type,
                sent_at, opened_at, replied_at,
                raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(instantly_email_id) DO UPDATE SET
                recipient_email = excluded.recipient_email,
                subject = excluded.subject,
                email_type = excluded.email_type,
                sent_at = excluded.sent_at,
                opened_at = excluded.opened_at,
                replied_at = excluded.replied_at,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at,
                updated_at = datetime('now')
        """, (
            email_id,
            email_data.get('campaign_id'),
            email_data.get('to'),
            email_data.get('subject'),
            email_data.get('type'),
            email_data.get('sent_at'),
            email_data.get('opened_at'),
            email_data.get('replied_at'),
            json.dumps(email_data)
        ))

        STATS["emails"] += 1

    conn.commit()
    print_success(f"Emails collected: {STATS['emails']}")

def collect_daily_analytics(conn):
    """Collect daily analytics for last 30 days"""
    print_step("Collecting daily analytics...")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    endpoint = f"/campaigns/analytics/daily?start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}"
    response = call_api(endpoint)

    if not response:
        return

    cursor = conn.cursor()
    daily_data = response if isinstance(response, list) else [response]

    for day in daily_data:
        date = day.get('date')
        if not date:
            continue

        cursor.execute("""
            INSERT INTO instantly_daily_analytics_raw (
                date, sent, opened, unique_opened, replies, unique_replies,
                clicks, unique_clicks, raw_json, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(date) DO UPDATE SET
                sent = excluded.sent,
                opened = excluded.opened,
                unique_opened = excluded.unique_opened,
                replies = excluded.replies,
                unique_replies = excluded.unique_replies,
                clicks = excluded.clicks,
                unique_clicks = excluded.unique_clicks,
                raw_json = excluded.raw_json,
                synced_at = excluded.synced_at,
                updated_at = datetime('now')
        """, (
            date,
            day.get('sent', 0),
            day.get('opened', 0),
            day.get('unique_opened', 0),
            day.get('replies', 0),
            day.get('unique_replies', 0),
            day.get('clicks', 0),
            day.get('unique_clicks', 0),
            json.dumps(day)
        ))

        STATS["daily_records"] += 1

    conn.commit()
    print_success(f"Daily records collected: {STATS['daily_records']}")

def collect_overview(conn):
    """Collect account overview"""
    print_step("Collecting overview...")

    response = call_api("/campaigns/analytics/overview")
    if not response:
        return

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO instantly_overview_raw (
            total_campaigns, total_leads, total_emails_sent,
            total_replies, total_opportunities,
            raw_json, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        response.get('total_campaigns', 0),
        response.get('total_leads', 0),
        response.get('total_emails_sent', 0),
        response.get('total_replies', 0),
        response.get('total_opportunities', 0),
        json.dumps(response)
    ))

    conn.commit()
    STATS["overview"] = 1
    print_success("Overview collected")

def main():
    """Main entry point"""

    print_header("INSTANTLY DATA COLLECTION")

    # Validate setup
    if not API_KEY:
        print_error("INSTANTLY_API_KEY not found in .env")
        return

    if not DB_PATH.exists():
        print_error(f"Database not found: {DB_PATH}")
        print("  Run: python init_database.py")
        return

    print(f"  Database: {DB_PATH}")
    print(f"  API Key: {API_KEY[:20]}...")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    try:
        # Collect data in order (campaigns first for foreign keys)
        campaign_ids = collect_campaigns(conn)

        if campaign_ids:
            collect_leads(conn, campaign_ids)
            collect_steps(conn, campaign_ids)

        collect_accounts(conn)
        collect_emails(conn)
        collect_daily_analytics(conn)
        collect_overview(conn)

        # Summary
        print_header("COLLECTION COMPLETE")
        print(f"""
  Records Collected:
    Campaigns:      {STATS['campaigns']:6}
    Leads:          {STATS['leads']:6}
    Steps:          {STATS['steps']:6}
    Accounts:       {STATS['accounts']:6}
    Emails:         {STATS['emails']:6}
    Daily Analytics:{STATS['daily_records']:6}
    Overview:       {STATS['overview']:6}

  Errors:           {STATS['errors']:6}

  Database: {DB_PATH}
  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

  Next Steps:
  - Open DB Browser for SQLite to explore data
  - Run: python collect_data.py --stats (to see current stats)
        """)

    except Exception as e:
        print_error(f"Collection failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
