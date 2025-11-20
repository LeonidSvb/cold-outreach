import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\enriched_data_500_companies_20251120_193016.csv')

found = df[
    (df['found_website'].notna()) |
    ((df['found_email'].notna()) & (df['found_email'] != '')) |
    (df['found_facebook'].notna()) |
    (df['found_instagram'].notna())
]

print('=' * 70)
print('=== COMPANIES WITH DATA FOUND ===')
print('=' * 70)
print(f'\nTotal: {len(found)}/500 companies have some data\n')

for idx, (i, row) in enumerate(found.head(30).iterrows(), 1):
    print(f'{idx}. {row["Business Name"]} ({row["search_city"]})')

    if pd.notna(row['found_website']):
        print(f'   Website: {row["found_website"]}')

    if pd.notna(row['found_email']) and row['found_email'] != '':
        print(f'   Email: {row["found_email"]}')

    if pd.notna(row['found_facebook']):
        print(f'   Facebook: {row["found_facebook"]}')

    if pd.notna(row['found_instagram']):
        print(f'   Instagram: {row["found_instagram"]}')

    print()

print('=' * 70)
print(f'\nFull results in CSV:')
print(r'C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\enriched_data_500_companies_20251120_193016.csv')
