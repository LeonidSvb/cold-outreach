#!/usr/bin/env python3
"""
AI Company Name Cleaner - Сокращает названия компаний до разговорной формы
Использует OpenAI для умного сокращения названий
"""

import os
import json
import csv
from datetime import datetime
from openai import OpenAI

def load_api_key():
    """Загружает OpenAI API ключ из .env"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
    
    # Fallback to environment variable
    return os.getenv('OPENAI_API_KEY')

def load_prompt():
    """Загружает dialogue-style промпт и создает структуру для OpenAI"""
    prompt_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'prompts', 'company_name_shortener.txt')
    
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"❌ Файл промпта не найден: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем только промпт (до разделителя ---)
    if '---' in content:
        prompt_content = content.split('---')[0].strip()
    else:
        prompt_content = content.strip()
    
    # Парсим dialogue-style промпт
    lines = prompt_content.split('\n')
    
    system_prompt = ""
    base_messages = []
    
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('SYSTEM_PROMPT:'):
            # Сохраняем предыдущую секцию
            if current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'system'
            current_content = []
        elif line.startswith('USER_INSTRUCTIONS:'):
            if current_section == 'system':
                system_prompt = '\n'.join(current_content).strip()
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'instructions'
            current_content = []
        elif line.startswith('USER_EXAMPLE_'):
            if current_section == 'instructions':
                # Добавляем инструкции как первое user сообщение
                base_messages.append({"role": "user", "content": '\n'.join(current_content).strip()})
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'user_example'
            current_content = []
        elif line.startswith('ASSISTANT_EXAMPLE_'):
            if current_section == 'user_example':
                base_messages.append({"role": "user", "content": '\n'.join(current_content).strip()})
            elif current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            current_section = 'assistant_example'
            current_content = []
        elif line.startswith('USER_REAL_INPUT:'):
            if current_section == 'assistant_example':
                base_messages.append({"role": "assistant", "content": '\n'.join(current_content).strip()})
            break
        elif line and not line.startswith(('SYSTEM_', 'USER_', 'ASSISTANT_')):
            current_content.append(line)
    
    return system_prompt, base_messages

def clean_company_name_ai(company_name, client, prompt_data):
    """Очищает название компании через OpenAI с dialogue-style промптом"""
    
    if not company_name or not company_name.strip():
        return ""
    
    try:
        system_prompt, base_messages = prompt_data
        
        # Создаем полный диалог
        messages = []
        
        # Добавляем system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Добавляем базовые сообщения (инструкции + примеры)
        messages.extend(base_messages)
        
        # Добавляем реальную компанию
        messages.append({"role": "user", "content": company_name})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=messages,
            max_tokens=20,
            temperature=0.1
        )
        
        cleaned_name = response.choices[0].message.content.strip()
        
        # Убираем кавычки и лишние символы
        cleaned_name = cleaned_name.strip('"\'')
        
        # Берем только первое слово/фразу до переноса строки или лишних символов
        if '\n' in cleaned_name:
            cleaned_name = cleaned_name.split('\n')[0]
        if '"' in cleaned_name:
            cleaned_name = cleaned_name.split('"')[0]
        if '→' in cleaned_name:
            cleaned_name = cleaned_name.split('→')[0]
        
        cleaned_name = cleaned_name.strip()
        
        return cleaned_name
        
    except Exception as e:
        print(f"OpenAI Error for '{company_name}': {e}")
        return company_name  # Возвращаем оригинал если ошибка

def process_csv_batch(input_file, batch_size=10, output_file=None):
    """Обрабатывает CSV файл батчами"""
    
    api_key = load_api_key()
    if not api_key:
        print("❌ OpenAI API ключ не найден!")
        return None
    
    client = OpenAI(api_key=api_key)
    prompt_data = load_prompt()
    
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_cleaned{ext}"
    
    results = []
    processed_count = 0
    
    print(f"Processing: {input_file}")
    print(f"Output file: {output_file}")
    print("-" * 50)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        batch = []
        for row in reader:
            batch.append(row)
            
            if len(batch) >= batch_size:
                process_batch(batch, client, prompt_template, results)
                processed_count += len(batch)
                print(f"Processed: {processed_count}")
                batch = []
        
        # Обрабатываем остаток
        if batch:
            process_batch(batch, client, prompt_template, results)
            processed_count += len(batch)
    
    # Сохраняем результаты
    if results:
        save_results(results, output_file)
    
    print(f"\nProcessed {processed_count} companies")
    print(f"Saved to: {output_file}")
    
    return output_file

def process_batch(batch, client, prompt_template, results):
    """Обрабатывает один батч компаний"""
    
    for row in batch:
        original = row.get('company_name', '')
        cleaned = clean_company_name_ai(original, client, prompt_data)
        
        row['cleaned_company_name'] = cleaned
        results.append(row)
        
        print(f"'{original}' -> '{cleaned}'")

def save_results(results, output_file):
    """Сохраняет результаты в CSV"""
    fieldnames = list(results[0].keys())
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def test_examples():
    """Тестирует на примерах"""
    
    api_key = load_api_key()
    if not api_key:
        print("❌ OpenAI API ключ не найден!")
        return
    
    client = OpenAI(api_key=api_key)
    prompt_data = load_prompt()
    
    examples = [
        "Big Fish Creative Inc.",
        "Greenhouse Marketing, Sales & Recruitment", 
        "The Communications Group, Inc.",
        "Altitude Stratégies",
        "Work Party Creative Group",
        "Victory Media Inc."
    ]
    
    print("Тестируем AI сокращатель:")
    print("=" * 60)
    
    results = []
    for company in examples:
        cleaned = clean_company_name_ai(company, client, prompt_template)
        results.append({"original": company, "cleaned": cleaned})
        print(f"'{company}' → '{cleaned}'")
    
    print("=" * 60)
    return results

def test_csv_sample(csv_file, sample_size=10):
    """Тестирует на 10 компаниях из CSV файла"""
    
    api_key = load_api_key()
    if not api_key:
        print("❌ OpenAI API ключ не найден!")
        return []
    
    client = OpenAI(api_key=api_key)
    prompt_data = load_prompt()
    
    print(f"Testing {sample_size} companies from {csv_file}")
    print("=" * 60)
    
    results = []
    with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
                
            original = row.get('company_name', '')
            if not original:
                continue
                
            cleaned = clean_company_name_ai(original, client, prompt_data)
            results.append({
                "original": original,
                "cleaned": cleaned,
                "row_data": row
            })
            
            print(f"{i+1:2d}. '{original}' → '{cleaned}'")
    
    print("=" * 60)
    return results

def analyze_results(results):
    """Анализирует результаты как AI аналитик"""
    
    print("\n" + "="*60)
    print("🔍 АНАЛИЗ РЕЗУЛЬТАТОВ (AI Аналитик)")
    print("="*60)
    
    # Анализируем каждый результат
    issues = []
    good_results = []
    
    for i, result in enumerate(results, 1):
        original = result["original"]
        cleaned = result["cleaned"]
        
        # Проверяем качество сокращения
        if len(cleaned.split()) > 3:
            issues.append(f"#{i} Слишком длинное: '{cleaned}' (>3 слов)")
        elif cleaned.lower().endswith(('inc', 'ltd', 'llc', 'corp', 'co')):
            issues.append(f"#{i} Остались суффиксы: '{cleaned}'")
        elif cleaned == original:
            issues.append(f"#{i} Не изменилось: '{cleaned}'")
        elif not cleaned or cleaned.strip() == "":
            issues.append(f"#{i} Пустой результат для: '{original}'")
        else:
            good_results.append(f"#{i} Хорошо: '{original}' → '{cleaned}'")
    
    # Выводим анализ
    print(f"✅ Хороших результатов: {len(good_results)}/{len(results)}")
    print(f"❌ Проблемных: {len(issues)}/{len(results)}")
    
    if good_results:
        print("\n✅ ХОРОШИЕ РЕЗУЛЬТАТЫ:")
        for good in good_results[:5]:  # Показываем первые 5
            print(f"   {good}")
    
    if issues:
        print("\n❌ ПРОБЛЕМЫ:")
        for issue in issues:
            print(f"   {issue}")
    
    # Рекомендации по улучшению
    print("\n💡 РЕКОМЕНДАЦИИ:")
    
    score = len(good_results) / len(results) * 10
    
    if score < 6:
        print("   - Переписать промпт полностью")
        print("   - Добавить больше примеров")
        print("   - Увеличить температуру до 0.3")
    elif score < 8:
        print("   - Улучшить правила в промпте")
        print("   - Добавить specific examples для проблемных случаев")
        print("   - Может увеличить max_tokens до 60")
    elif score < 9:
        print("   - Мелкие правки в промпте")
        print("   - Добавить 1-2 примера")
    else:
        print("   - Промпт почти идеальный!")
        print("   - Можно попробовать снизить температуру до 0.05")
    
    print(f"\n📊 ОЦЕНКА: {score:.1f}/10")
    print("="*60)
    
    return score

if __name__ == "__main__":
    print("AI Company Name Cleaner - Iterative Improvement")
    print("1 - Тест на примерах")
    print("2 - Тест на CSV файле (10 компаний)")
    print("3 - Обработать весь CSV файл")
    
    choice = input("Выбери (1/2/3): ").strip()
    
    if choice == "1":
        results = test_examples()
        if results:
            analyze_results(results)
    elif choice == "2":
        csv_file = input("Путь к CSV файлу: ").strip()
        if csv_file and os.path.exists(csv_file):
            results = test_csv_sample(csv_file)
            if results:
                score = analyze_results(results)
                print(f"\nДля улучшения отредактируй: prompts/company_name_shortener.txt")
                print(f"Затем запусти заново для следующей итерации")
        else:
            print("Файл не найден!")
    elif choice == "3":
        csv_file = input("Путь к CSV файлу: ").strip()
        if csv_file and os.path.exists(csv_file):
            process_csv_batch(csv_file)
        else:
            print("Файл не найден!")
    else:
        print("Тестируем на примерах:")
        results = test_examples()
        if results:
            analyze_results(results)