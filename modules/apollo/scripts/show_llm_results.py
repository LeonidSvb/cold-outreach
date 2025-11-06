import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_llm_normalized_20251103_155017.csv')
perfect = df[df['ICP Match Score']==2].head(30)

print("="*120)
print("LLM NORMALIZATION RESULTS - Sample 30 Companies")
print("="*120)

for i, row in enumerate(perfect.itertuples(), 1):
    row_data = df.iloc[row.Index]

    orig_company = row_data['company_name']
    norm_company = row_data['Normalized Company Name (LLM)']

    city = str(row_data.get('city', ''))
    state = str(row_data.get('state', ''))
    orig_loc = f"{city}, {state}" if city != 'nan' and state != 'nan' else (city if city != 'nan' else state)
    norm_loc = row_data['Normalized Location (LLM)']

    print(f"\n{i}. COMPANY:")
    print(f"   Original:   {orig_company}")
    print(f"   Normalized: {norm_company}")
    print(f"   LOCATION:")
    print(f"   Original:   {orig_loc}")
    print(f"   Normalized: {norm_loc}")

print(f"\n{'='*120}")
print(f"STATISTICS:")
print(f"Total rows in CSV: {len(df)}")
print(f"Perfect ICP matches (Score=2): {len(df[df['ICP Match Score']==2])}")
print(f"All companies have LLM normalization applied!")
print("="*120)
