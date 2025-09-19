#!/usr/bin/env python3
"""
Simple Instantly Campaign Retriever
No external dependencies - uses only built-in Python libraries
"""

import urllib.request
import urllib.parse
import json
import base64
import os
import sys
from datetime import datetime

def load_api_key():
    """Load API key from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    
    if not os.path.exists(env_path):
        print("Error: .env file not found")
        return None
        
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                return line.split('=', 1)[1].strip()
    
    print("Error: INSTANTLY_API_KEY not found in .env")
    return None

def make_instantly_request(endpoint, api_key, method='GET', data=None):
    """Make request to Instantly API"""
    base_url = "https://api.instantly.ai/api/v1"
    url = f"{base_url}/{endpoint}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers)
        else:
            json_data = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error making request: {e}")
        return None

def get_campaigns(api_key):
    """Retrieve all campaigns"""
    print("Fetching campaigns...")
    return make_instantly_request('campaign/list', api_key)

def get_campaign_stats(api_key, campaign_id):
    """Get campaign statistics"""
    return make_instantly_request(f'analytics/campaign/{campaign_id}', api_key)

def save_output(data, filename):
    """Save data to outputs folder"""
    outputs_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
    os.makedirs(outputs_dir, exist_ok=True)
    
    filepath = os.path.join(outputs_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            f.write(str(data))
    
    print(f"Saved: {filepath}")

def main():
    """Main execution function"""
    print("=== Instantly Campaign Data Retriever ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        sys.exit(1)
    
    print(f"Using API key: {api_key[:20]}...")
    print()
    
    # Get campaigns
    campaigns_data = get_campaigns(api_key)
    if not campaigns_data:
        print("Failed to retrieve campaigns")
        sys.exit(1)
    
    # Save raw campaigns data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_output(campaigns_data, f'campaigns_raw_{timestamp}.json')
    
    # Process campaigns
    if 'campaigns' in campaigns_data:
        campaigns = campaigns_data['campaigns']
        print(f"Found {len(campaigns)} campaigns:")
        print()
        
        campaign_summary = []
        
        for i, campaign in enumerate(campaigns, 1):
            campaign_id = campaign.get('id', 'N/A')
            name = campaign.get('name', 'Unnamed')
            status = campaign.get('status', 'Unknown')
            
            print(f"{i}. {name}")
            print(f"   ID: {campaign_id}")
            print(f"   Status: {status}")
            
            # Get campaign stats
            stats = get_campaign_stats(api_key, campaign_id)
            if stats:
                campaign['analytics'] = stats
                
                # Extract key metrics
                if 'data' in stats:
                    data = stats['data']
                    sent = data.get('sent', 0)
                    opened = data.get('opened', 0)
                    replied = data.get('replied', 0)
                    clicked = data.get('clicked', 0)
                    
                    open_rate = (opened / sent * 100) if sent > 0 else 0
                    reply_rate = (replied / sent * 100) if sent > 0 else 0
                    
                    print(f"   Sent: {sent}, Opened: {opened} ({open_rate:.1f}%)")
                    print(f"   Replied: {replied} ({reply_rate:.1f}%), Clicked: {clicked}")
            
            print()
            
            campaign_summary.append({
                'id': campaign_id,
                'name': name,
                'status': status,
                'has_analytics': stats is not None
            })
        
        # Save processed data
        save_output(campaigns, f'campaigns_with_analytics_{timestamp}.json')
        save_output(campaign_summary, f'campaign_summary_{timestamp}.json')
        
        print(f"✅ Successfully processed {len(campaigns)} campaigns")
        print(f"📁 Data saved to services/instantly/outputs/")
        
    else:
        print("No campaigns found in response")
        print("Raw response:", campaigns_data)

if __name__ == "__main__":
    main()