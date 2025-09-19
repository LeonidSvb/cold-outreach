---
description: Создать мастер-оркестратор для обработки CSV лидов с естественным языком
globs: core/processors/**/*.py, leads/**/*.csv
alwaysApply: false
---

id: "TASK-001"
title: "Создать мастер-оркестратор для обработки CSV лидов с natural language командами"
status: "planned"
priority: "P0"
labels: ["core", "orchestrator", "natural-language", "batch-processing"]
dependencies: []
created: "2025-01-10"

# 1) High-Level Objective

Создать central orchestrator который принимает команды на русском/английском языке и запускает соответствующие процессоры для массовой обработки CSV лидов (до 30K в месяц).

# 2) Background / Context

У нас есть отдельные процессоры в `core/processors/`:
- `company_name_cleaner_analytics.py` (готов к работе)
- `icebreaker_generator.py` (заготовка)
- `personalization_extractor.py` (заготовка)
- Нужен единый entry point для команд типа "Обработай 1000 лидов из apollo_export.csv с полным обогащением"

# 3) Assumptions & Constraints

- ASSUMPTION: Используем существующую архитектуру `core/processors/` вместо создания новой
- Constraint: Следуем принципам CLAUDE.md - DRY, простота, self-documenting scripts
- Constraint: Поддержка только HTTP скрейпинга, никакого Firecrawl
- Constraint: Все данные реальные, никаких моков

# 4) Dependencies (Other Tasks or Artifacts)

- core/processors/company_name_cleaner_analytics.py (уже существует)
- core/processors/icebreaker_generator.py (нужно завершить)
- core/processors/personalization_extractor.py (нужно завершить)

# 5) Context Plan

**Beginning (add to model context):**

- core/processors/company_name_cleaner_analytics.py
- core/processors/icebreaker_generator.py
- core/processors/personalization_extractor.py 
- core/processors/master_pipeline.py _(read-only)_
- CLAUDE.md _(read-only)_
- .env _(read-only)_

**End state (must exist after completion):**

- core/processors/master_pipeline.py (обновленный с NL командами)
- core/processors/command_parser.py
- core/processors/batch_orchestrator.py
- core/analytics/execution_tracker.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать парсер естественного языка**

   - File: `core/processors/command_parser.py`
   - Exported API:
     ```python
     from typing import Dict, List, Optional
     
     class ProcessingCommand:
         def __init__(self, action: str, input_file: str, processors: List[str], 
                      batch_size: int = 1000, filters: Dict = None):
             pass
     
     def parse_natural_language_command(command: str) -> ProcessingCommand:
         """Парсит команды типа 'Обработай 1000 лидов с айсбрейкерами'"""
         pass
     ```
   - Details:
     - Распознает ключевые слова: "обработай", "генерируй", "только айсбрейкеры", "полное обогащение"
     - Извлекает файлы CSV, количество лидов, типы процессоров
     - Возвращает структурированную команду для выполнения

2. **Расширить master_pipeline.py оркестратором**

   - File: `core/processors/master_pipeline.py`
   - Add natural language interface:
     ```python
     def execute_natural_command(command: str) -> Dict:
         """Main entry point для NL команд"""
         pass
         
     def orchestrate_processors(cmd: ProcessingCommand) -> Dict:
         """Координирует запуск нужных процессоров"""
         pass
     ```

3. **Создать batch orchestrator для массовой обработки**

   - File: `core/processors/batch_orchestrator.py`
   - Add parallel processing:
     ```python
     from concurrent.futures import ThreadPoolExecutor
     
     class BatchOrchestrator:
         def __init__(self, max_workers: int = 5):
             pass
             
         def process_csv_batch(self, csv_file: str, processors: List[str], 
                              batch_size: int = 1000) -> Dict:
             """Обработка CSV батчами с параллелизацией"""
             pass
     ```

4. **Создать analytics tracker**
   - File: `core/analytics/execution_tracker.py`
   - Cases:
     - Трек времени выполнения каждого процессора
     - Логирование ошибок с детализацией
     - Подсчет стоимости API вызовов
     - Метрики производительности (лиды/минуту)

# 7) Types & Interfaces

```python
# core/types/processing_types.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class ProcessorType(Enum):
    COMPANY_NAME_CLEANER = "company_name_cleaner"
    ICEBREAKER_GENERATOR = "icebreaker_generator"  
    PERSONALIZATION_EXTRACTOR = "personalization_extractor"
    WEBSITE_INTELLIGENCE = "website_intelligence"

@dataclass
class ProcessingResult:
    processor_name: str
    leads_processed: int
    success_count: int
    error_count: int
    execution_time_seconds: float
    cost_usd: float
    errors: List[Dict[str, Any]]

@dataclass
class BatchProcessingReport:
    total_leads: int
    processors_used: List[ProcessorType]
    results: List[ProcessingResult]
    total_time_seconds: float
    total_cost_usd: float
    output_file: str
```

# 8) Acceptance Criteria

- `core/processors/master_pipeline.py` принимает команды на русском языке
- Команда `python master_pipeline.py "Обработай 500 лидов из test.csv с айсбрейкерами"` работает
- Все существующие процессоры интегрированы в единый workflow
- Создается детальный JSON отчет по каждой обработке
- Поддержка batch размеров от 100 до 5000 лидов

# 9) Testing Strategy

- Интеграционные тесты с реальными CSV файлами из leads/1-raw/
- Тестирование команд на русском и английском языках
- Проверка parallel processing с разными размерами батчей
- Валидация JSON отчетов и error logging

# 10) Notes / Links

- Следовать SCRIPT_STATS pattern из существующих процессоров
- Использовать centralized .env для всех API keys  
- HTTP-only scraping согласно CLAUDE.md requirements
- Self-documenting с embedded analytics как в company_name_cleaner_analytics.py