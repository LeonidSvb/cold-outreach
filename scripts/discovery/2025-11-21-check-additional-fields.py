import pandas as pd
import os

print('=' * 100)
print('           CHECKING FOR CITY AND HOMEPAGE_CONTENT IN ALL SOURCES')
print('=' * 100)

# All sources
sources = {
    'AU_Cafes': [
        (r'C:\Users\79818\Downloads\aus client.xlsx', 'AU cafes'),
        (r'C:\Users\79818\Downloads\aus client - AU_cafes2.csv', None),
        (r'C:\Users\79818\Downloads\aus client - AU cafes (1).csv', None),
        (r'C:\Users\79818\Downloads\aus client - AU_Cafes3.csv', None)
    ],
    'AU_Resto': [
        (r'C:\Users\79818\Downloads\aus client.xlsx', 'AU resto'),
        (r'C:\Users\79818\Downloads\aus client - AU_Resto2.csv', None),
        (r'C:\Users\79818\Downloads\aus client - AU resto (3).csv', None)
    ],
    'NZ_Cafes': [
        (r'C:\Users\79818\Downloads\aus client.xlsx', 'NZ cafes'),
        (r'C:\Users\79818\Downloads\aus client - NZ_cafes2 (2).csv', None),
        (r'C:\Users\79818\Downloads\aus client - NZ cafes (4).csv', None)
    ],
    'NZ_Resto': [
        (r'C:\Users\79818\Downloads\aus client.xlsx', 'NZ resto'),
        (r'C:\Users\79818\Downloads\aus client - NZ_resto2.csv', None),
        (r'C:\Users\79818\Downloads\aus client - NZ resto (2).csv', None)
    ],
    'NZ_Accom': [
        (r'C:\Users\79818\Downloads\aus client.xlsx', 'NZ accom'),
        (r'C:\Users\79818\Downloads\aus client - NZ_accom2.csv', None),
        (r'C:\Users\79818\Downloads\aus client - NZ accom (2).csv', None)
    ]
}

def check_fields_in_file(file_path, sheet_name=None):
    """Check if file has city and content fields"""
    try:
        if file_path.endswith('.xlsx') and sheet_name:
            xls = pd.ExcelFile(file_path)
            df = pd.read_excel(xls, sheet_name=sheet_name, nrows=5)
        else:
            try:
                df = pd.read_csv(file_path, nrows=5)
            except:
                df = pd.read_csv(file_path, header=None, nrows=5)

        columns = [str(col).lower() for col in df.columns]

        # Check for city/location fields
        city_fields = [col for col in df.columns if any(x in str(col).lower() for x in ['city', 'location', 'search_city'])]

        # Check for content fields
        content_fields = [col for col in df.columns if any(x in str(col).lower() for x in ['content', 'homepage', 'description'])]

        return {
            'has_city': len(city_fields) > 0,
            'city_fields': city_fields,
            'has_content': len(content_fields) > 0,
            'content_fields': content_fields,
            'total_columns': len(df.columns)
        }
    except Exception as e:
        return {
            'has_city': False,
            'city_fields': [],
            'has_content': False,
            'content_fields': [],
            'error': str(e)
        }

# Check all sources
for niche_name, files in sources.items():
    print(f'\n{"=" * 100}')
    print(f'{niche_name}')
    print(f'{"=" * 100}')

    for file_path, sheet_name in files:
        if not os.path.exists(file_path):
            continue

        filename = sheet_name if sheet_name else os.path.basename(file_path)
        result = check_fields_in_file(file_path, sheet_name)

        print(f'\n{filename}')
        print(f'  Total columns: {result.get("total_columns", 0)}')

        if result.get('has_city'):
            print(f'  City fields: {result["city_fields"]}')
        else:
            print(f'  City fields: None')

        if result.get('has_content'):
            print(f'  Content fields: {result["content_fields"]}')
        else:
            print(f'  Content fields: None')

print('\n' + '=' * 100)
print('                              SUMMARY')
print('=' * 100)

# Summary
summary = {}
for niche_name, files in sources.items():
    has_city_anywhere = False
    has_content_anywhere = False

    for file_path, sheet_name in files:
        if not os.path.exists(file_path):
            continue
        result = check_fields_in_file(file_path, sheet_name)
        if result.get('has_city'):
            has_city_anywhere = True
        if result.get('has_content'):
            has_content_anywhere = True

    summary[niche_name] = {
        'has_city': has_city_anywhere,
        'has_content': has_content_anywhere
    }

print(f'\n{"Niche":<15} {"City Available":<20} {"Content Available"}')
print('-' * 100)
for niche, data in summary.items():
    city_status = 'YES' if data['has_city'] else 'NO'
    content_status = 'YES' if data['has_content'] else 'NO'
    print(f'{niche:<15} {city_status:<20} {content_status}')

print('\n' + '=' * 100)
