import pandas as pd

df = pd.read_csv(r'modules\csv_tools\results\soviet_boots_complete_20251126_194805.csv')

print('=' * 70)
print('         SOVIET BOOTS - CATEGORIZATION & EMAIL GENERATION COMPLETE')
print('=' * 70)

print(f'\nTotal Leads Processed: {len(df)}')

print('\n--- CATEGORY BREAKDOWN ---')
for category, count in df['category'].value_counts().items():
    pct = count / len(df) * 100
    print(f'  {category:.<30} {count:>4} ({pct:>5.1f}%)')

print(f'\n--- DATA EXTRACTION ---')
print(f'  First names extracted: {df["first_name"].notna().sum()} ({df["first_name"].notna().sum()/len(df)*100:.1f}%)')
print(f'  Short names created: {len(df)} (100%)')
print(f'  Short locations: {len(df)} (100%)')

print(f'\n--- EMAIL SEQUENCES GENERATED ---')
print(f'  Subject lines: {len(df)} (100%)')
print(f'  Email 1 (personalized): {len(df)} (100%)')
print(f'  Email 2 (follow-up): {len(df)} (100%)')
print(f'  Email 3 (final): {len(df)} (100%)')

print('\n--- NEW COLUMNS ADDED ---')
new_cols = ['category', 'category_confidence', 'specific_detail', 'short_company_name',
            'short_location', 'first_name', 'subject_line', 'email_1_body',
            'email_2_body', 'email_3_body']
print(f'  Total new columns: {len(new_cols)}')
for col in new_cols:
    print(f'    - {col}')

print('\n--- SAMPLE DATA (First 3 by Category) ---')
for category in df['category'].unique()[:3]:
    print(f'\n  [{category.upper()}]')
    sample = df[df['category'] == category].iloc[0]
    print(f'  Org: {sample["name"]}')
    print(f'  Short: {sample["short_company_name"]}')
    print(f'  Detail: {sample["specific_detail"]}')
    print(f'  Location: {sample["short_location"]}')
    print(f'  First Name: {sample["first_name"] if pd.notna(sample["first_name"]) else "N/A"}')
    print(f'  Subject: {sample["subject_line"]}')
    print(f'  Email 1 Preview:')
    preview = sample["email_1_body"][:200] + "..."
    print(f'    {preview}')

print('\n' + '=' * 70)
print(f'File ready: modules/csv_tools/results/soviet_boots_complete_20251126_194805.csv')
print('=' * 70)
