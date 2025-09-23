---
description: Завершить AI-генератор айсбрейкеров с поддержкой 10+ вариантов
globs: core/processors/icebreaker_generator.py, core/prompts/icebreaker_generator.txt
alwaysApply: false
---

id: "TASK-002"
title: "Завершить AI-генератор айсбрейкеров с поддержкой 10+ вариантов на лида"
status: "planned"
priority: "P0"
labels: ["ai", "icebreakers", "personalization", "openai"]
dependencies: ["task-001-master-pipeline-orchestrator.md"]
created: "2025-01-10"

# 1) High-Level Objective

Завершить implementation класса IcebreakerGenerator для генерации 10+ персонализированных айсбрейкеров на каждого лида используя все доступные данные (компания, веб-сайт, LinkedIn, контакт).

# 2) Background / Context

Файл `core/processors/icebreaker_generator.py` содержит заготовку класса. Нужно:
- Завершить implementation с dialogue-style prompting
- Создать prompt файл для генерации айсбрейкеров  
- Интегрировать с существующими данными от других процессоров
- Обеспечить разнообразие стилей: compliment, insight, question, common ground

# 3) Assumptions & Constraints

- ASSUMPTION: Используем OpenAI GPT-4 для максимального качества айсбрейкеров
- Constraint: Следуем SCRIPT_STATS pattern из company_name_cleaner_analytics.py
- Constraint: Айсбрейкеры должны звучать естественно, как от знакомого человека
- Constraint: Длина 1-2 предложения, conversational tone

# 4) Dependencies (Other Tasks or Artifacts)

- core/processors/personalization_extractor.py (insights для айсбрейкеров)
- services/website-intel/outputs/ (данные с сайтов компаний)
- core/prompts/company_name_shortener.txt (пример dialogue-style prompting)

# 5) Context Plan

**Beginning (add to model context):**

- core/processors/icebreaker_generator.py
- core/processors/company_name_cleaner_analytics.py _(read-only)_
- core/prompts/company_name_shortener.txt _(read-only)_
- .env _(read-only)_

**End state (must exist after completion):**

- core/processors/icebreaker_generator.py (завершенный)
- core/prompts/icebreaker_generator.txt
- core/processors/test_icebreaker_generation.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать dialogue-style prompt для генерации айсбрейкеров**

   - File: `core/prompts/icebreaker_generator.txt`
   - Content structure:
     ```
     system: Ты эксперт по cold outreach с 10+ летним опытом...
     
     user: Сгенерируй 10+ айсбрейкеров для этой компании:
     {company_data}
     
     assistant: Вот разнообразные айсбрейкеры основанные на данных...
     ```
   - Details:
     - Примеры высококонвертирующих айсбрейкеров
     - Разные стили: compliment, insight, question, common ground
     - Инструкции по персонализации и natural tone

2. **Завершить implementation IcebreakerGenerator класса**

   - File: `core/processors/icebreaker_generator.py`
   - Complete methods:
     ```python
     def generate_icebreakers(self, company_data: Dict, contact_data: Dict, 
                            insights_data: Dict = None) -> Dict:
         """Генерирует 10+ айсбрейкеров разных стилей"""
         pass
         
     def _parse_company_insights(self, data: Dict) -> str:
         """Извлекает ключевые insights для персонализации"""
         pass
         
     def _rank_icebreakers(self, icebreakers: List[Dict]) -> List[Dict]:
         """Ранжирует по natural authenticity"""
         pass
     ```

3. **Интегрировать с существующими данными**

   - File: `core/processors/icebreaker_generator.py`
   - Add data integration:
     ```python
     def load_enriched_data(self, csv_file: str) -> pd.DataFrame:
         """Загружает данные из leads/enriched/"""
         pass
         
     def batch_generate_icebreakers(self, leads_df: pd.DataFrame, 
                                   batch_size: int = 20) -> pd.DataFrame:
         """Массовая генерация с батчингом"""
         pass
     ```

4. **Создать тест с реальными данными**
   - File: `core/processors/test_icebreaker_generation.py`
   - Cases:
     - Генерация 10+ айсбрейкеров для тестовой компании
     - Проверка разнообразия стилей
     - Валидация качества персонализации
     - Тестирование batch processing

# 7) Types & Interfaces

```python
# core/types/icebreaker_types.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class IcebreakerStyle(Enum):
    COMPLIMENT = "compliment"
    INSIGHT = "insight" 
    QUESTION = "question"
    COMMON_GROUND = "common_ground"
    NEWS_BASED = "news_based"
    ACHIEVEMENT = "achievement"

@dataclass
class IcebreakerOption:
    text: str
    style: IcebreakerStyle
    confidence_score: float
    reasoning: str
    personalization_elements: List[str]

@dataclass
class IcebreakerResult:
    company_name: str
    contact_name: str
    icebreakers: List[IcebreakerOption]
    processing_time_seconds: float
    cost_usd: float
    data_sources_used: List[str]
```

# 8) Acceptance Criteria

- `core/processors/icebreaker_generator.py` генерирует 10+ уникальных айсбрейкеров
- Каждый айсбрейкер имеет confidence score и reasoning
- Поддержка batch processing для массовой обработки CSV
- Интеграция с данными из personalization_extractor и website intelligence
- JSON output с метаданными и статистикой

# 9) Testing Strategy

- Реальные данные компаний из leads/enriched/ для тестирования
- A/B тестирование разных стилей айсбрейкеров
- Проверка natural language quality через manual review
- Performance тесты с large batches (1000+ leads)

# 10) Notes / Links

- Изучить best practices от company_name_cleaner_analytics.py для SCRIPT_STATS
- Использовать тот же OpenAI client setup что и в других процессорах
- Сохранять all icebreaker variants для future A/B testing
- Dialogue-style prompting должен быть editable в external файле