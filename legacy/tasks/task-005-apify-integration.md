---
description: Интеграция Apify для расширенного web scraping и data enrichment
globs: services/apify/**, core/processors/apify_enricher.py
alwaysApply: false
---

id: "TASK-005"
title: "Интеграция Apify для advanced web scraping и LinkedIn data enrichment"
status: "planned"
priority: "P1"
labels: ["apify", "scraping", "linkedin", "enrichment", "data"]
dependencies: ["task-001-master-pipeline-orchestrator.md"]
created: "2025-01-10"

# 1) High-Level Objective

Интегрировать Apify для более мощного web scraping, LinkedIn data extraction, и general company enrichment как альтернативу/дополнение к существующему HTTP-only scraping.

# 2) Background / Context

Текущий website-intel использует HTTP-only scraping согласно CLAUDE.md. Apify может дать:
- Better JavaScript rendering для SPA websites
- LinkedIn company pages parsing
- Social media data extraction  
- More robust scraping для complex websites
- Structured data extraction from various sources

# 3) Assumptions & Constraints

- ASSUMPTION: Apify API key уже настроен в .env (APIFY_API_KEY exists)
- Constraint: Интегрироваться с existing architecture, не заменять полностью
- Constraint: Следовать service organization pattern
- Constraint: Cost-effective usage с proper monitoring

# 4) Dependencies (Other Tasks or Artifacts)

- services/website-intel/ (existing HTTP scraping)
- .env с APIFY_API_KEY
- core/processors/personalization_extractor.py для integration

# 5) Context Plan

**Beginning (add to model context):**

- .env _(read-only)_
- services/website-intel/scripts/ examples _(read-only)_
- core/processors/personalization_extractor.py _(read-only)_

**End state (must exist after completion):**

- services/apify/scripts/apify_scraper.py
- services/apify/scripts/linkedin_enricher.py
- services/apify/outputs/ (structured outputs)
- core/processors/apify_enricher.py (integration)
- services/apify/scripts/test_apify.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать Apify client integration**

   - File: `services/apify/scripts/apify_scraper.py`
   - Exported API:
     ```python
     from apify_client import ApifyClient
     from typing import Dict, List, Optional
     
     class ApifyScraper:
         def __init__(self):
             self.client = ApifyClient(os.getenv('APIFY_API_KEY'))
             
         def scrape_website(self, url: str, 
                           actor_id: str = "web-scraper") -> Dict:
             """Generic website scraping через Apify actors"""
             pass
             
         def extract_linkedin_company(self, company_name: str) -> Dict:
             """LinkedIn company data extraction"""
             pass
     ```

2. **Создать LinkedIn enrichment специально**

   - File: `services/apify/scripts/linkedin_enricher.py`
   - LinkedIn specific functionality:
     ```python
     def enrich_company_linkedin(self, company_name: str, 
                               website: str = None) -> Dict:
         """Получает LinkedIn company data"""
         pass
         
     def get_recent_posts(self, linkedin_url: str, 
                         limit: int = 5) -> List[Dict]:
         """Recent company posts для timely hooks"""
         pass
     ```

3. **Интегрировать с core processors**

   - File: `core/processors/apify_enricher.py`
   - Core integration:
     ```python
     def enrich_leads_with_apify(self, leads_df: pd.DataFrame) -> pd.DataFrame:
         """Обогащает leads данными через Apify"""
         pass
         
     def batch_linkedin_enrichment(self, companies: List[str]) -> Dict:
         """Массовое обогащение LinkedIn данных"""
         pass
     ```

4. **Создать тесты и cost monitoring**
   - File: `services/apify/scripts/test_apify.py`
   - Cases:
     - Website scraping через разные Apify actors
     - LinkedIn company data extraction
     - Cost tracking и usage monitoring
     - Integration с existing personalization pipeline

# 7) Types & Interfaces

```python
# services/apify/types/apify_types.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class ApifyScrapingResult:
    url: str
    actor_used: str
    data: Dict[str, Any]
    success: bool
    cost_credits: float
    execution_time_seconds: float
    timestamp: datetime

@dataclass
class LinkedInCompanyData:
    company_name: str
    linkedin_url: str
    description: str
    employee_count: str
    industry: str
    recent_posts: List[Dict]
    company_updates: List[Dict]
    follower_count: int
    specialties: List[str]

@dataclass
class ApifyEnrichmentResult:
    original_data: Dict
    apify_data: Dict
    linkedin_data: Optional[LinkedInCompanyData]
    enrichment_quality_score: float
    data_sources: List[str]
    total_cost_credits: float
```

# 8) Acceptance Criteria

- `services/apify/scripts/apify_scraper.py` успешно scrapes websites через Apify actors
- LinkedIn enrichment работает для company data extraction
- Integration с existing personalization_extractor.py функционирует
- Cost monitoring и credit usage tracking implemented
- Batch processing для mass enrichment готово

# 9) Testing Strategy

- Real company websites для testing scraping quality
- LinkedIn company pages для validation data extraction
- Cost monitoring testing с small batches first
- Quality comparison: HTTP scraping vs Apify results

# 10) Notes / Links

- Apify API documentation: https://docs.apify.com/
- Popular actors: Web Scraper, LinkedIn Company Scraper
- Monitor credits usage closely для cost control
- Integrate outputs с existing website-intel pipeline