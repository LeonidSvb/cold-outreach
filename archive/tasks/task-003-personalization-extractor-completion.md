---
description: Завершить extractor персонализации из website content
globs: core/processors/personalization_extractor.py, core/prompts/personalization_extractor.txt
alwaysApply: false
---

id: "TASK-003"
title: "Завершить extractor персонализации из website content и LinkedIn данных"
status: "planned"
priority: "P0"
labels: ["ai", "personalization", "website-scraping", "linkedin", "insights"]
dependencies: ["task-001-master-pipeline-orchestrator.md"]
created: "2025-01-10"

# 1) High-Level Objective

Завершить PersonalizationExtractor который анализирует scraped website content + LinkedIn данные и извлекает "золотые самородки" для персонализации cold outreach.

# 2) Background / Context

Файл `core/processors/personalization_extractor.py` содержит заготовку. Нужно:
- Анализировать content из services/website-intel/outputs/  
- Интегрироваться с существующим website scraping pipeline
- Извлекать specific insights: achievements, initiatives, pain points, timely hooks
- Готовить данные для icebreaker_generator.py

# 3) Assumptions & Constraints

- ASSUMPTION: Website content уже scraped через services/website-intel/scripts/
- Constraint: Только HTTP scraping, никакого Firecrawl согласно CLAUDE.md
- Constraint: Извлекать actionable insights, не generic summaries
- Constraint: Следовать SCRIPT_STATS pattern для analytics

# 4) Dependencies (Other Tasks or Artifacts)

- services/website-intel/outputs/ (scraped content)
- services/website-intel/scripts/domain_intelligence_extractor.py (существующий scraper)
- core/prompts/page_prioritizer.txt _(пример dialogue-style prompting)_

# 5) Context Plan

**Beginning (add to model context):**

- core/processors/personalization_extractor.py
- services/website-intel/outputs/ _(read-only examples)_
- services/website-intel/scripts/domain_intelligence_extractor.py _(read-only)_
- core/prompts/page_prioritizer.txt _(read-only)_

**End state (must exist after completion):**

- core/processors/personalization_extractor.py (завершенный)
- core/prompts/personalization_extractor.txt
- core/processors/test_personalization_extraction.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать dialogue-style prompt для извлечения insights**

   - File: `core/prompts/personalization_extractor.txt`
   - Content structure:
     ```
     system: Ты эксперт по анализу компаний для cold outreach. Твоя задача найти золотые самородки...
     
     user: Проанализируй контент этой компании и найди insights для персонализации:
     {website_content}
     {linkedin_data}
     
     assistant: Вот ключевые insights для персонализации...
     ```
   - Details:
     - Инструкции по поиску recent achievements, company initiatives  
     - Извлечение pain points и growth indicators
     - Определение conversation starters и shared interests

2. **Завершить implementation PersonalizationExtractor**

   - File: `core/processors/personalization_extractor.py`
   - Complete core methods:
     ```python
     def extract_insights(self, company_name: str, website_content: Dict, 
                         linkedin_data: Dict = None) -> Dict:
         """Извлекает персонализационные insights"""
         pass
         
     def _analyze_website_content(self, content: Dict) -> Dict:
         """Анализирует prioritized content от website-intel"""
         pass
         
     def _extract_timely_hooks(self, content: Dict) -> List[Dict]:
         """Находит recent news, achievements, initiatives"""
         pass
     ```

3. **Интегрировать с website intelligence pipeline**

   - File: `core/processors/personalization_extractor.py`
   - Add integration methods:
     ```python
     def load_website_intelligence(self, domain: str) -> Dict:
         """Загружает данные из services/website-intel/outputs/"""
         pass
         
     def batch_extract_insights(self, companies_df: pd.DataFrame) -> pd.DataFrame:
         """Массовое извлечение insights для CSV лидов"""
         pass
     ```

4. **Создать тест с реальными website данными**
   - File: `core/processors/test_personalization_extraction.py`
   - Cases:
     - Извлечение insights из real website content
     - Валидация quality extracted insights
     - Тестирование integration с website-intel outputs
     - Performance testing для batch processing

# 7) Types & Interfaces

```python
# core/types/personalization_types.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class InsightType(Enum):
    RECENT_ACHIEVEMENT = "recent_achievement"
    COMPANY_INITIATIVE = "company_initiative"
    PAIN_POINT = "pain_point"
    GROWTH_INDICATOR = "growth_indicator"
    SHARED_INTEREST = "shared_interest"
    TIMELY_HOOK = "timely_hook"

@dataclass
class PersonalizationInsight:
    type: InsightType
    text: str
    confidence_score: float
    source: str  # website page или LinkedIn
    relevance_for_outreach: str

@dataclass
class PersonalizationResult:
    company_name: str
    domain: str
    insights: List[PersonalizationInsight]
    conversation_starters: List[str]
    pain_points_identified: List[str]
    recent_achievements: List[str]
    processing_time_seconds: float
    cost_usd: float
```

# 8) Acceptance Criteria

- `core/processors/personalization_extractor.py` извлекает structured insights
- Интеграция с existing website-intel outputs работает
- Результаты готовы для использования в icebreaker_generator
- Batch processing для массовой обработки CSV files
- JSON output с detailed metadata и confidence scores

# 9) Testing Strategy

- Реальные website content данные из services/website-intel/outputs/
- Manual validation качества extracted insights
- Integration testing с website intelligence pipeline
- Performance optimization для large batches

# 10) Notes / Links

- Использовать existing website scraping infrastructure
- Следовать SCRIPT_STATS pattern для consistent analytics
- Insights должны быть actionable для sales context
- Integration с LinkedIn data (when available) для richer personalization