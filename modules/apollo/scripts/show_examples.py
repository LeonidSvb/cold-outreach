import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_processed_20251103_143944.csv')

print("=== NORMALIZATION EXAMPLES ===\n")
examples = df[df['ICP Match Score']==2].head(8)

print(f"{'Original Company Name':<45} -> {'Normalized':<30} | Location")
print("="*110)

for i, row in examples.iterrows():
    orig_name = str(row.get('company_name', 'N/A'))[:42]
    norm_name = str(row.get('Normalized Company Name', 'N/A'))[:28]
    city = str(row.get('city', ''))
    state = str(row.get('state', ''))
    norm_loc = str(row.get('Normalized Location', 'N/A'))

    orig_loc = f"{city}, {state}" if city != 'nan' and state != 'nan' else (city if city != 'nan' else state)

    print(f"{orig_name:<45} -> {norm_name:<30} | {orig_loc} -> {norm_loc}")
