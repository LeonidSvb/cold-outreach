#!/usr/bin/env python3
"""
=== SOVIET BOOTS SMART CATEGORIZER ===
Version: 1.0.0 | Created: 2025-01-26

PURPOSE:
Smart rule-based categorization and email generation for Soviet Boots leads.
Uses intelligent pattern matching instead of expensive AI API calls.

FEATURES:
- Multi-level categorization logic
- Keyword-based category detection
- Automatic detail extraction from source_keyword
- Email sequence generation per category
- Short name and location formatting

CATEGORIES:
1. museum - Museums, memorials, historic sites
2. military_shop - Shops selling military items
3. historical_society - Historical societies and preservation orgs
4. reenactment_group - Active reenactment groups
5. community_organization - Libraries, parks, cultural centers
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.shared.logging.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CATEGORIZATION RULES
# ============================================================================

CATEGORY_RULES = {
    "museum": {
        "name_keywords": ["museum", "memorial", "monument", "historic site", "exhibition", "gallery"],
        "exclude_keywords": ["shop", "store"],
        "priority": 1
    },
    "military_shop": {
        "name_keywords": ["shop", "store", "surplus", "collectibles", "depot", "supply"],
        "content_keywords": ["buy", "shop", "store", "merchandise", "gift shop"],
        "priority": 2
    },
    "historical_society": {
        "name_keywords": ["historical society", "history center", "preservation", "heritage", "historic house"],
        "exclude_keywords": ["museum"],
        "priority": 3
    },
    "reenactment_group": {
        "source_keywords": ["reenactment", "living history"],
        "exclude_name_keywords": ["museum", "historical society", "library", "memorial", "monument", "archive"],
        "priority": 4
    },
    "community_organization": {
        "name_keywords": ["library", "park", "chamber of commerce", "cultural center", "foundation", "association"],
        "priority": 5
    }
}

# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

EMAIL_TEMPLATES = {
    "museum": {
        "subject": "authentic soviet boots for exhibits",
        "email_1": """hey{greeting_name}

checked out {short_company_name} - saw you have {specific_detail}.

a friend of mine sources soviet boots from veterans - authentic pieces museums want for collections.

thought it might fit?

best,
Leo""",
        "email_2": """Hi{greeting_name}

Still worth making the connection or bad timing?

Best,
Leo""",
        "email_3": """Haven't heard back, so I'll assume it's not a fit right now

Will keep {short_company_name} in mind if something similar comes up"""
    },

    "military_shop": {
        "subject": "soviet boots - authentic source",
        "email_1": """hey{greeting_name}

saw {short_company_name}'s {specific_detail}.

a friend of mine sources soviet boots from veterans - authentic pieces collectors want.

thought it might be worth discussing if you're expanding inventory?

best,
Leo""",
        "email_2": """Hi{greeting_name}

Still worth making the connection or bad timing?

Best,
Leo""",
        "email_3": """Haven't heard back, so I'll assume it's not a fit right now

Will keep {short_company_name} in mind if something similar comes up"""
    },

    "historical_society": {
        "subject": "soviet boots from veterans",
        "email_1": """hey{greeting_name}

came across {short_company_name} - appreciate the work preserving {specific_detail}.

a friend of mine sources soviet boots from veterans - thought they might fit your collection.

worth connecting?

best,
Leo""",
        "email_2": """Hi{greeting_name}

Still worth making the connection or bad timing?

Best,
Leo""",
        "email_3": """Haven't heard back, so I'll assume it's not a fit right now

Will keep {short_company_name} in mind if something similar comes up"""
    },

    "reenactment_group": {
        "subject": "soviet boots for reenactment",
        "email_1": """hey{greeting_name}

saw you're involved with {specific_detail}.

a friend of mine sources soviet boots from veterans - authentic gear for kits.

thought it might fit?

best,
Leo""",
        "email_2": """Hi{greeting_name}

Still worth making the connection or bad timing?

Best,
Leo""",
        "email_3": """Haven't heard back, so I'll assume it's not a fit right now

Will keep {short_company_name} in mind if something similar comes up"""
    },

    "community_organization": {
        "subject": "soviet military history connection",
        "email_1": """hey{greeting_name}

saw {short_company_name} - interesting {specific_detail}.

a friend of mine sources soviet boots from veterans - thought it might interest your programs.

worth connecting?

best,
Leo""",
        "email_2": """Hi{greeting_name}

Still worth making the connection or bad timing?

Best,
Leo""",
        "email_3": """Haven't heard back, so I'll assume it's not a fit right now

Will keep {short_company_name} in mind if something similar comes up"""
    }
}

# ============================================================================
# CATEGORIZATION LOGIC
# ============================================================================

def categorize_organization(row):
    """
    Categorize organization based on name, content, and source keywords

    Returns: (category, confidence, specific_detail)
    """
    name = str(row.get('name', '')).lower()
    content = str(row.get('homepage_content', ''))[:2000].lower()  # First 2000 chars
    source_kw = str(row.get('source_keyword', '')).lower()

    # Check each category by priority
    categories_sorted = sorted(CATEGORY_RULES.items(), key=lambda x: x[1]['priority'])

    for category, rules in categories_sorted:
        # Check exclusions first
        if 'exclude_keywords' in rules:
            if any(kw in name for kw in rules['exclude_keywords']):
                continue

        if 'exclude_name_keywords' in rules:
            if any(kw in name for kw in rules['exclude_name_keywords']):
                continue

        # Check name keywords
        if 'name_keywords' in rules:
            if any(kw in name for kw in rules['name_keywords']):
                detail = extract_specific_detail(category, name, source_kw, content)
                return category, "high", detail

        # Check source keywords
        if 'source_keywords' in rules:
            if any(kw in source_kw for kw in rules['source_keywords']):
                detail = extract_specific_detail(category, name, source_kw, content)
                return category, "medium", detail

        # Check content keywords
        if 'content_keywords' in rules:
            if any(kw in content for kw in rules['content_keywords']):
                detail = extract_specific_detail(category, name, source_kw, content)
                return category, "medium", detail

    # Default: community_organization
    detail = extract_specific_detail("community_organization", name, source_kw, content)
    return "community_organization", "low", detail


def extract_specific_detail(category, name, source_kw, content):
    """Extract specific detail for personalization based on category"""

    if category == "museum":
        # Look for exhibit types in source_keyword or name
        if "wwii" in source_kw or "world war 2" in source_kw:
            return "wwii exhibits"
        elif "cold war" in source_kw or "eastern front" in source_kw:
            return "cold war pieces"
        elif "soviet" in source_kw or "russian" in source_kw:
            return "soviet military history"
        elif "red army" in source_kw:
            return "red army artifacts"
        else:
            return "military exhibits"

    elif category == "military_shop":
        if "surplus" in name:
            return "military surplus"
        elif "collectible" in name:
            return "military collectibles"
        else:
            return "military memorabilia"

    elif category == "historical_society":
        # Extract time period or focus
        if "revolutionary" in content or "revolution" in name:
            return "revolutionary war history"
        elif "civil war" in content or "civil war" in name:
            return "civil war history"
        elif "wwii" in source_kw or "world war" in source_kw:
            return "wwii local history"
        else:
            return "local history"

    elif category == "reenactment_group":
        # Use source_keyword as the detail, make it lowercase and casual
        source_clean = source_kw.replace("_", " ").lower()
        return source_clean if source_clean else "historical reenactment"

    elif category == "community_organization":
        if "library" in name:
            return "library programs"
        elif "park" in name:
            return "park programs"
        elif "chamber" in name:
            return "local business"
        else:
            return "community programs"

    return "history programs"


def create_short_company_name(name):
    """Create shortened version of company name"""
    # Remove common suffixes
    remove_terms = [
        "Museum & History Center",
        "Museum and History Center",
        "Historical Society",
        "History Center",
        "Memorial",
        "Monument",
        ", Inc.",
        " Inc.",
        "- Museum",
        " Museum",
        "The "
    ]

    short = name
    for term in remove_terms:
        short = short.replace(term, "")

    # Clean up
    short = short.strip().strip("-").strip(",").strip()

    # Limit length
    if len(short) > 40:
        short = short[:40].rsplit(' ', 1)[0]

    return short if short else name[:40]


def extract_short_location(address):
    """Extract City, State from full address"""
    if pd.isna(address) or not address:
        return ""

    # Address format: "Street, City, State ZIP, Country"
    parts = address.split(",")
    if len(parts) >= 3:
        city = parts[-3].strip()
        state_zip = parts[-2].strip()
        state = state_zip.split()[0] if state_zip else ""
        return f"{city}, {state}"

    return address[:30]


def extract_first_name_from_email(email):
    """Try to extract first name from email address"""
    if pd.isna(email) or not email:
        return None

    # Get part before @
    local_part = email.split('@')[0].lower()

    # Generic/role-based emails - skip these
    generic_keywords = [
        'info', 'contact', 'admin', 'office', 'hello', 'mail', 'support',
        'manager', 'director', 'curator', 'reception', 'sales', 'service',
        'help', 'inquiries', 'inquiry', 'team', 'general', 'membership',
        'volunteer', 'media', 'press', 'webmaster', 'postmaster'
    ]

    # Check if it's a generic email
    for keyword in generic_keywords:
        if keyword in local_part:
            return None

    # Try dot separator (john.smith)
    if '.' in local_part:
        parts = local_part.split('.')
        first = parts[0]
        # Clean up numbers
        first = re.sub(r'\d+', '', first)
        # Check if it's a valid name (2-12 chars, only letters)
        if first.isalpha() and 2 <= len(first) <= 12:
            return first.capitalize()

    # Try underscore separator (john_smith)
    if '_' in local_part:
        parts = local_part.split('_')
        first = parts[0]
        first = re.sub(r'\d+', '', first)
        if first.isalpha() and 2 <= len(first) <= 12:
            return first.capitalize()

    # Try to extract first name from single word (johnsmith or john)
    if local_part.isalpha() and 3 <= len(local_part) <= 10:
        return local_part.capitalize()

    return None


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_csv(input_file, output_file):
    """Process entire CSV file"""

    logger.info(f"Loading CSV: {input_file}")
    df = pd.read_csv(input_file)

    logger.info(f"Processing {len(df)} rows...")

    # Process each row
    results = []
    for idx, row in df.iterrows():
        category, confidence, detail = categorize_organization(row)

        short_name = create_short_company_name(row['name'])
        short_loc = extract_short_location(row.get('address', ''))
        first_name = extract_first_name_from_email(row.get('email', ''))

        # Get email templates for this category
        templates = EMAIL_TEMPLATES.get(category, EMAIL_TEMPLATES['community_organization'])

        # Create greeting name: " John," or ","
        greeting_name = f" {first_name}," if first_name else ","

        # Format email_1 with personalization
        email_1 = templates['email_1'].format(
            greeting_name=greeting_name,
            org_name=short_name,
            specific_detail=detail,
            short_company_name=short_name,
            location=short_loc
        )

        email_2 = templates['email_2'].format(
            greeting_name=greeting_name
        )

        email_3 = templates['email_3'].format(
            short_company_name=short_name
        )

        results.append({
            'category': category,
            'category_confidence': confidence,
            'specific_detail': detail,
            'short_company_name': short_name,
            'short_location': short_loc,
            'first_name': first_name,
            'subject_line': templates['subject'],
            'email_1_body': email_1,
            'email_2_body': email_2,
            'email_3_body': email_3
        })

        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} rows...")

    # Add new columns to dataframe
    for key in results[0].keys():
        df[key] = [r[key] for r in results]

    # Save result
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"Saved results to: {output_file}")

    # Show statistics
    logger.info("\nCategory breakdown:")
    for category, count in df['category'].value_counts().items():
        logger.info(f"  {category}: {count}")

    logger.info(f"\nFirst names extracted: {df['first_name'].notna().sum()}")

    return df


def main():
    """Main execution"""
    input_file = r"C:\Users\79818\Downloads\Soviet Boots - 950 US  (2).csv"

    output_dir = Path("modules/csv_tools/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"soviet_boots_complete_{timestamp}.csv"

    logger.info("Starting Soviet Boots categorization and email generation")

    df = process_csv(input_file, output_file)

    logger.info(f"\nProcessing complete!")
    logger.info(f"Total rows: {len(df)}")
    logger.info(f"Output file: {output_file}")

    return output_file


if __name__ == "__main__":
    main()
