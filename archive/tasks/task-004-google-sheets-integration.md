---
description: Создать интеграцию с Google Sheets для экспорта обогащенных лидов
globs: core/processors/google_sheets_exporter.py, services/google-sheets/
alwaysApply: false
---

id: "TASK-004"
title: "Создать Google Sheets интеграцию для экспорта enriched leads с хронологическим именованием"
status: "planned"
priority: "P1"
labels: ["google-sheets", "export", "integration", "output"]
dependencies: ["task-002-icebreaker-generator-completion.md", "task-003-personalization-extractor-completion.md"]
created: "2025-01-10"

# 1) High-Level Objective

Создать систему автоматического экспорта обогащенных лидов в Google Sheets с хронологическим именованием файлов и поддержкой multiple icebreakers per lead.

# 2) Background / Context

После обработки лидов через все процессоры нужно:
- Экспортировать результаты в Google Sheets  
- Использовать хронологическое именование: `Outreach_Leads_YYYYMMDD_HHMMSS`
- Включить original data + enrichments + AI outputs
- Создавать separate columns для каждого айсбрейкера (10+ per lead)
- Добавлять metadata: processing timestamps, costs, success rates

# 3) Assumptions & Constraints

- ASSUMPTION: Google Sheets API credentials будут в centralized .env
- Constraint: Следовать service organization pattern: services/google-sheets/
- Constraint: Поддержка large exports (1000+ leads) без превышения API limits
- Constraint: Human readable format для easy review и editing

# 4) Dependencies (Other Tasks or Artifacts)

- core/processors/icebreaker_generator.py (completed)
- core/processors/personalization_extractor.py (completed)
- leads/ready/ (final processed data)
- Google Sheets API credentials в .env

# 5) Context Plan

**Beginning (add to model context):**

- .env _(read-only)_
- leads/ready/ examples _(read-only)_
- core/processors/company_name_cleaner_analytics.py _(read-only для pattern)_

**End state (must exist after completion):**

- services/google-sheets/scripts/sheets_exporter.py
- services/google-sheets/outputs/ (export logs)
- core/processors/google_sheets_exporter.py
- services/google-sheets/scripts/test_export.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать Google Sheets service integration**

   - File: `services/google-sheets/scripts/sheets_exporter.py`
   - Exported API:
     ```python
     from typing import Dict, List, Optional
     import pandas as pd
     
     class GoogleSheetsExporter:
         def __init__(self, credentials_path: str = None):
             pass
             
         def create_leads_sheet(self, leads_df: pd.DataFrame, 
                               sheet_name: str = None) -> Dict:
             """Создает новую таблицу с хронологическим именем"""
             pass
             
         def format_icebreakers_columns(self, df: pd.DataFrame) -> pd.DataFrame:
             """Разбивает айсбрейкеры на separate columns"""
             pass
     ```

2. **Создать core processor wrapper**

   - File: `core/processors/google_sheets_exporter.py`
   - Integration с master pipeline:
     ```python
     def export_to_google_sheets(csv_file: str, 
                                include_metadata: bool = True) -> Dict:
         """Main export function для integration с orchestrator"""
         pass
         
     def generate_chronological_name() -> str:
         """Генерирует Outreach_Leads_YYYYMMDD_HHMMSS format"""
         pass
     ```

3. **Implement icebreakers column formatting**

   - File: `services/google-sheets/scripts/sheets_exporter.py`
   - Add specialized formatting:
     ```python
     def _format_multiple_icebreakers(self, icebreakers_json: str) -> Dict:
         """Разбивает JSON айсбрейкеров в отдельные колонки"""
         pass
         
     def _add_metadata_sheet(self, workbook_id: str, 
                           processing_stats: Dict) -> None:
         """Добавляет отдельный sheet с analytics"""
         pass
     ```

4. **Создать тест с реальными данными**
   - File: `services/google-sheets/scripts/test_export.py`
   - Cases:
     - Export sample CSV с multiple icebreakers
     - Проверка chronological naming
     - Валидация metadata sheet creation
     - Testing large batches (1000+ leads)

# 7) Types & Interfaces

```python
# services/google-sheets/types/export_types.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class ExportResult:
    sheet_id: str
    sheet_url: str
    sheet_name: str
    leads_exported: int
    export_time: datetime
    processing_stats: Dict
    error_count: int
    success_rate: float

@dataclass
class IcebreakerColumn:
    column_name: str  # "Icebreaker_1", "Icebreaker_2", etc.
    icebreaker_text: str
    style: str
    confidence_score: float

@dataclass
class LeadExportRow:
    # Original lead data
    company_name: str
    contact_name: str
    email: str
    website: str
    # Enriched data
    personalization_insights: str
    icebreakers: List[IcebreakerColumn]
    processing_metadata: Dict
```

# 8) Acceptance Criteria

- `core/processors/google_sheets_exporter.py` экспортирует CSV в Google Sheets
- Хронологическое именование: `Outreach_Leads_YYYYMMDD_HHMMSS` работает
- Multiple icebreakers displayed в separate columns (Icebreaker_1, Icebreaker_2, etc.)
- Metadata sheet с processing statistics создается
- API rate limiting предотвращает превышение Google Sheets limits

# 9) Testing Strategy

- Реальные processed leads из leads/ready/ для testing
- Integration testing с Google Sheets API
- Large batch testing (1000+ leads) для performance
- Manual review экспортированных sheets для quality validation

# 10) Notes / Links

- Google Sheets API v4 documentation: https://developers.google.com/sheets/api
- Следовать service organization pattern из CLAUDE.md
- Credentials management через centralized .env
- Consider adding share permissions setup для team access