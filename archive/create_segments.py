import pandas as pd
import json
from datetime import datetime

# Загружаем данные
csv_file = r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.csv"
df = pd.read_csv(csv_file)

# Создаем категории размеров
def categorize_company_size(employees):
    if pd.isna(employees) or employees == 0:
        return "Unknown"
    elif employees <= 10:
        return "Micro"
    elif employees <= 50:
        return "Small"
    else:
        return "Enterprise"

df['company_size_category'] = df['estimated_num_employees'].apply(categorize_company_size)

# Готовим структуру JSON
segments_data = {
    "metadata": {
        "source_file": "ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.csv",
        "created_date": "2025-01-19",
        "description": "Segmentation based on company size + seniority level. Micro companies (1-10 employees) get different approach than small companies (11-50 employees). Target segment size: ~200-250 leads for optimal A/B testing.",
        "segmentation_logic": {
            "strategy": "Company Size + Seniority",
            "micro_companies": "1-10 employees - focus on affordable solutions, quick setup",
            "small_companies": "11-50 employees - focus on scaling, automation, team growth",
            "enterprise": "51+ employees - VIP treatment, custom solutions",
            "segment_target_size": "200-250 leads"
        },
        "total_leads": len(df),
        "segments_count": 0
    },
    "segments": {}
}

# Сегментируем лиды
segments = {}

# 1. MICRO COMPANIES (1-10 employees)
micro_data = df[(df['company_size_category'] == 'Micro') &
                (df['seniority'].isin(['founder', 'owner']))].copy()

if len(micro_data) > 0:
    # Разбиваем на 2 сегмента
    mid_point = len(micro_data) // 2

    segments['micro_founders_01'] = {
        "description": "Founders & Owners in micro companies (1-10 employees) - Part 1",
        "criteria": "company_size: 1-10, seniority: founder/owner",
        "count": mid_point,
        "leads": micro_data.iloc[:mid_point].to_dict('records')
    }

    segments['micro_founders_02'] = {
        "description": "Founders & Owners in micro companies (1-10 employees) - Part 2",
        "criteria": "company_size: 1-10, seniority: founder/owner",
        "count": len(micro_data) - mid_point,
        "leads": micro_data.iloc[mid_point:].to_dict('records')
    }

# 2. SMALL COMPANIES (11-50 employees)
small_data = df[df['company_size_category'] == 'Small'].copy()

if len(small_data) > 0:
    # Разбиваем по сениорности
    founders = small_data[small_data['seniority'] == 'founder'].copy()
    owners = small_data[small_data['seniority'] == 'owner'].copy()
    csuite = small_data[small_data['seniority'].isin(['c_suite', 'vp', 'director'])].copy()

    # Founders
    if len(founders) > 250:
        mid_founders = len(founders) // 2
        segments['small_founders_01'] = {
            "description": "Founders in small companies (11-50 employees) - Part 1",
            "criteria": "company_size: 11-50, seniority: founder",
            "count": mid_founders,
            "leads": founders.iloc[:mid_founders].to_dict('records')
        }
        segments['small_founders_02'] = {
            "description": "Founders in small companies (11-50 employees) - Part 2",
            "criteria": "company_size: 11-50, seniority: founder",
            "count": len(founders) - mid_founders,
            "leads": founders.iloc[mid_founders:].to_dict('records')
        }
    else:
        segments['small_founders'] = {
            "description": "Founders in small companies (11-50 employees)",
            "criteria": "company_size: 11-50, seniority: founder",
            "count": len(founders),
            "leads": founders.to_dict('records')
        }

    # Owners
    if len(owners) > 250:
        mid_owners = len(owners) // 2
        segments['small_owners_01'] = {
            "description": "Owners in small companies (11-50 employees) - Part 1",
            "criteria": "company_size: 11-50, seniority: owner",
            "count": mid_owners,
            "leads": owners.iloc[:mid_owners].to_dict('records')
        }
        segments['small_owners_02'] = {
            "description": "Owners in small companies (11-50 employees) - Part 2",
            "criteria": "company_size: 11-50, seniority: owner",
            "count": len(owners) - mid_owners,
            "leads": owners.iloc[mid_owners:].to_dict('records')
        }
    else:
        segments['small_owners'] = {
            "description": "Owners in small companies (11-50 employees)",
            "criteria": "company_size: 11-50, seniority: owner",
            "count": len(owners),
            "leads": owners.to_dict('records')
        }

    # C-suite
    if len(csuite) > 0:
        segments['small_csuite'] = {
            "description": "C-suite in small companies (11-50 employees)",
            "criteria": "company_size: 11-50, seniority: c_suite/vp/director",
            "count": len(csuite),
            "leads": csuite.to_dict('records')
        }

# 3. ENTERPRISE (51+ employees)
enterprise_data = df[df['company_size_category'] == 'Enterprise'].copy()

if len(enterprise_data) > 0:
    segments['vip_enterprise'] = {
        "description": "All enterprise companies (51+ employees) - VIP segment",
        "criteria": "company_size: 51+, all seniority levels",
        "count": len(enterprise_data),
        "leads": enterprise_data.to_dict('records')
    }

# Обновляем метаданные
segments_data["segments"] = segments
segments_data["metadata"]["segments_count"] = len(segments)

# Сохраняем JSON
output_file = r"C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(segments_data, f, indent=2, ensure_ascii=False)

print(f"Создан файл: {output_file}")
print(f"Всего сегментов: {len(segments)}")
for seg_name, seg_data in segments.items():
    print(f"   - {seg_name}: {seg_data['count']} лидов")