#!/usr/bin/env python3
"""
=== MAILS.SO EMAIL VALIDATOR ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Core email validation logic using Mails.so API

FEATURES:
- Batch submission
- Polling for results
- Merging with original data
- NO UI dependencies - pure Python

USAGE:
from modules.email_verification.validator import MailsValidator

validator = MailsValidator(api_key='your-key')
batch_id = validator.submit_batch(emails)
results = validator.poll_results(batch_id)
"""

import requests
import time
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class MailsValidator:
    """Email validation using Mails.so API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.mails.so/v1/batch'

    def submit_batch(self, emails: List[str], name: Optional[str] = None) -> Dict:
        """
        Submit batch of emails for validation

        Args:
            emails: List of email addresses
            name: Optional batch name

        Returns:
            dict with batch_id, size, created_at
        """
        headers = {
            'x-mails-api-key': self.api_key,
            'Content-Type': 'application/json'
        }

        payload = {'emails': emails}
        if name:
            payload['name'] = name

        response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'batch_id': result.get('id'),
                'size': result.get('size'),
                'created_at': result.get('created_at'),
                'submitted_at': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': response.text,
                'status_code': response.status_code
            }

    def check_status(self, batch_id: str) -> Optional[Dict]:
        """
        Check batch validation status

        Args:
            batch_id: Batch ID from submission

        Returns:
            dict with status or None if error
        """
        url = f'{self.base_url}/{batch_id}'
        headers = {'x-mails-api-key': self.api_key}

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            print(f'Error checking status: {e}')
            return None

    def poll_results(self, batch_id: str, max_wait_minutes: int = 30,
                     callback=None) -> Optional[Dict]:
        """
        Poll batch status until complete

        Args:
            batch_id: Batch ID from submission
            max_wait_minutes: Maximum time to wait
            callback: Optional callback function for progress updates

        Returns:
            Complete validation results or None if timeout
        """
        start_time = time.time()
        iteration = 0

        while True:
            iteration += 1
            elapsed = time.time() - start_time

            if callback:
                callback(iteration, int(elapsed))

            result = self.check_status(batch_id)

            if not result:
                time.sleep(15)
                continue

            finished_at = result.get('finished_at')

            if finished_at:
                return result

            # Check timeout
            if elapsed > max_wait_minutes * 60:
                return None

            # Smart polling interval
            if elapsed < 60:
                wait = 10
            elif elapsed < 300:
                wait = 30
            else:
                wait = 60

            time.sleep(wait)

    def process_results(self, validation_results: Dict) -> pd.DataFrame:
        """
        Convert validation results to DataFrame

        Args:
            validation_results: Results from poll_results()

        Returns:
            DataFrame with validation data
        """
        emails_data = validation_results.get('emails', [])

        if not emails_data:
            return pd.DataFrame()

        return pd.DataFrame(emails_data)

    def merge_with_original(self, validation_df: pd.DataFrame,
                           original_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge validation results with original data

        Args:
            validation_df: DataFrame from process_results()
            original_df: Original data with emails

        Returns:
            Merged DataFrame
        """
        return validation_df.merge(original_df, on='email', how='left')

    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate validation statistics

        Args:
            df: DataFrame with validation results

        Returns:
            dict with statistics
        """
        if 'result' not in df.columns:
            return {}

        total = len(df)
        result_counts = df['result'].value_counts().to_dict()

        stats = {
            'total': total,
            'deliverable': result_counts.get('deliverable', 0),
            'unknown': result_counts.get('unknown', 0),
            'risky': result_counts.get('risky', 0),
            'undeliverable': result_counts.get('undeliverable', 0)
        }

        # Percentages
        for key in ['deliverable', 'unknown', 'risky', 'undeliverable']:
            stats[f'{key}_pct'] = (stats[key] / total * 100) if total > 0 else 0

        # Free emails
        if 'is_free' in df.columns:
            stats['free_emails'] = df['is_free'].sum()
            stats['corporate_emails'] = total - stats['free_emails']

        return stats

    def filter_by_result(self, df: pd.DataFrame, result: str) -> pd.DataFrame:
        """
        Filter DataFrame by validation result

        Args:
            df: DataFrame with results
            result: 'deliverable', 'unknown', 'risky', or 'undeliverable'

        Returns:
            Filtered DataFrame
        """
        if 'result' not in df.columns:
            return df

        return df[df['result'] == result].copy()

    def filter_corporate_only(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out free email providers

        Args:
            df: DataFrame with results

        Returns:
            DataFrame with corporate emails only
        """
        if 'is_free' not in df.columns:
            return df

        return df[df['is_free'] == False].copy()
