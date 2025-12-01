import pandas as pd

file_path = r'C:\Users\79818\Downloads\aus client.xlsx'
xls = pd.ExcelFile(file_path)

print('=' * 90)
print('           USABLE EMAILS ANALYSIS (Deliverable + Risky + Unknown)')
print('=' * 90)

usable_results = ['deliverable', 'risky', 'unknown']
all_usable = []

for i, sheet in enumerate(xls.sheet_names, 1):
    df = pd.read_excel(xls, sheet_name=sheet)

    print(f'\n{"=" * 90}')
    print(f'{i}. {sheet.upper()}')
    print(f'{"=" * 90}')

    # Find email column
    email_col = None
    for col in df.columns:
        if 'email' in col.lower() and col not in ['Email.1', 'ID']:
            if df[col].notna().sum() > 0:
                email_col = col
                break

    if email_col and 'Result' in df.columns:
        print(f'Total rows: {len(df)}')

        # All validation results
        print(f'\n--- All Validation Results ---')
        result_counts = df['Result'].value_counts()
        for result, count in result_counts.items():
            percentage = (count / len(df)) * 100
            status = '[INCLUDED]' if result in usable_results else '[EXCLUDED]'
            print(f'  {status} {result:15}: {count:4} ({percentage:5.1f}%)')

        # Filter usable
        usable = df[df['Result'].isin(usable_results)]
        print(f'\n>>> USABLE EMAILS: {len(usable)} / {len(df)} ({len(usable)/len(df)*100:.1f}%)')

        # Breakdown by status
        print(f'\n--- Usable Breakdown ---')
        for status in usable_results:
            count = len(usable[usable['Result'] == status])
            if count > 0:
                print(f'  {status:15}: {count:4}')

        # Provider distribution
        if 'Provider' in df.columns:
            print(f'\n--- Provider Distribution (Usable) ---')
            providers = usable['Provider'].value_counts().head(8)
            for provider, count in providers.items():
                print(f'  {provider:20}: {count:3}')

        # Store for summary
        all_usable.append({
            'sheet': sheet,
            'total': len(df),
            'usable': len(usable),
            'deliverable': len(usable[usable['Result'] == 'deliverable']),
            'risky': len(usable[usable['Result'] == 'risky']),
            'unknown': len(usable[usable['Result'] == 'unknown'])
        })
    else:
        print('[WARNING] No email validation data found')

print('\n' + '=' * 90)
print('                              SUMMARY TABLE')
print('=' * 90)

print(f'\n{"Niche":<25} {"Total":<8} {"Usable":<8} {"Deliver":<8} {"Risky":<8} {"Unknown":<8} {"Rate"}')
print('-' * 90)

total_all = 0
total_usable = 0
total_deliverable = 0
total_risky = 0
total_unknown = 0

for item in all_usable:
    rate = (item['usable'] / item['total'] * 100) if item['total'] > 0 else 0
    print(f"{item['sheet']:<25} {item['total']:<8} {item['usable']:<8} "
          f"{item['deliverable']:<8} {item['risky']:<8} {item['unknown']:<8} {rate:5.1f}%")

    total_all += item['total']
    total_usable += item['usable']
    total_deliverable += item['deliverable']
    total_risky += item['risky']
    total_unknown += item['unknown']

print('-' * 90)
total_rate = (total_usable / total_all * 100) if total_all > 0 else 0
print(f"{'TOTAL':<25} {total_all:<8} {total_usable:<8} "
      f"{total_deliverable:<8} {total_risky:<8} {total_unknown:<8} {total_rate:5.1f}%")

print('\n' + '=' * 90)
print('                         KEY INSIGHTS')
print('=' * 90)
print(f'Total usable emails: {total_usable:,}')
print(f'Usable rate: {total_rate:.1f}%')
print(f'\nQuality breakdown:')
print(f'  High quality (deliverable): {total_deliverable} ({total_deliverable/total_usable*100:.1f}%)')
print(f'  Medium risk (risky):        {total_risky} ({total_risky/total_usable*100:.1f}%)')
print(f'  Unknown (to verify):        {total_unknown} ({total_unknown/total_usable*100:.1f}%)')
print('=' * 90)
