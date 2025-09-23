#!/usr/bin/env python3
"""
Извлечение сырых текстовых данных из уже обработанного CSV
Быстрое решение для получения актуального текста сайтов
"""

import pandas as pd
import json
import sys
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from html.parser import HTMLParser

class TextOnlyParser(HTMLParser):
    """Парсер для извлечения ТОЛЬКО текста и ссылок"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.links = []
        self.current_tag = None
        self.ignore_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'meta', 'link'}
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href' and attr[1]:
                    href = attr[1].strip()
                    if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                        self.links.append(href)
                        
    def handle_endtag(self, tag):
        self.current_tag = None
        
    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            text = data.strip()
            if len(text) > 10:
                self.text_content.append(text)
    
    def get_clean_data(self):
        full_text = ' '.join(self.text_content)
        clean_text = re.sub(r'\s+', ' ', full_text)
        clean_text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', ' ', clean_text)
        unique_links = list(set(self.links))
        
        return {
            "text": clean_text[:5000],  # Первые 5KB текста
            "text_length": len(clean_text),
            "links": unique_links[:50]  # Максимум 50 ссылок
        }

def scrape_domain_now(domain: str) -> dict:
    """Быстро скрейпить домен для получения сырых данных"""
    try:
        if not domain.startswith(('http://', 'https://')):
            url = f"https://{domain}"
        else:
            url = domain
            
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            content = response.read(100000).decode('utf-8', errors='ignore')  # 100KB
            
            parser = TextOnlyParser()
            parser.feed(content)
            clean_data = parser.get_clean_data()
            
            return {
                "domain": domain,
                "success": True,
                "text": clean_data["text"],
                "text_length": clean_data["text_length"],
                "links": clean_data["links"],
                "raw_content": content[:10000]  # Первые 10KB raw HTML для справки
            }
            
    except Exception as e:
        return {
            "domain": domain,
            "success": False,
            "error": str(e),
            "text": "",
            "links": []
        }

def main():
    """Извлечь сырые данные из CSV результатов"""
    csv_file = "text_only_results_text_only_20250910_152817.csv"
    
    if not os.path.exists(csv_file):
        print(f"CSV файл не найден: {csv_file}")
        return
    
    print("="*60)
    print("ИЗВЛЕЧЕНИЕ СЫРЫХ ДАННЫХ ИЗ CSV РЕЗУЛЬТАТОВ")
    print("="*60)
    
    # Читаем CSV с результатами
    df = pd.read_csv(csv_file)
    successful_domains = df[df['text_extraction_success'] == True]['domain'].tolist()
    
    print(f"Найдено {len(successful_domains)} успешных доменов")
    print("Извлекаем сырые данные...")
    
    start_time = time.time()
    raw_data = {}
    
    # Быстро скрейпим все домены параллельно
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(scrape_domain_now, domain): domain 
                  for domain in successful_domains}
        
        completed = 0
        for future in futures:
            try:
                result = future.result()
                raw_data[result["domain"]] = result
                completed += 1
                
                if completed % 10 == 0:
                    print(f"Обработано: {completed}/{len(successful_domains)}")
                    
            except Exception as e:
                print(f"Ошибка: {str(e)}")
    
    # Сохраняем сырые данные
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_file = f"lumid_raw_text_data_{session_id}.json"
    
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    successful = sum(1 for r in raw_data.values() if r["success"])
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ИЗВЛЕЧЕНИЯ СЫРЫХ ДАННЫХ")
    print("="*60)
    print(f"Время: {elapsed:.1f} секунд")
    print(f"Успешно: {successful}/{len(successful_domains)} доменов")
    print(f"Файл: {raw_file}")
    
    # Показываем примеры данных
    print(f"\nПРИМЕРЫ ИЗВЛЕЧЕННОГО ТЕКСТА:")
    for domain, data in list(raw_data.items())[:3]:
        if data["success"]:
            print(f"\n{domain}:")
            print(f"  Текст: {data['text'][:200]}...")
            print(f"  Длина: {data['text_length']} символов")
            print(f"  Ссылки: {len(data['links'])}")
    
    print(f"\nТеперь у вас есть сырые текстовые данные в {raw_file}")

if __name__ == "__main__":
    main()