import csv

# Читаем все канадские лиды
with open(r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_batch50_20250910_151323.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Получаем все уникальные URL
unique_urls = []
seen = set()
for row in rows:
    url = row["company_url"].strip()
    if url and url not in seen:
        unique_urls.append(url)
        seen.add(url)

print(f'Подготовлены все {len(unique_urls)} URL для скрейпинга')

# Выводим список для актора Apify
urls_for_actor = '\n'.join(unique_urls)
print('\nВСЕ URL ДЛЯ АКТОРА:')
print(urls_for_actor)