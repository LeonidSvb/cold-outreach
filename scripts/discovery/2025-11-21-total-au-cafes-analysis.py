import pandas as pd
import numpy as np

print('=' * 90)
print('           TOTAL AU CAFES ANALYSIS (Main Excel + 3 CSV files)')
print('=' * 90)

all_emails_list = []
all_data = []

# 1. Main Excel file - AU cafes sheet
print('\n1. Main Excel: aus client.xlsx - AU cafes sheet')
print('-' * 90)
xls = pd.ExcelFile(r'C:\Users\79818\Downloads\aus client.xlsx')
df_main = pd.read_excel(xls, sheet_name='AU cafes')

email_col_main = None
for col in df_main.columns:
    if 'email' in col.lower() and col not in ['Email.1', 'ID']:
        if df_main[col].notna().sum() > 0:
            email_col_main = col
            break

if email_col_main:
    emails_main = df_main[email_col_main].dropna()
    print(f'Total rows: {len(df_main)}')
    print(f'Total emails: {len(emails_main)}')
    print(f'Unique emails: {emails_main.nunique()}')

    if 'Result' in df_main.columns:
        usable_results = ['deliverable', 'risky', 'unknown']
        usable_main = df_main[df_main['Result'].isin(usable_results)]
        print(f'Usable emails: {len(usable_main)}')

        results = df_main['Result'].value_counts()
        print(f'\nValidation breakdown:')
        for result, count in results.items():
            print(f'  {result:15}: {count:4}')
    else:
        usable_main = df_main
        print(f'Usable emails: {len(emails_main)} (no validation)')

    all_emails_list.extend(emails_main.tolist())
    all_data.append({
        'source': 'Main Excel - AU cafes',
        'total': len(df_main),
        'emails': len(emails_main),
        'unique': emails_main.nunique(),
        'usable': len(usable_main)
    })

# 2. AU_cafes2.csv
print('\n\n2. AU_cafes2.csv')
print('-' * 90)
df1 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_cafes2.csv', header=None)

email_col_idx = None
for i, col in enumerate(df1.columns):
    sample = df1[col].astype(str).head(10)
    if sample.str.contains('@').sum() > 5:
        email_col_idx = i
        break

if email_col_idx is not None:
    emails1 = df1[email_col_idx].dropna()
    emails1 = emails1[emails1.astype(str).str.contains('@', na=False)]
    print(f'Total rows: {len(df1)}')
    print(f'Total emails: {len(emails1)}')
    print(f'Unique emails: {emails1.nunique()}')

    result_col_idx = email_col_idx + 1
    usable_results = ['deliverable', 'risky', 'unknown']
    usable1 = df1[df1[result_col_idx].isin(usable_results)]
    print(f'Usable emails: {len(usable1)}')

    if result_col_idx < len(df1.columns):
        results = df1[result_col_idx].value_counts()
        if any(r in usable_results for r in results.index if pd.notna(r)):
            print(f'\nValidation breakdown:')
            for result, count in results.items():
                if pd.notna(result):
                    print(f'  {result:15}: {count:4}')

    all_emails_list.extend(emails1.tolist())
    all_data.append({
        'source': 'AU_cafes2.csv',
        'total': len(df1),
        'emails': len(emails1),
        'unique': emails1.nunique(),
        'usable': len(usable1)
    })

# 3. AU cafes (1).csv
print('\n\n3. AU cafes (1).csv')
print('-' * 90)
df2 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU cafes (1).csv')

email_col2 = None
for col in df2.columns:
    if 'email' in col.lower():
        if df2[col].notna().sum() > 0:
            email_col2 = col
            break

if email_col2:
    emails2 = df2[email_col2].dropna()
    print(f'Total rows: {len(df2)}')
    print(f'Total emails: {len(emails2)}')
    print(f'Unique emails: {emails2.nunique()}')
    print(f'Usable emails: {len(emails2)} (no validation data)')

    all_emails_list.extend(emails2.tolist())
    all_data.append({
        'source': 'AU cafes (1).csv',
        'total': len(df2),
        'emails': len(emails2),
        'unique': emails2.nunique(),
        'usable': len(emails2)
    })

# 4. AU_Cafes3.csv
print('\n\n4. AU_Cafes3.csv')
print('-' * 90)
df3 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_Cafes3.csv')

email_col3 = None
for col in df3.columns:
    if 'email' in col.lower() and col not in ['Email.1', 'ID']:
        if df3[col].notna().sum() > 0:
            email_col3 = col
            break

if email_col3:
    emails3 = df3[email_col3].dropna()
    print(f'Total rows: {len(df3)}')
    print(f'Total emails: {len(emails3)}')
    print(f'Unique emails: {emails3.nunique()}')

    if 'Result' in df3.columns:
        usable_results = ['deliverable', 'risky', 'unknown']
        usable3 = df3[df3['Result'].isin(usable_results)]
        print(f'Usable emails: {len(usable3)}')

        results = df3['Result'].value_counts()
        print(f'\nValidation breakdown:')
        for result, count in results.items():
            print(f'  {result:15}: {count:4}')
    else:
        usable3 = df3
        print(f'Usable emails: {len(emails3)} (no validation)')

    all_emails_list.extend(emails3.tolist())
    all_data.append({
        'source': 'AU_Cafes3.csv',
        'total': len(df3),
        'emails': len(emails3),
        'unique': emails3.nunique(),
        'usable': len(usable3)
    })

# Final Summary
print('\n' + '=' * 90)
print('                           FINAL SUMMARY')
print('=' * 90)

print(f'\n{"Source":<30} {"Total Rows":<12} {"Emails":<10} {"Unique":<10} {"Usable":<10}')
print('-' * 90)

total_rows = 0
total_emails = 0
total_unique = 0
total_usable = 0

for item in all_data:
    print(f"{item['source']:<30} {item['total']:<12} {item['emails']:<10} "
          f"{item['unique']:<10} {item['usable']:<10}")
    total_rows += item['total']
    total_emails += item['emails']
    total_unique += item['unique']
    total_usable += item['usable']

print('-' * 90)
print(f"{'SUBTOTAL (before deduplication)':<30} {total_rows:<12} {total_emails:<10} "
      f"{total_unique:<10} {total_usable:<10}")

# Global deduplication
all_emails_series = pd.Series(all_emails_list)
all_emails_series = all_emails_series[all_emails_series.notna()]
global_unique = all_emails_series.nunique()
duplicates = len(all_emails_series) - global_unique

print('\n' + '=' * 90)
print('                        DEDUPLICATION RESULTS')
print('=' * 90)
print(f'Total emails across all sources:  {len(all_emails_series):,}')
print(f'Global unique emails:              {global_unique:,}')
print(f'Duplicates removed:                {duplicates:,}')
print(f'Deduplication rate:                {(duplicates/len(all_emails_series)*100):.1f}%')
print('\n' + '=' * 90)
print(f'              FINAL USABLE AU CAFES EMAILS: {global_unique:,}')
print('=' * 90)
