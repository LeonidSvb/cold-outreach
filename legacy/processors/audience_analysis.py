#!/usr/bin/env python3
"""
Анализ целевой аудитории канадских маркетинговых агентств
"""

import csv
import pandas as pd
from collections import Counter
import json

def analyze_audience(csv_path):
    """Анализ данных целевой аудитории"""
    print("Анализ канадской аудитории маркетинговых агентств")
    print("=" * 60)
    
    # Загрузка данных
    try:
        df = pd.read_csv(csv_path)
        print(f"Всего записей: {len(df)}")
        print()
        
        # Анализ размеров компаний
        print("1. РАЗМЕРЫ КОМПАНИЙ:")
        print("-" * 30)
        company_sizes = df['estimated_num_employees'].dropna()
        print(f"Средний размер компании: {company_sizes.mean():.1f} сотрудников")
        print(f"Медианный размер: {company_sizes.median():.0f} сотрудников")
        
        # Категоризация по размерам
        def categorize_size(size):
            if pd.isna(size):
                return "Неизвестно"
            elif size <= 10:
                return "Малые (1-10)"
            elif size <= 20:
                return "Средние (11-20)"
            elif size <= 50:
                return "Крупные (21-50)"
            else:
                return "Очень крупные (50+)"
        
        df['size_category'] = df['estimated_num_employees'].apply(categorize_size)
        size_distribution = df['size_category'].value_counts()
        
        for category, count in size_distribution.items():
            percentage = (count / len(df)) * 100
            print(f"{category}: {count} компаний ({percentage:.1f}%)")
        print()
        
        # Анализ должностей/сениорности
        print("2. УРОВНИ ПРИНЯТИЯ РЕШЕНИЙ:")
        print("-" * 30)
        seniority_counts = df['seniority'].value_counts()
        
        decision_maker_mapping = {
            'c_suite': 'CEO/CTO/COO (Высший)',
            'founder': 'Основатель (Высший)',
            'owner': 'Владелец (Высший)', 
            'partner': 'Партнер (Высший)',
            'president': 'Президент (Высший)',
            'vp': 'Вице-президент (Средний)',
            'director': 'Директор (Средний)',
            'head': 'Руководитель (Средний)',
            'manager': 'Менеджер (Низкий)',
            'entry': 'Начальный (Низкий)'
        }
        
        for seniority, count in seniority_counts.items():
            percentage = (count / len(df)) * 100
            level = decision_maker_mapping.get(seniority, seniority)
            print(f"{level}: {count} контактов ({percentage:.1f}%)")
        print()
        
        # Географический анализ
        print("3. ГЕОГРАФИЯ (ТОП ПРОВИНЦИИ):")
        print("-" * 30)
        provinces = df['state'].value_counts().head(10)
        
        for province, count in provinces.items():
            percentage = (count / len(df)) * 100
            print(f"{province}: {count} компаний ({percentage:.1f}%)")
        print()
        
        # Анализ типов компаний
        print("4. ТИПЫ КОМПАНИЙ (по названию):")
        print("-" * 30)
        
        # Классификация по ключевым словам в названиях
        company_types = {
            'Цифровой маркетинг': ['digital', 'seo', 'online', 'web'],
            'Креатив/Дизайн': ['creative', 'design', 'brand', 'advertising'],
            'Медиа/Коммуникации': ['media', 'communications', 'group', 'agency'],
            'Консалтинг': ['consulting', 'strategies', 'solutions'],
            'Продакшн': ['production', 'film', 'video']
        }
        
        type_counts = {}
        for company_type, keywords in company_types.items():
            count = 0
            for _, row in df.iterrows():
                company_name = str(row['company_name']).lower()
                if any(keyword in company_name for keyword in keywords):
                    count += 1
            type_counts[company_type] = count
        
        for company_type, count in type_counts.items():
            percentage = (count / len(df)) * 100
            print(f"{company_type}: {count} компаний ({percentage:.1f}%)")
        print()
        
        # Анализ контактной информации
        print("5. КАЧЕСТВО КОНТАКТНЫХ ДАННЫХ:")
        print("-" * 30)
        verified_emails = df['email_status'].value_counts()
        phone_available = df['phone_number'].notna().sum()
        
        for status, count in verified_emails.items():
            percentage = (count / len(df)) * 100
            print(f"Email {status}: {count} ({percentage:.1f}%)")
        
        print(f"Телефоны доступны: {phone_available} ({(phone_available/len(df))*100:.1f}%)")
        print()
        
        # Топ города
        print("6. ТОП ГОРОДА:")
        print("-" * 30)
        cities = df['city'].value_counts().head(8)
        for city, count in cities.items():
            percentage = (count / len(df)) * 100
            print(f"{city}: {count} компаний ({percentage:.1f}%)")
        
        return {
            'total_records': len(df),
            'avg_company_size': company_sizes.mean(),
            'size_distribution': size_distribution.to_dict(),
            'seniority_distribution': seniority_counts.to_dict(),
            'top_provinces': provinces.head(5).to_dict(),
            'company_types': type_counts,
            'verified_emails': verified_emails.to_dict()
        }
        
    except Exception as e:
        print(f"Ошибка при анализе: {e}")
        return None

if __name__ == "__main__":
    csv_path = "../../leads/raw/lumid_canada_20250108.csv"
    results = analyze_audience(csv_path)