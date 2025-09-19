#!/usr/bin/env python3
"""
Dashboard Generator - Создание HTML dashboard файла с актуальными данными
"""

import os
import json
import shutil
from datetime import datetime
from dashboard_manager import DashboardManager

class DashboardGenerator:
    """Генератор готового HTML dashboard файла"""
    
    def __init__(self):
        self.dashboard_manager = DashboardManager()
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'dashboard')
        
        # Создаем выходную папку
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_dashboard(self) -> str:
        """
        Генерирует готовый HTML dashboard файл с встроенными данными
        
        Returns:
            str: Путь к сгенерированному dashboard файлу
        """
        
        print("Генерация Dashboard...")
        
        # Получаем актуальные данные
        dashboard_data = self.dashboard_manager.get_dashboard_data()
        
        # Читаем HTML template
        template_path = os.path.join(self.templates_dir, 'dashboard.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Вставляем данные прямо в HTML как JavaScript переменную
        data_json = json.dumps(dashboard_data, ensure_ascii=False, indent=2)
        
        # Заменяем загрузку данных через fetch на прямое встраивание
        fetch_replacement = f"""
            // Встроенные данные dashboard (обновлено {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            dashboardData = {data_json};
            renderDashboard();
        """
        
        # Заменяем асинхронную загрузку на синхронную
        html_content = html_content.replace(
            'loadDashboardData();',
            fetch_replacement
        )
        
        # Убираем функцию loadDashboardData так как данные уже встроены
        html_content = html_content.replace(
            '''async function loadDashboardData() {
            try {
                showLoading();
                
                // Симулируем загрузку данных (в реальности данные загружаются из JSON файлов)
                const response = await fetch('data/dashboard_data.json');
                if (!response.ok) {
                    throw new Error('Не удалось загрузить данные dashboard');
                }
                
                dashboardData = await response.json();
                renderDashboard();
                
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
                showError('Не удалось загрузить данные dashboard. Проверьте наличие файла data/dashboard_data.json');
            }
        }''',
            '''function loadDashboardData() {
            // Данные уже встроены в HTML
            renderDashboard();
        }'''
        )
        
        # Сохраняем готовый dashboard
        output_file = os.path.join(self.output_dir, 'index.html')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Создаем краткий README
        readme_path = os.path.join(self.output_dir, 'README.md')
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"""# Cold Outreach Analytics Dashboard

## Быстрый старт
Откройте `index.html` в браузере для просмотра аналитики.

## Обновление данных
Dashboard автоматически обновляется при каждом запуске скрипта.

Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Структура данных
- Последние 5 запусков: максимальная детализация
- Старые запуски: краткая сводка  
- Общая статистика и тренды
- Инсайты и рекомендации

## Особенности
✅ Автономная работа (не требует сервера)
✅ Встроенные данные (быстрая загрузка)
✅ Адаптивный дизайн
✅ Интерактивная детализация
✅ Автообновление каждые 30 секунд
""")
        
        print(f"Dashboard сгенерирован: {output_file}")
        print(f"README создан: {readme_path}")
        print(f"Откройте {output_file} в браузере")
        
        return output_file
    
    def create_sample_data(self):
        """Создает пример данных для тестирования dashboard"""
        
        # Создаем тестовые данные на основе наших реальных результатов
        sample_sessions = [
            {
                "session_id": "website_intel_20250910_140558",
                "script_name": "website_intelligence_processor",
                "timestamp": "2025-09-10T14:05:58",
                "date": "2025-09-10",
                "time": "14:05:58",
                "summary": {
                    "duration": 223.6,
                    "success_rate": 100.0,
                    "items_processed": 3,
                    "api_cost": 0.0041,
                    "errors_count": 0,
                    "status": "completed"
                },
                "detailed_data": {
                    "performance_metrics": {
                        "avg_processing_time": 74.5,
                        "avg_pages_found": 33.7,
                        "avg_pages_selected": 2.7
                    },
                    "processing_results": [
                        {
                            "company": "Altitude",
                            "domain": "altitudestrategies.ca", 
                            "pages_found": 1,
                            "pages_selected": 1,
                            "processing_time": 9.1
                        },
                        {
                            "company": "Big Fish Creative",
                            "domain": "bigfishcreative.ca",
                            "pages_found": 50, 
                            "pages_selected": 4,
                            "processing_time": 163.3
                        },
                        {
                            "company": "Stryve Digital Marketing",
                            "domain": "stryvemarketing.com",
                            "pages_found": 50,
                            "pages_selected": 3,
                            "processing_time": 51.3
                        }
                    ],
                    "quality_metrics": {
                        "discovery_success_rate": 100,
                        "ai_selection_success_rate": 0,  # AI упал, использовался fallback
                        "avg_relevance_score": 8.5
                    },
                    "api_calls_breakdown": [
                        {"endpoint": "chat/completions", "calls": 3, "tokens": 1247, "cost": 0.0041}
                    ],
                    "timing_breakdown": {
                        "discovery_phase": 45.2,
                        "ai_analysis_phase": 12.8,
                        "processing_phase": 165.6
                    },
                    "configuration": {
                        "max_pages_per_domain": 50,
                        "ai_model": "gpt-3.5-turbo",
                        "parallel_workers": 3,
                        "timeout": 10
                    }
                },
                "detail_level": "maximum",
                "position": 1,
                "is_recent": True
            }
        ]
        
        # Создаем агрегированные метрики
        aggregated = {
            "overview": {
                "total_scripts_run": 1,
                "total_companies_processed": 3,
                "total_api_cost": 0.0041,
                "total_processing_time": 223.6,
                "average_success_rate": 100.0,
                "most_used_script": "website_intelligence_processor"
            },
            "by_script": {
                "website_intelligence_processor": {
                    "total_runs": 1,
                    "total_items": 3,
                    "total_cost": 0.0041,
                    "total_time": 223.6,
                    "avg_success_rate": 100.0,
                    "last_run": "2025-09-10T14:05:58"
                }
            },
            "trends": {
                "daily_activity": [
                    {
                        "date": "2025-09-10",
                        "sessions_count": 1,
                        "items_processed": 3,
                        "total_cost": 0.0041,
                        "scripts": ["website_intelligence_processor"]
                    }
                ]
            }
        }
        
        # Создаем инсайты
        insights = {
            "performance_alerts": [],
            "recommendations": [
                {
                    "priority": "medium",
                    "message": "AI приоритизация упала в резерв. Проверить настройки OpenAI API.",
                    "action": "Проверить API ключ и доступность модели gpt-3.5-turbo"
                }
            ],
            "cost_optimization": [
                {
                    "type": "efficiency",
                    "message": "Отличная эффективность: $0.0014 на домен при 100% успешности",
                    "current": 0.0041,
                    "projection": "Полная обработка 735 доменов: ~$1.00"
                }
            ]
        }
        
        # Создаем полные данные dashboard
        sample_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_sessions": 1,
                "first_session": "2025-09-10T14:05:58",
                "dashboard_version": "1.0.0"
            },
            "current_session": sample_sessions[0],
            "recent_sessions": {
                "count": 1,
                "detail_level": "maximum", 
                "sessions": sample_sessions
            },
            "older_sessions": {
                "count": 0,
                "detail_level": "brief",
                "sessions": []
            },
            "aggregated_metrics": aggregated,
            "insights": insights
        }
        
        # Сохраняем тестовые данные для отладки
        sample_file = os.path.join(self.data_dir, 'sample_dashboard_data.json')
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        
        print(f"Пример данных создан: {sample_file}")
        return sample_data

def generate_dashboard_now():
    """Быстрая функция для генерации dashboard"""
    generator = DashboardGenerator()
    
    # Создаем тестовые данные если нет реальных
    if not os.path.exists(generator.dashboard_manager.sessions_file):
        print("Нет реальных данных сессий. Создаем тестовые данные...")
        sample_data = generator.create_sample_data()
        
        # Сохраняем как реальную сессию
        generator.dashboard_manager.save_session(
            "website_intelligence_processor",
            {
                "total_runtime": 223.6,
                "success_rate": 100.0,
                "items_processed": 3,
                "total_cost": 0.0041,
                "errors": [],
                "performance_metrics": sample_data["current_session"]["detailed_data"]["performance_metrics"],
                "processing_results": sample_data["current_session"]["detailed_data"]["processing_results"],
                "session_stats": {},
                "detailed_logs": [],
                "configuration": sample_data["current_session"]["detailed_data"]["configuration"],
                "api_calls": sample_data["current_session"]["detailed_data"]["api_calls_breakdown"],
                "timing_details": sample_data["current_session"]["detailed_data"]["timing_breakdown"],
                "quality_metrics": sample_data["current_session"]["detailed_data"]["quality_metrics"],
                "raw_results": []
            }
        )
    
    # Генерируем dashboard
    return generator.generate_dashboard()

if __name__ == "__main__":
    dashboard_file = generate_dashboard_now()
    print(f"\nDashboard готов!")
    print(f"Откройте файл: {dashboard_file}")
    print(f"Или используйте: file:///{dashboard_file.replace(chr(92), '/')}")
    