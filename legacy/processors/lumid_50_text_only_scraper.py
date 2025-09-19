#!/usr/bin/env python3
"""
Lumid Canada - 50 сайтов - TEXT ONLY скрейпер
Финальная быстрая версия для 50 сайтов из lumid_canada_20250108.csv
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from text_only_website_scraper import TextOnlyWebsiteScraper

def main():
    """Обработка 50 сайтов из Lumid Canada"""
    input_file = "../../leads/raw/lumid_canada_20250108.csv"
    
    if not os.path.exists(input_file):
        print(f"Файл не найден: {input_file}")
        return
    
    print("="*80)
    print("LUMID CANADA - TEXT ONLY SCRAPER - 50 САЙТОВ")
    print("="*80)
    
    scraper = TextOnlyWebsiteScraper()
    
    # Обрабатываем 50 сайтов (убираем limit для полной обработки)
    result_file = scraper.process_csv_text_only(input_file, limit=50)
    
    print(f"\nРЕЗУЛЬТАТЫ СОХРАНЕНЫ: {result_file}")
    print("Теперь у вас есть чистые текстовые данные для персонализации!")
    
if __name__ == "__main__":
    main()