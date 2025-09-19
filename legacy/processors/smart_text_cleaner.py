#!/usr/bin/env python3
"""
УМНАЯ ОЧИСТКА ТЕКСТА
Сохраняем максимум полезного контента, убираем только мусор
"""

import json
import re

def smart_clean_text(raw_html):
    """Умная очистка HTML - убираем мусор, сохраняем контент"""
    
    if not raw_html:
        return ""
    
    # 1. Убираем скрипты и стили полностью
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<head[^>]*>.*?</head>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Убираем служебные теги
    text = re.sub(r'<meta[^>]*/?>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<link[^>]*/?>', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<noscript[^>]*>.*?</noscript>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 3. Заменяем блочные теги на пробелы
    block_tags = ['div', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'section', 'article', 'nav', 'header', 'footer', 'aside']
    for tag in block_tags:
        text = re.sub(f'</?{tag}[^>]*>', ' ', text, flags=re.IGNORECASE)
    
    # 4. Убираем остальные HTML теги
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 5. Декодируем HTML entities
    html_entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', 
        '&#39;': "'", '&nbsp;': ' ', '&mdash;': '-', '&ndash;': '-',
        '&rsquo;': "'", '&lsquo;': "'", '&rdquo;': '"', '&ldquo;': '"'
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    # 6. Убираем JavaScript мусор
    js_patterns = [
        r'function\s*\([^)]*\)\s*\{[^}]*\}',
        r'var\s+\w+\s*=\s*[^;]+;',
        r'window\.\w+\s*=\s*[^;]+;',
        r'document\.\w+\s*=\s*[^;]+;',
        r'\w+\s*:\s*function\s*\([^)]*\)\s*\{[^}]*\}',
        r'addEventListener\([^)]+\)',
        r'removeEventListener\([^)]+\)',
        r'setTimeout\([^)]+\)',
        r'setInterval\([^)]+\)',
        r'return\s+[^;]+;'
    ]
    
    for pattern in js_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # 7. Убираем CSS мусор  
    css_patterns = [
        r'[a-zA-Z-]+\s*:\s*[^;]+;',
        r'\.\w+\s*\{[^}]*\}',
        r'#\w+\s*\{[^}]*\}',
        r'@\w+[^{]*\{[^}]*\}',
        r'rgba?\([^)]+\)',
        r'\d+px\b', r'\d+em\b', r'\d+%\b',
        r'rgb\([^)]+\)', r'#[0-9a-fA-F]{3,6}\b'
    ]
    
    for pattern in css_patterns:
        text = re.sub(pattern, ' ', text)
    
    # 8. Убираем служебные фразы
    junk_phrases = [
        r'cookie policy', r'privacy policy', r'terms of service', r'terms and conditions',
        r'accept all cookies', r'decline cookies', r'manage cookies',
        r'subscribe to newsletter', r'sign up for', r'follow us on',
        r'all rights reserved', r'copyright \d{4}', r'powered by',
        r'skip to content', r'skip to main content', r'back to top',
        r'loading\.\.\.', r'please wait', r'error \d+',
        r'page not found', r'404', r'403', r'500'
    ]
    
    for phrase in junk_phrases:
        text = re.sub(phrase, ' ', text, flags=re.IGNORECASE)
    
    # 9. Убираем повторяющиеся символы и пробелы
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    
    # 10. Убираем короткие бессмысленные фрагменты
    words = text.split()
    meaningful_words = []
    
    for word in words:
        # Пропускаем очень короткие или подозрительные слова
        if len(word) < 2:
            continue
        if word.isdigit() and len(word) < 4:
            continue
        if re.match(r'^[^\w]*$', word):  # Только символы
            continue
        if len(set(word)) == 1:  # Повторяющиеся символы
            continue
            
        meaningful_words.append(word)
    
    # 11. Собираем финальный текст
    clean_text = ' '.join(meaningful_words)
    
    # 12. Финальная очистка
    clean_text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    return clean_text

def process_lumid_data():
    """Обработать данные Lumid с умной очисткой"""
    raw_file = "lumid_raw_text_data_20250910_153635.json"
    
    print("УМНАЯ ОЧИСТКА ТЕКСТА - МАКСИМУМ КОНТЕНТА")
    print("="*50)
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    smart_clean_data = {}
    
    for domain, data in raw_data.items():
        if data["success"]:
            # Используем raw_content для максимального извлечения
            raw_html = data.get("raw_content", "")
            if not raw_html:
                raw_html = data["text"]
            
            # Умная очистка
            clean_text = smart_clean_text(raw_html)
            
            # Если результат слишком короткий, берем оригинальный
            if len(clean_text) < 100 and len(data["text"]) > len(clean_text):
                clean_text = data["text"]
            
            smart_clean_data[domain] = {
                "domain": domain,
                "clean_text": clean_text,
                "text_length": len(clean_text),
                "words_count": len(clean_text.split()),
                "success": True
            }
        else:
            smart_clean_data[domain] = {
                "domain": domain,
                "clean_text": "",
                "text_length": 0,
                "words_count": 0,
                "success": False,
                "error": data.get("error", "")
            }
    
    # Сохраняем
    output_file = "lumid_smart_clean_text.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(smart_clean_data, f, indent=2, ensure_ascii=False)
    
    print(f"Умно очищенные данные: {output_file}")
    
    # Статистика
    successful = [d for d in smart_clean_data.values() if d["success"]]
    total_text = sum(d["text_length"] for d in successful)
    total_words = sum(d["words_count"] for d in successful)
    
    print(f"\nСТАТИСТИКА:")
    print(f"Успешно: {len(successful)} доменов")
    print(f"Общий текст: {total_text:,} символов")
    print(f"Общие слова: {total_words:,} слов")
    print(f"Среднее на домен: {total_text//len(successful):,} символов")
    
    # Топ 5 по объему
    top_domains = sorted(successful, key=lambda x: x["text_length"], reverse=True)[:5]
    print(f"\nТОП 5 ПО ОБЪЕМУ ТЕКСТА:")
    for i, d in enumerate(top_domains, 1):
        print(f"{i}. {d['domain']}: {d['text_length']:,} символов, {d['words_count']:,} слов")
    
    return output_file

if __name__ == "__main__":
    process_lumid_data()