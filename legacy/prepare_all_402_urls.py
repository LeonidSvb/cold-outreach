import csv
import json

# Читаем главный файл с 735 компаниями
with open(r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_20250108.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Получаем все уникальные URL
unique_urls = list(set(r['company_url'] for r in rows if r['company_url'] and r['company_url'].strip()))

print(f"ПОДГОТОВЛЕНО {len(unique_urls)} УНИКАЛЬНЫХ URL ДЛЯ МАССОВОГО СКРЕЙПИНГА")

# Создаем JSON для актора - делим на батчи по 200
batch_size = 200
for i in range(0, len(unique_urls), batch_size):
    batch = unique_urls[i:i+batch_size]
    start_urls = [{"url": url} for url in batch]
    batch_num = (i // batch_size) + 1
    print(f"\nБАТЧ {batch_num}: {len(batch)} URL")
    if batch_num == 1:  # Выводим первый батч
        print("JSON для первого батча:")
        print(json.dumps(start_urls, indent=2))
        break