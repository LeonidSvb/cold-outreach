import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\apollo\results\call_centers_llm_normalized_20251103_155017.csv')

print("="*80)
print("FINAL STATISTICS - LLM Normalized Dataset")
print("="*80)

print(f"\nTotal companies: {len(df)}")
print(f"Perfect ICP matches (Score=2): {len(df[df['ICP Match Score']==2])}")
print(f"Maybe matches (Score=1): {len(df[df['ICP Match Score']==1])}")
print(f"No match (Score=0): {len(df[df['ICP Match Score']==0])}")

llm_normalized = len(df[df['Normalized Company Name (LLM)'] != ''])
print(f"\nCompanies with LLM normalization: {llm_normalized}")

print(f"\nTotal columns: {len(df.columns)}")

print("\nKey columns for outreach:")
key_cols = [
    "company_name",
    "Normalized Company Name (LLM)",
    "Normalized Location (LLM)",
    "ICP Match Score",
    "email",
    "title",
    "phone_number",
    "linkedin_url"
]
for col in key_cols:
    print(f"  - {col}")

print("\n" + "="*80)
print("FILE LOCATIONS:")
print("="*80)
print("1. Main result: modules/apollo/results/call_centers_llm_normalized_20251103_155017.csv")
print("2. Downloads: C:\\Users\\79818\\Downloads\\call_centers_FINAL_LLM_normalized.csv")
print("3. Documentation: modules/apollo/docs/NORMALIZATION_PATTERNS_ANALYSIS.md")
print("="*80)
