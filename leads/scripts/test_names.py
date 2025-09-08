#!/usr/bin/env python3
"""
Автоматический тест сокращателя названий компаний
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from company_name_cleaner import test_csv_sample, analyze_results

def run_test():
    csv_file = r"C:\Users\79818\Desktop\Outreach - new\leads\Lumid - verification - Canada.csv"
    
    print("ITERACIYA #1 - Pervyy test prompta")
    print("="*60)
    
    try:
        results = test_csv_sample(csv_file, 10)
        
        if results:
            score = analyze_results(results)
            
            # Записываем результаты в файл промпта
            update_prompt_with_results(score, results)
        else:
            print("Net rezultatov dlya analiza")
    
    except Exception as e:
        print(f"Oshibka: {e}")

def update_prompt_with_results(score, results):
    """Обновляет файл промпта результатами тестирования"""
    
    prompt_path = r"C:\Users\79818\Desktop\Outreach - new\prompts\company_name_shortener.txt"
    
    # Читаем текущий промпт
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Обновляем метрики
    if '---' in content:
        prompt_part = content.split('---')[0]
        
        # Новые метрики
        new_metrics = f"""---
ИТЕРАЦИЯ: #1
ЭФФЕКТИВНОСТЬ: {score:.1f}/10
МОДЕЛЬ: gpt-3.5-turbo
ТЕМПЕРАТУРА: 0.1
МАКС ТОКЕНЫ: 50
ДАТА ТЕСТА: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}

РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:
{format_test_results(results[:5])}

СТАТУС: {'ГОТОВ' if score >= 9 else 'ТРЕБУЕТ УЛУЧШЕНИЯ'}
"""
    else:
        prompt_part = content
        new_metrics = f"""
---
ИТЕРАЦИЯ: #1
ЭФФЕКТИВНОСТЬ: {score:.1f}/10
МОДЕЛЬ: gpt-3.5-turbo  
ТЕМПЕРАТУРА: 0.1
МАКС ТОКЕНЫ: 50
"""
    
    # Сохраняем обновленный файл
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt_part.strip() + '\n\n' + new_metrics)
    
    print(f"\nObnovlen fayl prompta: {prompt_path}")

def format_test_results(results):
    """Форматирует результаты для записи в файл"""
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"  {i}. '{result['original']}' → '{result['cleaned']}'")
    return '\n'.join(formatted)

if __name__ == "__main__":
    run_test()