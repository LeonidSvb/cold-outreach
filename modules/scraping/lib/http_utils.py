#!/usr/bin/env python3
"""
HTTP Utilities для web scraping
Переиспользуемый HTTP client с retry логикой

Источник кода: scraping_parallel_website_email_extractor.py (проверенный в боевых условиях)
"""

import time
import random
import requests
from typing import Dict, Optional
from urllib.parse import urljoin


class HTTPClient:
    """
    HTTP клиент для scraping с автоматическими retry и rate limiting

    Использование:
        client = HTTPClient(timeout=15, retries=3)
        result = client.fetch('https://example.com')

        if result['status'] == 'success':
            html = result['content']
    """

    def __init__(self, timeout: int = 15, retries: int = 3, delay_min: float = 0.5, delay_max: float = 1.5):
        """
        Args:
            timeout: Таймаут для HTTP запроса (секунды)
            retries: Количество повторных попыток при ошибке
            delay_min: Минимальная задержка между запросами (секунды)
            delay_max: Максимальная задержка между запросами (секунды)
        """
        self.timeout = timeout
        self.retries = retries
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    def fetch(self, url: str, check_content_length: bool = True) -> Dict:
        """
        Fetch URL с автоматическим retry и валидацией

        Args:
            url: URL для загрузки
            check_content_length: Проверять ли что контент не пустой (для detection static/dynamic)

        Returns:
            {
                'status': 'success' | 'timeout' | 'connection_error' | 'http_error' | 'dynamic',
                'content': HTML content (если success),
                'url': Final URL после редиректов,
                'error': Описание ошибки (если failed)
            }
        """
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Rate limiting - случайная задержка между запросами
        time.sleep(random.uniform(self.delay_min, self.delay_max))

        for attempt in range(self.retries):
            try:
                response = requests.get(
                    url,
                    headers={'User-Agent': self.user_agent},
                    timeout=self.timeout,
                    allow_redirects=True
                )

                # Проверка статус кода
                if response.status_code != 200:
                    return {
                        'status': f'http_error_{response.status_code}',
                        'error': f'HTTP {response.status_code}',
                        'url': url
                    }

                # Проверка что это HTML
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' not in content_type:
                    return {
                        'status': 'not_html',
                        'error': f'Content-Type: {content_type}',
                        'url': url
                    }

                # Проверка на динамический сайт (если нужно)
                if check_content_length:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text_content = soup.get_text().strip()

                    # Если контента мало - вероятно динамический сайт (React/Vue/etc)
                    if len(text_content) < 200:
                        return {
                            'status': 'dynamic',
                            'error': 'Low content (likely JS-rendered)',
                            'url': response.url
                        }

                # Успех!
                return {
                    'status': 'success',
                    'content': response.text,
                    'url': response.url
                }

            except requests.Timeout:
                if attempt < self.retries - 1:
                    # Retry с exponential backoff
                    time.sleep(2 ** attempt)
                    continue
                return {
                    'status': 'timeout',
                    'error': f'Timeout after {self.timeout}s',
                    'url': url
                }

            except requests.ConnectionError:
                if attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {
                    'status': 'connection_error',
                    'error': 'Connection failed',
                    'url': url
                }

            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e)[:100],
                    'url': url
                }

        return {
            'status': 'max_retries',
            'error': f'Failed after {self.retries} attempts',
            'url': url
        }

    def fetch_multiple_pages(self, base_url: str, paths: list) -> Dict:
        """
        Fetch несколько страниц на одном домене (для smart scraping)

        Args:
            base_url: Базовый URL (например, https://example.com)
            paths: Список путей для проверки (например, ['/about', '/contact'])

        Returns:
            {
                'pages': [
                    {'url': '...', 'content': '...', 'status': 'success'},
                    {'url': '...', 'status': 'timeout', 'error': '...'}
                ]
            }
        """
        results = []

        for path in paths:
            full_url = urljoin(base_url, path)
            result = self.fetch(full_url, check_content_length=False)
            results.append(result)

        return {'pages': results}


# Предопределённые списки страниц для smart scraping
IMPORTANT_PAGES = {
    'contact': ['/contact', '/contact-us', '/contactus', '/get-in-touch'],
    'about': ['/about', '/about-us', '/our-story', '/who-we-are'],
    'team': ['/team', '/our-team', '/leadership', '/meet-the-team'],
    'services': ['/services', '/what-we-do', '/our-services'],
    'careers': ['/careers', '/jobs', '/join-us', '/work-with-us']
}


def get_smart_pages(categories: list = None) -> list:
    """
    Получить список важных страниц для smart scraping

    Args:
        categories: Список категорий ['contact', 'about', 'team', ...]
                   Если None - вернёт все

    Returns:
        Список путей для проверки
    """
    if categories is None:
        categories = IMPORTANT_PAGES.keys()

    pages = []
    for category in categories:
        if category in IMPORTANT_PAGES:
            pages.extend(IMPORTANT_PAGES[category])

    return pages
