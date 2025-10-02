# Архитектурные Решения и План Реализации Frontend

**Дата:** 2025-10-02
**Спринт:** First Campaign Launch
**Статус:** Утверждено к реализации

---

## 📋 EXECUTIVE SUMMARY

### О чём этот документ
Результат обсуждения архитектуры frontend для платформы холодного outreach. Ключевой вопрос: **делать wizard UI на 10 шагов или модульную систему независимых скриптов?**

### Что решили
**Выбрали модульный подход:**
- Один универсальный `/script-runner` для всех Python скриптов
- Каждый скрипт запускается независимо через dropdown
- Отдельные страницы создаём только для специфичного UI (например `/offers`)
- **Никакого wizard** - это лишняя сложность

### Почему это важно
- Быстрее MVP (3-4 дня вместо 2-3 недель)
- Легко тестировать каждый скрипт отдельно
- Соответствует индустриальным стандартам для internal tools
- Идеально для solo entrepreneur (ты)

### Что дальше
Следуем пошаговому плану реализации на 4 дня (см. раздел "План Реализации")

---

## 🎯 ЧАСТЬ 1: АРХИТЕКТУРНОЕ РЕШЕНИЕ

### Контекст задачи

**Проблема:**
План спринта требует реализовать 10-шаговый workflow:
```
Upload CSV → Column Detection → Preview → Select Columns →
Normalize → Generate Icebreakers → Review → Assign Offer →
Split Batches → Upload to Instantly
```

**Вопрос:**
Делать всё как один большой wizard с переходами между шагами или сделать модульную систему, где каждый скрипт работает независимо?

---

### Сравнение подходов

#### ❌ Подход 1: Wizard UI (отклонён)

**Что это:**
- Один большой компонент `WizardFlow.tsx`
- 10 последовательных шагов
- State management для всего workflow
- Невозможно запустить отдельный шаг

**Аналогия:**
Кухонный комбайн "всё-в-одном". Если сломался блендер, не работает и миксер.

**Проблемы:**
- ❌ Высокая сложность (10 компонентов + state management)
- ❌ Сложно тестировать (нужен весь flow)
- ❌ Если один шаг сломался → вся система не работает
- ❌ Жёсткая последовательность (нельзя пропустить шаг)
- ❌ Долгая разработка (2-3 недели)
- ❌ Подходит для non-technical пользователей, не для тебя

**Когда используется:**
- SaaS продукты для конечных пользователей
- Когда важна простота для нетехнических людей
- Когда workflow всегда один и тот же

---

#### ✅ Подход 2: Модульная система (выбран)

**Что это:**
- Один универсальный `/script-runner` для всех скриптов
- Dropdown со всеми доступными скриптами
- Каждый скрипт запускается независимо
- Можно запускать в любом порядке

**Аналогия:**
Отдельный блендер, отдельный миксер, отдельный тостер. Если блендер сломался, миксер всё равно работает.

**Преимущества:**
- ✅ Простая архитектура (переиспользуем существующий UI)
- ✅ Легко тестировать (каждый скрипт отдельно)
- ✅ Гибкость (запускай что хочешь, когда хочешь)
- ✅ Быстрая разработка (3-4 дня)
- ✅ Индустриальный стандарт для internal tools
- ✅ Идеально для solo entrepreneur

**Когда используется:**
- Internal tools для команды
- Инженерные инструменты
- Когда нужна максимальная гибкость
- **Наш случай - именно это**

---

### Финальное решение

**ВЫБИРАЕМ: Модульный подход**

**Архитектура:**

```
Frontend:
├── /script-runner              # Универсальный интерфейс для ВСЕХ скриптов
│   ├── Upload CSV (если нужен файл)
│   ├── Dropdown с выбором скрипта
│   ├── Динамическая форма конфигурации
│   ├── Кнопка "Run Script"
│   └── Real-time статус выполнения
│
├── /offers                     # Отдельная страница (специальный UI)
│   ├── Список offers
│   ├── Создание offer
│   └── CRUD операции
│
└── /dashboard                  # Отдельная страница (аналитика)
    └── Instantly analytics

Backend:
├── GET /api/scripts            # Список всех доступных скриптов
├── POST /api/run-script/{id}   # Запуск выбранного скрипта
└── GET /api/job/{id}/status    # Статус выполнения
```

**Список скриптов в dropdown:**
1. Parse CSV (парсинг CSV → сохранение в leads table)
2. Normalize Company Names (OpenAI нормализация названий)
3. Normalize Cities (OpenAI сокращение городов)
4. Generate Icebreakers (генерация icebreakers с выбором offer)
5. Split into Batches (разбивка на batch по 200-300 лидов)
6. Upload to Instantly (загрузка batch в кампанию)

**Специальные страницы создаём только когда:**
- Нужен сложный CRUD интерфейс (как `/offers`)
- Нужна кастомная визуализация (как `/dashboard`)
- Generic config форма не подходит

**НЕ создаём отдельные страницы для:**
- Простых data processing скриптов
- Скриптов со стандартными параметрами
- Разовых операций

---

### Сравнительная таблица

| Критерий | Wizard | Модули | Победитель |
|----------|--------|--------|------------|
| **Сложность кода** | Высокая (10 компонентов) | Низкая (1 универсальная страница) | ✅ Модули |
| **Время разработки** | 2-3 недели | 3-4 дня | ✅ Модули |
| **Тестирование** | Сложно (весь flow) | Легко (каждый скрипт) | ✅ Модули |
| **Отладка** | Сложно (найти сломанный шаг) | Легко (изолированные скрипты) | ✅ Модули |
| **Гибкость** | Низкая (фиксированный порядок) | Высокая (любой порядок) | ✅ Модули |
| **Для кого** | Non-technical пользователи | Solo entrepreneur (ты) | ✅ Модули |
| **Индустрия** | SaaS продукты | Internal tools | ✅ Модули |
| **Переиспользование UI** | Нет | Да (один универсальный UI) | ✅ Модули |

**Итог: Модули побеждают по всем параметрам для нашего случая**

---

### Обоснование решения

**Почему модульный подход правильный:**

1. **Ты solo entrepreneur** - тебе нужна гибкость, не упрощение для нетехнических пользователей
2. **Быстрый MVP** - 3-4 дня вместо 2-3 недель
3. **Легко тестировать** - каждый скрипт независимо
4. **Индустриальный стандарт** - так делают internal tools в Google, Facebook, etc.
5. **Уже есть основа** - `/script-runner` работает на 70%, просто добавить скрипты

**Когда можно пересмотреть:**
- Если наймёшь нетехнических сотрудников
- Если будешь делать SaaS для клиентов
- Если workflow станет слишком сложным для модулей

**Но сейчас** - модули это 100% правильный выбор.

---

## 📊 ЧАСТЬ 2: АНАЛИЗ ТЕКУЩЕГО СОСТОЯНИЯ FRONTEND

### Что уже работает (✅)

#### Инфраструктура (100% готово)
```
✅ Next.js 15.5.3 с App Router
✅ TypeScript с правильными типами
✅ shadcn/ui компоненты установлены
✅ Tailwind CSS настроен
✅ FastAPI backend работает на порту 8002
✅ CORS настроен для localhost:3000-3003
```

#### UI Компоненты (80% готово)
```
✅ FileUpload.tsx
   - Drag & drop интерфейс
   - Валидация файлов (CSV, размер)
   - Обработка ошибок
   - Работает идеально

✅ CsvPreview.tsx
   - Автоопределение типов колонок
   - Превью последних 15 строк
   - Показать/скрыть колонки
   - Статистика (строки, колонки, типы)
   - Визуальные индикаторы типов
   - Работает идеально

✅ ConfigForm.tsx
   - Динамическая генерация форм
   - Разные типы полей (text, number, select)
   - Валидация
   - Работает с любым конфигом скрипта

✅ JobStatus.tsx
   - Real-time прогресс
   - Логи выполнения
   - Обработка ошибок
   - Превью результатов
```

#### Страницы (60% готово)
```
✅ Homepage (/)
   - Карточки навигации по инструментам
   - Статусы (Ready/Dev/Planned)
   - Чистый дизайн

✅ /script-runner (ОСНОВА!)
   - Секция загрузки файлов
   - Dropdown с последними файлами
   - Превью CSV
   - Dropdown выбора скрипта
   - Форма конфигурации
   - Отслеживание статуса задач
   - ЭТО НАША БАЗА - 70% ГОТОВА

✅ /dashboard
   - Аналитика кампаний Instantly
   - Для спринта не релевантно
```

#### API Routes (50% готово)
```
✅ /api/scripts - список скриптов
✅ /api/upload - загрузка CSV
✅ /api/uploaded-files - список файлов
✅ /api/files/[fileId]/preview - превью CSV
✅ /api/run-script - запуск скрипта

❌ Отсутствуют:
   - /api/offers/* (CRUD для offers)
   - Supabase интеграция
```

#### Backend (40% готово)
```
✅ Базовый фреймворк script runner
✅ Загрузка и анализ CSV
✅ Хранение метаданных (JSON файлы)
✅ Система отслеживания задач
✅ CSV transformer интеграция

❌ Отсутствуют:
   - Supabase интеграция
   - Конкретные endpoints скриптов
   - Endpoints для offers
   - Batch processing endpoints
   - Instantly upload endpoint
```

---

### Критические проблемы (❌)

#### 1. Нет Supabase интеграции (0%)
```
❌ Нет Supabase client utilities в frontend
❌ Нет database операций (users, offers, leads, batches)
❌ Нет Storage интеграции
❌ Нет RLS setup
❌ CSV файлы хранятся локально в /backend/uploads/ (временно!)

Влияние: КРИТИЧНО - данные не сохраняются в БД
Приоритет: #1 - Исправить первым делом
```

#### 2. База данных не создана (0%)
```
❌ Таблицы не созданы в Supabase:
   - users
   - offers
   - leads
   - batches
   - campaigns
   - events
   - email_accounts
   - file_metadata

Влияние: КРИТИЧНО - ничего нельзя сохранить
Приоритет: #1 - Создать до всего остального
```

#### 3. Python скрипты не интегрированы (0%)
```
❌ normalize_company_name.py - не интегрирован
❌ normalize_city.py - не интегрирован
❌ generate_icebreakers.py - не интегрирован
❌ split_into_batches.py - не существует
❌ instantly_uploader.py - не адаптирован под Supabase

Влияние: ВЫСОКОЕ - нет обработки данных
Приоритет: #2 - После настройки БД
```

#### 4. Backend API endpoints отсутствуют (0%)
```
❌ POST /api/parse-csv
❌ POST /api/normalize-company
❌ POST /api/normalize-city
❌ POST /api/generate-icebreakers
❌ POST /api/split-batches
❌ POST /api/upload-to-instantly
❌ GET /api/offers
❌ POST /api/offers
❌ PUT /api/offers/{id}
❌ DELETE /api/offers/{id}

Влияние: КРИТИЧНО - скрипты нельзя вызвать
Приоритет: #2 - Вместе со скриптами
```

#### 5. Страница Offers отсутствует (0%)
```
❌ /offers страница не существует
❌ Нет CRUD интерфейса для offers
❌ Нет dropdown для выбора offer в script-runner

Влияние: ВЫСОКОЕ - нельзя назначить offers батчам
Приоритет: #3 - После базовых скриптов
```

---

### Оценка готовности

**По компонентам:**
```
Инфраструктура:        ████████████████████ 100%
UI Компоненты:         ████████████████     80%
Страницы:              ████████████         60%
Frontend API Routes:   ██████████           50%
Backend API:           ████████             40%
Database интеграция:   ░░░░░░░░░░░░░░░░░░░░  0%
Processing скрипты:    ░░░░░░░░░░░░░░░░░░░░  0%
Offers управление:     ░░░░░░░░░░░░░░░░░░░░  0%

ОБЩАЯ ГОТОВНОСТЬ:      ████████░░░░░░░░░░░░ 35%
```

**По требованиям спринта:**
```
CSV Upload:            ████████████████     80% (работает, нужен Supabase)
Column Detection:      ████████████████████ 100% (работает отлично)
Preview Data:          ████████████████████ 100% (работает отлично)
Normalize Data:        ░░░░░░░░░░░░░░░░░░░░  0% (нет скрипта/endpoint)
Generate Icebreakers:  ░░░░░░░░░░░░░░░░░░░░  0% (нет скрипта/endpoint)
Split Batches:         ░░░░░░░░░░░░░░░░░░░░  0% (нет скрипта/endpoint)
Upload to Instantly:   ░░░░░░░░░░░░░░░░░░░░  0% (нет скрипта/endpoint)
Offers Management:     ░░░░░░░░░░░░░░░░░░░░  0% (нет страницы)
```

---

### Сильные стороны (используем)

**Что уже отлично:**
1. **Universal Script Runner** - идеальная база, просто добавить скрипты
2. **CSV компоненты** - профессиональное качество, переиспользуемые
3. **Динамические Config Forms** - работают автоматически для любого скрипта
4. **Job Tracking** - real-time мониторинг прогресса работает
5. **Чистая архитектура** - легко расширять

**Быстрые победы:**
1. Оставляем существующий `/script-runner` как главный интерфейс
2. Добавляем все скрипты в dropdown (новых страниц не нужно)
3. Переиспользуем FileUpload и CsvPreview
4. Динамические формы обрабатывают все параметры скриптов

---

## 🚀 ЧАСТЬ 3: ПЛАН РЕАЛИЗАЦИИ (4 ДНЯ)

### DAY 1: База данных + Supabase интеграция

#### Утро (3-4 часа)

**1.1 Создать Database Schema**
```sql
-- Запустить SQL миграцию в Supabase
-- Создать все таблицы:
-- users, offers, leads, batches, campaigns, events, email_accounts, file_metadata

-- Вставить default user
INSERT INTO users (id, email)
VALUES ('00000000-0000-0000-0000-000000000001', 'default@user.com');

-- Создать 2-3 sample offers
INSERT INTO offers (code, name, value_prop, angle)
VALUES
  ('A1', 'AI Automation', 'Save 20h/week', 'Efficiency'),
  ('A2', 'Lead Generation', 'Double your pipeline', 'Growth'),
  ('B1', 'Cold Email Setup', 'Launch in 7 days', 'Speed');

-- Проверить
SELECT * FROM offers;
```

**1.2 Setup Supabase Storage**
```
- Создать bucket 'csv-files'
- Настроить access policies (private)
- Тестировать загрузку файла через Supabase UI
```

#### День (3-4 часа)

**1.3 Frontend Supabase Client**

Файл: `frontend/src/lib/supabase.ts`
```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export async function uploadCsvToSupabase(file: File) {
  const fileName = `${Date.now()}_${file.name}`

  // Upload to Storage
  const { data: storageData, error: storageError } = await supabase
    .storage
    .from('csv-files')
    .upload(`uploads/${fileName}`, file)

  if (storageError) throw storageError

  // Save metadata
  const { data: metadata, error: metadataError } = await supabase
    .from('file_metadata')
    .insert({
      filename: fileName,
      original_name: file.name,
      upload_date: new Date().toISOString(),
      size: file.size
    })
    .select()
    .single()

  if (metadataError) throw metadataError
  return metadata
}
```

Файл: `frontend/src/lib/api/offers.ts`
```typescript
import { supabase } from '../supabase'

export async function getAllOffers() {
  const { data, error } = await supabase
    .from('offers')
    .select('*')
    .eq('user_id', '00000000-0000-0000-0000-000000000001')
    .order('created_at', { ascending: false })

  if (error) throw error
  return data
}

export async function createOffer(offer: {
  code: string
  name: string
  value_prop: string
  angle: string
}) {
  const { data, error } = await supabase
    .from('offers')
    .insert({
      ...offer,
      user_id: '00000000-0000-0000-0000-000000000001'
    })
    .select()
    .single()

  if (error) throw error
  return data
}
```

**1.4 Обновить FileUpload Component**
```typescript
// Изменить /api/upload чтобы использовать Supabase
// Протестировать: Upload CSV → файл в Supabase Storage + metadata в таблице
```

#### Вечер (1-2 часа)

**1.5 Backend Supabase Integration**

Файл: `backend/db/supabase.py`
```python
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def save_leads_to_db(file_id: str, leads: list[dict]):
    """Сохранить распарсенные CSV leads в БД"""
    for lead in leads:
        supabase.table('leads').insert({
            'file_id': file_id,
            'user_id': '00000000-0000-0000-0000-000000000001',
            'email': lead.get('email'),
            'company_name': lead.get('company_name'),
            'first_name': lead.get('first_name'),
            'last_name': lead.get('last_name'),
            'city': lead.get('city'),
            'country': lead.get('country'),
            'website': lead.get('website'),
            'raw_data': lead
        }).execute()

def get_leads_by_file(file_id: str):
    """Получить все leads для файла"""
    response = supabase.table('leads')\
        .select('*')\
        .eq('file_id', file_id)\
        .execute()
    return response.data

def update_lead_normalized(lead_id: str, normalized_company: str, normalized_city: str):
    """Обновить нормализованные поля"""
    supabase.table('leads').update({
        'normalized_company_name': normalized_company,
        'normalized_city': normalized_city
    }).eq('id', lead_id).execute()
```

**Итог Дня 1:**
- ✅ Схема БД готова
- ✅ Frontend загружает в Supabase
- ✅ Backend подключён к Supabase
- ✅ Offers существуют в БД

---

### DAY 2: Processing скрипты + API endpoints

#### Утро (3-4 часа)

**2.1 Parse CSV Script**

Файл: `backend/scripts/parse_csv.py`
```python
import csv
from backend.db.supabase import supabase, save_leads_to_db

def parse_csv_from_storage(file_id: str):
    """Скачать CSV из Supabase Storage и распарсить в leads table"""

    # Получить метаданные файла
    response = supabase.table('file_metadata')\
        .select('*')\
        .eq('id', file_id)\
        .single()\
        .execute()

    file_metadata = response.data
    filename = file_metadata['filename']

    # Скачать из storage
    csv_data = supabase.storage\
        .from_('csv-files')\
        .download(f'uploads/{filename}')

    # Парсить CSV
    csv_text = csv_data.decode('utf-8')
    reader = csv.DictReader(csv_text.splitlines())

    leads = []
    for row in reader:
        leads.append({
            'email': row.get('Email') or row.get('email'),
            'company_name': row.get('Company') or row.get('company_name'),
            'first_name': row.get('First Name') or row.get('first_name'),
            # etc...
        })

    # Сохранить в БД
    save_leads_to_db(file_id, leads)

    return {
        'success': True,
        'leads_parsed': len(leads),
        'file_id': file_id
    }
```

**2.2 Normalize Company Names**
```python
# Адаптировать существующий normalize_company_name.py
# - Читать из leads table (по file_id)
# - Вызывать OpenAI API
# - Обновлять normalized_company_name колонку
# Тестировать на 10 тестовых лидах
```

#### День (3-4 часа)

**2.3 Normalize Cities**
```python
# Адаптировать normalize_city.py
# Аналогично company names
# Обновлять normalized_city колонку
# Тестировать на 10 лидах
```

**2.4 Generate Icebreakers**
```python
# Адаптировать generate_icebreakers.py
# Использовать ТОЛЬКО CSV данные (company, city)
# БЕЗ web scraping в этом спринте
# Требовать offer_id параметр
# Сохранять в icebreaker колонку
# Тестировать на 10 лидах
```

#### Вечер (2-3 часа)

**2.5 Split into Batches**

Файл: `backend/scripts/split_batches.py`
```python
from backend.db.supabase import supabase

def split_into_batches(file_id: str, batch_size: int = 250):
    """Разбить leads на batches"""

    # Получить все leads
    leads = supabase.table('leads')\
        .select('*')\
        .eq('file_id', file_id)\
        .execute().data

    batches_created = []

    # Разбить на chunks
    for i in range(0, len(leads), batch_size):
        chunk = leads[i:i+batch_size]

        # Создать batch
        batch = supabase.table('batches').insert({
            'name': f'Batch {i//batch_size + 1}',
            'file_id': file_id,
            'size': len(chunk),
            'user_id': '00000000-0000-0000-0000-000000000001'
        }).execute().data[0]

        # Обновить leads
        for lead in chunk:
            supabase.table('leads').update({
                'batch_id': batch['id']
            }).eq('id', lead['id']).execute()

        batches_created.append(batch['id'])

    return {
        'success': True,
        'batches_created': len(batches_created),
        'batch_ids': batches_created
    }
```

**2.6 FastAPI Endpoints**

Файл: `backend/main.py`
```python
AVAILABLE_SCRIPTS = [
    {
        "id": "parse_csv",
        "name": "Parse CSV",
        "description": "Парсинг CSV и сохранение в БД",
        "requires_file": True,
        "config": []
    },
    {
        "id": "normalize_company_names",
        "name": "Normalize Company Names",
        "description": "Очистка названий компаний через OpenAI",
        "requires_file": True,
        "config": []
    },
    {
        "id": "normalize_cities",
        "name": "Normalize Cities",
        "description": "Сокращение названий городов",
        "requires_file": True,
        "config": []
    },
    {
        "id": "generate_icebreakers",
        "name": "Generate Icebreakers",
        "description": "Генерация персонализированных icebreakers",
        "requires_file": True,
        "config": [
            {
                "key": "offer_id",
                "label": "Выбрать Offer",
                "type": "select",
                "options": []  # Подгружать динамически
            }
        ]
    },
    {
        "id": "split_batches",
        "name": "Split into Batches",
        "description": "Разбить на батчи по 200-300 лидов",
        "requires_file": True,
        "config": [
            {
                "key": "batch_size",
                "label": "Размер батча",
                "type": "number",
                "default": 250
            }
        ]
    },
    {
        "id": "upload_to_instantly",
        "name": "Upload to Instantly",
        "description": "Загрузить батч в Instantly кампанию",
        "requires_file": False,
        "config": [
            {
                "key": "batch_id",
                "label": "Batch ID",
                "type": "text"
            },
            {
                "key": "campaign_id",
                "label": "Instantly Campaign ID",
                "type": "text"
            }
        ]
    }
]

@app.post("/api/run-script/{script_id}")
async def run_script(script_id: str, config: dict, file_id: str = None):
    if script_id == "parse_csv":
        return parse_csv_from_storage(file_id)
    elif script_id == "normalize_company_names":
        return await normalize_company_names(file_id)
    elif script_id == "normalize_cities":
        return await normalize_cities(file_id)
    elif script_id == "generate_icebreakers":
        return await generate_icebreakers(file_id, config['offer_id'])
    elif script_id == "split_batches":
        return await split_into_batches(file_id, config['batch_size'])
    elif script_id == "upload_to_instantly":
        return await upload_to_instantly(config['batch_id'], config['campaign_id'])
    else:
        raise HTTPException(status_code=404, detail="Script not found")
```

**Тестировать все endpoints через Postman**

**Итог Дня 2:**
- ✅ Все processing скрипты работают
- ✅ Все API endpoints созданы
- ✅ Можно обрабатывать лиды end-to-end (кроме Instantly upload)

---

### DAY 3: Instantly upload + Offers page + тестирование

#### Утро (3-4 часа)

**3.1 Instantly Upload Script**
```python
# Адаптировать modules/instantly/instantly_csv_uploader_curl.py
# - Читать batch из batches table
# - Получать leads для batch (с icebreakers)
# - Загружать в Instantly через curl (обход Cloudflare)
# - Сохранять instantly_lead_id обратно в leads table
# - Добавлять offer_code в custom field
# Тестировать на батче из 10 лидов
```

**3.2 Instantly Upload Endpoint**
```python
@app.post("/api/upload-to-instantly")
async def upload_to_instantly(batch_id: str, campaign_id: str):
    # Вызвать instantly upload скрипт
    # Обновить batch status
    # Вернуть результат
```

#### День (2-3 часа)

**3.3 Offers Management Page**

Файл: `frontend/src/app/offers/page.tsx`
```typescript
'use client'

import { useState, useEffect } from 'react'
import { getAllOffers, createOffer } from '@/lib/api/offers'
import { Button } from '@/components/ui/button'

export default function OffersPage() {
  const [offers, setOffers] = useState([])
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    fetchOffers()
  }, [])

  const fetchOffers = async () => {
    const data = await getAllOffers()
    setOffers(data)
  }

  return (
    <div>
      <h1>Управление Offers</h1>

      <Button onClick={() => setShowCreateModal(true)}>
        Создать Offer
      </Button>

      {/* Таблица offers */}
      <table>
        {offers.map(offer => (
          <tr key={offer.id}>
            <td>{offer.code}</td>
            <td>{offer.name}</td>
            <td>{offer.value_prop}</td>
            <td>
              <Button>Edit</Button>
              <Button>Delete</Button>
            </td>
          </tr>
        ))}
      </table>

      {/* Modal создания */}
      {showCreateModal && <CreateOfferModal onSave={createOffer} />}
    </div>
  )
}
```

**3.4 Добавить Offer Selection в Script Runner**
```typescript
// В generate_icebreakers шаге
// - Dropdown для выбора offer
// - Подгрузка offers из /api/offers
// - Передача offer_id в icebreaker generation
```

#### Вечер (2-3 часа)

**3.5 Integration Testing (10 лидов)**
```
1. Загрузить 10-lead тестовый CSV
2. Запустить normalize company names
3. Запустить normalize cities
4. Выбрать offer и сгенерировать icebreakers
5. Разбить на batches
6. Проверить batch в Supabase
7. Загрузить в Instantly тестовую кампанию
8. Проверить в Instantly UI
9. Проверить все данные в Supabase
```

**3.6 Исправить найденные проблемы**
```
- Отладка ошибок
- Подстройка промптов если нужно
- Исправление API ошибок
- Обновление документации
```

**Итог Дня 3:**
- ✅ Полный pipeline работает end-to-end
- ✅ Offers management готов
- ✅ Интеграция протестирована на 10 лидах
- ✅ Готово к 1500 лид кампании

---

### DAY 4: Production запуск + мониторинг (опционально)

#### Утро (2-3 часа)

**4.1 Запуск 1500 Lead Campaign**
```
1. Загрузить полный CSV с 1500 лидами
2. Запустить нормализацию (company + city)
3. Сгенерировать icebreakers (назначить offers батчам)
4. Разбить на 6 батчей (~250 каждый)
5. Проверить батчи в Supabase
6. Загрузить батчи в Instantly кампании
```

**4.2 Мониторинг Upload Progress**
```
- Смотреть job status
- Проверять error logs
- Верифицировать данные в Instantly
- Проверять консистентность данных в Supabase
```

#### День (3-4 часа) - БОНУС

**4.3 Instantly Event Sync (бонусная фича)**
```python
# Создать backend/scripts/sync_instantly_events.py
# - Получать events из Instantly API (send, open, click, reply)
# - Сохранять в events table
# - Линковать к leads через instantly_lead_id
# - Тестировать incremental sync
```

**4.4 Setup Cron Job (бонус)**
```
- Создать простой cron скрипт
- Запускать sync_instantly_events.py каждые 10 минут
- Тестировать: Отправить тестовый email → event появляется в Supabase
```

**Итог Дня 4:**
- ✅ Кампания запущена с 1500 лидами
- ✅ Все лиды в Instantly
- ✅ Event sync работает (бонус)
- ✅ Спринт завершён!

---

## ⚠️ РИСКИ И МИТИГАЦИЯ

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| OpenAI API rate limits | Средняя | Высокое | Retry логика, задержки между запросами |
| Instantly Cloudflare блоки | Низкая | Высокое | Уже используем curl метод (работает) |
| Парсинг больших CSV падает | Средняя | Среднее | Stream processing, по кускам |
| Supabase free tier лимиты | Низкая | Среднее | Мониторить usage, upgrade при необходимости |
| Таймаут выполнения скриптов | Средняя | Высокое | Разбивать на меньшие батчи, async обработка |
| Проблемы миграции данных | Средняя | Высокое | Тестировать на маленьком датасете (10 лидов) |

---

## ✅ КРИТЕРИИ УСПЕХА

### Технические метрики:
- ✅ 100% лидов распарсено из CSV
- ✅ 95%+ успешная нормализация
- ✅ 100% icebreaker generation coverage
- ✅ 100% успешная загрузка в Instantly
- ✅ <5 минут общее время обработки 1500 лидов

### Бизнес метрики:
- ✅ Кампания запущена в Instantly
- ✅ 2-3 offers A/B тестируются по батчам
- ✅ Event sync работает (бонус)
- ✅ Готово к масштабированию до 10K+ лидов/месяц

---

## 📝 ТЕХНИЧЕСКИЕ ЗАМЕТКИ

### Environment Variables
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
OPENAI_API_KEY=sk-xxx
INSTANTLY_API_KEY=xxx
```

### Стратегия тестирования
1. День 1: Тестировать database операции вручную
2. День 2: Тестировать каждый скрипт на 10 лидах
3. День 3: Integration тест на 10 лидах
4. День 4: Запуск с 1500 лидами

### Rollback план
- Хранить CSV файлы в Supabase Storage (backup)
- Можно перезапустить любой скрипт в любое время
- Database транзакции для критичных операций
- Ручная верификация перед Instantly upload

---

## 🎯 СЛЕДУЮЩИЙ СПРИНТ

После завершения этого спринта:
1. Website scraping для улучшенных icebreakers
2. Продвинутая сегментация (seniority, industry)
3. Multi-user аутентификация + RLS
4. Dashboard аналитика визуализации
5. Email sequence builder

---

## 📚 ССЫЛКИ НА ДОКУМЕНТАЦИЮ

- **Оригинальный план спринта:** `sprint-plan.md`
- **SQL схема:** `docs/sql/001_core_schema.sql`
- **ADR:** `docs/ADR.md`
- **CHANGELOG:** `CHANGELOG.md`
- **CLAUDE.md:** Coding guidelines (Python + Next.js)
