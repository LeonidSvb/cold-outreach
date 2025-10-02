# Cold Outreach Automation Platform - Claude Coding Guidelines

## 🌍 ОБЩИЕ ПРАВИЛА (Python + Next.js)

### Основные принципы

- **Простота превыше всего** - предпочитайте простые решения сложным
- **DRY (Don't Repeat Yourself)** - избегайте дублирования кода
- **Environment Awareness** - код работает одинаково в dev, test, prod
- **Focused Changes** - только запрошенные изменения, никакого scope creep
- **Conservative Technology** - исчерпайте существующие решения перед добавлением нового

### Критически важно

- **НИКОГДА не используйте эмодзи** в Python/Next.js коде (проблемы с Windows encoding)
- **Все комментарии только на английском** (для обоих стеков)
- **MANDATORY:** Экранируйте JSON placeholders двойными скобками перед .format() вызовами

---

## 📂 Организация кода

### Чистота кодовой базы
- Держите codebase очень чистым и организованным
- Следуйте существующей структуре файлов и naming conventions
- Группируйте связанную функциональность вместе
- Удаляйте неиспользуемый код и imports

### Размер файлов
- Держите файлы под 200-300 строк кода
- Рефакторьте большие файлы, разбивая на модули
- Разбивайте сложные компоненты на composable части

### Именование файлов (January 2025)

**Python Scripts:** `{purpose}.py`
- Примеры: `apollo_lead_collector.py`, `openai_mass_processor.py`
- Простые описательные имена без дат

**Results:** `{script_name}_{YYYYMMDD_HHMMSS}.json`
- Примеры: `apollo_leads_20250119_143022.json`
- Timestamp обеспечивает уникальность и хронологию

**React Components:** `{ComponentName}.tsx`
- Примеры: `FileUpload.tsx`, `DashboardPage.tsx`
- PascalCase для компонентов

**Directories:**
- Python: `snake_case` (например, `modules/apollo/`)
- Next.js: `kebab-case` (например, `script-runner/`)

### Организация модулей
- Каждый модуль содержит только связанную функциональность
- Все скрипты имеют embedded configs (no external config files)
- Results в module-specific results/ folders
- **НИКОГДА не создавайте пустые папки** - только когда нужно
- **УДАЛЯЙТЕ пустые папки** сразу после cleanup

---

## ⚠️ Error Handling

### Guard Clauses (Early Returns)
- Обрабатывайте errors и edge cases в начале функций
- Используйте early returns для ошибок
- Избегайте глубокой вложенности if
- Помещайте "happy path" последним

**Python пример:**
```python
def process_csv(file_path: str):
    if not file_path:
        raise ValueError("File path is required")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Happy path
    return pd.read_csv(file_path)
```

**Next.js пример:**
```typescript
export async function fetchData(id: string) {
  if (!id) throw new Error('ID is required');

  const response = await fetch(`/api/data/${id}`);
  if (!response.ok) throw new Error('Fetch failed');

  return await response.json();
}
```

### Error Messages
- Пишите понятные сообщения: "Failed to save user data", не "Error 500"
- Логируйте ошибки с контекстом
- Не глотайте errors - показывайте пользователю или логируйте
- Fail fast and clearly

---

## 📊 Data и Testing

### No Fake Data in Production
- Mocking только для тестов
- **Никогда не добавляйте** stubbing или fake data в dev/prod
- Используйте реальные данные и proper error handling

### Environment Files
- **НИКОГДА не перезаписывайте .env** без явного разрешения
- Всегда спрашивайте перед изменением environment конфигурации
- Делайте backup существующих .env при необходимости изменений

---

## 🔧 Git и Version Control

### Commit Standards
- Чёткие описательные commit messages: "fix user login bug", не "fix"
- Atomic commits - один commit = одна feature/fix
- Review изменений через git diff перед коммитом
- **Никогда не коммитьте:** secrets, .env файлы, временные файлы

### Branch Management
- Описательные branch names: `feature/add-auth`, `fix/login-crash`
- Один branch = одна задача, не мешайте фичи
- Удаляйте merged branches для чистоты репозитория
- Для solo projects можно работать в main, но делайте частые commits

---

## ⚡ Performance

### Оптимизация
- Оптимизируйте для читаемости сначала, производительность потом
- Не добавляйте библиотеки без необходимости - каждая добавляет вес
- Профилируйте перед оптимизацией, не гадайте
- Для небольших проектов: readability > performance

### Batch Processing
- Планируйте изменения заранее - что нужно изменить во всех файлах
- Делайте массовые изменения одним batch, не файл за файлом
- Используйте find/replace, regex для массовых правок
- Коммитьте batches изменений, не каждый файл отдельно

---

## 🐍 PYTHON-СПЕЦИФИЧНЫЕ ПРАВИЛА

### Основные принципы
- Пишите чёткий технический код с точными примерами
- Функциональное программирование; избегайте классов где возможно
- Описательные имена переменных: `is_active`, `has_permission`
- `snake_case` для директорий и файлов

### FastAPI Backend

**Структура функций:**
- `def` для чистых функций, `async def` для асинхронных
- Type hints для всех сигнатур функций
- Pydantic модели вместо словарей для валидации
- Структура файла: router, sub-routes, utilities, типы

**Роуты и эндпоинты:**
- Функциональные компоненты и Pydantic модели
- Декларативные определения роутов с type annotations
- Минимизируйте `@app.on_event("startup")`, используйте lifespan context managers
- Middleware для логирования, мониторинга, оптимизации

**Валидация:**
- Pydantic `BaseModel` для input/output
- Schema классы для каждой модели данных
- Валидация на уровне роутов, бизнес-логика отдельно

**API Response Format:**
```python
# Success
{"success": true, "data": {...}, "message": "Success"}

# Error
{"success": false, "error": "Error message", "details": {...}}
```

### Web Scraping (HTTP-Only)
- **ТОЛЬКО встроенные Python библиотеки** (urllib, requests)
- **НИКОГДА внешние сервисы** типа Firecrawl, Selenium
- requests для HTTP GET/POST
- BeautifulSoup для parsing HTML
- Rate limiting и random delays между запросами
- Retry с exponential backoff

### CSV/Pandas Processing
- pandas для манипуляции и анализа
- Method chaining для трансформаций
- `loc` и `iloc` для явного выбора данных
- `groupby` для агрегации
- Автоопределение delimiter
- Валидация column types
- Обработка encoding (UTF-8, latin1)

### Асинхронность
- `async def` для I/O-bound задач
- httpx для асинхронных HTTP запросов
- Connection pooling для database
- Background tasks для длительных операций

### Dependencies
- FastAPI
- Pydantic v2
- httpx (HTTP requests)
- pandas (CSV processing)
- python-dotenv (.env files)

### Стандарт структуры скрипта
```python
#!/usr/bin/env python3
"""
=== SCRIPT NAME ===
Version: 1.0.0 | Created: YYYY-MM-DD

PURPOSE:
Brief description

FEATURES:
- Key capabilities

USAGE:
1. Configure CONFIG section
2. Run: python script_name.py
3. Results saved to results/

IMPROVEMENTS:
v1.0.0 - Initial version
"""

CONFIG = {
    "API_SETTINGS": {...},
    "PROCESSING": {...},
    "OUTPUT": {...}
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0
}

def main():
    pass

if __name__ == "__main__":
    main()
```

### Testing (Python)
- pytest для unit тестов
- **ТОЛЬКО реальные данные** (no mocks в production)
- Тестируйте edge cases и error handling
- Integration тесты для API endpoints
- Structured logging (JSON)
- Performance metrics (время, API costs)

---

## ⚛️ NEXT.JS-СПЕЦИФИЧНЫЕ ПРАВИЛА

### Основные принципы
- Пишите краткий технический TypeScript код
- Функциональное и декларативное программирование
- Описательные имена переменных: `isLoading`, `hasError`
- Структура файла: component, subcomponents, helpers, types

### TypeScript
- TypeScript для всего кода
- **Предпочитайте `interface` вместо `type`**
- Избегайте enums; используйте maps
- Всегда определяйте proper types для props и state

```typescript
// ✅ Хорошо
interface FileUploadProps {
  onUpload: (file: File) => void;
  maxSize?: number;
}

export function FileUpload({ onUpload, maxSize }: FileUploadProps) {
  // Component logic
}
```

### React Server Components (RSC)
- **Минимизируйте `'use client'`** - используйте Server Components по умолчанию
- `'use client'` только для Web API access в небольших компонентах
- Избегайте для data fetching или state management
- Wrap client components в Suspense с fallback

```typescript
// ✅ Server Component (по умолчанию)
async function DashboardPage() {
  const data = await fetchData();
  return <Dashboard data={data} />;
}

// ✅ Client Component (минимальный)
'use client';
export function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  // Только client-side логика
}
```

### UI и Styling

**Tailwind CSS:**
- Tailwind для всех стилей; избегайте CSS files
- **Desktop-first подход** (НЕ mobile-first для этого проекта)
- `cn()` utility из `lib/utils.ts` для conditional classes

**shadcn/ui:**
- shadcn/ui + Radix UI для компонентов
- Следуйте shadcn/ui conventions
- Кастомизация в `components/ui/`

```typescript
import { cn } from "@/lib/utils";

export function Button({ variant, isLoading, children }: ButtonProps) {
  return (
    <button
      className={cn(
        "px-4 py-2 rounded-md font-medium",
        variant === 'primary' && "bg-blue-600 text-white",
        isLoading && "opacity-50 cursor-not-allowed"
      )}
    >
      {children}
    </button>
  );
}
```

### Performance Optimization

**Images:**
- Next.js Image component
- WebP format, size data
- Lazy loading для изображений

**Code Splitting:**
- Dynamic imports для тяжелых компонентов
- Lazy loading для non-critical компонентов

```typescript
import dynamic from 'next/dynamic';

const CSVTransformer = dynamic(() => import('./CSVTransformer'), {
  loading: () => <Spinner />,
  ssr: false
});
```

### Data Fetching

**Server-Side:**
- Server Components для data fetching
- Proper error handling и loading states
- React Suspense для async компонентов

**Client-Side:**
- SWR или TanStack Query
- Proper caching strategies

```typescript
// Server Component
async function DashboardPage() {
  const data = await fetch('http://localhost:8000/api/data', {
    cache: 'no-store'
  });
  return <Dashboard data={await data.json()} />;
}

// Client Component
'use client';
import useSWR from 'swr';

export function FileList() {
  const { data, error, isLoading } = useSWR('/api/files', fetcher);
  if (isLoading) return <Skeleton />;
  return <FileListView files={data} />;
}
```

### State Management
- `nuqs` для URL search parameter state
- `useState` только для truly local UI state
- Избегайте `useEffect` когда возможно
- Zustand для complex global state (если нужен)

### Backend Integration (FastAPI)
- Next.js API routes как proxy к FastAPI backend
- Backend URL: `http://localhost:8000` (dev)
- Proper CORS handling в FastAPI
- Environment variables для API endpoints

```typescript
// src/app/api/upload/route.ts
export async function POST(request: NextRequest) {
  const formData = await request.formData();

  const response = await fetch('http://localhost:8000/api/upload', {
    method: 'POST',
    body: formData,
  });

  return NextResponse.json(await response.json());
}
```

### Supabase Integration

**КРИТИЧНО ВАЖНО:**
- Используйте `@supabase/ssr` (НЕ deprecated `auth-helpers-nextjs`)
- Используйте ТОЛЬКО `getAll` и `setAll` методы
- **НИКОГДА не используйте** `get`, `set`, `remove` методы

```typescript
// Browser Client
import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

// Server Client
import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            );
          } catch {
            // Ignore if called from Server Component
          }
        },
      },
    }
  );
}
```

### Component Structure
```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

// Types/Interfaces
interface FileUploadProps {
  onUpload: (file: File) => void;
}

// Main Component
export function FileUpload({ onUpload }: FileUploadProps) {
  // State
  const [file, setFile] = useState<File | null>(null);

  // Event handlers
  const handleUpload = () => {
    if (file) onUpload(file);
  };

  // Render
  return <div>...</div>;
}

// Helper functions
function formatSize(bytes: number) {
  return `${bytes / 1024} KB`;
}
```

---

## 📁 PROJECT STRUCTURE (Updated January 2025)

```
├── modules/             # MODULAR ARCHITECTURE
│   ├── shared/          # Common utilities
│   │   ├── logger.py    # Auto-logging system
│   │   └── google_sheets.py
│   ├── apollo/          # Apollo API integration
│   │   ├── apollo_lead_collector.py
│   │   └── results/     # Timestamped JSON results
│   ├── openai/          # OpenAI processing
│   │   ├── openai_mass_processor.py
│   │   └── results/
│   ├── scraping/        # Web scraping (HTTP-only)
│   │   └── results/
│   ├── sheets/          # Google Sheets operations
│   │   └── results/
│   └── instantly/       # Instantly API
│       └── results/
├── data/                # DATA MANAGEMENT
│   ├── raw/            # Original CSVs
│   ├── processed/      # Final processed data
│   └── logs/           # Auto-logger outputs
├── frontend/            # NEXT.JS APP
│   ├── src/
│   │   ├── app/        # App Router pages
│   │   ├── components/ # React components
│   │   │   └── ui/     # shadcn/ui components
│   │   └── lib/        # Utilities
├── backend/             # FASTAPI BACKEND
│   ├── main.py
│   ├── routers/
│   └── models/
├── dashboard/           # AUTO-GENERATED ANALYTICS
│   └── index.html      # Interactive dashboard
└── archive/             # ARCHIVED FILES
```

### Path Configuration
- Core tools: `../../.env` для root config
- Service scripts: `../../../.env` для root config
- Frontend API routes: `http://localhost:8000` (FastAPI backend)
- Lead data flow: raw → processed (2-stage pipeline)
- File naming: YYYYMMDD format (local Bali timezone)

---

## ✅ КЛЮЧЕВЫЕ КОНВЕНЦИИ

### Python
1. Простота превыше всего
2. DRY принцип
3. Real data only (no mocks в production)
4. HTTP-only scraping (встроенные библиотеки)
5. Embedded configs (no external config files)
6. No emojis (Windows encoding issues)
7. English comments

### Next.js
1. Server Components First (RSC по умолчанию)
2. Type Safety (TypeScript + interfaces)
3. Tailwind Only (no CSS files)
4. Desktop-first (НЕ mobile для этого проекта)
5. Performance (code splitting, lazy loading)
6. Error Handling (early returns, guard clauses)
7. No Emojis (consistency с Python)
8. English Comments

### Общие
- All icebreakers и emails на английском (или другом нужном языке, НЕ русском)
- Никогда не используйте эмодзи в скриптах
- Все комментарии на английском
