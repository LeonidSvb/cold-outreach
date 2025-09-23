import csv
import json
from datetime import datetime
from collections import Counter
import os

print("МАССОВЫЙ СКРЕЙПЕР ВСЕХ КАНАДСКИХ ЛИДОВ")
print("=" * 50)

# Собираем ВСЕ канадские файлы
raw_files = [
    r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_20250108.csv',
    r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_batch50_20250910_151323.csv'
]

all_companies = []
all_urls = set()

# Читаем все файлы и собираем уникальные URL
for file_path in raw_files:
    if os.path.exists(file_path):
        print(f"Читаю: {os.path.basename(file_path)}")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('company_url') and row['company_url'].strip():
                    url = row['company_url'].strip()
                    if url not in all_urls and 'canada' in str(row).lower():
                        all_companies.append(row)
                        all_urls.add(url)

print(f"НАЙДЕНО УНИКАЛЬНЫХ КАНАДСКИХ САЙТОВ: {len(all_urls)}")

# Проверяем уже скрейпленные
already_scraped = set()
processed_file = r'C:\Users\79818\Desktop\Outreach - new\leads\processed\canadian_leads_scraped_20250910.csv'
if os.path.exists(processed_file):
    with open(processed_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            already_scraped.add(row['url'])

remaining_urls = all_urls - already_scraped
print(f"УЖЕ СКРЕЙПЛЕНО: {len(already_scraped)}")
print(f"ОСТАЕТСЯ СКРЕЙПАТЬ: {len(remaining_urls)}")

# Готовим список для Apify актора
urls_for_scraping = list(remaining_urls)
print(f"\nПОДГОТОВЛЕН СПИСОК ИЗ {len(urls_for_scraping)} URL ДЛЯ МАССОВОГО СКРЕЙПИНГА")

# Выводим первые 10 для проверки
print("\nПРИМЕР ПЕРВЫХ 10 URL:")
for i, url in enumerate(urls_for_scraping[:10], 1):
    print(f"  {i}. {url}")

print(f"\nГОТОВ К МАССОВОМУ СКРЕЙПИНГУ {len(urls_for_scraping)} САЙТОВ!")