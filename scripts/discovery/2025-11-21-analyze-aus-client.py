import pandas as pd

file_path = r'C:\Users\79818\Downloads\aus client.xlsx'
xls = pd.ExcelFile(file_path)

print('=' * 70)
print(f'TOTAL SHEETS: {len(xls.sheet_names)}')
print('=' * 70)

all_stats = []

for i, sheet in enumerate(xls.sheet_names, 1):
    df = pd.read_excel(xls, sheet_name=sheet)

    # Get unique emails if Email column exists
    email_cols = [col for col in df.columns if 'email' in col.lower()]
    unique_emails = df[email_cols[0]].nunique() if email_cols and len(df) > 0 else 0

    stats = {
        'num': i,
        'sheet': sheet,
        'rows': len(df),
        'cols': len(df.columns),
        'unique_emails': unique_emails
    }
    all_stats.append(stats)

    print(f"{i:2}. {sheet:35} | Rows: {len(df):4} | Unique Emails: {unique_emails:4}")

print('=' * 70)
print(f'TOTAL UNIQUE EMAILS ACROSS ALL SHEETS: {sum([s["unique_emails"] for s in all_stats])}')
print(f'TOTAL ROWS ACROSS ALL SHEETS: {sum([s["rows"] for s in all_stats])}')
print('=' * 70)

# Show sample columns from first few sheets
print('\n=== SAMPLE COLUMNS FROM FIRST 3 SHEETS ===')
for i in range(min(3, len(xls.sheet_names))):
    sheet = xls.sheet_names[i]
    df = pd.read_excel(xls, sheet_name=sheet, nrows=0)
    print(f'\n{sheet}:')
    print(df.columns.tolist())
