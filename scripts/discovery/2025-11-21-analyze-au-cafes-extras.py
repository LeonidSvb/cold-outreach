import pandas as pd
import os

files = [
    r'C:\Users\79818\Downloads\aus client - AU_cafes2.csv',
    r'C:\Users\79818\Downloads\aus client - AU cafes (1).csv',
    r'C:\Users\79818\Downloads\aus client - AU_Cafes3.csv'
]

print('=' * 90)
print('                AU CAFES - ADDITIONAL FILES ANALYSIS')
print('=' * 90)

all_emails = []
file_stats = []

for i, file_path in enumerate(files, 1):
    filename = os.path.basename(file_path)

    if not os.path.exists(file_path):
        print(f'\n{i}. {filename}')
        print('   [ERROR] File not found!')
        continue

    try:
        # Try different separators
        try:
            df = pd.read_csv(file_path)
        except:
            df = pd.read_csv(file_path, sep='\t')

        print(f'\n{i}. {filename}')
        print('-' * 90)
        print(f'   Total rows: {len(df)}')
        print(f'   Total columns: {len(df.columns)}')

        # Find email column
        email_col = None
        for col in df.columns:
            if 'email' in col.lower() and col not in ['Email.1', 'ID']:
                if df[col].notna().sum() > 0:
                    email_col = col
                    break

        if email_col:
            emails_count = df[email_col].notna().sum()
            unique_count = df[email_col].nunique()

            print(f'   Email column: "{email_col}"')
            print(f'   Total emails: {emails_count}')
            print(f'   Unique emails: {unique_count}')

            # Check if validation data exists
            if 'Result' in df.columns:
                result_counts = df['Result'].value_counts()
                print(f'\n   Validation Results:')
                for result, count in result_counts.items():
                    percentage = (count / len(df)) * 100
                    print(f'     {result:15}: {count:4} ({percentage:5.1f}%)')

                # Usable emails
                usable_results = ['deliverable', 'risky', 'unknown']
                usable = df[df['Result'].isin(usable_results)]
                print(f'\n   >>> USABLE: {len(usable)} ({len(usable)/len(df)*100:.1f}%)')
            else:
                print(f'\n   [WARNING] No validation results found')

            # Collect all emails for deduplication
            file_emails = df[email_col].dropna().unique().tolist()
            all_emails.extend(file_emails)

            file_stats.append({
                'file': filename,
                'total_rows': len(df),
                'total_emails': emails_count,
                'unique_emails': unique_count,
                'usable': len(usable) if 'Result' in df.columns else 0
            })
        else:
            print(f'   [WARNING] No email column found')
            print(f'   Columns: {df.columns.tolist()[:5]}...')

    except Exception as e:
        print(f'   [ERROR] Failed to read file: {str(e)}')

print('\n' + '=' * 90)
print('                              SUMMARY')
print('=' * 90)

if file_stats:
    print(f'\n{"File":<40} {"Rows":<8} {"Emails":<8} {"Unique":<8} {"Usable":<8}')
    print('-' * 90)

    total_rows = 0
    total_emails = 0
    total_unique = 0
    total_usable = 0

    for stat in file_stats:
        print(f"{stat['file']:<40} {stat['total_rows']:<8} {stat['total_emails']:<8} "
              f"{stat['unique_emails']:<8} {stat['usable']:<8}")
        total_rows += stat['total_rows']
        total_emails += stat['total_emails']
        total_unique += stat['unique_emails']
        total_usable += stat['usable']

    print('-' * 90)
    print(f"{'TOTAL':<40} {total_rows:<8} {total_emails:<8} {total_unique:<8} {total_usable:<8}")

    # Global unique across all files
    global_unique = len(set(all_emails))
    duplicates = len(all_emails) - global_unique

    print('\n' + '=' * 90)
    print('                         DEDUPLICATION ANALYSIS')
    print('=' * 90)
    print(f'Total emails across all files: {len(all_emails):,}')
    print(f'Global unique emails: {global_unique:,}')
    print(f'Duplicates removed: {duplicates:,}')
    print(f'Deduplication rate: {(duplicates/len(all_emails)*100):.1f}%')
    print('=' * 90)
else:
    print('\n[ERROR] No files were successfully processed')
