#!/usr/bin/env python3
"""
=== INSTANTLY COMPREHENSIVE DATA COLLECTOR ===
Version: 1.0.0 | Created: 2025-01-21

PURPOSE:
Complete data extraction from Instantly API v2 - campaigns, accounts, analytics, warmup data

FEATURES:
- Full campaign analytics and statistics
- All email accounts data and vitals testing
- Warmup analytics for all accounts
- Campaign steps and daily analytics
- Account health and deliverability metrics
- Comprehensive error handling and retry logic

USAGE:
1. Ensure INSTANTLY_API_KEY is set in .env file
2. Run: python instantly_data_collector.py
3. All data saved to results/ with timestamp

IMPROVEMENTS:
v1.0.0 - Initial version with comprehensive API v2 coverage
"""

import json
import time
import base64
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import urllib.request
import urllib.parse
import urllib.error

# Simple logging function
def auto_log(module_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"[{module_name}] Starting {func.__name__}")
            result = func(*args, **kwargs)
            print(f"[{module_name}] Completed {func.__name__}")
            return result
        return wrapper
    return decorator

# ============================================================================
# CONFIG SECTION
# ============================================================================

CONFIG = {
    "INSTANTLY_API": {
        "BASE_URL": "https://api.instantly.ai/api/v2",
        "TIMEOUT_SECONDS": 30,
        "RETRY_ATTEMPTS": 3,
        "RETRY_DELAY": 2
    },

    "DATA_COLLECTION": {
        "COLLECT_CAMPAIGNS": True,
        "COLLECT_ACCOUNTS": True,
        "COLLECT_WARMUP_ANALYTICS": True,
        "COLLECT_CAMPAIGN_ANALYTICS": True,
        "COLLECT_DAILY_ANALYTICS": True,
        "COLLECT_STEPS_ANALYTICS": True,
        "TEST_ACCOUNT_VITALS": True,
        "DAYS_BACK_ANALYTICS": 30
    },

    "OUTPUT": {
        "SAVE_JSON": True,
        "RESULTS_DIR": "results",
        "SEPARATE_FILES": True,
        "COMBINE_ALL": True
    }
}

# ============================================================================
# SCRIPT STATISTICS
# ============================================================================

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0,
    "data_points_collected": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class InstantlyDataCollector:
    def __init__(self):
        self.config = CONFIG
        self.api_key = self._load_api_key()
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.collected_data = {}

    def _load_api_key(self) -> Optional[str]:
        """Load and decode API key from .env file"""
        env_path = Path(__file__).parent.parent.parent / ".env"

        if not env_path.exists():
            print("Error: .env file not found")
            return None

        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('INSTANTLY_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()

                    # Try to decode if base64 encoded
                    try:
                        decoded = base64.b64decode(api_key).decode('utf-8')
                        print(f"API key decoded from base64")
                        return decoded
                    except:
                        print(f"Using API key as-is")
                        return api_key

        print("Error: INSTANTLY_API_KEY not found in .env")
        return None

    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Instantly API with retry logic"""
        url = f"{self.config['INSTANTLY_API']['BASE_URL']}/{endpoint}"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        for attempt in range(self.config['INSTANTLY_API']['RETRY_ATTEMPTS']):
            try:
                if method == 'GET':
                    req = urllib.request.Request(url, headers=headers)
                else:
                    json_data = json.dumps(data).encode('utf-8') if data else None
                    req = urllib.request.Request(url, data=json_data, headers=headers, method=method)

                with urllib.request.urlopen(req, timeout=self.config['INSTANTLY_API']['TIMEOUT_SECONDS']) as response:
                    return json.loads(response.read().decode())

            except urllib.error.HTTPError as e:
                error_body = ""
                try:
                    error_body = e.read().decode()
                except:
                    pass

                print(f"HTTP Error {e.code} on attempt {attempt + 1}: {e.reason}")
                if error_body:
                    print(f"Error details: {error_body}")

                if attempt == self.config['INSTANTLY_API']['RETRY_ATTEMPTS'] - 1:
                    return None

                time.sleep(self.config['INSTANTLY_API']['RETRY_DELAY'])

            except Exception as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.config['INSTANTLY_API']['RETRY_ATTEMPTS'] - 1:
                    return None

                time.sleep(self.config['INSTANTLY_API']['RETRY_DELAY'])

        return None

    @auto_log("instantly_data_collector")
    def collect_all_data(self) -> Dict[str, Any]:
        """Collect all available data from Instantly API"""
        if not self.api_key:
            return {}

        print(f"Starting comprehensive Instantly data collection")
        print(f"API Key (first 20 chars): {self.api_key[:20]}...")
        print()

        start_time = time.time()

        # Test API connection first
        if not self._test_connection():
            print("API connection failed - stopping collection")
            return {}

        # Collect all data types
        if self.config["DATA_COLLECTION"]["COLLECT_CAMPAIGNS"]:
            self._collect_campaigns()

        if self.config["DATA_COLLECTION"]["COLLECT_ACCOUNTS"]:
            self._collect_accounts()

        if self.config["DATA_COLLECTION"]["COLLECT_WARMUP_ANALYTICS"]:
            self._collect_warmup_analytics()

        if self.config["DATA_COLLECTION"]["COLLECT_CAMPAIGN_ANALYTICS"]:
            self._collect_campaign_analytics()

        if self.config["DATA_COLLECTION"]["COLLECT_DAILY_ANALYTICS"]:
            self._collect_daily_analytics()

        if self.config["DATA_COLLECTION"]["COLLECT_STEPS_ANALYTICS"]:
            self._collect_steps_analytics()

        if self.config["DATA_COLLECTION"]["TEST_ACCOUNT_VITALS"]:
            self._test_account_vitals()

        # Save all collected data
        self._save_results(start_time)

        processing_time = time.time() - start_time
        print(f"\nData collection completed in {processing_time:.2f} seconds")
        print(f"Total data points collected: {len(self.collected_data)}")

        return self.collected_data

    def _test_connection(self) -> bool:
        """Test API connection"""
        print("Testing API connection...")

        # Try to get workspace info (simpler endpoint)
        result = self._make_request('workspaces/current')

        if result:
            print("API connection successful")
            return True
        else:
            print("API connection failed")
            return False

    def _collect_campaigns(self):
        """Collect all campaigns data"""
        print("Collecting campaigns...")

        campaigns = self._make_request('campaigns')
        if campaigns:
            self.collected_data['campaigns'] = campaigns
            campaign_count = len(campaigns) if isinstance(campaigns, list) else len(campaigns.get('data', []))
            print(f"   Found {campaign_count} campaigns")
        else:
            print("   Failed to collect campaigns")

    def _collect_accounts(self):
        """Collect all email accounts data"""
        print("Collecting email accounts...")

        accounts = self._make_request('accounts')
        if accounts:
            self.collected_data['accounts'] = accounts
            account_count = len(accounts) if isinstance(accounts, list) else len(accounts.get('data', []))
            print(f"   Found {account_count} email accounts")
        else:
            print("   Failed to collect accounts")

    def _collect_warmup_analytics(self):
        """Collect warmup analytics for all accounts"""
        print("Collecting warmup analytics...")

        if 'accounts' not in self.collected_data:
            print("   No accounts data available for warmup analytics")
            return

        accounts_data = self.collected_data['accounts']
        account_emails = []

        # Extract email addresses from accounts
        if isinstance(accounts_data, list):
            account_emails = [acc.get('email') for acc in accounts_data if acc.get('email')]
        elif isinstance(accounts_data, dict) and 'data' in accounts_data:
            account_emails = [acc.get('email') for acc in accounts_data['data'] if acc.get('email')]

        if not account_emails:
            print("   No email addresses found in accounts data")
            return

        # Request warmup analytics
        warmup_data = self._make_request('accounts/warmup-analytics', 'POST', {'emails': account_emails})

        if warmup_data:
            self.collected_data['warmup_analytics'] = warmup_data
            print(f"   Collected warmup analytics for {len(account_emails)} accounts")
        else:
            print("   Failed to collect warmup analytics")

    def _collect_campaign_analytics(self):
        """Collect detailed campaign analytics"""
        print("Collecting campaign analytics...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.config["DATA_COLLECTION"]["DAYS_BACK_ANALYTICS"])).strftime('%Y-%m-%d')

        # Get analytics for all campaigns
        analytics = self._make_request(f'campaigns/analytics?start_date={start_date}&end_date={end_date}')

        if analytics:
            self.collected_data['campaign_analytics'] = analytics
            analytics_count = len(analytics) if isinstance(analytics, list) else 1
            print(f"   Collected analytics for {analytics_count} campaigns")
        else:
            print("   Failed to collect campaign analytics")

        # Get analytics overview
        overview = self._make_request(f'campaigns/analytics/overview?start_date={start_date}&end_date={end_date}')

        if overview:
            self.collected_data['analytics_overview'] = overview
            print(f"   Collected analytics overview")
        else:
            print("   Failed to collect analytics overview")

    def _collect_daily_analytics(self):
        """Collect daily campaign analytics"""
        print("Collecting daily analytics...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.config["DATA_COLLECTION"]["DAYS_BACK_ANALYTICS"])).strftime('%Y-%m-%d')

        daily_analytics = self._make_request(f'campaigns/analytics/daily?start_date={start_date}&end_date={end_date}')

        if daily_analytics:
            self.collected_data['daily_analytics'] = daily_analytics
            days_count = len(daily_analytics) if isinstance(daily_analytics, list) else 1
            print(f"   Collected daily analytics for {days_count} days")
        else:
            print("   Failed to collect daily analytics")

    def _collect_steps_analytics(self):
        """Collect campaign steps analytics"""
        print("Collecting steps analytics...")

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=self.config["DATA_COLLECTION"]["DAYS_BACK_ANALYTICS"])).strftime('%Y-%m-%d')

        steps_analytics = self._make_request(f'campaigns/analytics/steps?start_date={start_date}&end_date={end_date}')

        if steps_analytics:
            self.collected_data['steps_analytics'] = steps_analytics
            steps_count = len(steps_analytics) if isinstance(steps_analytics, list) else 1
            print(f"   Collected steps analytics for {steps_count} steps")
        else:
            print("   Failed to collect steps analytics")

    def _test_account_vitals(self):
        """Test account vitals"""
        print("Testing account vitals...")

        if 'accounts' not in self.collected_data:
            print("   No accounts data available for vitals testing")
            return

        accounts_data = self.collected_data['accounts']
        account_emails = []

        # Extract email addresses from accounts
        if isinstance(accounts_data, list):
            account_emails = [acc.get('email') for acc in accounts_data if acc.get('email')]
        elif isinstance(accounts_data, dict) and 'data' in accounts_data:
            account_emails = [acc.get('email') for acc in accounts_data['data'] if acc.get('email')]

        if not account_emails:
            print("   No email addresses found in accounts data")
            return

        # Test account vitals
        vitals_data = self._make_request('accounts/test/vitals', 'POST', {'accounts': account_emails})

        if vitals_data:
            self.collected_data['account_vitals'] = vitals_data
            print(f"   Tested vitals for {len(account_emails)} accounts")
        else:
            print("   Failed to test account vitals")

    def _save_results(self, start_time: float):
        """Save all collected results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save individual files if requested
        if self.config["OUTPUT"]["SEPARATE_FILES"]:
            for data_type, data in self.collected_data.items():
                filename = f"instantly_{data_type}_{timestamp}.json"
                filepath = self.results_dir / filename

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"Saved: {filename}")

        # Save combined file if requested
        if self.config["OUTPUT"]["COMBINE_ALL"]:
            combined_data = {
                "metadata": {
                    "timestamp": timestamp,
                    "collection_time": time.time() - start_time,
                    "api_version": "v2",
                    "data_types_collected": list(self.collected_data.keys()),
                    "total_data_points": len(self.collected_data)
                },
                "data": self.collected_data
            }

            filename = f"instantly_complete_data_{timestamp}.json"
            filepath = self.results_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, indent=2, ensure_ascii=False)

            print(f"Saved combined: {filename}")

def main():
    """Main execution function"""
    print("=== INSTANTLY COMPREHENSIVE DATA COLLECTOR ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    collector = InstantlyDataCollector()
    results = collector.collect_all_data()

    if results:
        print(f"\nCollection successful!")
        print(f"Results saved to: {collector.results_dir}")
        print(f"Data types collected: {', '.join(results.keys())}")
    else:
        print(f"\nCollection failed!")

if __name__ == "__main__":
    main()