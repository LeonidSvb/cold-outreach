import requests
import json
import base64
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Any
import time

class InstantlyAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.instantly.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def make_request(self, endpoint: str, method: str = "GET", data: dict = None):
        """Make API request with error handling"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return None
    
    def get_all_campaigns(self):
        """Retrieve all email campaigns from Instantly account"""
        print("Retrieving all campaigns...")
        campaigns = self.make_request("campaign/list")
        if campaigns:
            print(f"Found {len(campaigns)} campaigns")
            return campaigns
        return []
    
    def get_campaign_details(self, campaign_id: str):
        """Get detailed information about a specific campaign"""
        return self.make_request(f"campaign/{campaign_id}")
    
    def get_campaign_analytics(self, campaign_id: str):
        """Get analytics data for a specific campaign"""
        return self.make_request(f"analytics/campaign/{campaign_id}")
    
    def get_campaign_sequences(self, campaign_id: str):
        """Get email sequences for a campaign"""
        return self.make_request(f"campaign/{campaign_id}/sequences")
    
    def update_campaign(self, campaign_id: str, update_data: dict):
        """Update campaign information"""
        return self.make_request(f"campaign/{campaign_id}", method="PATCH", data=update_data)
    
    def analyze_campaign_performance(self, campaign_data: dict, analytics_data: dict = None):
        """Analyze campaign performance and generate insights"""
        analysis = {
            'campaign_id': campaign_data.get('id'),
            'campaign_name': campaign_data.get('name'),
            'status': campaign_data.get('status'),
            'created_at': campaign_data.get('created_at'),
            'total_leads': campaign_data.get('total_leads', 0),
            'sent_count': analytics_data.get('sent', 0) if analytics_data else 0,
            'opened_count': analytics_data.get('opened', 0) if analytics_data else 0,
            'clicked_count': analytics_data.get('clicked', 0) if analytics_data else 0,
            'replied_count': analytics_data.get('replied', 0) if analytics_data else 0,
            'bounced_count': analytics_data.get('bounced', 0) if analytics_data else 0,
        }
        
        # Calculate rates
        if analysis['sent_count'] > 0:
            analysis['open_rate'] = round((analysis['opened_count'] / analysis['sent_count']) * 100, 2)
            analysis['click_rate'] = round((analysis['clicked_count'] / analysis['sent_count']) * 100, 2)
            analysis['reply_rate'] = round((analysis['replied_count'] / analysis['sent_count']) * 100, 2)
            analysis['bounce_rate'] = round((analysis['bounced_count'] / analysis['sent_count']) * 100, 2)
        else:
            analysis['open_rate'] = 0
            analysis['click_rate'] = 0
            analysis['reply_rate'] = 0
            analysis['bounce_rate'] = 0
        
        return analysis
    
    def generate_optimization_recommendations(self, analysis: dict):
        """Generate optimization recommendations based on campaign analysis"""
        recommendations = []
        
        # Open rate recommendations
        if analysis['open_rate'] < 20:
            recommendations.append({
                'type': 'Subject Line Optimization',
                'priority': 'High',
                'impact': 8,
                'effort': 3,
                'recommendation': 'Open rate is below industry average (20-25%). Consider A/B testing subject lines with personalization, urgency, or curiosity gaps.'
            })
        
        # Click rate recommendations
        if analysis['click_rate'] < 2:
            recommendations.append({
                'type': 'Content Optimization',
                'priority': 'Medium',
                'impact': 6,
                'effort': 5,
                'recommendation': 'Click rate is low. Review email content for clear CTAs, value proposition, and mobile optimization.'
            })
        
        # Reply rate recommendations
        if analysis['reply_rate'] < 1:
            recommendations.append({
                'type': 'Personalization Enhancement',
                'priority': 'High',
                'impact': 9,
                'effort': 6,
                'recommendation': 'Reply rate suggests low engagement. Increase personalization, research prospects better, and adjust messaging tone.'
            })
        
        # Bounce rate recommendations
        if analysis['bounce_rate'] > 5:
            recommendations.append({
                'type': 'List Hygiene',
                'priority': 'Critical',
                'impact': 10,
                'effort': 4,
                'recommendation': 'High bounce rate indicates poor list quality. Implement email verification and remove invalid addresses.'
            })
        
        return recommendations
    
    def create_campaign_update_data(self, analysis: dict, recommendations: list):
        """Create update data for campaign based on analysis"""
        update_data = {
            'tags': [
                f"analyzed_{datetime.now().strftime('%Y%m%d')}",
                f"open_rate_{analysis['open_rate']}pct",
                f"reply_rate_{analysis['reply_rate']}pct"
            ],
            'notes': f"""
Campaign Analysis Report - {datetime.now().strftime('%Y-%m-%d')}

Performance Metrics:
- Open Rate: {analysis['open_rate']}%
- Click Rate: {analysis['click_rate']}%
- Reply Rate: {analysis['reply_rate']}%
- Bounce Rate: {analysis['bounce_rate']}%

Total Stats:
- Sent: {analysis['sent_count']}
- Opened: {analysis['opened_count']}
- Clicked: {analysis['clicked_count']}
- Replied: {analysis['replied_count']}
- Bounced: {analysis['bounced_count']}

Top Recommendations:
{chr(10).join([f"- {rec['recommendation']}" for rec in recommendations[:3]])}

Analysis completed by Claude AI Campaign Optimizer
            """.strip()
        }
        
        return update_data

def main():
    # Initialize analyzer
    api_key = "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0OnpoTXlidndIZ3JuZQ=="
    analyzer = InstantlyAnalyzer(api_key)
    
    # Results tracking
    results = {
        'total_campaigns': 0,
        'successful_updates': 0,
        'failed_updates': 0,
        'campaign_analyses': [],
        'all_recommendations': []
    }
    
    print("Starting Instantly Campaign Analysis and Update Process...")
    print("=" * 60)
    
    # Step 1: Retrieve all campaigns
    campaigns = analyzer.get_all_campaigns()
    if not campaigns:
        print("No campaigns found or failed to retrieve campaigns.")
        return results
    
    results['total_campaigns'] = len(campaigns)
    print(f"Found {len(campaigns)} campaigns to analyze and update")
    
    # Step 2: Analyze each campaign
    for i, campaign in enumerate(campaigns, 1):
        print(f"\nProcessing Campaign {i}/{len(campaigns)}: {campaign.get('name', 'Unnamed')}")
        print("-" * 40)
        
        campaign_id = campaign.get('id')
        if not campaign_id:
            print("Campaign ID not found, skipping...")
            continue
        
        # Get detailed campaign data
        campaign_details = analyzer.get_campaign_details(campaign_id)
        if not campaign_details:
            print("Failed to get campaign details, using basic data...")
            campaign_details = campaign
        
        # Get analytics data
        analytics = analyzer.get_campaign_analytics(campaign_id)
        if not analytics:
            print("Failed to get analytics data, proceeding with available data...")
        
        # Analyze campaign performance
        analysis = analyzer.analyze_campaign_performance(campaign_details, analytics)
        results['campaign_analyses'].append(analysis)
        
        # Generate recommendations
        recommendations = analyzer.generate_optimization_recommendations(analysis)
        results['all_recommendations'].extend(recommendations)
        
        # Print analysis summary
        print(f"Campaign: {analysis['campaign_name']}")
        print(f"Status: {analysis['status']}")
        print(f"Total Leads: {analysis['total_leads']}")
        print(f"Open Rate: {analysis['open_rate']}%")
        print(f"Click Rate: {analysis['click_rate']}%")
        print(f"Reply Rate: {analysis['reply_rate']}%")
        print(f"Bounce Rate: {analysis['bounce_rate']}%")
        print(f"Recommendations: {len(recommendations)}")
        
        # Step 3: Update campaign with analysis data
        update_data = analyzer.create_campaign_update_data(analysis, recommendations)
        
        print("Updating campaign with analysis data...")
        update_result = analyzer.update_campaign(campaign_id, update_data)
        
        if update_result:
            print("✓ Campaign updated successfully")
            results['successful_updates'] += 1
        else:
            print("✗ Failed to update campaign")
            results['failed_updates'] += 1
        
        # Add delay to respect rate limits
        time.sleep(1)
    
    # Generate final report
    print("\n" + "=" * 60)
    print("CAMPAIGN ANALYSIS AND UPDATE SUMMARY")
    print("=" * 60)
    
    print(f"Total Campaigns Found: {results['total_campaigns']}")
    print(f"Successful Updates: {results['successful_updates']}")
    print(f"Failed Updates: {results['failed_updates']}")
    print(f"Success Rate: {(results['successful_updates']/results['total_campaigns']*100):.1f}%" if results['total_campaigns'] > 0 else "N/A")
    
    return results

if __name__ == "__main__":
    results = main()