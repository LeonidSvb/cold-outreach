---
description: Создать генератор email последовательностей с subject lines и offers
globs: core/processors/sequence_builder.py, core/prompts/email_sequence.txt
alwaysApply: false
---

id: "TASK-006"
title: "Создать генератор 2-email sequences с subject lines и personalized offers"
status: "planned"
priority: "P1"
labels: ["email-sequences", "copywriting", "offers", "ai", "outreach"]
dependencies: ["task-002-icebreaker-generator-completion.md"]
created: "2025-01-10"

# 1) High-Level Objective

Создать систему генерации complete email sequences (initial + follow-up) с персонализированными subject lines, offers, и call-to-actions для AI automation/lead generation услуг.

# 2) Background / Context

После генерации айсбрейкеров нужно:
- Создать полные email templates с subject + body + CTA
- Сгенерировать follow-up письмо для non-responders  
- Персонализировать offers под индустрию/размер компании
- Интегрироваться с icebreaker data для consistent messaging

# 3) Assumptions & Constraints

- ASSUMPTION: Продаем AI automation и lead generation services ($1K-$15K price range)
- Constraint: 2-email sequence: initial outreach + follow-up
- Constraint: Каждый email должен иметь clear value proposition
- Constraint: Subject lines optimized для high open rates

# 4) Dependencies (Other Tasks or Artifacts)

- core/processors/icebreaker_generator.py (completed для personalization)
- core/processors/personalization_extractor.py (company insights)
- Business context: AI automation services, target SMBs

# 5) Context Plan

**Beginning (add to model context):**

- core/processors/icebreaker_generator.py _(read-only)_
- core/processors/personalization_extractor.py _(read-only)_
- core/prompts/icebreaker_generator.txt _(read-only для pattern)_

**End state (must exist after completion):**

- core/processors/sequence_builder.py
- core/prompts/email_sequence.txt
- core/prompts/offer_copywriter.txt
- core/processors/test_sequence_generation.py

# 6) Low-Level Steps (Ordered, information-dense)

1. **Создать dialogue-style prompts для email sequences**

   - File: `core/prompts/email_sequence.txt`
   - Content structure:
     ```
     system: Ты expert copywriter для B2B cold outreach специализирующийся на AI automation...
     
     user: Создай email sequence для компании:
     {company_data}
     {icebreakers}
     {personalization_insights}
     
     assistant: Email 1 - Initial Outreach:
     Subject: ...
     Body: {icebreaker} + value prop + CTA
     
     Email 2 - Follow-up:
     Subject: ...
     ```

2. **Создать offer copywriting prompt**

   - File: `core/prompts/offer_copywriter.txt`
   - Specialized для AI automation services:
     ```
     system: Ты copywriter специализирующийся на AI automation и lead generation...
     
     user: Создай personalized offer для:
     Industry: {industry}
     Company Size: {company_size}  
     Pain Points: {pain_points}
     
     assistant: Вот специализированный offer...
     ```

3. **Implement SequenceBuilder класс**

   - File: `core/processors/sequence_builder.py`
   - Core functionality:
     ```python
     class SequenceBuilder:
         def __init__(self):
             self.stats = SCRIPT_STATS.copy()
             
         def generate_email_sequence(self, company_data: Dict, 
                                   icebreakers: List[Dict],
                                   insights: Dict) -> Dict:
             """Генерирует complete 2-email sequence"""
             pass
             
         def create_personalized_offer(self, company_data: Dict) -> Dict:
             """AI automation offer под компанию"""
             pass
             
         def generate_subject_lines(self, email_body: str, 
                                  company_name: str) -> List[str]:
             """Multiple subject options для A/B testing"""
             pass
     ```

4. **Создать тесты с реальными company data**
   - File: `core/processors/test_sequence_generation.py`
   - Cases:
     - Full sequence generation для sample companies
     - Subject line variety и quality
     - Offer personalization validation
     - Integration с icebreaker data

# 7) Types & Interfaces

```python
# core/types/sequence_types.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class EmailType(Enum):
    INITIAL_OUTREACH = "initial_outreach"
    FOLLOW_UP = "follow_up"
    BREAK_UP = "break_up"

@dataclass
class EmailTemplate:
    type: EmailType
    subject_lines: List[str]  # Multiple options для A/B testing
    body: str
    cta: str
    personalization_elements: List[str]
    estimated_read_time: int  # seconds

@dataclass
class PersonalizedOffer:
    offer_text: str
    value_proposition: str
    price_range: str
    service_focus: str  # automation, lead gen, etc.
    roi_estimate: str
    industry_specific_benefits: List[str]

@dataclass
class EmailSequenceResult:
    company_name: str
    emails: List[EmailTemplate]
    personalized_offer: PersonalizedOffer
    sequence_rationale: str
    processing_time_seconds: float
    cost_usd: float
```

# 8) Acceptance Criteria

- `core/processors/sequence_builder.py` генерирует complete 2-email sequences
- Subject lines optimized для high open rates (multiple variants)
- Personalized offers под AI automation/lead generation services
- Integration с icebreaker data для consistent messaging
- JSON output готовый для import в email tools

# 9) Testing Strategy

- Manual review email quality и natural flow
- A/B testing different subject line approaches
- Offer personalization validation для different industries
- Integration testing с icebreaker generation pipeline

# 10) Notes / Links

- Focus на AI automation и lead generation как core services
- Price range $1K-$15K для SMB market positioning
- Study high-converting cold email templates для inspiration
- Consider industry-specific pain points для offer personalization