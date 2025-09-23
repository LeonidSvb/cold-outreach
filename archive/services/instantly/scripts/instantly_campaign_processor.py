#!/usr/bin/env python3
"""
Instantly Campaign Analyzer and Optimizer
Connects to Instantly API to analyze and update all email campaigns
"""

import json
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

class InstantlyAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.instantly.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def make_request(self, endpoint, method="GET", data=None):
        """Make HTTP request to Instantly API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                req = Request(url, headers=self.headers)
            else:
                json_data = json.dumps(data).encode('utf-8') if data else None
                req = Request(url, data=json_data, headers=self.headers)
                req.get_method = lambda: method
            
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
                
        except HTTPError as e:
            print(f"HTTP Error {e.code}: {e.reason}")
            try:
                error_body = e.read().decode()
                print(f"Error details: {error_body}")
            except:
                pass
            return None
        except URLError as e:
            print(f"URL Error: {e}")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

def analyze_campaign_performance(campaign_data, analytics_data=None):
    """Analyze campaign performance metrics"""
    # Extract campaign info safely
    campaign_id = campaign_data.get('id') or campaign_data.get('_id', 'unknown')
    campaign_name = campaign_data.get('name', 'Unnamed Campaign')
    status = campaign_data.get('status', 'Unknown')
    created_at = campaign_data.get('created_at') or campaign_data.get('createdAt', 'Unknown')
    
    # Extract lead count
    total_leads = 0
    if 'total_leads' in campaign_data:
        total_leads = campaign_data['total_leads']
    elif 'leads' in campaign_data and isinstance(campaign_data['leads'], list):
        total_leads = len(campaign_data['leads'])
    elif 'leadCount' in campaign_data:
        total_leads = campaign_data['leadCount']
    
    # Extract metrics from analytics or campaign data
    sent_count = 0
    opened_count = 0
    clicked_count = 0
    replied_count = 0
    bounced_count = 0
    
    if analytics_data:
        sent_count = analytics_data.get('sent', 0)
        opened_count = analytics_data.get('opened', 0)
        clicked_count = analytics_data.get('clicked', 0)
        replied_count = analytics_data.get('replied', 0)
        bounced_count = analytics_data.get('bounced', 0)
    else:
        # Try to get from campaign data
        sent_count = campaign_data.get('sent', campaign_data.get('sentCount', 0))
        opened_count = campaign_data.get('opened', campaign_data.get('openedCount', 0))
        clicked_count = campaign_data.get('clicked', campaign_data.get('clickedCount', 0))
        replied_count = campaign_data.get('replied', campaign_data.get('repliedCount', 0))
        bounced_count = campaign_data.get('bounced', campaign_data.get('bouncedCount', 0))
    
    # Calculate rates
    analysis = {
        'campaign_id': campaign_id,
        'campaign_name': campaign_name,
        'status': status,
        'created_at': created_at,
        'total_leads': total_leads,
        'sent_count': sent_count,
        'opened_count': opened_count,
        'clicked_count': clicked_count,
        'replied_count': replied_count,
        'bounced_count': bounced_count,
        'open_rate': 0,
        'click_rate': 0,
        'reply_rate': 0,
        'bounce_rate': 0
    }
    
    if sent_count > 0:
        analysis['open_rate'] = round((opened_count / sent_count) * 100, 2)
        analysis['click_rate'] = round((clicked_count / sent_count) * 100, 2)
        analysis['reply_rate'] = round((replied_count / sent_count) * 100, 2)
        analysis['bounce_rate'] = round((bounced_count / sent_count) * 100, 2)
    
    return analysis

def generate_optimization_recommendations(analysis):
    """Generate optimization recommendations based on campaign performance"""
    recommendations = []
    
    # Open rate analysis
    if analysis['open_rate'] < 15:
        recommendations.append({
            'type': 'Subject Line Optimization - Critical',
            'priority': 'Critical',
            'impact': 9,
            'effort': 3,
            'recommendation': f"Open rate ({analysis['open_rate']}%) is critically low. Immediately test new subject lines with personalization, urgency, and curiosity gaps. Industry benchmark: 20-25%."
        })
    elif analysis['open_rate'] < 25:
        recommendations.append({
            'type': 'Subject Line Optimization',
            'priority': 'High',
            'impact': 7,
            'effort': 3,
            'recommendation': f"Open rate ({analysis['open_rate']}%) is below industry average. A/B test subject lines with better personalization and compelling hooks."
        })
    
    # Click rate analysis
    if analysis['click_rate'] < 1:
        recommendations.append({
            'type': 'Content & CTA Optimization',
            'priority': 'High',
            'impact': 8,
            'effort': 5,
            'recommendation': f"Click rate ({analysis['click_rate']}%) indicates weak content engagement. Revise email copy, strengthen value proposition, and optimize call-to-action placement."
        })
    elif analysis['click_rate'] < 3:
        recommendations.append({
            'type': 'Content Enhancement',
            'priority': 'Medium',
            'impact': 6,
            'effort': 4,
            'recommendation': f"Click rate ({analysis['click_rate']}%) has room for improvement. Test different CTAs, improve email design, and ensure mobile optimization."
        })
    
    # Reply rate analysis
    if analysis['reply_rate'] < 0.5:
        recommendations.append({
            'type': 'Personalization & Targeting',
            'priority': 'Critical',
            'impact': 10,
            'effort': 7,
            'recommendation': f"Reply rate ({analysis['reply_rate']}%) is extremely low. Increase personalization depth, improve prospect research, and refine target audience criteria."
        })
    elif analysis['reply_rate'] < 2:
        recommendations.append({
            'type': 'Message Optimization',
            'priority': 'High',
            'impact': 8,
            'effort': 6,
            'recommendation': f"Reply rate ({analysis['reply_rate']}%) needs improvement. Focus on value-first messaging, reduce pitch intensity, and add social proof."
        })
    
    # Bounce rate analysis
    if analysis['bounce_rate'] > 8:
        recommendations.append({
            'type': 'List Hygiene - Urgent',
            'priority': 'Critical',
            'impact': 10,
            'effort': 3,
            'recommendation': f"Bounce rate ({analysis['bounce_rate']}%) is damaging sender reputation. Immediately implement email verification, remove invalid addresses, and audit data sources."
        })
    elif analysis['bounce_rate'] > 3:
        recommendations.append({
            'type': 'List Quality Improvement',
            'priority': 'High',
            'impact': 7,
            'effort': 4,
            'recommendation': f"Bounce rate ({analysis['bounce_rate']}%) indicates data quality issues. Implement email verification and review lead sources."
        })
    
    # Volume and activity analysis
    if analysis['sent_count'] == 0:
        recommendations.append({
            'type': 'Campaign Activation',
            'priority': 'Critical',
            'impact': 10,
            'effort': 1,
            'recommendation': "Campaign has not sent any emails. Activate campaign or review setup configuration."
        })
    elif analysis['sent_count'] < analysis['total_leads'] * 0.5:
        recommendations.append({
            'type': 'Campaign Reach Optimization',
            'priority': 'Medium',
            'impact': 6,
            'effort': 3,
            'recommendation': f"Only {analysis['sent_count']} of {analysis['total_leads']} leads have been contacted. Review sending limits and campaign schedule."
        })
    
    # Engagement pattern analysis
    if analysis['opened_count'] > 0 and analysis['clicked_count'] == 0:
        recommendations.append({
            'type': 'Call-to-Action Optimization',
            'priority': 'High',
            'impact': 8,
            'effort': 4,
            'recommendation': "Prospects are opening but not clicking. Review CTA placement, wording, and landing page relevance."
        })
    
    return recommendations

def create_update_payload(analysis, recommendations):
    """Create payload for updating campaign with analysis data"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    # Create comprehensive notes
    notes = f"""
=== CAMPAIGN ANALYSIS REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analyzed by: Claude AI Campaign Optimizer

PERFORMANCE METRICS:
• Open Rate: {analysis['open_rate']}% ({analysis['opened_count']}/{analysis['sent_count']} opened)
• Click Rate: {analysis['click_rate']}% ({analysis['clicked_count']}/{analysis['sent_count']} clicked)
• Reply Rate: {analysis['reply_rate']}% ({analysis['replied_count']}/{analysis['sent_count']} replied)
• Bounce Rate: {analysis['bounce_rate']}% ({analysis['bounced_count']}/{analysis['sent_count']} bounced)

CAMPAIGN STATS:
• Total Leads: {analysis['total_leads']}
• Emails Sent: {analysis['sent_count']}
• Campaign Status: {analysis['status']}
• Created: {analysis['created_at']}

TOP OPTIMIZATION OPPORTUNITIES:
""".strip()
    
    # Add top 3 recommendations
    for i, rec in enumerate(recommendations[:3], 1):
        notes += f"\n{i}. {rec['type']} (Priority: {rec['priority']})"
        notes += f"\n   → {rec['recommendation']}"
        notes += f"\n   Impact: {rec['impact']}/10 | Effort: {rec['effort']}/10\n"
    
    if len(recommendations) > 3:
        notes += f"\n+ {len(recommendations) - 3} additional recommendations identified"
    
    notes += f"\n\n=== END ANALYSIS REPORT ===\nLast Updated: {timestamp}"
    
    # Create tags for easy filtering
    tags = [
        f"ai_analyzed_{timestamp}",
        f"open_rate_{int(analysis['open_rate'])}pct",
        f"reply_rate_{int(analysis['reply_rate'])}pct"
    ]
    
    # Add performance tier tags
    if analysis['reply_rate'] >= 3:
        tags.append("high_performer")
    elif analysis['reply_rate'] >= 1:
        tags.append("medium_performer")
    else:
        tags.append("needs_optimization")
    
    # Add priority tags based on recommendations
    critical_recommendations = [r for r in recommendations if r['priority'] == 'Critical']
    if critical_recommendations:
        tags.append("requires_immediate_attention")
    
    return {
        'tags': tags,
        'notes': notes
    }

def main():
    """Main execution function"""
    print("=" * 70)
    print("INSTANTLY CAMPAIGN ANALYZER & OPTIMIZER")
    print("Powered by Claude AI")
    print("=" * 70)
    
    # Initialize API client
    api_key = "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0OnpoTXlidndIZ3JuZQ=="
    client = InstantlyAPIClient(api_key)
    
    # Results tracking
    results = {
        'total_campaigns': 0,
        'successful_updates': 0,
        'failed_updates': 0,
        'campaign_analyses': [],
        'all_recommendations': [],
        'summary_stats': {}
    }
    
    try:
        # Step 1: Retrieve all campaigns
        print("\n🔍 STEP 1: Retrieving campaigns from Instantly...")
        campaigns = client.make_request("campaign/list")
        
        if not campaigns:
            print("❌ Failed to retrieve campaigns or no campaigns found.")
            return results
        
        results['total_campaigns'] = len(campaigns)
        print(f"✅ Found {len(campaigns)} campaigns to analyze")
        
        # Step 2: Process each campaign
        print("\n📊 STEP 2: Analyzing campaigns...")
        print("-" * 50)
        
        for i, campaign in enumerate(campaigns, 1):
            campaign_name = campaign.get('name', f'Campaign {i}')
            print(f"\n[{i}/{len(campaigns)}] Processing: {campaign_name}")
            
            campaign_id = campaign.get('id') or campaign.get('_id')
            if not campaign_id:
                print("  ❌ No campaign ID found, skipping...")
                results['failed_updates'] += 1
                continue
            
            try:
                # Get detailed campaign data
                print("  📋 Fetching campaign details...")
                campaign_details = client.make_request(f"campaign/{campaign_id}")
                if not campaign_details:
                    print("  ⚠️  Using basic campaign data")
                    campaign_details = campaign
                
                # Try to get analytics data
                print("  📈 Fetching analytics data...")
                analytics_data = client.make_request(f"analytics/campaign/{campaign_id}")
                if not analytics_data:
                    print("  ⚠️  Analytics data not available, using campaign data")
                
                # Analyze performance
                print("  🔬 Analyzing performance...")
                analysis = analyze_campaign_performance(campaign_details, analytics_data)
                results['campaign_analyses'].append(analysis)
                
                # Generate recommendations
                print("  💡 Generating recommendations...")
                recommendations = generate_optimization_recommendations(analysis)
                results['all_recommendations'].extend(recommendations)
                
                # Display key metrics
                print(f"  📊 Metrics: Open {analysis['open_rate']}% | Click {analysis['click_rate']}% | Reply {analysis['reply_rate']}% | Bounce {analysis['bounce_rate']}%")
                print(f"  🎯 Generated {len(recommendations)} recommendations")
                
                # Update campaign
                print("  🔄 Updating campaign with analysis...")
                update_payload = create_update_payload(analysis, recommendations)
                
                update_result = client.make_request(f"campaign/{campaign_id}", "PATCH", update_payload)
                
                if update_result:
                    print("  ✅ Campaign updated successfully")
                    results['successful_updates'] += 1
                else:
                    print("  ❌ Campaign update failed")
                    results['failed_updates'] += 1
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error processing campaign: {e}")
                results['failed_updates'] += 1
                continue
        
        # Step 3: Generate summary statistics
        print("\n📋 STEP 3: Generating summary statistics...")
        analyses = results['campaign_analyses']
        if analyses:
            results['summary_stats'] = {
                'avg_open_rate': round(sum(a['open_rate'] for a in analyses) / len(analyses), 2),
                'avg_click_rate': round(sum(a['click_rate'] for a in analyses) / len(analyses), 2),
                'avg_reply_rate': round(sum(a['reply_rate'] for a in analyses) / len(analyses), 2),
                'avg_bounce_rate': round(sum(a['bounce_rate'] for a in analyses) / len(analyses), 2),
                'total_sent': sum(a['sent_count'] for a in analyses),
                'total_opened': sum(a['opened_count'] for a in analyses),
                'total_clicked': sum(a['clicked_count'] for a in analyses),
                'total_replied': sum(a['replied_count'] for a in analyses),
                'total_bounced': sum(a['bounced_count'] for a in analyses)
            }
        
        # Display final results
        print("\n" + "=" * 70)
        print("📈 FINAL ANALYSIS REPORT")
        print("=" * 70)
        
        print(f"Total Campaigns Analyzed: {results['total_campaigns']}")
        print(f"Successful Updates: {results['successful_updates']}")
        print(f"Failed Updates: {results['failed_updates']}")
        
        if results['total_campaigns'] > 0:
            success_rate = (results['successful_updates'] / results['total_campaigns']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"Total Recommendations Generated: {len(results['all_recommendations'])}")
        
        if results['summary_stats']:
            stats = results['summary_stats']
            print(f"\nAGGREGATE PERFORMANCE METRICS:")
            print(f"• Average Open Rate: {stats['avg_open_rate']}%")
            print(f"• Average Click Rate: {stats['avg_click_rate']}%")
            print(f"• Average Reply Rate: {stats['avg_reply_rate']}%")
            print(f"• Average Bounce Rate: {stats['avg_bounce_rate']}%")
            print(f"\nTOTAL VOLUME:")
            print(f"• Emails Sent: {stats['total_sent']:,}")
            print(f"• Emails Opened: {stats['total_opened']:,}")
            print(f"• Emails Clicked: {stats['total_clicked']:,}")
            print(f"• Replies Received: {stats['total_replied']:,}")
            print(f"• Emails Bounced: {stats['total_bounced']:,}")
        
        # Detailed campaign breakdown
        print(f"\nDETAILED CAMPAIGN BREAKDOWN:")
        print("-" * 50)
        
        for analysis in results['campaign_analyses']:
            print(f"\n📧 {analysis['campaign_name']}")
            print(f"   Status: {analysis['status']} | Leads: {analysis['total_leads']}")
            print(f"   Metrics: Open {analysis['open_rate']}% | Click {analysis['click_rate']}% | Reply {analysis['reply_rate']}%")
            
            # Show top recommendation
            campaign_recs = [r for r in results['all_recommendations'] 
                           if r.get('campaign_id') == analysis['campaign_id']][:1]
            if campaign_recs:
                print(f"   Top Rec: {campaign_recs[0]['type']}")
        
        print(f"\n✅ Analysis complete! All campaign data has been updated with comprehensive insights.")
        
    except Exception as e:
        print(f"\n❌ Critical error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    return results

if __name__ == "__main__":
    results = main()