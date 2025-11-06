#!/usr/bin/env python3
"""
=== Apollo ICP Analyzer ===
Version: 2.0.0 | Created: 2025-11-03

PURPOSE:
Analyze Apollo CSV data and add ICP scoring for call center prospects.
"""

import sys
import os
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv",
    "OUTPUT_DIR": r"C:\Users\79818\Desktop\Outreach - new\modules\apollo\results",
    "BATCH_SIZE": 200,
    "ENCODING": "utf-8"
}

LEGAL_SUFFIXES = [
    r'\s+LLC\s*$', r'\s+Inc\.\s*$', r'\s+Inc\s*$',
    r'\s+Incorporated\s*$', r'\s+Ltd\.\s*$', r'\s+Ltd\s*$',
    r'\s+Limited\s*$', r'\s+Corp\.\s*$', r'\s+Corp\s*$',
    r'\s+Corporation\s*$', r'\s+Co\.\s*$', r'\s+Co\s*$',
    r'\s+Company\s*$', r'\s+PLC\s*$', r'\s+Pty\s*$',
    r'\s+GmbH\s*$', r'\s+AG\s*$', r'\s+SRL\s*$',
    r'\s+SARL\s*$', r'\s+Inc.*$'
]

CALL_CENTER_KEYWORDS = [
    'call center', 'contact center', 'call centre', 'contact centre',
    'telemarketing', 'outbound call', 'inbound call', 'telefundraising',
    'telesales', 'phone sales', 'dialer', 'bpo', 'business process outsourcing',
    'customer contact', 'customer service', 'phone support', 'call handling',
    'call operations', 'call management', 'call center operations', 'outsourcing'
]

LOCATION_ABBREVIATIONS = {
    'New York': 'NYC', 'Los Angeles': 'LA', 'San Francisco': 'SF',
    'Washington': 'DC', 'Boston': 'Boston', 'Miami': 'Miami',
    'Chicago': 'Chicago', 'Atlanta': 'Atlanta', 'Dallas': 'Dallas',
    'Houston': 'Houston', 'Phoenix': 'Phoenix', 'Philadelphia': 'Philadelphia',
    'Seattle': 'Seattle', 'Austin': 'Austin', 'Denver': 'Denver',
    'United States': 'US', 'United Kingdom': 'UK', 'Australia': 'Aus',
    'New Zealand': 'NZ', 'Canada': 'Canada', 'India': 'India',
    'Philippines': 'Philippines', 'Mexico': 'Mexico'
}

US_STATE_ABBREVIATIONS = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
    'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK',
    'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',
    'Wisconsin': 'WI', 'Wyoming': 'WY'
}

def normalize_company_name(name: str) -> str:
    if pd.isna(name) or not name:
        return ""

    name = str(name).strip()

    for suffix in LEGAL_SUFFIXES:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)

    name = name.strip()
    return name


def normalize_location(city: str, state: str, country: str) -> str:
    if pd.isna(country):
        country = ""
    if pd.isna(state):
        state = ""
    if pd.isna(city):
        city = ""

    country = str(country).strip()
    state = str(state).strip()
    city = str(city).strip()

    if not city and not state and not country:
        return ""

    if city in LOCATION_ABBREVIATIONS:
        return LOCATION_ABBREVIATIONS[city]

    if city:
        city_clean = city.title()
        if len(city_clean) <= 8:
            return city_clean
        if city_clean in LOCATION_ABBREVIATIONS:
            return LOCATION_ABBREVIATIONS[city_clean]
        return city_clean

    if state:
        state_clean = state.strip()
        if len(state_clean) == 2:
            return state_clean
        if state_clean in US_STATE_ABBREVIATIONS:
            return US_STATE_ABBREVIATIONS[state_clean]
        if len(state_clean) <= 8:
            return state_clean
        return state_clean

    if country:
        country_clean = country.strip()
        if country_clean in LOCATION_ABBREVIATIONS:
            return LOCATION_ABBREVIATIONS[country_clean]
        return country_clean

    return ""


def has_call_center_keywords(
    company_name: str, industry: str, headline: str, keywords: str
) -> bool:
    text = f"{company_name} {industry} {headline} {keywords}".lower()

    for keyword in CALL_CENTER_KEYWORDS:
        if keyword in text:
            return True

    return False


def score_icp(
    company_name: str,
    industry: str,
    headline: str,
    keywords: str,
    title: str,
    estimated_employees: int,
) -> tuple:
    if pd.isna(company_name):
        company_name = ""
    if pd.isna(industry):
        industry = ""
    if pd.isna(headline):
        headline = ""
    if pd.isna(keywords):
        keywords = ""
    if pd.isna(title):
        title = ""

    company_name = str(company_name).lower()
    industry = str(industry).lower()
    headline = str(headline).lower()
    keywords = str(keywords).lower()
    title = str(title).lower()

    try:
        est_emp = int(estimated_employees) if estimated_employees else 0
    except (ValueError, TypeError):
        est_emp = 0

    if "outsourc" in industry or "offshoring" in industry or "bpo" in industry:
        reasoning = "Outsourcing/BPO industry indicates strong call center operations. Likely handles high-volume customer interactions."
        return 2, reasoning

    if has_call_center_keywords(company_name, industry, headline, keywords):
        reasoning = "Clear call center indicators found in company data. Keywords match call center operations profile."
        return 2, reasoning

    if "contact" in industry or "customer service" in industry or "telecom" in industry:
        if est_emp >= 10:
            reasoning = f"Customer contact/service industry with {est_emp}+ employees. Likely phone-based operations but not explicitly confirmed."
            return 1, reasoning

    if "call" in title or "contact" in title or "customer" in title:
        if est_emp >= 10:
            reasoning = f"Title suggests customer contact focus, but insufficient confirmation of phone-based operations."
            return 1, reasoning

    if est_emp >= 50 and ("service" in industry or "support" in industry or "customer" in industry):
        reasoning = f"Large company ({est_emp}+ employees) in service/support industry. Possible call center operations but unclear."
        return 1, reasoning

    reasoning = "No clear call center indicators found in company profile, industry, or keywords."
    return 0, reasoning


def process_batch(df_batch: pd.DataFrame, batch_num: int) -> pd.DataFrame:
    print(f"Processing batch {batch_num}: {len(df_batch)} rows")

    df_batch = df_batch.copy()
    df_batch['normalized_company_name'] = df_batch['company_name'].apply(
        normalize_company_name
    )

    df_batch['normalized_location'] = df_batch.apply(
        lambda row: normalize_location(
            row.get('city', ''),
            row.get('state', ''),
            row.get('country', '')
        ),
        axis=1
    )

    results = []
    for idx, row in df_batch.iterrows():
        score, reasoning = score_icp(
            company_name=row.get('company_name', ''),
            industry=row.get('industry', ''),
            headline=row.get('headline', ''),
            keywords=row.get('keywords', ''),
            title=row.get('title', ''),
            estimated_employees=row.get('estimated_num_employees', 0)
        )
        results.append({'icp_score': score, 'reasoning': reasoning})

    results_df = pd.DataFrame(results)
    df_batch['icp_score'] = results_df['icp_score'].values
    df_batch['reasoning'] = results_df['reasoning'].values

    print(f"Batch {batch_num} complete")
    return df_batch


def main():
    print("Starting Apollo ICP Analysis")
    print(f"Input file: {CONFIG['INPUT_FILE']}")

    if not os.path.exists(CONFIG['INPUT_FILE']):
        print(f"ERROR: File not found: {CONFIG['INPUT_FILE']}")
        sys.exit(1)

    try:
        df = pd.read_csv(CONFIG['INPUT_FILE'], encoding=CONFIG['ENCODING'])
        print(f"Loaded CSV: {len(df)} total rows")
    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        sys.exit(1)

    os.makedirs(CONFIG['OUTPUT_DIR'], exist_ok=True)

    processed_batches = []
    total_rows = len(df)
    batch_size = CONFIG['BATCH_SIZE']
    num_batches = (total_rows + batch_size - 1) // batch_size

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, total_rows)
        batch = df.iloc[start_idx:end_idx].copy()

        batch = process_batch(batch, i + 1)
        processed_batches.append(batch)

    df_final = pd.concat(processed_batches, ignore_index=True)
    print(f"All {num_batches} batches processed: {len(df_final)} total rows")

    score_counts = df_final['icp_score'].value_counts().to_dict()
    score_2 = score_counts.get(2, 0)
    score_1 = score_counts.get(1, 0)
    score_0 = score_counts.get(0, 0)

    print(f"ICP Score Distribution: Score 2: {score_2}, Score 1: {score_1}, Score 0: {score_0}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(CONFIG['OUTPUT_DIR'], f"apollo_icp_analyzed_{timestamp}.csv")

    try:
        df_final.to_csv(output_file, index=False, encoding=CONFIG['ENCODING'])
        print(f"Results saved to: {output_file}")
    except Exception as e:
        print(f"ERROR: Failed to save CSV: {e}")
        sys.exit(1)

    print("Apollo ICP Analysis completed successfully")
    return output_file, score_counts


if __name__ == "__main__":
    try:
        output_file, stats = main()
        print(f"\n{'='*60}")
        print("АНАЛИЗ ЗАВЕРШЁН")
        print(f"{'='*60}")
        print(f"Результаты сохранены: {output_file}")
        print(f"\nРаспределение ICP scores:")
        print(f"  Score 2 (Perfect Fit): {stats.get(2, 0)} компаний")
        print(f"  Score 1 (Maybe): {stats.get(1, 0)} компаний")
        print(f"  Score 0 (Not a Fit): {stats.get(0, 0)} компаний")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)
