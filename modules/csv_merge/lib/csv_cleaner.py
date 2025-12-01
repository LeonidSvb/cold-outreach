"""
CSV Cleaner - Atomic module for normalizing merge keys
"""
import re
from urllib.parse import urlparse
from typing import Optional


def clean_email(email: str) -> Optional[str]:
    """
    Normalize email address

    Rules:
    - Lowercase
    - Trim whitespace
    - Remove mailto: prefix
    - Validate @ symbol

    Args:
        email: Raw email string

    Returns:
        Cleaned email or None if invalid
    """
    if not email or not isinstance(email, str):
        return None

    # Clean
    email = email.strip().lower()
    email = email.replace('mailto:', '')
    email = email.replace(' ', '')

    # Validate
    if '@' not in email:
        return None

    # Basic regex validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return email

    return None


def clean_website_to_domain(url: str) -> Optional[str]:
    """
    Normalize website URL to clean domain

    Examples:
        https://www.apple.com/abc → apple.com
        http://apple.com → apple.com
        www.apple.com → apple.com
        apple.com/xyz?test=1 → apple.com

    Args:
        url: Raw URL string

    Returns:
        Clean domain or None if invalid
    """
    if not url or not isinstance(url, str):
        return None

    # Clean
    url = url.strip().lower()

    # Add protocol if missing (for urlparse)
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # Remove www.
        domain = domain.replace('www.', '')

        # Remove port
        if ':' in domain:
            domain = domain.split(':')[0]

        # Remove trailing slash
        domain = domain.rstrip('/')

        return domain if domain else None

    except Exception:
        return None


def clean_generic(value: str) -> Optional[str]:
    """
    Generic cleaning: lowercase + trim

    Args:
        value: Raw string

    Returns:
        Cleaned string or None
    """
    if not value or not isinstance(value, str):
        return None

    cleaned = value.strip().lower()
    return cleaned if cleaned else None
