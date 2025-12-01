import pandas as pd
import numpy as np

print('=' * 90)
print('         AU CAFES - USABLE EMAILS COUNT (after deduplication)')
print('=' * 90)

all_emails_dict = {}  # email -> validation_result

usable_results = ['deliverable', 'risky', 'unknown']

# 1. Main Excel - AU cafes
xls = pd.ExcelFile(r'C:\Users\79818\Downloads\aus client.xlsx')
df_main = pd.read_excel(xls, sheet_name='AU cafes')

email_col = None
for col in df_main.columns:
    if 'email' in col.lower() and col not in ['Email.1', 'ID']:
        if df_main[col].notna().sum() > 0:
            email_col = col
            break

if email_col and 'Result' in df_main.columns:
    for _, row in df_main.iterrows():
        email = row[email_col]
        result = row['Result']
        if pd.notna(email) and pd.notna(result):
            if email not in all_emails_dict:
                all_emails_dict[email] = result

# 2. AU_cafes2.csv
df1 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_cafes2.csv', header=None)

email_col_idx = None
for i, col in enumerate(df1.columns):
    sample = df1[col].astype(str).head(10)
    if sample.str.contains('@').sum() > 5:
        email_col_idx = i
        break

if email_col_idx is not None:
    result_col_idx = email_col_idx + 1
    for _, row in df1.iterrows():
        email = row[email_col_idx]
        result = row[result_col_idx] if result_col_idx < len(df1.columns) else None
        if pd.notna(email) and '@' in str(email):
            if email not in all_emails_dict:
                all_emails_dict[email] = result if pd.notna(result) else 'no_validation'

# 3. AU cafes (1).csv (no validation)
df2 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU cafes (1).csv')

email_col2 = None
for col in df2.columns:
    if 'email' in col.lower():
        if df2[col].notna().sum() > 0:
            email_col2 = col
            break

if email_col2:
    for _, row in df2.iterrows():
        email = row[email_col2]
        if pd.notna(email):
            if email not in all_emails_dict:
                all_emails_dict[email] = 'no_validation'

# 4. AU_Cafes3.csv
df3 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_Cafes3.csv')

email_col3 = None
for col in df3.columns:
    if 'email' in col.lower() and col not in ['Email.1', 'ID']:
        if df3[col].notna().sum() > 0:
            email_col3 = col
            break

if email_col3 and 'Result' in df3.columns:
    for _, row in df3.iterrows():
        email = row[email_col3]
        result = row['Result']
        if pd.notna(email) and pd.notna(result):
            if email not in all_emails_dict:
                all_emails_dict[email] = result

# Analyze
total_unique = len(all_emails_dict)

deliverable = sum(1 for r in all_emails_dict.values() if r == 'deliverable')
risky = sum(1 for r in all_emails_dict.values() if r == 'risky')
unknown = sum(1 for r in all_emails_dict.values() if r == 'unknown')
undeliverable = sum(1 for r in all_emails_dict.values() if r == 'undeliverable')
no_validation = sum(1 for r in all_emails_dict.values() if r == 'no_validation')

usable_count = deliverable + risky + unknown + no_validation

print(f'\nTotal unique emails: {total_unique}')
print('\n--- Validation Status Breakdown ---')
print(f'  Deliverable:     {deliverable:4} ({deliverable/total_unique*100:5.1f}%)')
print(f'  Risky:           {risky:4} ({risky/total_unique*100:5.1f}%)')
print(f'  Unknown:         {unknown:4} ({unknown/total_unique*100:5.1f}%)')
print(f'  No validation:   {no_validation:4} ({no_validation/total_unique*100:5.1f}%)')
print(f'  Undeliverable:   {undeliverable:4} ({undeliverable/total_unique*100:5.1f}%)')

print('\n' + '=' * 90)
print(f'           USABLE EMAILS (Deliverable + Risky + Unknown + No Validation)')
print('=' * 90)
print(f'\nTotal usable: {usable_count} / {total_unique} ({usable_count/total_unique*100:.1f}%)')
print(f'\nQuality breakdown:')
print(f'  High quality (deliverable):  {deliverable:4} ({deliverable/usable_count*100:5.1f}%)')
print(f'  Medium risk (risky):         {risky:4} ({risky/usable_count*100:5.1f}%)')
print(f'  Unknown:                     {unknown:4} ({unknown/usable_count*100:5.1f}%)')
print(f'  No validation (assume OK):   {no_validation:4} ({no_validation/usable_count*100:5.1f}%)')

print('\n' + '=' * 90)
print(f'              FINAL AU CAFES USABLE EMAILS: {usable_count}')
print('=' * 90)
