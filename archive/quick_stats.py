import csv

# Читаем исходный файл с канадскими лидами
with open(r'C:\Users\79818\Desktop\Outreach - new\leads\raw\lumid_canada_batch50_20250910_151323.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print('ПОЛНАЯ СТАТИСТИКА ПО КАНАДСКИМ ЛИДАМ:')
print(f'  • Всего компаний в исходном файле: {len(rows)}')
print(f'  • Компаний с URL: {len([r for r in rows if r["company_url"] and r["company_url"].strip()])}')

unique_urls = set(r["company_url"] for r in rows if r["company_url"] and r["company_url"].strip())
print(f'  • Уникальных сайтов для скрейпинга: {len(unique_urls)}')

print('\nПЕРВЫЕ 10 URL ДЛЯ ТЕСТА:')
for i, url in enumerate(list(unique_urls)[:10], 1):
    print(f'  {i}. {url}')

print(f'\nВСЕГО САЙТОВ ДЛЯ ПОЛНОГО СКРЕЙПИНГА: {len(unique_urls)}')

# Проверяем результаты скрейпинга
try:
    with open(r'C:\Users\79818\Desktop\Outreach - new\leads\processed\canadian_leads_scraped_20250910.csv', 'r', encoding='utf-8') as f:
        scraped_reader = csv.DictReader(f)
        scraped_rows = list(scraped_reader)
    
    print(f'\nРЕЗУЛЬТАТЫ ПОСЛЕДНЕГО СКРЕЙПИНГА:')
    print(f'  • Уже скрейпано сайтов: {len(scraped_rows)}')
    print(f'  • Средняя длина контента: {sum(len(r["text_content"]) for r in scraped_rows) // len(scraped_rows) if scraped_rows else 0} символов')
    print(f'  • Остается скрейпать: {len(unique_urls) - len(scraped_rows)} сайтов')
    
except FileNotFoundError:
    print('\nФайл с результатами скрейпинга не найден.')