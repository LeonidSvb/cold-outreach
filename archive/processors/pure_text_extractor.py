#!/usr/bin/env python3
"""
ЧИСТЫЙ ТЕКСТ - без HTML мусора
Извлекаем только полезный контент для персонализации
"""

import json
import re
from html.parser import HTMLParser

class PureTextExtractor(HTMLParser):
    """Извлекает ТОЛЬКО полезный текст"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = None
        # Игнорируем полностью эти теги
        self.skip_tags = {
            'script', 'style', 'meta', 'link', 'head', 'nav', 'footer', 
            'header', 'aside', 'iframe', 'noscript', 'svg', 'path'
        }
        self.in_skip_tag = False
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.in_skip_tag = True
        self.current_tag = tag.lower()
        
    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.in_skip_tag = False
        # Добавляем пробел после блочных элементов
        if tag.lower() in ['div', 'p', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            self.text_parts.append(' ')
        self.current_tag = None
        
    def handle_data(self, data):
        if not self.in_skip_tag:
            text = data.strip()
            if text and len(text) > 2:  # Только значимый текст
                self.text_parts.append(text)
    
    def get_clean_text(self):
        """Получить очищенный текст"""
        full_text = ' '.join(self.text_parts)
        
        # Убираем повторяющиеся пробелы
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Убираем служебные слова и фразы
        junk_patterns = [
            r'Cookie Policy', r'Privacy Policy', r'Terms of Service',
            r'Accept all cookies', r'Decline', r'window\._wpemojiSettings',
            r'function\(\w+\)', r'var \w+\s*=', r'return \w+',
            r'Copyright \d{4}', r'\(\w+\)', r'undefined', r'null',
            r'addEventListener', r'removeEventListener', r'localStorage',
            r'sessionStorage', r'documentElement', r'innerHTML'
        ]
        
        for pattern in junk_patterns:
            full_text = re.sub(pattern, ' ', full_text, flags=re.IGNORECASE)
        
        # Убираем лишние символы
        full_text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', ' ', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text

def clean_raw_data():
    """Очистить сырые данные и оставить только текст"""
    raw_file = "lumid_raw_text_data_20250910_153635.json"
    
    print("ОЧИСТКА СЫРЫХ ДАННЫХ - ТОЛЬКО ПОЛЕЗНЫЙ ТЕКСТ")
    print("="*60)
    
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    clean_data = {}
    
    for domain, data in raw_data.items():
        if data["success"]:
            # Извлекаем чистый текст из raw_content
            parser = PureTextExtractor()
            parser.feed(data.get("raw_content", ""))
            clean_text = parser.get_clean_text()
            
            # Если текст слишком короткий, используем уже очищенный
            if len(clean_text) < 50:
                clean_text = data["text"]
            
            clean_data[domain] = {
                "domain": domain,
                "clean_text": clean_text,
                "text_length": len(clean_text),
                "original_text": data["text"][:500],  # Для сравнения
                "success": True
            }
        else:
            clean_data[domain] = {
                "domain": domain,
                "clean_text": "",
                "text_length": 0,
                "success": False,
                "error": data.get("error", "")
            }
    
    # Сохраняем очищенные данные
    output_file = "lumid_clean_text_only.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=2, ensure_ascii=False)
    
    print(f"Очищенные данные сохранены: {output_file}")
    
    # Показываем примеры
    print("\nПРИМЕРЫ ОЧИЩЕННОГО ТЕКСТА:")
    print("="*60)
    
    count = 0
    for domain, data in clean_data.items():
        if data["success"] and len(data["clean_text"]) > 100:
            print(f"\n{domain}:")
            print(f"Длина: {data['text_length']} символов")
            print(f"Текст: {data['clean_text'][:300]}...")
            count += 1
            if count >= 3:
                break
    
    # Статистика
    successful = sum(1 for d in clean_data.values() if d["success"])
    total_text = sum(d["text_length"] for d in clean_data.values())
    
    print(f"\nСТАТИСТИКА:")
    print(f"Успешно очищено: {successful} доменов")
    print(f"Общий объем текста: {total_text} символов")
    print(f"Средний размер: {total_text//successful:.0f} символов на домен")
    print(f"Файл готов для персонализации: {output_file}")

if __name__ == "__main__":
    clean_raw_data()