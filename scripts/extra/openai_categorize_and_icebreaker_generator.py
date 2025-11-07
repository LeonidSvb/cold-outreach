#!/usr/bin/env python3
"""
=== CATEGORY ANALYZER & ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Analyze enriched leads, categorize by industry, and generate personalized icebreakers

FEATURES:
- Automatic categorization (HVAC, Landscaping, Other)
- Priority scoring for outreach sequencing
- AI-powered icebreaker generation in casual style
- Multiple icebreaker variants (5-7 per company)
- Texas market geographic hook

USAGE:
1. Configure INPUT_CSV from personalization enricher
2. Run: python categorize_and_icebreaker_generator.py
3. Get categorized CSV + icebreakers ready for outreach
"""

import sys
import csv
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import Counter

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_CSV": "modules/scraping/results/personalization_enriched_20251106_140031.csv",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": 0.7
}

def categorize_company(category_name: str, business_type: str, services: str) -> Dict:
    """Categorize company by industry"""

    category_lower = category_name.lower()
    business_lower = business_type.lower()
    services_lower = services.lower()

    combined = f"{category_lower} {business_lower} {services_lower}"

    # HVAC Category
    hvac_keywords = ['hvac', 'heating', 'air conditioning', 'ac ', 'furnace', 'cooling', 'heat pump']
    if any(keyword in combined for keyword in hvac_keywords):
        return {
            "category": "HVAC",
            "priority": 8,
            "reason": "High-value service business with recurring revenue potential"
        }

    # Landscaping Category
    landscape_keywords = ['landscape', 'landscaping', 'lawn care', 'lawn service', 'tree service',
                          'lawn mowing', 'yard service', 'sprinkler', 'irrigation']
    if any(keyword in combined for keyword in landscape_keywords):
        return {
            "category": "Landscaping",
            "priority": 7,
            "reason": "Seasonal business with high local competition"
        }

    # Auto/Truck Repair
    auto_keywords = ['auto repair', 'truck repair', 'mechanic', 'automotive', 'car care']
    if any(keyword in combined for keyword in auto_keywords):
        return {
            "category": "Auto_Repair",
            "priority": 6,
            "reason": "Service business with customer retention focus"
        }

    # Other
    return {
        "category": "Other",
        "priority": 5,
        "reason": "Requires manual review"
    }

def generate_icebreakers(company_data: Dict) -> Dict:
    """
    Generate 5-7 icebreaker variants using OpenAI

    Style: Short, casual, Texas market hook
    Format: Hey {Name/Role}, {compliment} {specific detail} - I'm in Texas too. {CTA}.
    """

    title_field = [k for k in company_data.keys() if 'title' in k.lower()][0]
    company_name = company_data[title_field]
    business_type = company_data.get('business_type', '')
    services = company_data.get('services', '')
    hooks = company_data.get('personalization_hooks', '')
    location = company_data.get('city', 'Texas')
    owner_name = company_data.get('owner_name', '')
    category = company_data.get('category', 'Unknown')

    try:
        client = OpenAI()

        prompt = f"""Generate 7 short, casual icebreaker variants for cold email outreach to this company.

Company: {company_name}
Location: {location}, Texas
Category: {category}
Business: {business_type}
Services: {services}
Owner: {owner_name if owner_name else "Unknown"}
Hooks: {hooks}

STYLE EXAMPLES (match this vibe):
- "Hey Renaud, impressed by your Directeur artistique at Altitude - I'm also in the Quebec market. Wanted to run something by you."
- "Hey Brent, awesome to see you drive luxury sales at Big Fish - I'm also in the Washington market. Had something you might find interesting."
- "Hey Grace, love how you lead marketing at Stryve - I'm active in Ontario too. Figured I'd reach out quickly."

RULES:
1. Keep it 1-2 lines max (same length as examples)
2. Start with "Hey {{{{name}}}}" (use placeholder for first name)
3. Use casual compliments: "awesome to see", "love how", "impressed by", "cool to see"
4. Mention specific detail about their business (service, specialty, market)
5. Geographic hook: "I'm also in Texas" or "I'm active in {location} too"
6. End with soft CTA: "Wanted to run something by you", "Had something interesting", "Figured I'd reach out"
7. No emojis, no exclamation marks (keep professional-casual)
8. Make each variant feel different (vary structure and wording)

Return ONLY valid JSON array (no markdown, no code blocks):
[
  "icebreaker variant 1",
  "icebreaker variant 2",
  "icebreaker variant 3",
  "icebreaker variant 4",
  "icebreaker variant 5",
  "icebreaker variant 6",
  "icebreaker variant 7"
]"""

        response = client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are an expert cold email copywriter. Generate short, casual icebreakers that sound natural and conversational. Match the exact style and length of the examples provided."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=CONFIG["OPENAI_TEMPERATURE"]
        )

        ai_response = response.choices[0].message.content.strip()

        # Clean response
        ai_response = re.sub(r'^```json\s*', '', ai_response)
        ai_response = re.sub(r'^```\s*', '', ai_response)
        ai_response = re.sub(r'\s*```$', '', ai_response)
        ai_response = ai_response.strip()

        # Parse JSON
        icebreakers = json.loads(ai_response)

        return {
            "status": "success",
            "icebreakers": icebreakers,
            "tokens_used": response.usage.total_tokens
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for {company_name}: {e}")
        return {
            "status": "json_error",
            "icebreakers": [],
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Icebreaker generation failed for {company_name}: {e}")
        return {
            "status": "error",
            "icebreakers": [],
            "error": str(e)
        }

def process_companies(input_file: str) -> List[Dict]:
    """Process companies: categorize + generate icebreakers"""

    logger.info(f"Reading CSV: {input_file}")

    # Read CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter only successful AI summaries
    successful_rows = [r for r in rows if r.get('ai_summary_status') == 'success']

    logger.info(f"Processing {len(successful_rows)} companies with AI summaries...")

    results = []
    total_tokens = 0

    for i, row in enumerate(successful_rows, 1):
        title_field = [k for k in row.keys() if 'title' in k.lower()][0]
        company_name = row[title_field]

        logger.info(f"[{i}/{len(successful_rows)}] Processing: {company_name[:40]}")

        # Step 1: Categorize
        category_info = categorize_company(
            row.get('categoryName', ''),
            row.get('business_type', ''),
            row.get('services', '')
        )

        enriched = {**row}
        enriched['category'] = category_info['category']
        enriched['priority'] = category_info['priority']
        enriched['priority_reason'] = category_info['reason']

        logger.info(f"  Category: {category_info['category']} (Priority: {category_info['priority']})")

        # Step 2: Generate icebreakers
        logger.info(f"  Generating icebreakers...")
        icebreaker_result = generate_icebreakers(enriched)

        if icebreaker_result['status'] == 'success':
            icebreakers = icebreaker_result['icebreakers']
            enriched['icebreaker_count'] = len(icebreakers)

            # Store icebreakers as separate columns
            for idx, icebreaker in enumerate(icebreakers[:7], 1):
                enriched[f'icebreaker_{idx}'] = icebreaker

            total_tokens += icebreaker_result['tokens_used']
            logger.info(f"  ✓ Generated {len(icebreakers)} icebreakers")
        else:
            enriched['icebreaker_count'] = 0
            enriched['icebreaker_error'] = icebreaker_result.get('error', '')
            logger.error(f"  ✗ Icebreaker generation failed")

        results.append(enriched)

    logger.info(f"\nTotal OpenAI tokens used: {total_tokens:,}")

    return results

def save_results(results: List[Dict]) -> str:
    """Save categorized results with icebreakers"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/openai/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"categorized_with_icebreakers_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    # Write CSV
    fieldnames = list(results[0].keys())

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def print_analysis(results: List[Dict]):
    """Print category analysis and recommendations"""

    # Category distribution
    categories = Counter(r['category'] for r in results)

    print(f"\n{'='*70}")
    print(f"CATEGORY ANALYSIS & OUTREACH RECOMMENDATIONS")
    print(f"{'='*70}")
    print(f"\nCategory Distribution:")
    for category, count in categories.most_common():
        percentage = count / len(results) * 100
        print(f"  {category:20} {count:3} companies ({percentage:.1f}%)")

    # Priority analysis
    print(f"\n{'='*70}")
    print(f"RECOMMENDED OUTREACH PRIORITY")
    print(f"{'='*70}")

    # Sort by priority
    sorted_by_priority = sorted(results, key=lambda x: x.get('priority', 0), reverse=True)

    print(f"\n🎯 HIGHEST PRIORITY (Start here):")
    for i, company in enumerate(sorted_by_priority[:5], 1):
        title_field = [k for k in company.keys() if 'title' in k.lower()][0]
        print(f"{i}. {company[title_field][:40]:40} | {company['category']:12} | Priority: {company['priority']}")
        print(f"   Why: {company['priority_reason']}")
        print(f"   Services: {company.get('services', 'N/A')[:60]}")
        print()

    # Show sample icebreakers
    print(f"{'='*70}")
    print(f"SAMPLE ICEBREAKERS (First company)")
    print(f"{'='*70}\n")

    first_company = sorted_by_priority[0]
    title_field = [k for k in first_company.keys() if 'title' in k.lower()][0]
    print(f"Company: {first_company[title_field]}")
    print(f"Category: {first_company['category']}")
    print(f"\nIcebreaker Variants:\n")

    for i in range(1, 8):
        icebreaker_key = f'icebreaker_{i}'
        if icebreaker_key in first_company and first_company[icebreaker_key]:
            print(f"{i}. {first_company[icebreaker_key]}")

    print(f"\n{'='*70}")

    # Recommendations
    print(f"\n💡 OUTREACH STRATEGY RECOMMENDATIONS:")
    print(f"{'='*70}")

    hvac_count = categories.get('HVAC', 0)
    landscape_count = categories.get('Landscaping', 0)

    if hvac_count > 0:
        print(f"\n1. HVAC Companies ({hvac_count} leads):")
        print(f"   - HIGHEST value: $5-15K/year potential per client")
        print(f"   - Pain point: Customer acquisition cost, seasonal demand")
        print(f"   - Hook: AI automation for booking, follow-ups, reviews")
        print(f"   - Best time: NOW (winter season approaching)")
        print(f"   ✅ RECOMMENDED: Start with HVAC first")

    if landscape_count > 0:
        print(f"\n2. Landscaping Companies ({landscape_count} leads):")
        print(f"   - MEDIUM value: $2-8K/year potential per client")
        print(f"   - Pain point: Seasonal cash flow, crew scheduling")
        print(f"   - Hook: Off-season lead generation, automated scheduling")
        print(f"   - Best time: Fall/Winter (preparing for spring)")
        print(f"   ✅ RECOMMENDED: Second batch")

    print(f"\n{'='*70}\n")

def main():
    """Main execution"""

    logger.info("=== CATEGORY ANALYZER & ICEBREAKER GENERATOR STARTED ===")

    # Process companies
    results = process_companies(CONFIG["INPUT_CSV"])

    # Save results
    output_file = save_results(results)

    # Print analysis
    print_analysis(results)

    logger.info(f"✓ Complete! Results saved to: {output_file}")

if __name__ == "__main__":
    main()
