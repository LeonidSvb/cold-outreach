#!/usr/bin/env python3
"""
Text Utilities для обработки HTML и извлечения данных
Переиспользуемые функции для cleaning и extraction

Источник: scraping_website_personalization_enricher.py + scraping_extract_emails_from_websites.py
"""

import re
from typing import List, Set
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


def clean_html_to_text(html: str, max_length: int = None) -> str:
    """
    Очистка HTML → чистый текст без тегов и скриптов

    Args:
        html: Сырой HTML
        max_length: Максимальная длина текста (для экономии токенов AI)

    Returns:
        Чистый текст без тегов
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')

        # Удаляем ненужные элементы (скрипты, стили, навигация)
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()

        # Извлекаем текст
        text = soup.get_text(separator=' ', strip=True)

        # Очистка пробелов
        text = ' '.join(text.split())

        # Обрезка по длине (если нужно)
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text

    except Exception as e:
        return ""


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


def extract_phones(text: str) -> List[str]:
    """
    Извлечение телефонных номеров (US формат)

    Args:
        text: Текст для поиска

    Returns:
        Список уникальных номеров телефонов
    """
    patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 или 123-456-7890
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',           # 123-456-7890
        r'\d{10}'                                  # 1234567890
    ]

    phones = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        phones.update(matches)

    return sorted(list(phones))


def detect_site_type(html: str) -> dict:
    """
    Определение типа сайта: статический или динамический (React/Vue/etc)

    Args:
        html: HTML код страницы

    Returns:
        {
            'type': 'static' | 'dynamic',
            'confidence': 0.0-1.0,
            'indicators': ['список индикаторов']
        }
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().strip()

        indicators = []

        # Индикатор 1: Мало текста
        if len(text) < 200:
            indicators.append('low_text_content')

        # Индикатор 2: Есть React/Vue root элементы
        if soup.find('div', id='root') or soup.find('div', id='app'):
            indicators.append('spa_root_element')

        # Индикатор 3: Много script тегов
        scripts = soup.find_all('script')
        if len(scripts) > 10:
            indicators.append('many_scripts')

        # Индикатор 4: Упоминание JS фреймворков в коде
        html_lower = html.lower()
        if 'react' in html_lower or 'vue' in html_lower or 'angular' in html_lower:
            indicators.append('js_framework_detected')

        # Определяем тип
        if len(indicators) >= 2:
            return {
                'type': 'dynamic',
                'confidence': min(len(indicators) * 0.3, 1.0),
                'indicators': indicators
            }
        else:
            return {
                'type': 'static',
                'confidence': 1.0 - (len(indicators) * 0.2),
                'indicators': indicators if indicators else ['sufficient_content']
            }

    except Exception:
        return {
            'type': 'unknown',
            'confidence': 0.0,
            'indicators': ['parsing_error']
        }
