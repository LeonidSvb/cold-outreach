import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\email_verification\results\US_1900_DELIVERABLE_20251116_153306.csv', encoding='utf-8-sig')

print('=== SAMPLE DATA WITH ICEBREAKERS ===\n')

sample = df[['name', 'website', 'city', 'state', 'niche', 'rating', 'reviews', 'business_summary', 'icebreaker']].head(15)

for idx, row in sample.iterrows():
    print(f'Company: {row["name"]}')
    print(f'Website: {row["website"]}')
    print(f'Location: {row["city"]}, {row["state"]}')
    print(f'Niche: {row["niche"]}')
    print(f'Rating: {row["rating"]} ({row["reviews"]} reviews)')
    print(f'Summary: {row["business_summary"][:100]}...')
    print(f'ICEBREAKER: {row["icebreaker"]}')
    print('-'*80)
    print()
