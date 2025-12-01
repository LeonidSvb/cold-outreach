import pandas as pd

# Read both CSVs
print('Loading files...')
df1 = pd.read_csv(r'C:\Users\79818\Downloads\batch_18758a12-b275-431c-a009-449d0db08ff7_all_with_original.csv', encoding='utf-8-sig')
df2 = pd.read_csv(r'C:\Users\79818\Downloads\batch_e7a3381d-227f-4875-9afa-4dd0a35e792a_all_with_original.csv', encoding='utf-8-sig')

print(f'File 1 (Check 1): {len(df1)} emails')
print(f'File 2 (Check 2): {len(df2)} emails')
print()

# Normalize email column names
email_col1 = 'Email' if 'Email' in df1.columns else 'email'
email_col2 = 'Email' if 'Email' in df2.columns else 'email'

# Merge on email to compare
merged = df1.merge(df2, left_on=email_col1, right_on=email_col2, suffixes=('_check1', '_check2'), how='inner')

print(f'Common emails between both checks: {len(merged)}')
print()

# Find where Result changed
changes = merged[merged['Result_check1'] != merged['Result_check2']].copy()

print(f'EMAILS WHERE STATUS CHANGED: {len(changes)}')
print('=' * 100)
print()

if len(changes) > 0:
    for idx, row in changes.head(30).iterrows():
        email = row['Email_check1'] if 'Email_check1' in row else row['email_check1']
        res1 = row['Result_check1']
        res2 = row['Result_check2']
        reason1 = row['Reason_check1'] if pd.notna(row['Reason_check1']) else 'N/A'
        reason2 = row['Reason_check2'] if pd.notna(row['Reason_check2']) else 'N/A'

        print(f'{email:50} | {res1:15} -> {res2:15} | {reason1:20} -> {reason2:20}')

    if len(changes) > 30:
        print(f'\n... and {len(changes) - 30} more changes')

    print()
    print('=' * 100)
    print('BREAKDOWN OF CHANGES:')
    print()

    for old_status in ['deliverable', 'risky', 'unknown', 'undeliverable']:
        if old_status in changes['Result_check1'].values:
            subset = changes[changes['Result_check1'] == old_status]
            print(f'FROM {old_status.upper()} (Check 1):')
            for new_status, count in subset['Result_check2'].value_counts().items():
                print(f'  -> {new_status}: {count} emails')
            print()
else:
    print('No status changes found - results are consistent!')
