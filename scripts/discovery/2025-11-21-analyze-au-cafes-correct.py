import pandas as pd
import numpy as np

print('=' * 90)
print('                AU CAFES - CORRECT ANALYSIS')
print('=' * 90)

# File 1: AU_cafes2.csv (no headers)
print('\n1. AU_cafes2.csv')
print('-' * 90)
df1 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_cafes2.csv', header=None)
print(f'Total rows: {len(df1)}')
print(f'Total columns: {len(df1.columns)}')

# Try to find email column (usually has @ symbol)
email_col_idx = None
for i, col in enumerate(df1.columns):
    sample = df1[col].astype(str).head(10)
    if sample.str.contains('@').sum() > 5:
        email_col_idx = i
        break

if email_col_idx is not None:
    emails1 = df1[email_col_idx].dropna()
    emails1 = emails1[emails1.astype(str).str.contains('@', na=False)]
    print(f'Email column index: {email_col_idx}')
    print(f'Total emails: {len(emails1)}')
    print(f'Unique emails: {emails1.nunique()}')

    # Check for validation results (usually next to email)
    result_col_idx = email_col_idx + 1
    if result_col_idx < len(df1.columns):
        results = df1[result_col_idx].value_counts()
        if any(r in ['deliverable', 'undeliverable', 'risky', 'unknown'] for r in results.index if pd.notna(r)):
            print(f'\nValidation Results:')
            for result, count in results.items():
                if pd.notna(result):
                    percentage = (count / len(df1)) * 100
                    print(f'  {result:15}: {count:4} ({percentage:5.1f}%)')

            usable_results = ['deliverable', 'risky', 'unknown']
            usable1 = df1[df1[result_col_idx].isin(usable_results)]
            print(f'\n>>> USABLE: {len(usable1)} ({len(usable1)/len(df1)*100:.1f}%)')
        else:
            usable1 = pd.DataFrame()
    else:
        usable1 = pd.DataFrame()

    print(f'\nSample emails:')
    print(emails1.head(5).tolist())
else:
    emails1 = pd.Series()
    usable1 = pd.DataFrame()
    print('[WARNING] No email column found')

# File 2: AU cafes (1).csv
print('\n\n2. AU cafes (1).csv')
print('-' * 90)
df2 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU cafes (1).csv')
print(f'Total rows: {len(df2)}')
print(f'Total columns: {len(df2.columns)}')
print(f'Columns: {df2.columns.tolist()}')

email_col2 = None
for col in df2.columns:
    if 'email' in col.lower():
        if df2[col].notna().sum() > 0:
            email_col2 = col
            break

if email_col2:
    emails2 = df2[email_col2].dropna()
    print(f'\nEmail column: "{email_col2}"')
    print(f'Total emails: {len(emails2)}')
    print(f'Unique emails: {emails2.nunique()}')

    if 'Result' in df2.columns:
        results2 = df2['Result'].value_counts()
        print(f'\nValidation Results:')
        for result, count in results2.items():
            percentage = (count / len(df2)) * 100
            print(f'  {result:15}: {count:4} ({percentage:5.1f}%)')

        usable_results = ['deliverable', 'risky', 'unknown']
        usable2 = df2[df2['Result'].isin(usable_results)]
        print(f'\n>>> USABLE: {len(usable2)} ({len(usable2)/len(df2)*100:.1f}%)')
    else:
        usable2 = pd.DataFrame()
        print('\n[WARNING] No validation results - all emails assumed usable')

    print(f'\nSample emails:')
    print(emails2.head(5).tolist())
else:
    emails2 = pd.Series()
    usable2 = pd.DataFrame()

# File 3: AU_Cafes3.csv
print('\n\n3. AU_Cafes3.csv')
print('-' * 90)
df3 = pd.read_csv(r'C:\Users\79818\Downloads\aus client - AU_Cafes3.csv')
print(f'Total rows: {len(df3)}')
print(f'Total columns: {len(df3.columns)}')

email_col3 = None
for col in df3.columns:
    if 'email' in col.lower() and col not in ['Email.1', 'ID']:
        if df3[col].notna().sum() > 0:
            email_col3 = col
            break

if email_col3:
    emails3 = df3[email_col3].dropna()
    print(f'\nEmail column: "{email_col3}"')
    print(f'Total emails: {len(emails3)}')
    print(f'Unique emails: {emails3.nunique()}')

    if 'Result' in df3.columns:
        results3 = df3['Result'].value_counts()
        print(f'\nValidation Results:')
        for result, count in results3.items():
            percentage = (count / len(df3)) * 100
            print(f'  {result:15}: {count:4} ({percentage:5.1f}%)')

        usable_results = ['deliverable', 'risky', 'unknown']
        usable3 = df3[df3['Result'].isin(usable_results)]
        print(f'\n>>> USABLE: {len(usable3)} ({len(usable3)/len(df3)*100:.1f}%)')
    else:
        usable3 = pd.DataFrame()
else:
    emails3 = pd.Series()
    usable3 = pd.DataFrame()

# Summary
print('\n' + '=' * 90)
print('                              SUMMARY')
print('=' * 90)

all_emails = pd.concat([emails1, emails2, emails3], ignore_index=True)
all_emails = all_emails[all_emails.notna()]

print(f'\nFile 1 (AU_cafes2):        {len(emails1):4} emails, {emails1.nunique():4} unique, {len(usable1):4} usable')
print(f'File 2 (AU cafes (1)):     {len(emails2):4} emails, {emails2.nunique():4} unique, {len(usable2) if len(usable2) > 0 else len(emails2):4} usable')
print(f'File 3 (AU_Cafes3):        {len(emails3):4} emails, {emails3.nunique():4} unique, {len(usable3):4} usable')
print('-' * 90)
print(f'Total across all files:    {len(all_emails):4} emails')
print(f'Global unique:             {all_emails.nunique():4} emails')
print(f'Duplicates removed:        {len(all_emails) - all_emails.nunique():4} emails')
print(f'Deduplication rate:        {((len(all_emails) - all_emails.nunique())/len(all_emails)*100):.1f}%')
print('=' * 90)
