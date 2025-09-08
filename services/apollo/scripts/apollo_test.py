import requests
import json
from dotenv import load_dotenv
import os

# Загружаем переменные окружения
load_dotenv()

API_KEY = os.getenv('APOLLO_API_KEY')
BASE_URL = "https://api.apollo.io/v1"

def test_apollo_connection():
    """Простой тест подключения к Apollo API"""
    print("🔍 Тестируем подключение к Apollo API...")
    
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'X-Api-Key': API_KEY
    }
    
    # Простой запрос поиска организаций
    data = {
        'q_organization_name': 'tesla',  # Поиск Tesla
        'page': 1,
        'per_page': 5  # Только 5 результатов для теста
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mixed_companies/search",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Подключение успешно!")
            print(f"📊 Найдено компаний: {len(result.get('organizations', []))}")
            
            # Показываем первые результаты
            for org in result.get('organizations', [])[:3]:
                print(f"🏢 {org.get('name', 'N/A')}")
                print(f"   Домен: {org.get('website_url', 'N/A')}")
                print(f"   LinkedIn: {org.get('linkedin_url', 'N/A')}")
                print(f"   Индустрия: {org.get('industry', 'N/A')}")
                print(f"   Размер: {org.get('estimated_num_employees', 'N/A')} сотрудников")
                print("---")
                
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

def test_people_search():
    """Простой тест поиска людей"""
    print("\n👥 Тестируем поиск людей...")
    
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'X-Api-Key': API_KEY
    }
    
    data = {
        'q_organization_name': 'microsoft',
        'person_titles': ['CEO', 'CTO', 'VP'],
        'page': 1,
        'per_page': 3
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mixed_people/search",
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Поиск людей успешен!")
            print(f"📊 Найдено людей: {len(result.get('people', []))}")
            
            for person in result.get('people', [])[:3]:
                print(f"👤 {person.get('first_name', '')} {person.get('last_name', '')}")
                print(f"   Должность: {person.get('title', 'N/A')}")
                print(f"   Компания: {person.get('organization', {}).get('name', 'N/A')}")
                print(f"   LinkedIn: {person.get('linkedin_url', 'N/A')}")
                print("---")
                
        else:
            print(f"❌ Ошибка поиска людей: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Apollo API ключ не найден в .env файле")
    else:
        test_apollo_connection()
        test_people_search()