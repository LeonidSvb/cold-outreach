#!/usr/bin/env python3
"""
FIXED Text Utilities - Исправлена проблема с concatenation emails

CHANGES:
1. Improved email regex - prevents concatenation
2. TLD validation - only known TLDs
3. Post-processing cleanup - removes appended text
"""

import re
from typing import List
from bs4 import BeautifulSoup

# Known valid TLDs (top 100 most common)
VALID_TLDS = {
    # Generic
    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
    # Country codes (Europe + common)
    'de', 'uk', 'fr', 'it', 'es', 'nl', 'pl', 'ch', 'at', 'be', 'cz', 'dk',
    'fi', 'gr', 'hu', 'ie', 'no', 'pt', 'ro', 'ru', 'se', 'sk', 'si', 'hr',
    'bg', 'ee', 'lt', 'lv', 'lu', 'mt', 'cy', 'is', 'li', 'mc', 'rs', 'ua',
    'us', 'ca', 'au', 'nz', 'jp', 'cn', 'in', 'br', 'mx', 'ar', 'cl',
    # New TLDs
    'io', 'co', 'ai', 'xyz', 'online', 'site', 'tech', 'store', 'app',
    # Regional
    'eu', 'asia', 'africa',
}


def is_valid_email(email: str) -> bool:
    """
    FIXED: Improved email validation

    Changes:
    - Validates TLD against known list
    - Checks email length
    - More strict format validation
    """
    if not email or '@' not in email or len(email) < 5:
        return False

    # Exclude common false positives
    exclude_patterns = [
        r'@example\.',
        r'@test\.',
        r'@domain\.',
        r'@email\.',
        r'@yoursite\.',
        r'@sentry\.io',
        r'@2x\.png',
        r'@3x\.png',
        r'remove-this',  # spam trap
        r'noreply@',
        r'no-reply@',
    ]

    email_lower = email.lower()
    for pattern in exclude_patterns:
        if re.search(pattern, email_lower):
            return False

    # Basic format validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False

    # Validate TLD
    try:
        tld = email.split('.')[-1].lower()
        if tld not in VALID_TLDS:
            return False
    except:
        return False

    # Email should not be too long
    if len(email) > 254:  # RFC 5321
        return False

    return True


def extract_emails(text: str) -> List[str]:
    """
    FIXED: Extract emails with anti-concatenation protection

    Changes:
    - Improved regex with lookahead/lookbehind
    - TLD validation
    - Post-processing cleanup
    - Numeric prefix removal
    """
    # Step 1: Find potential emails with improved regex
    # Capture everything that looks like email (even broken ones)
    email_pattern = r'(?<![a-zA-Z0-9])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,20})(?=\s|$|[^a-zA-Z0-9])'

    matches = re.findall(email_pattern, text)

    # Step 2: Clean and validate each match
    valid_emails = set()

    for match in matches:
        email = match.strip().lower()

        # STEP 1: Remove numeric prefixes (e.g., "102info@" -> "info@")
        # Pattern: digits at start followed by letters before @
        email = re.sub(r'^[\d\-]+([a-z])', r'\1', email)

        # STEP 2: Find and extract valid TLD from potentially concatenated domain
        # Look for known TLDs in the domain part
        if '@' in email:
            local, domain = email.rsplit('@', 1)

            # Try to find valid TLD in domain
            # Check if domain ends with concatenated text after valid TLD
            tld_found = None
            for tld in sorted(VALID_TLDS, key=len, reverse=True):  # Check longer TLDs first
                # Pattern: .tld followed by extra letters
                pattern = rf'\.{re.escape(tld)}[a-z]+$'
                if re.search(pattern, domain):
                    # Remove extra letters after valid TLD
                    domain = re.sub(pattern, f'.{tld}', domain)
                    tld_found = tld
                    break

            # If no concatenation found, check if domain has valid TLD
            if not tld_found:
                # Check multi-part TLDs like .co.uk
                for tld in VALID_TLDS:
                    if domain.endswith(f'.{tld}'):
                        tld_found = tld
                        break

            email = f'{local}@{domain}'

        # Validate
        if is_valid_email(email):
            valid_emails.add(email)

    return sorted(list(valid_emails))


def extract_emails_from_html(html: str) -> List[str]:
    """
    FIXED: Extract emails from HTML with better parsing

    Changes:
    - Better separator handling to prevent concatenation
    - Mailto links extracted separately
    - Duplicate removal
    """
    all_emails = set()

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Method 1: Extract from mailto: links FIRST (most reliable)
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link.get('href', '').replace('mailto:', '').split('?')[0].strip()
            if is_valid_email(email):
                all_emails.add(email.lower())

        # Method 2: Extract from text (with better separation)
        # Add space after common tags to prevent concatenation
        for tag in soup.find_all(['p', 'div', 'span', 'a', 'li', 'td']):
            tag_text = tag.get_text()
            if '@' in tag_text:
                # Process tag separately to avoid concatenation with siblings
                emails = extract_emails(tag_text)
                all_emails.update(emails)

        # Method 3: Fallback - full text extraction
        full_text = soup.get_text(separator=' ')
        text_emails = extract_emails(full_text)
        all_emails.update(text_emails)

    except Exception as e:
        # Fallback to simple text extraction
        try:
            simple_emails = extract_emails(html)
            all_emails.update(simple_emails)
        except:
            pass

    return sorted(list(all_emails))


# Backward compatibility
clean_html_to_text = None  # Import from original if needed


def test_email_extraction():
    """Test cases for fixed email extraction"""

    test_cases = [
        # Case 1: Concatenated domain
        ("Contact: info@sovjet-ereveld.nlIBAN", ["info@sovjet-ereveld.nl"]),

        # Case 2: Multiple concatenations
        ("info@militex.chBewertungen", ["info@militex.ch"]),

        # Case 3: Phone number prefix
        ("102info@army-surplus.cz", ["info@army-surplus.cz"]),

        # Case 4: Multiple emails in text
        ("Email us: contact@test.com or info@example.org", ["contact@test.com", "info@example.org"]),

        # Case 5: Invalid TLD
        ("fake@test.invalidtld", []),

        # Case 6: Spam trap
        ("hstaebler@remove-this.crestawald.ch", []),

        # Case 7: Normal email
        ("Contact: info@museum.de", ["info@museum.de"]),
    ]

    print("=== TESTING FIXED EMAIL EXTRACTION ===\n")

    for i, (text, expected) in enumerate(test_cases, 1):
        result = extract_emails(text)
        status = "✓" if result == expected else "✗"
        print(f"Test {i}: {status}")
        print(f"  Input: {text}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
        print()


if __name__ == "__main__":
    test_email_extraction()
