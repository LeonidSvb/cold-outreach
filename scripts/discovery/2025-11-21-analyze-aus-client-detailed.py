import pandas as pd

file_path = r'C:\Users\79818\Downloads\aus client.xlsx'
xls = pd.ExcelFile(file_path)

print('=' * 90)
print('                      AUS CLIENT - DETAILED ANALYSIS')
print('=' * 90)

for i, sheet in enumerate(xls.sheet_names, 1):
    df = pd.read_excel(xls, sheet_name=sheet)

    print(f'\n{"=" * 90}')
    print(f'{i}. {sheet.upper()}')
    print(f'{"=" * 90}')

    print(f'Total rows: {len(df)}')
    print(f'Total columns: {len(df.columns)}')

    # Find email column
    email_col = None
    for col in df.columns:
        if 'email' in col.lower() and col not in ['Email.1', 'ID']:
            if df[col].notna().sum() > 0:
                email_col = col
                break

    if email_col:
        print(f'\nEmail column: "{email_col}"')
        print(f'Total emails: {df[email_col].notna().sum()}')
        print(f'Unique emails: {df[email_col].nunique()}')

        # Check if validation results exist
        if 'Result' in df.columns:
            result_counts = df['Result'].value_counts()
            print(f'\n--- Validation Results ---')
            for result, count in result_counts.items():
                percentage = (count / len(df)) * 100
                print(f'  {result:15}: {count:4} ({percentage:5.1f}%)')

            # Deliverable count
            deliverable = df[df['Result'] == 'deliverable']
            print(f'\n>>> DELIVERABLE: {len(deliverable)} unique emails')

            # Provider distribution for deliverable
            if 'Provider' in df.columns and len(deliverable) > 0:
                print(f'\n--- Provider Distribution (Deliverable) ---')
                providers = deliverable['Provider'].value_counts().head(5)
                for provider, count in providers.items():
                    print(f'  {provider:20}: {count:3}')
        else:
            print('\n[WARNING] No validation results found')
    else:
        print('\n[WARNING] No email column found')

    # Show sample business info
    business_cols = [col for col in df.columns if col.lower() in ['business name', 'name', 'website']]
    if business_cols and len(df) > 0:
        print(f'\n--- Sample Businesses (first 3) ---')
        sample = df[business_cols].head(3)
        for idx, row in sample.iterrows():
            values = ' | '.join([f'{k}: {v}' for k, v in row.items() if pd.notna(v)])
            print(f'  {values[:80]}')

print('\n' + '=' * 90)
print('                              SUMMARY')
print('=' * 90)

total_rows = 0
total_unique_emails = 0
total_deliverable = 0

for sheet in xls.sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet)
    total_rows += len(df)

    # Find email column
    email_col = None
    for col in df.columns:
        if 'email' in col.lower() and col not in ['Email.1', 'ID']:
            if df[col].notna().sum() > 0:
                email_col = col
                break

    if email_col:
        total_unique_emails += df[email_col].nunique()

    if 'Result' in df.columns:
        total_deliverable += len(df[df['Result'] == 'deliverable'])

print(f'Total rows across all sheets: {total_rows:,}')
print(f'Total unique emails: {total_unique_emails:,}')
print(f'Total deliverable emails: {total_deliverable:,}')
print(f'Deliverable rate: {(total_deliverable/total_unique_emails*100):.1f}%')
print('=' * 90)
