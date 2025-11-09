#!/usr/bin/env python3
"""
Text Utilities для обработки HTML и извлечения данных
Переиспользуемые функции для cleaning и extraction

Источник: scraping_website_personalization_enricher.py + scraping_extract_emails_from_websites.py
"""

import re
from typing import List, Set
from bs4 import BeautifulSoup


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
    Валидация email адреса
    Фильтрует частые ложные срабатывания (example.com, test.com, etc)

    Args:
        email: Email адрес для проверки

    Returns:
        True если email валидный
    """
    if not email or '@' not in email:
        return False

    # Исключаем частые ложные срабатывания
    exclude_patterns = [
        r'@example\.',
        r'@test\.',
        r'@domain\.',
        r'@email\.',
        r'@yoursite\.',
        r'@sentry\.io',
        r'@2x\.png',
        r'@3x\.png',
    ]

    for pattern in exclude_patterns:
        if re.search(pattern, email, re.IGNORECASE):
            return False

    # Валидный email паттерн
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def extract_emails(text: str) -> List[str]:
    """
    Извлечение всех email адресов из текста

    Args:
        text: Текст для поиска (может быть HTML или чистый текст)

    Returns:
        Список уникальных валидных email адресов
    """
    # Regex паттерн для email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Находим все совпадения
    emails = set(re.findall(email_pattern, text))

    # Фильтруем невалидные
    valid_emails = {email.lower() for email in emails if is_valid_email(email)}

    return sorted(list(valid_emails))


def extract_emails_from_html(html: str) -> List[str]:
    """
    Извлечение emails из HTML (включая mailto: ссылки)

    Args:
        html: HTML код страницы

    Returns:
        Список уникальных email адресов
    """
    all_emails = set()

    try:
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Извлечь из текста
        text = soup.get_text()
        text_emails = extract_emails(text)
        all_emails.update(text_emails)

        # 2. Извлечь из mailto: ссылок
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link.get('href', '').replace('mailto:', '').split('?')[0].strip()
            if is_valid_email(email):
                all_emails.add(email.lower())

    except Exception:
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
