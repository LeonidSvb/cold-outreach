import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\enriched_data_500_companies_20251120_191742.csv')

print('=' * 60)
print('=== INTERMEDIATE RESULTS (First 50) ===')
print('=' * 60)

found_website = df['found_website'].notna().sum()
found_email = (df['found_email'].notna() & (df['found_email'] != '')).sum()
found_fb = df['found_facebook'].notna().sum()
found_ig = df['found_instagram'].notna().sum()

print(f'\nProcessed: {len(df)} companies\n')
print(f'Found Website:   {found_website:3d}/{len(df)} ({found_website/len(df)*100:5.1f}%)')
print(f'Found Email:     {found_email:3d}/{len(df)} ({found_email/len(df)*100:5.1f}%)')
print(f'Found Facebook:  {found_fb:3d}/{len(df)} ({found_fb/len(df)*100:5.1f}%)')
print(f'Found Instagram: {found_ig:3d}/{len(df)} ({found_ig/len(df)*100:5.1f}%)')

any_data = (df['found_website'].notna() |
            ((df['found_email'].notna()) & (df['found_email'] != '')) |
            df['found_facebook'].notna() |
            df['found_instagram'].notna()).sum()

print(f'\nCompanies with ANY data: {any_data}/{len(df)} ({any_data/len(df)*100:.1f}%)')

# Sample of found websites
print('\n' + '=' * 60)
print('Sample websites found:')
print('=' * 60)
websites = df[df['found_website'].notna()]['found_website'].head(10)
for i, website in enumerate(websites, 1):
    print(f'{i}. {website}')

# Sample of found emails
if found_email > 0:
    print('\n' + '=' * 60)
    print('Emails found:')
    print('=' * 60)
    emails = df[df['found_email'].notna() & (df['found_email'] != '')]['found_email']
    for i, email in enumerate(emails, 1):
        print(f'{i}. {email}')
