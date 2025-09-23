#!/usr/bin/env python3
"""
Website Intelligence Processor с интеграцией Dashboard
Обновленная версия с автоматическим обновлением dashboard
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к dashboard модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))

# Импорты
from website_intelligence_processor import WebsiteIntelligenceProcessor
from dashboard_manager import save_session_data
from dashboard_generator import generate_dashboard_now

class WebsiteIntelligenceWithDashboard(WebsiteIntelligenceProcessor):
    """Website Intelligence Processor с интеграцией dashboard"""
    
    def __init__(self):
        super().__init__()
        self.dashboard_data = {
            "script_name": "website_intelligence_processor",
            "start_time": time.time(),
            "session_id": f"website_intel_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "detailed_logs": [],
            "environment_info": {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "script_version": "1.1.0"
            }
        }
        
    def log_dashboard_event(self, event_type: str, message: str, data: dict = None):
        """Логирование событий для dashboard"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message,
            "data": data or {}
        }
        self.dashboard_data["detailed_logs"].append(log_entry)
        print(f"[{event_type}] {message}")
        
    def process_domain(self, domain: str):
        """Переопределенный метод с логированием для dashboard"""
        self.log_dashboard_event("DOMAIN_START", f"Начало обработки домена: {domain}")
        
        start_time = time.time()
        result = super().process_domain(domain)
        processing_time = time.time() - start_time
        
        if result:
            self.log_dashboard_event("DOMAIN_SUCCESS", f"Домен обработан успешно за {processing_time:.2f}с", {
                "domain": domain,
                "pages_found": result["total_pages_found"],
                "pages_selected": len(result["selected_pages"]),
                "processing_time": processing_time,
                "cost": result.get("analysis_cost", 0)
            })
        else:
            self.log_dashboard_event("DOMAIN_ERROR", f"Ошибка обработки домена: {domain}", {
                "domain": domain,
                "processing_time": processing_time
            })
            
        return result
    
    def process_csv_file(self, input_file: str, test_limit: int = None):
        """Переопределенный метод с полной интеграцией dashboard"""
        
        self.log_dashboard_event("SESSION_START", f"Начало обработки CSV: {input_file}", {
            "input_file": input_file,
            "test_limit": test_limit
        })
        
        # Запускаем основную обработку
        start_time = time.time()
        output_file = super().process_csv_file(input_file, test_limit)
        total_time = time.time() - start_time
        
        # Получаем финальный отчет
        session_report = self.get_session_report()
        session_summary = session_report["session_summary"]
        
        # Подготавливаем данные для dashboard
        dashboard_session_data = {
            # Основные метрики
            "total_runtime": total_time,
            "success_rate": session_summary["success_rate"],
            "items_processed": session_summary["domains_processed"],
            "total_cost": session_summary["total_cost"],
            "errors": [],
            
            # Детальная производительность
            "performance_metrics": {
                "avg_processing_time": session_summary["average_time_per_domain"],
                "avg_pages_found": session_summary["average_pages_per_domain"],
                "total_pages_discovered": session_summary["total_pages_found"],
                "successful_ai_prioritizations": session_summary["successful_ai_prioritizations"],
                "api_calls_made": session_summary["total_api_calls"]
            },
            
            # Результаты обработки
            "processing_results": [
                {
                    "domain": log["data"]["domain"],
                    "success": log["event_type"] == "DOMAIN_SUCCESS",
                    "processing_time": log["data"]["processing_time"],
                    "pages_found": log["data"].get("pages_found", 0),
                    "pages_selected": log["data"].get("pages_selected", 0),
                    "cost": log["data"].get("cost", 0)
                }
                for log in self.dashboard_data["detailed_logs"] 
                if log["event_type"] in ["DOMAIN_SUCCESS", "DOMAIN_ERROR"] and "domain" in log["data"]
            ],
            
            # Статистика сессии  
            "session_stats": session_summary,
            
            # Детальные логи
            "detailed_logs": self.dashboard_data["detailed_logs"],
            
            # Ошибки (если есть)
            "error_details": [
                log["message"] for log in self.dashboard_data["detailed_logs"] 
                if log["event_type"] == "DOMAIN_ERROR"
            ],
            
            # Конфигурация
            "configuration": {
                "input_file": input_file,
                "output_file": output_file,
                "test_limit": test_limit,
                "parallel_workers": 3,
                "max_pages_per_domain": 50,
                "ai_model": "gpt-3.5-turbo",
                "session_id": self.dashboard_data["session_id"]
            },
            
            # Информация о среде
            "environment_info": self.dashboard_data["environment_info"],
            
            # API вызовы
            "api_calls": [
                {
                    "endpoint": "chat/completions",
                    "calls": session_summary["total_api_calls"],
                    "total_cost": session_summary["total_cost"]
                }
            ],
            
            # Разбивка по времени
            "timing_details": {
                "total_session_time": total_time,
                "avg_per_domain": session_summary["average_time_per_domain"],
                "setup_time": 2.0,  # Приблизительно
                "processing_time": total_time - 2.0,
                "cleanup_time": 0.5
            },
            
            # Метрики качества
            "quality_metrics": {
                "domains_processed": session_summary["domains_processed"],
                "success_rate": session_summary["success_rate"],
                "ai_success_rate": (session_summary["successful_ai_prioritizations"] / max(session_summary["domains_processed"], 1)) * 100,
                "avg_pages_quality": session_summary["average_pages_per_domain"],
                "cost_efficiency": session_summary["total_cost"] / max(session_summary["domains_processed"], 1)
            },
            
            # Сырые результаты (последние несколько для примера)
            "raw_results": self.dashboard_data["detailed_logs"][-10:]  # Последние 10 записей
        }
        
        self.log_dashboard_event("SESSION_COMPLETE", f"Сессия завершена. Обработано: {session_summary['domains_processed']} доменов", {
            "total_time": total_time,
            "success_rate": session_summary["success_rate"],
            "output_file": output_file
        })
        
        # Сохраняем данные в dashboard
        session_id = save_session_data("website_intelligence_processor", dashboard_session_data)
        
        # Генерируем обновленный dashboard
        dashboard_file = generate_dashboard_now()
        
        self.log_dashboard_event("DASHBOARD_UPDATED", f"Dashboard обновлен: {dashboard_file}")
        
        print(f"\nСЕССИЯ ЗАВЕРШЕНА!")
        print(f"Данные сохранены в dashboard: {session_id}")
        print(f"Откройте dashboard: {dashboard_file}")
        print(f"Результаты CSV: {output_file}")
        
        return output_file

def main():
    """Основная функция с интеграцией dashboard"""
    processor = WebsiteIntelligenceWithDashboard()
    
    # Обработка с первыми 3 доменами для демонстрации
    input_file = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    
    try:
        output_file = processor.process_csv_file(input_file, test_limit=3)
        
        print(f"\n{'='*80}")
        print("ФИНАЛЬНЫЙ ОТЧЕТ С DASHBOARD ИНТЕГРАЦИЕЙ")
        print(f"{'='*80}")
        
        session_report = processor.get_session_report()
        session = session_report["session_summary"]
        
        print(f"Домены обработаны: {session['domains_processed']}")
        print(f"Всего страниц найдено: {session['total_pages_found']}")
        print(f"Среднее количество страниц: {session['average_pages_per_domain']}")
        print(f"AI приоритизаций успешно: {session['successful_ai_prioritizations']}")
        print(f"Процент успеха: {session['success_rate']}%")
        print(f"Общая стоимость: ${session['total_cost']}")
        print(f"Общее время: {session['total_runtime']}с")
        print(f"Среднее время на домен: {session['average_time_per_domain']}с")
        print(f"Выходной файл: {output_file}")
        
        print(f"\nDashboard доступен в папке: dashboard/index.html")
        print(f"Dashboard автоматически обновляется после каждого запуска")
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()