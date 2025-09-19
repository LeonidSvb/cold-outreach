import csv
import os

# Собираем все уникальные URL
raw_files = [
    r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_20250108.csv',
    r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_batch50_20250910_151323.csv'
]

all_urls = set()
for file_path in raw_files:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('company_url') and row['company_url'].strip():
                    url = row['company_url'].strip()
                    if 'canada' in str(row).lower():
                        all_urls.add(url)

# Исключаем уже скрейпленные
already_scraped = set()
processed_file = r'C:\Users\79818\Desktop\Outreach - new\leads\processed\canadian_leads_scraped_20250910.csv'
if os.path.exists(processed_file):
    with open(processed_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            already_scraped.add(row['url'])

remaining_urls = list(all_urls - already_scraped)

# Выводим JSON для актора
import json
start_urls = [{"url": url} for url in remaining_urls]
print(json.dumps(start_urls[:100]))  # Первые 100 для теста батчами