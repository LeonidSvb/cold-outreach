#!/usr/bin/env python3
"""
Test script for personalization_extractor
Tests the extraction of personalization insights from real website content
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from personalization_extractor import PersonalizationExtractor

# Test data - real website content from Canadian companies
test_companies = [
    {
        "company_name": "Big Fish Creative",
        "contact_name": "Brent G",
        "raw_content_data": {
            "https://bigfishcreative.ca/about-bfc": {
                "title": "About Big Fish Creative",
                "text": """About Big Fish Creative

Call us 'obsessed', but we can't get enough of innovative digital design and results-driven strategy.

Big Fish Creative was founded in 2016 to help brands and businesses navigate their digital customer journey. Based on the Canadian West Coast, we work closely with entrepreneurs and decision-makers to understand their audiences and help them build the right marketing campaigns and processes to create a loyal client base. We believe the right product vision and marketing strategy can increase revenue and keep clients coming back.

We are rooted in our passion for creating the remarkable, thriving on using our expertise in strategic problem solving, addicted to the challenge of what's next while endlessly striving to be one step ahead. We are a tight-knit team of expert creators, dedicated to seeking innovative and effective solutions.

We Build Digital Solutions For Brands & Businesses Worldwide

Industries That we Specialize In:
Medical Spas, Dentistry, Retail & eCommerce, Automotive, Education & Training, Technology & Software, Home Improvement, Construction, Travel & Hospitality, Event Planning, Telecommunications, Manufacturing, Industrial, Professional Consulting, Energy & Utilities, Fitness & Wellness

Recent portfolio includes: Sempre Uno, Fundamental Power Solutions, Crunch Fitness, Beachcomber Hot Tubs, Cadieux Glow, Gallery Vancouver

Services: Remarkable Creative, Strategic Digital Marketing, Fearless Problem Solving""",
                "word_count": 215
            }
        }
    },
    {
        "company_name": "Stryve Digital Marketing", 
        "contact_name": "Grace Cole",
        "raw_content_data": {
            "https://stryvemarketing.com/about": {
                "title": "About Stryve - B2B Digital Marketing Agency",
                "text": """We're a B2B digital marketing and design agency that's all about growing together.

We'll meet you where you're at.

We've helped enterprise marketing teams and scale-up companies build their digital marketing capabilities to capture emerging opportunities. We take a holistic and consultative view of your marketing, regardless of which tactics we're executing.

FOCUSED ON DIGITAL SINCE 2008

Key milestones:
- 2023: Stryve celebrates 15 years of marketing and design excellence - unveiled a special edition crystalized logo
- 2021: Became a premier Pantheon partner after years of successful website launches  
- 2020: Won WebAward for outstanding achievement in B2B (Axonify site) and manufacturing (Emtek site)
- 2020: Named a Top Growing Company in Canada by The Globe and Mail
- 2019: Became a HubSpot agency partner
- 2018: Won Best Marketing Campaign award - Uberflip recognized work with Syngenta
- 2018: Committed to agile marketing - moved all work to Jira
- 2017: Moved office to Catalyst137 - North America's largest IoT campus
- 2014: Voted Favourite Marketing Firm in Waterloo Region twice
- 2012: Stryve founders Sourov De and Ryan Burgio named to Top 40 Under 40
- 2008: Founded Stryve Group to help companies figure out social media

Team includes: Sourov De (Managing Partner), Ryan Burgio (Managing Partner), Sarah Rosenquist (Digital Marketing Director & Head of Operations), Grace Cole (Creative Director & Head of HR), Kaleigh Bulford (Digital Marketing Director & Head of Marketing), and others.

A flexible, multi-talented team. Stryvers develop their skills and experience in many tactics and industries. This allows us to cross-pollinate ideas and insights, consider how decisions impact the larger marketing picture, and move faster.""",
                "word_count": 318
            }
        }
    }
]

def main():
    print("Testing Personalization Extractor with Real Canadian Company Data")
    print("=" * 70)
    
    try:
        # Initialize extractor
        extractor = PersonalizationExtractor()
        
        # Test each company
        for i, company in enumerate(test_companies, 1):
            print(f"\nTesting Company {i}/{len(test_companies)}: {company['company_name']}")
            print("-" * 50)
            
            result = extractor.extract_insights(
                company['raw_content_data'],
                company['company_name'],
                company['contact_name']
            )
            
            if result['processing_stats']['success']:
                print(f"\nSUCCESS - Extracted {len(result['personalization_insights'])} insights:")
                print("\nPERSONALIZATION INSIGHTS:")
                
                for j, insight in enumerate(result['personalization_insights'], 1):
                    print(f"\n{j}. [{insight.get('personalization_value', 'UNKNOWN')}] {insight.get('insight_type', 'unknown').upper()}")
                    print(f"   Insight: {insight.get('insight', 'No insight')}")
                    print(f"   Outreach Application: {insight.get('outreach_application', 'No application')}")
                
                print(f"\nSUMMARY: {result.get('summary', 'No summary')}")
                print(f"\nRECOMMENDED APPROACH: {result.get('recommended_approach', 'No recommendation')}")
                
            else:
                print(f"\nFAILED - No insights extracted")
                if result['processing_stats']['errors']:
                    print(f"   Errors: {result['processing_stats']['errors']}")
        
        # Generate final report
        extractor.generate_session_report()
        
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()