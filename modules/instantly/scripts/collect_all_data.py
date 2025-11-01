#!/usr/bin/env python3
"""
=== INSTANTLY FULL DATA COLLECTOR ===
Version: 2.0.0 | Created: 2025-11-01

PURPOSE:
Collect ALL data from Instantly API v2 with proper pagination

FEATURES:
- Correct limit (100 max)
- Proper response parsing (items not leads)
- Full pagination support
- Progress tracking
- All endpoints covered

USAGE:
python collect_all_data.py
"""

import sqlite3
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "instantly_all.db"
API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"

STATS = {
    "campaigns": 0,
    "leads": 0,
    "steps": 0,
    "accounts": 0,
    "daily_records": 0,
    "overview": 0,
    "errors": 0
}

def call_api(endpoint, method="GET", data=None):
    """Call Instantly API using curl"""
    url = f"{BASE_URL}{endpoint}"

    cmd = [
        "curl", "-s",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json"
    ]

    if method == "POST":
        cmd.extend(["-X", "POST"])
        if data:
            cmd.extend(["-d", json.dumps(data)])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            print(f"  [ERROR] Curl failed: {result.stderr}")
            return None

        if not result.stdout:
            print(f"  [ERROR] Empty response")
            return None

        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        print(f"  [ERROR] Timeout (60s)")
        return None
    except json.JSONDecodeError as e:
        print(f"  [ERROR] Invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None

def collect_with_pagination(conn, table, endpoint, method="GET", post_data=None, transform_fn=None, extra_params=None):
    """Collect data with pagination support"""

    cursor = conn.cursor()
    total_collected = 0
    page_num = 1

    # Initial request
    if method == "POST":
        data = post_data.copy() if post_data else {}
        data['limit'] = 100
        response = call_api(endpoint, "POST", data)
    else:
        response = call_api(endpoint, "GET")

    if not response:
        return total_collected

    # Process items
    items = response.get('items', [])

    if items and transform_fn:
        for item in items:
            if extra_params:
                transform_fn(cursor, item, extra_params)
            else:
                transform_fn(cursor, item)
        conn.commit()
        total_collected += len(items)
        print(f"  Page {page_num}: {len(items)} records")

    # Pagination
    next_cursor = response.get('next_starting_after')

    while next_cursor:
        page_num += 1

        if method == "POST":
            data = post_data.copy() if post_data else {}
            data['limit'] = 100
            data['starting_after'] = next_cursor
            response = call_api(endpoint, "POST", data)
        else:
            response = call_api(f"{endpoint}?starting_after={next_cursor}&limit=100", "GET")

        if not response:
            break

        items = response.get('items', [])

        if not items:
            break

        if transform_fn:
            for item in items:
                if extra_params:
                    transform_fn(cursor, item, extra_params)
                else:
                    transform_fn(cursor, item)
            conn.commit()
            total_collected += len(items)
            print(f"  Page {page_num}: {len(items)} records (total: {total_collected})")

        next_cursor = response.get('next_starting_after')

    return total_collected

def transform_campaign(cursor, campaign):
    """Transform and insert campaign"""
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
        campaign.get('campaign_id'),
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

def transform_lead(cursor, lead, extra_params=None):
    """Transform and insert lead"""
    email = lead.get('email')

    # Get campaign from lead JSON (can be None for leads without campaign)
    campaign_id = lead.get('campaign')

    if not email:
        return

    cursor.execute("""
        INSERT INTO instantly_leads_raw (
            instantly_lead_id, instantly_campaign_id,
            email, first_name, last_name, company_name,
            lead_status, raw_json, synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(instantly_lead_id) DO UPDATE SET
            instantly_campaign_id = excluded.instantly_campaign_id,
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
        str(lead.get('status')),
        json.dumps(lead)
    ))

def transform_account(cursor, account):
    """Transform and insert account"""
    email = account.get('email')
    if not email:
        return

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

def collect_campaigns(conn):
    """Collect campaigns analytics"""
    print("\n>>> Collecting campaigns analytics...")

    response = call_api("/campaigns/analytics")

    if not response or not isinstance(response, list):
        print("  [ERROR] No campaign analytics found")
        return []

    cursor = conn.cursor()
    campaign_ids = []

    for campaign in response:
        campaign_id = campaign.get('campaign_id')
        if campaign_id:
            campaign_ids.append(campaign_id)
            transform_campaign(cursor, campaign)

    conn.commit()
    STATS["campaigns"] = len(campaign_ids)
    print(f"  [OK] Campaigns collected: {len(campaign_ids)}")

    return campaign_ids

def collect_leads(conn, campaign_ids):
    """Collect ALL leads without campaign filter (API bug workaround)"""
    print(f"\n>>> Collecting ALL leads (without campaign filter)...")
    print("  Note: Instantly API has a bug - returns wrong leads for inactive campaigns")
    print("  Solution: Collect all leads at once, campaign field is in lead JSON")

    count = collect_with_pagination(
        conn,
        'instantly_leads_raw',
        '/leads/list',
        method='POST',
        post_data={},  # NO campaign_id filter!
        transform_fn=transform_lead,
        extra_params=None  # No filtering needed
    )

    STATS["leads"] = count
    print(f"\n  [OK] TOTAL LEADS: {count}")

    # Show distribution by campaign
    cursor = conn.cursor()
    campaigns_with_leads = cursor.execute("""
        SELECT
            COALESCE(instantly_campaign_id, 'None') as campaign,
            COUNT(*) as count
        FROM instantly_leads_raw
        GROUP BY instantly_campaign_id
        ORDER BY count DESC
    """).fetchall()

    print("\n  Distribution by campaign:")
    for campaign, lead_count in campaigns_with_leads:
        if campaign == 'None':
            print(f"    No campaign (deleted/archived):  {lead_count:>6}")
        else:
            # Get campaign name
            name = cursor.execute(
                "SELECT campaign_name FROM instantly_campaigns_raw WHERE instantly_campaign_id = ?",
                (campaign,)
            ).fetchone()
            name = name[0][:30] if name else campaign[:30]
            print(f"    {name:30}  {lead_count:>6}")

def collect_accounts(conn):
    """Collect email accounts"""
    print("\n>>> Collecting accounts...")

    count = collect_with_pagination(
        conn,
        'instantly_accounts_raw',
        '/accounts',
        method='GET',
        transform_fn=transform_account
    )

    STATS["accounts"] = count
    print(f"  [OK] Accounts collected: {count}")

def collect_steps(conn, campaign_ids):
    """Collect steps for all campaigns"""
    print(f"\n>>> Collecting steps for {len(campaign_ids)} campaigns...")

    cursor = conn.cursor()
    total_steps = 0

    for campaign_id in campaign_ids:
        response = call_api(f"/campaigns/analytics/steps?campaign_id={campaign_id}")

        if not response or not isinstance(response, list):
            continue

        for step in response:
            step_number = step.get('step')

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

            total_steps += 1

    conn.commit()
    STATS["steps"] = total_steps
    print(f"  [OK] Steps collected: {total_steps}")

def collect_daily_analytics(conn):
    """Collect daily analytics"""
    print("\n>>> Collecting daily analytics...")

    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    response = call_api(f"/campaigns/analytics/daily?start_date={start_date}&end_date={end_date}")

    if not response or not isinstance(response, list):
        print("  [ERROR] No daily analytics found")
        return

    cursor = conn.cursor()

    for day in response:
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

    conn.commit()
    STATS["daily_records"] = len(response)
    print(f"  [OK] Daily records collected: {len(response)}")

def collect_overview(conn):
    """Collect overview"""
    print("\n>>> Collecting overview...")

    response = call_api("/campaigns/analytics/overview")

    if not response:
        print("  [ERROR] No overview found")
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
        response.get('emails_sent_count', 0),
        response.get('reply_count', 0),
        response.get('total_opportunities', 0),
        json.dumps(response)
    ))

    conn.commit()
    STATS["overview"] = 1
    print(f"  [OK] Overview collected")

def main():
    """Main entry point"""

    print("\n" + "=" * 80)
    print("  INSTANTLY FULL DATA COLLECTION")
    print("=" * 80)

    if not API_KEY:
        print("  [ERROR] INSTANTLY_API_KEY not found in .env")
        return

    if not DB_PATH.exists():
        print(f"  [ERROR] Database not found: {DB_PATH}")
        print("  Run: python init_database.py")
        return

    print(f"\n  Database: {DB_PATH}")
    print(f"  API Key: {API_KEY[:20]}...")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    conn = sqlite3.connect(DB_PATH)

    try:
        # Collect everything
        campaign_ids = collect_campaigns(conn)
        collect_accounts(conn)

        if campaign_ids:
            collect_leads(conn, campaign_ids)
            collect_steps(conn, campaign_ids)

        collect_daily_analytics(conn)
        collect_overview(conn)

        # Summary
        print("\n" + "=" * 80)
        print("  COLLECTION COMPLETE")
        print("=" * 80)
        print(f"""
  Records Collected:
    Campaigns:       {STATS['campaigns']:6}
    Leads:           {STATS['leads']:6}
    Steps:           {STATS['steps']:6}
    Accounts:        {STATS['accounts']:6}
    Daily Analytics: {STATS['daily_records']:6}
    Overview:        {STATS['overview']:6}

  Errors:            {STATS['errors']:6}

  Database: {DB_PATH}
  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)

    except Exception as e:
        print(f"\n  [ERROR] Collection failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
