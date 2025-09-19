# ULTRA PARALLEL ARCHITECTURE RULES
## Обязательные принципы для всех скриптов обработки больших данных

### 🚀 БАЗОВЫЕ ПРИНЦИПЫ МАКСИМАЛЬНОЙ ПАРАЛЛЕЛЬНОСТИ

#### 1. 2-ФАЗНАЯ АРХИТЕКТУРА (обязательна для 100+ элементов)
```
ФАЗА 1: МАССОВЫЙ СБОР ДАННЫХ (HTTP/API)
- 20-50 параллельных потоков
- Никакого AI анализа
- Сохранение сырых данных
- Быстрое завершение фазы

ФАЗА 2: БАТЧ AI ОБРАБОТКА  
- 3-5 AI потоков (rate limits)
- Группировка по токенам/лимитам
- Оптимизированные промпты
- Сохранение результатов
```

#### 2. КОНФИГУРАЦИЯ ПОТОКОВ
```python
ULTRA_CONFIG = {
    "max_http_workers": 30,      # HTTP/скрейпинг
    "max_api_workers": 10,       # API вызовы (не OpenAI)  
    "max_ai_workers": 5,         # OpenAI запросы
    "batch_size_tokens": 15000,  # OpenAI батчи
    "http_timeout": 10,          # Таймаут HTTP
    "retry_attempts": 2          # Повторы
}
```

#### 3. RATE LIMITS (актуальные на 2025)
```
OpenAI GPT-3.5-turbo:
- 60,000 tokens/min
- 3,500 requests/min
- Батчи: 15,000 токенов максимум

OpenAI GPT-4:
- 10,000 tokens/min
- 500 requests/min  
- Батчи: 8,000 токенов максимум

Apollo API:
- 500 requests/min
- Батчи: 50 записей

Instantly API:
- 100 requests/min
- Батчи: 20 операций

HTTP Scraping:
- БЕЗ ЛИМИТОВ (только сетевые ограничения)
- Потоки: 20-50 одновременно
```

### 🎯 ОБЯЗАТЕЛЬНАЯ СТРУКТУРА СКРИПТОВ

#### 1. ПРОГРЕСС-МОНИТОРИНГ
```python
class ProgressTracker:
    def __init__(self, total_items):
        self.total_items = total_items
        self.current_item = 0
        self.start_time = time.time()
        self.phase1_completed = 0
        self.phase2_completed = 0
        
    def get_progress_info(self):
        # Возвращает детальный прогресс каждые 10-15 сек
```

#### 2. ПОТОКОБЕЗОПАСНОСТЬ  
```python
self.lock = threading.Lock()

# Обязательно для всех операций с общими данными
with self.lock:
    self.progress_stats["completed"] += 1
```

#### 3. ОБРАБОТКА ОШИБОК
```python
# Никогда не останавливать весь процесс из-за одной ошибки
try:
    result = process_item(item)
except Exception as e:
    errors.append(f"{item}: {str(e)}")
    continue  # ПРОДОЛЖАЕМ ОБРАБОТКУ
```

### 📊 ПРОИЗВОДИТЕЛЬНОСТЬ И МЕТРИКИ

#### ЦЕЛЕВЫЕ ПОКАЗАТЕЛИ:
```
HTTP Scraping: 50-100 сайтов/мин
OpenAI анализ: 20-50 доменов/мин  
Apollo lead generation: 200-500 лидов/мин
CSV processing: 1000-5000 записей/мин

Общая цель: 2000 элементов за 20-40 минут
```

#### ОБЯЗАТЕЛЬНЫЕ МЕТРИКИ В КАЖДОМ СКРИПТЕ:
```python
metrics = {
    "total_runtime": time_elapsed,
    "items_per_minute": items_processed / (time_elapsed / 60),
    "success_rate": successful_items / total_items,
    "error_count": len(errors),
    "phase1_time": phase1_duration,
    "phase2_time": phase2_duration,
    "cost_breakdown": {"openai": ai_cost, "other": other_costs},
    "resource_usage": {"max_threads": max_workers, "peak_memory": memory_peak}
}
```

### 🔧 ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ

#### 1. ИМЕНОВАНИЕ ФАЙЛОВ
```
ultra_parallel_[service]_[operation].py
Примеры:
- ultra_parallel_website_scraper.py
- ultra_parallel_apollo_collector.py  
- ultra_parallel_instantly_processor.py
```

#### 2. СОХРАНЕНИЕ ДАННЫХ
```python
# ВСЕГДА 3 типа выходных файлов:
1. raw_data_{session_id}.json        # Сырые данные фазы 1
2. processed_data_{session_id}.csv   # Финальные результаты
3. session_log_{session_id}.txt      # Детальные логи
```

#### 3. КОНФИГУРИРУЕМОСТЬ
```python  
# Все параметры через ULTRA_CONFIG
ULTRA_CONFIG = {
    "max_workers": 30,        # Настраиваемо
    "batch_size": 50,         # Настраиваемо
    "save_intermediate": True, # Настраиваемо
    "ai_model": "gpt-3.5-turbo" # Настраиваемо
}
```

### 🚨 КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА

#### 1. НИКОГДА НЕ БЛОКИРОВАТЬ
- Ошибка одного элемента НЕ останавливает обработку
- Таймауты обязательны для всех сетевых операций
- Retry механизм с exponential backoff

#### 2. ПАМЯТЬ И РЕСУРСЫ
- Очищать данные после обработки батча
- Не держать в памяти больше 1000 элементов
- Streaming обработка для больших файлов

#### 3. МОНИТОРИНГ
- Прогресс каждые 10-15 секунд
- ETA (estimated time arrival) всегда показывать
- Детальная статистика ошибок

### 📝 ШАБЛОН СКРИПТА

```python
#!/usr/bin/env python3
"""
Ultra Parallel [SERVICE_NAME] Processor
2-фазная архитектура для максимальной производительности
"""

import sys, os, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

ULTRA_CONFIG = {
    "max_phase1_workers": 30,
    "max_phase2_workers": 5, 
    "batch_size": 50,
    "timeout": 10,
    "save_raw": True
}

class UltraParallel[ServiceName]Processor:
    def __init__(self):
        self.session_id = f"ultra_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        self.progress_tracker = None
        self.lock = threading.Lock()
        
    def phase1_mass_collection(self, items):
        """Фаза 1: Массовый сбор данных"""
        # ThreadPoolExecutor с максимальным количеством потоков
        
    def phase2_batch_processing(self):
        """Фаза 2: Батч AI/API обработка"""
        # Оптимальные батчи по лимитам сервиса
        
    def process_ultra_fast(self, input_file, limit=None):
        """Главная функция ультра-быстрой обработки"""
        # Координация фаз + сохранение результатов
```

### 🎯 ПРИМЕНЕНИЕ К СУЩЕСТВУЮЩИМ СЕРВИСАМ

#### Website Intelligence:
- Фаза 1: HTTP scraping всех сайтов (30 потоков)
- Фаза 2: OpenAI анализ батчами (5 потоков)
- Цель: 2000 сайтов за 30 минут

#### Apollo Lead Collection:
- Фаза 1: Массовый поиск компаний (10 потоков) 
- Фаза 2: Обогащение контактами (5 потоков)
- Цель: 5000 лидов за 25 минут

#### Instantly Campaign Management:  
- Фаза 1: Подготовка кампаний (20 потоков)
- Фаза 2: Массовая загрузка лидов (5 потоков)
- Цель: 1000 кампаний за 15 минут

---

## 🔥 ИТОГОВОЕ ПРАВИЛО
**ЛЮБОЙ СКРИПТ ДЛЯ 100+ ЭЛЕМЕНТОВ ДОЛЖЕН ИСПОЛЬЗОВАТЬ 2-ФАЗНУЮ ULTRA PARALLEL АРХИТЕКТУРУ**

Скорость обработки должна быть в 5-10 раз быстрее традиционного последовательного подхода.