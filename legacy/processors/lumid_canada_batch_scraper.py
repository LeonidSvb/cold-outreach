#!/usr/bin/env python3
"""
Lumid Canada Batch Website Intelligence Scraper
Массовый скрейпинг первых 50 сайтов из lumid_canada_20250108.csv
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime

# Добавляем путь к dashboard модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))

# Импорты
from website_intelligence_with_dashboard import WebsiteIntelligenceWithDashboard

SCRIPT_STATS = {
    "script_name": "lumid_canada_batch_scraper",
    "version": "1.0.0",
    "purpose": "Массовый скрейпинг первых 50 сайтов из lumid_canada_20250108.csv для персонализации",
    "total_runs": 0,
    "success_count": 0,
    "error_count": 0,
    "last_run": None,
    "avg_processing_time": 0,
    "improvements": [
        "v1.0.0 - Создание скрипта для батч-обработки lumid данных",
        "Интеграция с dashboard системой",
        "HTTP-только скрейпинг согласно требованиям проекта"
    ]
}

class LumidCanadaBatchScraper:
    """Батч-скрейпер для канадских компаний Lumid"""
    
    def __init__(self):
        self.processor = WebsiteIntelligenceWithDashboard()
        self.start_time = time.time()
        self.session_id = f"lumid_canada_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def prepare_batch_file(self, input_file: str, batch_size: int = 50) -> str:
        """Подготавливает CSV файл с первыми batch_size записями"""
        print(f"Подготовка батча из первых {batch_size} записей...")
        
        # Читаем исходный файл
        df = pd.read_csv(input_file)
        print(f"Исходный файл содержит {len(df)} записей")
        
        # Берем первые batch_size записей с валидными доменами
        valid_domains = df[df['company_domain'].notna() & (df['company_domain'] != '')]
        batch_df = valid_domains.head(batch_size)
        
        print(f"Отобрано {len(batch_df)} записей с валидными доменами")
        
        # Сохраняем батч-файл
        batch_filename = f"lumid_canada_batch50_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        batch_file_path = os.path.join(os.path.dirname(input_file), batch_filename)
        batch_df.to_csv(batch_file_path, index=False)
        
        print(f"Батч-файл создан: {batch_file_path}")
        return batch_file_path
        
    def process_batch(self, input_file: str, batch_size: int = 50):
        """Основной метод обработки батча"""
        print(f"\n{'='*80}")
        print("LUMID CANADA BATCH SCRAPER - ЗАПУСК")
        print(f"{'='*80}")
        print(f"Входной файл: {input_file}")
        print(f"Размер батча: {batch_size}")
        print(f"Session ID: {self.session_id}")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        try:
            # Подготавливаем батч-файл
            batch_file = self.prepare_batch_file(input_file, batch_size)
            
            # Запускаем обработку всего батча (без лимита test_limit)
            print(f"\nЗАПУСК МАССОВОГО СКРЕЙПИНГА...")
            print(f"Обработка всех {batch_size} сайтов...")
            
            output_file = self.processor.process_csv_file(batch_file, test_limit=None)
            
            # Получаем финальную статистику
            session_report = self.processor.get_session_report()
            session_summary = session_report["session_summary"]
            
            total_time = time.time() - self.start_time
            
            # Обновляем статистику скрипта
            SCRIPT_STATS["total_runs"] += 1
            SCRIPT_STATS["success_count"] += session_summary["domains_processed"]
            SCRIPT_STATS["last_run"] = datetime.now().isoformat()
            SCRIPT_STATS["avg_processing_time"] = total_time
            
            print(f"\n{'='*80}")
            print("LUMID CANADA BATCH SCRAPER - РЕЗУЛЬТАТЫ")
            print(f"{'='*80}")
            print(f"✅ Батч-файл: {batch_file}")
            print(f"✅ Выходной файл: {output_file}")
            print(f"✅ Доменов обработано: {session_summary['domains_processed']}")
            print(f"✅ Всего страниц найдено: {session_summary['total_pages_found']}")
            print(f"✅ Успешных AI приоритизаций: {session_summary['successful_ai_prioritizations']}")
            print(f"✅ Процент успеха: {session_summary['success_rate']}%")
            print(f"💰 Общая стоимость: ${session_summary['total_cost']:.4f}")
            print(f"⏱️  Общее время: {total_time:.2f}с")
            print(f"⚡ Среднее время на домен: {session_summary['average_time_per_domain']:.2f}с")
            print(f"📊 Dashboard обновлен автоматически")
            print(f"{'='*80}")
            
            return {
                "success": True,
                "batch_file": batch_file,
                "output_file": output_file,
                "session_summary": session_summary,
                "total_time": total_time,
                "session_id": self.session_id
            }
            
        except Exception as e:
            SCRIPT_STATS["error_count"] += 1
            print(f"\n❌ ОШИБКА при обработке батча: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }

def main():
    """Основная функция"""
    # Путь к исходному файлу
    input_file = "../../leads/raw/lumid_canada_20250108.csv"
    
    # Проверяем существование файла
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        print("Убедитесь, что файл существует в папке leads/raw/")
        return
        
    # Создаем и запускаем скрейпер
    scraper = LumidCanadaBatchScraper()
    result = scraper.process_batch(input_file, batch_size=50)
    
    if result["success"]:
        print(f"\n🎉 БАТЧ-СКРЕЙПИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"Результаты сохранены в: {result['output_file']}")
        print(f"Время выполнения: {result['total_time']:.2f} секунд")
        print(f"Откройте dashboard/index.html для детального анализа")
    else:
        print(f"\n❌ БАТЧ-СКРЕЙПИНГ ЗАВЕРШЕН С ОШИБКОЙ: {result['error']}")
        
    # Выводим статистику скрипта
    print(f"\n📈 СТАТИСТИКА СКРИПТА:")
    print(f"Всего запусков: {SCRIPT_STATS['total_runs']}")
    print(f"Успешных обработок: {SCRIPT_STATS['success_count']}")
    print(f"Ошибок: {SCRIPT_STATS['error_count']}")
    print(f"Последний запуск: {SCRIPT_STATS['last_run']}")

if __name__ == "__main__":
    main()