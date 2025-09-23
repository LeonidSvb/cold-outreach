import pandas as pd
import numpy as np

# Загружаем данные
file_path = r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.csv"
df = pd.read_csv(file_path)

print("=== АНАЛИЗ БАЗЫ ЛИДОВ ===")
print(f"Общее количество записей: {len(df)}")
print()

# 1. АНАЛИЗ РАЗМЕРА КОМПАНИЙ
print("=== 1. РАСПРЕДЕЛЕНИЕ ПО РАЗМЕРУ КОМПАНИЙ ===")
print("Размеры компаний (количество сотрудников):")

# Создаем категории размеров
def categorize_company_size(employees):
    if pd.isna(employees) or employees == 0:
        return "Неизвестно"
    elif employees <= 10:
        return "Микро (1-10)"
    elif employees <= 50:
        return "Малая (11-50)"
    elif employees <= 200:
        return "Средняя (51-200)"
    elif employees <= 1000:
        return "Большая (201-1000)"
    else:
        return "Корпорация (1000+)"

df['company_size_category'] = df['estimated_num_employees'].apply(categorize_company_size)
size_distribution = df['company_size_category'].value_counts()
print(size_distribution)
print()

# 2. ГЕОГРАФИЧЕСКОЕ РАСПРЕДЕЛЕНИЕ
print("=== 2. ГЕОГРАФИЧЕСКОЕ РАСПРЕДЕЛЕНИЕ ===")
country_dist = df['country'].value_counts()
print("По странам:")
print(country_dist)
print()

if 'United States' in country_dist.index:
    us_data = df[df['country'] == 'United States']
    state_dist = us_data['state'].value_counts().head(10)
    print("Топ-10 штатов США:")
    print(state_dist)
    print()

# 3. ОТРАСЛЕВОЕ РАСПРЕДЕЛЕНИЕ
print("=== 3. ОТРАСЛЕВОЕ РАСПРЕДЕЛЕНИЕ ===")
industry_dist = df['industry'].value_counts().head(10)
print("Топ-10 индустрий:")
print(industry_dist)
print()

# 4. КАЧЕСТВО ЛИДОВ
print("=== 4. КАЧЕСТВО ЛИДОВ ===")
email_status_dist = df['email_status'].value_counts()
print("Статус email:")
print(email_status_dist)
print()

engage_dist = df['is_likely_to_engage'].value_counts()
print("Вероятность отклика:")
print(engage_dist)
print()

# 5. СЕНИОРНОСТЬ
print("=== 5. УРОВНИ СЕНИОРНОСТИ ===")
seniority_dist = df['seniority'].value_counts()
print("Распределение по сениорности:")
print(seniority_dist)
print()

# 6. РАСЧЕТЫ ДЛЯ СЕГМЕНТАЦИИ
print("=== 6. РЕКОМЕНДАЦИИ ПО СЕГМЕНТАЦИИ ===")
total_leads = len(df)
segment_size_250 = total_leads // 250
remainder_250 = total_leads % 250

segment_size_300 = total_leads // 300
remainder_300 = total_leads % 300

print(f"При сегментах по 250 лидов: {segment_size_250} полных сегментов + {remainder_250} в последнем")
print(f"При сегментах по 300 лидов: {segment_size_300} полных сегментов + {remainder_300} в последнем")
print()

# 7. КАЧЕСТВЕННАЯ СЕГМЕНТАЦИЯ
print("=== 7. АНАЛИЗ ДЛЯ КАЧЕСТВЕННОЙ СЕГМЕНТАЦИИ ===")

# Комбинированный анализ: размер + индустрия
high_quality = df[
    (df['email_status'] == 'verified') &
    (df['is_likely_to_engage'] == True)
]

print(f"Высококачественных лидов (verified email + likely to engage): {len(high_quality)}")

# Микро-сегментация по размеру и отрасли
marketing_agencies = df[df['industry'] == 'marketing & advertising']
print(f"Маркетинговых агентств: {len(marketing_agencies)}")

small_companies = df[df['estimated_num_employees'] <= 50]
medium_companies = df[(df['estimated_num_employees'] > 50) & (df['estimated_num_employees'] <= 200)]
large_companies = df[df['estimated_num_employees'] > 200]

print(f"Малые компании (≤50): {len(small_companies)}")
print(f"Средние компании (51-200): {len(medium_companies)}")
print(f"Крупные компании (>200): {len(large_companies)}")