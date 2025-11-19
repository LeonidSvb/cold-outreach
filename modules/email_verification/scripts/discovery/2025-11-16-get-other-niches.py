import pandas as pd

df = pd.read_csv(r'C:\Users\79818\Desktop\Outreach - new\modules\email_verification\results\US_1900_DELIVERABLE_20251116_153306.csv', encoding='utf-8-sig')

# Get different niches
other = df[df['niche'] != 'electricians'][['name', 'website', 'niche']].head(6)
print(other.to_string(index=False))
