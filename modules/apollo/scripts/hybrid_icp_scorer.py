#!/usr/bin/env python3
"""
=== HYBRID ICP SCORER ===
Combines code-based speed with LLM intelligence

STRATEGY:
- 90% of rows: Fast code-based scoring (free, instant)
- 10% of rows: LLM analysis (uncertain cases only)

RESULT:
- Best of both worlds: speed + accuracy
- Minimal cost (~$0.02 for 1,772 rows)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import json
from openai import OpenAI

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "USE_LLM_FOR_UNCERTAIN": True,  # Set to False for pure code-based
    "LLM_MODEL": "gpt-4o-mini",  # Cheap and smart
}

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def code_based_score(row):
    """Fast keyword-based scoring"""
    company_name = str(row.get('company_name', '')).lower()
    industry = str(row.get('industry', '')).lower()
    keywords = str(row.get('keywords', '')).lower()
    title = str(row.get('title', '')).lower()

    combined = f"{company_name} {industry} {keywords} {title}"

    # Perfect indicators
    perfect = [
        'call center', 'contact center', 'bpo', 'telemarketing',
        'outbound call', 'inbound call', 'telefundraising', 'telesales'
    ]

    if industry == 'outsourcing/offshoring':
        return {"score": 2, "confidence": "high", "method": "code"}

    for indicator in perfect:
        if indicator in combined:
            return {"score": 2, "confidence": "high", "method": "code"}

    # Maybe indicators
    maybe = ['customer support', 'customer service', 'lead generation', 'cold calling']
    for indicator in maybe:
        if indicator in combined:
            return {"score": 1, "confidence": "medium", "method": "code"}

    return {"score": 0, "confidence": "high", "method": "code"}


def is_uncertain(row, code_result):
    """Determine if we need LLM for this row"""
    score = code_result['score']
    confidence = code_result['confidence']

    # Always use LLM for score = 1 (ambiguous)
    if score == 1:
        return True

    # Use LLM if keywords are empty but industry is promising
    keywords = str(row.get('keywords', ''))
    industry = str(row.get('industry', '')).lower()

    if not keywords or keywords == '[]':
        if industry in ['information technology', 'telecommunications', 'marketing']:
            return True

    # Use LLM for large companies (might be enterprise with different structure)
    employees = row.get('estimated_num_employees', 0)
    if employees > 500:
        return True

    return False


def llm_based_score(row):
    """Use LLM for nuanced analysis"""
    prompt = f"""You are an expert at identifying call centers for an AI call analytics service.

ICP (Ideal Customer Profile):
- Companies with high-volume phone calling operations
- Call centers, contact centers, BPO, telemarketing, customer support with phone calls
- NOT: companies that just have a support email or chat

Company Data:
- Name: {row.get('company_name', 'N/A')}
- Industry: {row.get('industry', 'N/A')}
- Keywords: {row.get('keywords', 'N/A')}
- Job Title: {row.get('title', 'N/A')}
- Headline: {row.get('headline', 'N/A')}
- Employees: {row.get('estimated_num_employees', 'N/A')}

Tasks:
1. Analyze if this company does high-volume phone calling
2. Score ICP match:
   - 2 = Perfect fit (clear call center / telemarketing)
   - 1 = Maybe (some phone support, unclear volume)
   - 0 = Not a fit (no phone calling operations)
3. Provide brief reasoning

Return ONLY valid JSON (no markdown):
{{
    "icp_score": 2,
    "reasoning": "Brief explanation"
}}"""

    try:
        response = client.chat.completions.create(
            model=CONFIG["LLM_MODEL"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0,  # Deterministic
            max_tokens=150
        )

        content = response.choices[0].message.content.strip()

        # Remove markdown if present
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]

        result = json.loads(content)
        return {
            "score": result["icp_score"],
            "confidence": "high",
            "method": "llm",
            "reasoning": result.get("reasoning", "")
        }

    except Exception as e:
        logger.error("LLM scoring failed", error=str(e), company=row.get('company_name'))
        # Fallback to code result
        return code_based_score(row)


def hybrid_score(row):
    """Hybrid approach: code first, LLM for uncertain cases"""

    # Step 1: Quick code-based check
    code_result = code_based_score(row)

    # Step 2: If uncertain and LLM enabled → use LLM
    if CONFIG["USE_LLM_FOR_UNCERTAIN"] and is_uncertain(row, code_result):
        llm_result = llm_based_score(row)
        return llm_result

    return code_result


def main():
    logger.info("Starting hybrid ICP scoring")

    # Read CSV
    df = pd.read_csv(CONFIG["INPUT_FILE"])
    logger.info("CSV loaded", rows=len(df))

    # Score each row
    results = []
    code_count = 0
    llm_count = 0

    logger.info("Processing rows...")
    for idx, row in df.iterrows():
        result = hybrid_score(row)
        results.append(result)

        if result['method'] == 'code':
            code_count += 1
        else:
            llm_count += 1

        if (idx + 1) % 100 == 0:
            logger.info("Progress", processed=idx+1, total=len(df))

    # Add results to dataframe
    df['icp_score'] = [r['score'] for r in results]
    df['scoring_method'] = [r['method'] for r in results]
    df['reasoning'] = [r.get('reasoning', '') for r in results]

    # Save
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"hybrid_scored_{timestamp}.csv"
    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)

    # Statistics
    logger.info("Processing complete")
    logger.info("Method distribution", code_based=code_count, llm_based=llm_count)
    logger.info("Cost estimate",
                llm_calls=llm_count,
                estimated_cost=f"${(llm_count * 300 * 0.15 / 1_000_000):.4f}")

    score_dist = df['icp_score'].value_counts().to_dict()
    logger.info("Score distribution",
                perfect=score_dist.get(2, 0),
                maybe=score_dist.get(1, 0),
                no_match=score_dist.get(0, 0))

    logger.info("Output saved", file=str(output_file))

    # Show LLM reasoning examples
    if llm_count > 0:
        print("\n=== LLM REASONING EXAMPLES ===")
        llm_rows = df[df['scoring_method'] == 'llm'].head(5)
        for idx, row in llm_rows.iterrows():
            print(f"\nCompany: {row['company_name']}")
            print(f"Score: {row['icp_score']}")
            print(f"Reasoning: {row['reasoning']}")


if __name__ == "__main__":
    main()
