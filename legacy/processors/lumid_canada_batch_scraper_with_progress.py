#!/usr/bin/env python3
"""
Lumid Canada Batch Website Intelligence Scraper С ПРОГРЕСС-БАРОМ
Массовый скрейпинг с детальным логированием и отслеживанием прогресса
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime
import threading

# Добавляем путь к dashboard модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'dashboard'))

# Импорты
from website_intelligence_with_dashboard import WebsiteIntelligenceWithDashboard

class ProgressTracker:
    """Отслеживание прогресса с таймером"""
    
    def __init__(self, total_items):
        self.total_items = total_items
        self.current_item = 0
        self.start_time = time.time()
        self.completed_domains = []
        self.failed_domains = []
        self.running = True
        
    def update(self, domain=None, success=True):
        """Обновить прогресс"""
        self.current_item += 1
        if domain:
            if success:
                self.completed_domains.append(domain)
            else:
                self.failed_domains.append(domain)
        
    def get_progress_info(self):
        """Получить информацию о прогрессе"""
        elapsed = time.time() - self.start_time
        if self.current_item > 0:
            avg_time = elapsed / self.current_item
            remaining_time = avg_time * (self.total_items - self.current_item)
        else:
            avg_time = 0
            remaining_time = 0
            
        progress_percent = (self.current_item / self.total_items) * 100
        
        return {
            "current": self.current_item,
            "total": self.total_items,
            "percent": progress_percent,
            "elapsed": elapsed,
            "remaining": remaining_time,
            "avg_per_item": avg_time,
            "success_count": len(self.completed_domains),
            "failed_count": len(self.failed_domains)
        }
        
    def stop(self):
        """Остановить отслеживание"""
        self.running = False

class LumidCanadaBatchScraperWithProgress:
    """Батч-скрейпер с прогресс-баром"""
    
    def __init__(self):
        self.processor = WebsiteIntelligenceWithDashboard()
        self.start_time = time.time()
        self.session_id = f"lumid_canada_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.progress_tracker = None
        
    def progress_monitor_thread(self):
        """Поток для отображения прогресса каждые 10 секунд"""
        while self.progress_tracker and self.progress_tracker.running:
            time.sleep(10)  # Обновляем каждые 10 секунд
            if self.progress_tracker.running:
                info = self.progress_tracker.get_progress_info()
                print(f"\n{'='*60}")
                print(f"🕐 ПРОГРЕСС: {info['current']}/{info['total']} ({info['percent']:.1f}%)")
                print(f"⏱️  Прошло времени: {info['elapsed']:.0f}с ({info['elapsed']/60:.1f}мин)")
                print(f"⏰ Осталось примерно: {info['remaining']:.0f}с ({info['remaining']/60:.1f}мин)")
                print(f"⚡ Среднее время на домен: {info['avg_per_item']:.1f}с")
                print(f"✅ Успешно обработано: {info['success_count']}")
                print(f"❌ Ошибок: {info['failed_count']}")
                print(f"{'='*60}\n")
        
    def prepare_batch_file(self, input_file: str, batch_size: int = 50) -> str:
        """Подготавливает CSV файл с первыми batch_size записями"""
        print(f"📂 Подготовка батча из первых {batch_size} записей...")
        
        # Читаем исходный файл
        df = pd.read_csv(input_file)
        print(f"📊 Исходный файл содержит {len(df)} записей")
        
        # Берем первые batch_size записей с валидными доменами
        valid_domains = df[df['company_domain'].notna() & (df['company_domain'] != '')]
        batch_df = valid_domains.head(batch_size)
        
        print(f"✅ Отобрано {len(batch_df)} записей с валидными доменами")
        
        # Выводим список доменов для обработки
        print(f"\n📋 СПИСОК ДОМЕНОВ ДЛЯ ОБРАБОТКИ:")
        for i, domain in enumerate(batch_df['company_domain'].tolist(), 1):
            print(f"  {i:2d}. {domain}")
        print()
        
        # Сохраняем батч-файл
        batch_filename = f"lumid_canada_batch50_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        batch_file_path = os.path.join(os.path.dirname(input_file), batch_filename)
        batch_df.to_csv(batch_file_path, index=False)
        
        print(f"💾 Батч-файл создан: {batch_file_path}")
        return batch_file_path, len(batch_df)
        
    def process_batch(self, input_file: str, batch_size: int = 50):
        """Основной метод обработки батча с прогресс-баром"""
        print(f"\n{'='*80}")
        print("🚀 LUMID CANADA BATCH SCRAPER WITH PROGRESS - ЗАПУСК")
        print(f"{'='*80}")
        print(f"📁 Входной файл: {input_file}")
        print(f"📊 Размер батча: {batch_size}")
        print(f"🆔 Session ID: {self.session_id}")
        print(f"🕐 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💻 Обработка: HTTP-только скрейпинг + OpenAI анализ")
        print(f"⚡ Параллельность: 3 потока")
        print(f"{'='*80}")
        
        try:
            # Подготавливаем батч-файл
            batch_file, actual_count = self.prepare_batch_file(input_file, batch_size)
            
            # Инициализируем трекер прогресса
            self.progress_tracker = ProgressTracker(actual_count)
            
            # Запускаем поток мониторинга прогресса
            progress_thread = threading.Thread(target=self.progress_monitor_thread)
            progress_thread.daemon = True
            progress_thread.start()
            
            print(f"\n🔥 ЗАПУСК МАССОВОГО СКРЕЙПИНГА...")
            print(f"🎯 Обработка всех {actual_count} сайтов с прогресс-мониторингом...")
            print(f"📡 Каждые 10 секунд будет обновляться статус прогресса")
            print(f"{'='*80}")
            
            # Запускаем обработку всего батча
            output_file = self.processor.process_csv_file(batch_file, test_limit=None)
            
            # Останавливаем трекер прогресса
            self.progress_tracker.stop()
            
            # Получаем финальную статистику
            session_report = self.processor.get_session_report()
            session_summary = session_report["session_summary"]
            
            total_time = time.time() - self.start_time
            
            print(f"\n{'='*80}")
            print("🎉 LUMID CANADA BATCH SCRAPER - РЕЗУЛЬТАТЫ")
            print(f"{'='*80}")
            print(f"✅ Батч-файл: {batch_file}")
            print(f"✅ Выходной файл: {output_file}")
            print(f"📊 Доменов обработано: {session_summary['domains_processed']}")
            print(f"🔍 Всего страниц найдено: {session_summary['total_pages_found']}")
            print(f"🤖 Успешных AI приоритизаций: {session_summary['successful_ai_prioritizations']}")
            print(f"📈 Процент успеха: {session_summary['success_rate']}%")
            print(f"💰 Общая стоимость: ${session_summary['total_cost']:.4f}")
            print(f"⏱️  Общее время: {total_time:.2f}с ({total_time/60:.1f}мин)")
            print(f"⚡ Среднее время на домен: {session_summary['average_time_per_domain']:.2f}с")
            print(f"📊 Dashboard обновлен автоматически")
            
            # Детальная статистика производительности
            print(f"\n📋 ДЕТАЛЬНАЯ СТАТИСТИКА:")
            print(f"  🔗 API вызовов: {session_summary.get('total_api_calls', 'N/A')}")
            print(f"  📄 Среднее страниц на домен: {session_summary['average_pages_per_domain']:.1f}")
            print(f"  💸 Средняя стоимость на домен: ${session_summary['total_cost']/max(session_summary['domains_processed'], 1):.4f}")
            print(f"  🚀 Скорость обработки: {session_summary['domains_processed']/(total_time/60):.1f} доменов/мин")
            
            print(f"{'='*80}")
            
            # Рекомендации по улучшению
            print(f"\n🎯 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")
            if session_summary['success_rate'] < 90:
                print(f"  ⚠️  Процент успеха {session_summary['success_rate']}% - стоит проверить проблемные домены")
            if session_summary['average_time_per_domain'] > 30:
                print(f"  ⚠️  Среднее время {session_summary['average_time_per_domain']:.1f}с - можно увеличить параллельность")
            if session_summary['total_cost'] > 5.0:
                print(f"  💰 Высокая стоимость ${session_summary['total_cost']:.2f} - рассмотрите использование gpt-3.5-turbo")
            
            print(f"\n🌐 СЛЕДУЮЩИЕ ШАГИ:")
            print(f"  1. 📊 Откройте dashboard/index.html для анализа результатов")
            print(f"  2. 📄 Проверьте выходной файл: {os.path.basename(output_file)}")
            print(f"  3. 🔄 Для оставшихся {745-actual_count} доменов запустите еще один батч")
            print(f"  4. ⚙️  Настройте параметры скрейпинга при необходимости")
            
            return {
                "success": True,
                "batch_file": batch_file,
                "output_file": output_file,
                "session_summary": session_summary,
                "total_time": total_time,
                "session_id": self.session_id,
                "performance_metrics": {
                    "domains_per_minute": session_summary['domains_processed']/(total_time/60),
                    "cost_per_domain": session_summary['total_cost']/max(session_summary['domains_processed'], 1),
                    "pages_per_domain": session_summary['average_pages_per_domain'],
                    "api_calls": session_summary.get('total_api_calls', 0)
                }
            }
            
        except Exception as e:
            if self.progress_tracker:
                self.progress_tracker.stop()
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
    print(f"🎯 LUMID CANADA BATCH SCRAPER WITH PROGRESS")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Путь к исходному файлу
    input_file = "../../leads/raw/lumid_canada_20250108.csv"
    
    # Проверяем существование файла
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        print("📁 Убедитесь, что файл существует в папке leads/raw/")
        return
        
    print(f"✅ Файл найден: {input_file}")
    
    # Создаем и запускаем скрейпер
    scraper = LumidCanadaBatchScraperWithProgress()
    result = scraper.process_batch(input_file, batch_size=50)
    
    if result["success"]:
        print(f"\n🎉 БАТЧ-СКРЕЙПИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"📁 Результаты: {os.path.basename(result['output_file'])}")
        print(f"⏱️  Время: {result['total_time']:.1f}с ({result['total_time']/60:.1f}мин)")
        
        perf = result['performance_metrics']
        print(f"⚡ Производительность: {perf['domains_per_minute']:.1f} доменов/мин")
        print(f"💰 Стоимость: ${perf['cost_per_domain']:.4f}/домен")
        print(f"📄 Страниц: {perf['pages_per_domain']:.1f}/домен")
        
        print(f"\n📊 Откройте dashboard/index.html для детального анализа")
    else:
        print(f"\n❌ БАТЧ-СКРЕЙПИНГ ЗАВЕРШЕН С ОШИБКОЙ: {result['error']}")

if __name__ == "__main__":
    main()