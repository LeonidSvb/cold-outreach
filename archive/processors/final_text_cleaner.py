#!/usr/bin/env python3
"""
ФИНАЛЬНЫЙ ОЧИСТИТЕЛЬ - ТОЛЬКО ЧИСТЫЙ КОНТЕНТ
Максимально агрессивная очистка, оставляем только читаемый текст
"""

import json
import re
from html import unescape

def brutal_clean_text(raw_html):
    """Брутальная очистка - убираем все кроме читаемого текста"""
    
    if not raw_html:
        return ""
    
    # 1. Убираем весь код полностью
    text = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<head[^>]*>.*?</head>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # 2. Убираем HTML теги, но сохраняем содержимое
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 3. Декодируем HTML entities
    text = unescape(text)
    
    # 4. Убираем JavaScript остатки
    text = re.sub(r'function\s*\([^)]*\)\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'var\s+\w+\s*=\s*[^;]+;', '', text)
    text = re.sub(r'const\s+\w+\s*=\s*[^;]+;', '', text)
    text = re.sub(r'let\s+\w+\s*=\s*[^;]+;', '', text)
    text = re.sub(r'if\s*\([^)]+\)\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'for\s*\([^)]+\)\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'while\s*\([^)]+\)\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'class\s+\w+\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'window\.\w+[^;]*;', '', text)
    text = re.sub(r'document\.\w+[^;]*;', '', text)
    text = re.sub(r'this\.\w+[^;]*;', '', text)
    text = re.sub(r'return\s+[^;]+;', '', text)
    text = re.sub(r'\w+\.\w+\([^)]*\)', '', text)
    text = re.sub(r'new\s+\w+\([^)]*\)', '', text)
    text = re.sub(r'typeof\s+\w+', '', text)
    text = re.sub(r'undefined', '', text)
    text = re.sub(r'null', '', text)
    text = re.sub(r'true', '', text)
    text = re.sub(r'false', '', text)
    
    # 5. Убираем CSS остатки
    text = re.sub(r'--wp--preset--[^:]*:[^;]*;', '', text)
    text = re.sub(r'[a-zA-Z-]+\s*:\s*[^;]*;', '', text)
    text = re.sub(r'\d+px', '', text)
    text = re.sub(r'\d+em', '', text)
    text = re.sub(r'\d+rem', '', text)
    text = re.sub(r'\d+%', '', text)
    text = re.sub(r'rgba?\([^)]+\)', '', text)
    text = re.sub(r'#[0-9a-fA-F]{3,6}', '', text)
    text = re.sub(r'linear-gradient[^;]*', '', text)
    text = re.sub(r'\.[\w-]+\s*\{[^}]*\}', '', text)
    text = re.sub(r'#[\w-]+\s*\{[^}]*\}', '', text)
    text = re.sub(r'@[\w-]+[^{]*\{[^}]*\}', '', text)
    
    # 6. Убираем технические фразы
    tech_patterns = [
        r':root', r':where', r':not', r':first-child', r':last-child',
        r'alignleft', r'alignright', r'aligncenter', r'alignfull', r'alignwide',
        r'wp-site-blocks', r'is-layout-\w+', r'margin-inline-\w+',
        r'addEventListener', r'removeEventListener', r'querySelector',
        r'getElementById', r'getElementsBy\w+', r'createElement',
        r'appendChild', r'removeChild', r'innerHTML', r'textContent',
        r'setAttribute', r'getAttribute', r'hasAttribute',
        r'preventDefault', r'stopPropagation', r'currentScript',
        r'sessionStorage', r'localStorage', r'navigator\.userAgent',
        r'Math\.\w+', r'Date\(\)', r'setTimeout', r'setInterval',
        r'Promise\.all', r'async\s+await', r'new\s+Promise',
        r'document\.ready', r'window\.load', r'DOMContentLoaded'
    ]
    
    for pattern in tech_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 7. Убираем служебные строки
    service_patterns = [
        r'cookie\s+policy', r'privacy\s+policy', r'terms\s+of\s+service',
        r'all\s+rights\s+reserved', r'copyright\s+\d{4}',
        r'skip\s+to\s+content', r'back\s+to\s+top', r'scroll\s+to\s+top',
        r'loading\.\.\.', r'please\s+wait', r'page\s+not\s+found',
        r'subscribe\s+to\s+newsletter', r'sign\s+up', r'log\s+in',
        r'create\s+account', r'forgot\s+password', r'remember\s+me',
        r'accept\s+cookies', r'decline\s+cookies', r'manage\s+cookies'
    ]
    
    for pattern in service_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 8. Убираем числовые последовательности и коды
    text = re.sub(r'\b\d{4,}\b', '', text)  # Длинные числа
    text = re.sub(r'[a-fA-F0-9]{8,}', '', text)  # Хэши
    text = re.sub(r'\w{20,}', '', text)  # Очень длинные строки
    
    # 9. Убираем повторы символов
    text = re.sub(r'(.)\1{3,}', '', text)  # 4+ одинаковых символа подряд
    
    # 10. Нормализуем пробелы
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    
    # 11. Убираем мусорные слова
    junk_words = {
        'var', 'const', 'let', 'function', 'return', 'typeof', 'instanceof',
        'undefined', 'null', 'NaN', 'Infinity', 'arguments', 'this',
        'prototype', 'constructor', 'hasOwnProperty', 'toString',
        'valueOf', 'parseInt', 'parseFloat', 'isNaN', 'isFinite',
        'encodeURIComponent', 'decodeURIComponent', 'setTimeout', 'setInterval',
        'clearTimeout', 'clearInterval', 'addEventListener', 'removeEventListener',
        'preventDefault', 'stopPropagation', 'getElementById', 'querySelector',
        'getElementsByClassName', 'getElementsByTagName', 'createElement',
        'appendChild', 'removeChild', 'insertBefore', 'replaceChild',
        'innerHTML', 'textContent', 'setAttribute', 'getAttribute',
        'classList', 'className', 'style', 'offsetWidth', 'offsetHeight',
        'scrollTop', 'scrollLeft', 'clientWidth', 'clientHeight'
    }
    
    words = text.split()
    clean_words = []
    
    for word in words:
        # Убираем знаки препинания для проверки
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        # Пропускаем если:
        if len(word) < 2:  # Слишком короткое
            continue
        if clean_word in junk_words:  # Технический мусор
            continue
        if word.isdigit() and len(word) < 4:  # Короткие числа
            continue
        if len(set(word)) == 1:  # Одинаковые символы
            continue
        if re.match(r'^[^\w]*$', word):  # Только символы
            continue
        if len(clean_word) == 0:  # Пустое после очистки
            continue
            
        clean_words.append(word)
    
    # 12. Собираем финальный текст
    final_text = ' '.join(clean_words)
    
    # 13. Финальная очистка
    final_text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\'\"]', ' ', final_text)
    final_text = re.sub(r'\s+', ' ', final_text).strip()
    
    return final_text

def create_final_clean_data():
    """Создать финальные чистые данные"""
    raw_file = "lumid_raw_text_data_20250910_153635.json"
    
    print("ФИНАЛЬНАЯ ОЧИСТКА - ТОЛЬКО ЧИТАЕМЫЙ КОНТЕНТ")
    print("="*50)
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    final_data = {}
    
    for domain, data in raw_data.items():
        if data["success"]:
            # Берем raw_content для максимального извлечения
            raw_content = data.get("raw_content", "")
            
            # Брутальная очистка
            clean_text = brutal_clean_text(raw_content)
            
            # Если результат пустой, пробуем оригинальный текст
            if len(clean_text) < 50:
                clean_text = brutal_clean_text(data["text"])
            
            # Если все еще пустой, берем оригинал
            if len(clean_text) < 20:
                clean_text = data["text"]
            
            final_data[domain] = {
                "domain": domain,
                "clean_text": clean_text,
                "text_length": len(clean_text),
                "words_count": len(clean_text.split()) if clean_text else 0,
                "success": True
            }
        else:
            final_data[domain] = {
                "domain": domain,
                "clean_text": "",
                "text_length": 0,
                "words_count": 0,
                "success": False,
                "error": data.get("error", "")
            }
    
    # Сохраняем финальные данные
    output_file = "lumid_final_clean_text.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2, ensure_ascii=False)
    
    print(f"Финальные чистые данные: {output_file}")
    
    # Статистика
    successful = [d for d in final_data.values() if d["success"]]
    total_text = sum(d["text_length"] for d in successful)
    total_words = sum(d["words_count"] for d in successful)
    
    print(f"\nСТАТИСТИКА:")
    print(f"Успешно: {len(successful)} доменов")
    print(f"Общий текст: {total_text:,} символов")
    print(f"Общие слова: {total_words:,} слов")
    if len(successful) > 0:
        print(f"Среднее на домен: {total_text//len(successful):,} символов")
        print(f"Среднее слов: {total_words//len(successful):,} слов")
    
    # Показываем примеры
    print(f"\nПРИМЕРЫ ЧИСТОГО ТЕКСТА:")
    examples = [d for d in successful if d["text_length"] > 200][:3]
    for d in examples:
        print(f"\n{d['domain']}:")
        print(f"  {d['clean_text'][:200]}...")
    
    return output_file

if __name__ == "__main__":
    create_final_clean_data()