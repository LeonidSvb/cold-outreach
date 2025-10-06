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

### Commit Standards (Conventional Commits)
**MANDATORY: Always use Conventional Commits format**

```
<type>(<scope>): <subject>

[optional body]
[optional footer]
```

**Types:**
- `feat(scope):` - новая фича
- `fix(scope):` - баг фикс
- `docs(scope):` - только документация
- `refactor(scope):` - рефакторинг без изменения функциональности
- `test(scope):` - добавление тестов
- `chore(scope):` - техническая работа (dependencies, config)

**Examples:**
```bash
feat(csv-upload): Add preview before upload
fix(instantly-sync): Resolve API timeout in sync service
docs(task-004): Update status to done with test results
refactor(logging): Simplify module structure
```

**Rules:**
- Atomic commits - один commit = одна feature/fix
- Review изменений через git diff перед коммитом
- **Никогда не коммитьте:** secrets, .env файлы, временные файлы

### Branch Management
- Описательные branch names: `feature/add-auth`, `fix/login-crash`
- Один branch = одна задача, не мешайте фичи
- Удаляйте merged branches для чистоты репозитория
- Для solo projects можно работать в main, но делайте частые commits

### CHANGELOG Management
**Source of Truth:** Git commits (Conventional Commits)

**Auto-generation:**
```bash
# Python script (primary method)
python scripts/generate_changelog.py

# NPM alternative (universal)
npm run changelog
```

**Rules:**
- CHANGELOG.md генерируется из git commits автоматически
- Ручные правки только в секциях: "Next Session Plan", "Known Issues"
- Все остальные секции (Added/Fixed/Changed) = auto-generated
- Не дублируйте информацию между commits и CHANGELOG

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

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

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
    logger.info("Script started")
    try:
        # Main logic here
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error("Script failed", error=e)
        raise

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

**📖 Module Template:** See `/docs/MODULE_TEMPLATE.md` for standard module structure
**🎯 Reference Implementation:** `modules/instantly/` (perfect example)

```
├── modules/             # MODULAR ARCHITECTURE
│   ├── shared/          # Common utilities
│   │   ├── logger.py    # Auto-logging system
│   │   └── google_sheets.py
│   ├── instantly/       # ⭐ Reference implementation (follow this structure)
│   │   ├── docs/        # Documentation
│   │   ├── scripts/     # Executable scripts
│   │   ├── tests/       # Integration tests
│   │   ├── results/     # JSON outputs
│   │   └── data/        # Input files & cache
│   ├── apollo/          # Apollo API integration
│   │   └── results/     # Timestamped JSON results
│   ├── openai/          # OpenAI processing
│   │   └── results/
│   ├── scraping/        # Web scraping (HTTP-only)
│   │   └── results/
│   └── sheets/          # Google Sheets operations
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
8. **MANDATORY: Universal Logger in ALL new scripts** - `from modules.logging.shared.universal_logger import get_logger`

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

---

## 🤖 AI AGENT AUTOMATION RULES

### Workflow Philosophy
**User speaks natural language → AI does everything automatically**

User should NEVER manually:
- ❌ Write `git commit` commands
- ❌ Run `npm run changelog`
- ❌ Edit CHANGELOG.md manually
- ❌ Update TASK-XXX.md files
- ❌ Run Python scripts manually

AI Agent does automatically:
- ✅ Write code
- ✅ Commit with Conventional Commits format
- ✅ Generate CHANGELOG from commits
- ✅ Update TASK status when done
- ✅ Show user what was done

### Commit Automation (MANDATORY)

**Every time AI makes significant changes:**

1. **Write code** (user requested feature/fix)
2. **Commit immediately** with Conventional Commits:
   ```bash
   git add .
   git commit -m "feat(scope): Description of change"
   ```
3. **Generate CHANGELOG** (after batch of commits):
   ```bash
   python scripts/generate_changelog.py
   ```
4. **Show user** what was done (brief summary)

**Conventional Commits Examples:**
```bash
feat(csv-upload): Add preview button with deduplication
fix(instantly-sync): Resolve timeout in API calls
docs(task-004): Mark status as done
refactor(logging): Simplify module structure
chore(deps): Update Supabase to v2.58.0
```

### Control Points (Safety Gates)

**Auto-execute (no approval needed):**
- ✅ Code changes (user sees result in chat)
- ✅ `git add .` (safe, reversible)
- ✅ `git commit -m` (safe, can revert)
- ✅ CHANGELOG updates (auto-generated, user sees diff)
- ✅ TASK-XXX.md status updates (documentation only)

**Ask before executing (require approval):**
- ⏸️ `git push` - Ask: "Ready to push to GitHub. Push now?"
- ⏸️ Database migrations (production) - Ask: "Apply migration to production DB?"
- ⏸️ `.env` changes - Show what's changing, wait for approval
- ⏸️ Dependency updates - Show new versions before installing
- ⏸️ API key rotation - Always ask before changing

**Never auto-execute:**
- ❌ `npm publish` (public release)
- ❌ `rm -rf` (destructive)
- ❌ Production deployments without approval
- ❌ Billing/payment operations

### CHANGELOG Generation

**When to generate:**
- End of work session (primary)
- User explicitly requests it
- Before major git push

**Primary Method: AI Direct Generation (Recommended)**

AI generates CHANGELOG with context and understanding:

```
1. Read git log (all commits since last release)
2. Understand context and relationships between commits
3. Group by logical features (not just commit type)
4. Improve formulations for readability
5. Add relevant details and explanations
6. Format with proper structure and hierarchy
7. Preserve "Next Session Plan" and "Known Issues"
8. Show user diff for review
9. Commit and push after approval
```

**Quality comparison:**
- Python script: Mechanical parsing, copies commit messages as-is (6/10)
- AI Direct: Understands context, groups logically, improves wording (9/10)

**Example:**
```markdown
# Python Script output (mechanical):
### Added
- Add button
- Fix timeout

# AI Direct output (contextual):
### Added
- **CSV Upload Interface**:
  - Upload to Supabase button with preview
  - Real-time validation before upload
  - Deduplication based on email field

### Fixed
- **Instantly Sync**: Increased API timeout from 30s to 60s to prevent failures on large datasets
```

**Fallback Method: Python Script**

Available as backup when AI unavailable:
```bash
python scripts/generate_changelog.py
# or
npm run changelog
```

**Use Python script only when:**
- AI agent unavailable
- Need speed (automated CI/CD)
- Other developers without AI agent

**Manual edits allowed only in:**
- `### Next Session Plan` - user's notes about next tasks
- `### Known Issues` - current bugs/WIP items
- All other sections = AI-generated (don't edit manually)

### TASK File Updates

**When to update:**
- Task started: `status: "in_progress"`
- Task completed: `status: "done"` + `completed: "YYYY-MM-DD"`
- Major blockers found: update in task notes

**Format:**
```yaml
# Before:
status: "planned"

# During:
status: "in_progress"

# After completion:
status: "done"
completed: "2025-10-05"
```

**Commit after update:**
```bash
git commit -m "docs(task-004): Mark as completed"
```

### User Workflow Examples

**Example 1: New Feature**
```
User: "Add upload button to CSV preview"

AI:
1. [writes code for button]
2. [git add .]
3. [git commit -m "feat(csv-upload): Add upload button to preview"]
4. [python scripts/generate_changelog.py]
5. Responds: "✅ Upload button added! CHANGELOG updated."

User sees: Summary of what was done
User does NOT see: Git commands, script execution
```

**Example 2: Bug Fix**
```
User: "Fix timeout in Instantly sync"

AI:
1. [fixes code]
2. [git commit -m "fix(instantly-sync): Increase timeout to 60s"]
3. [generate changelog]
4. Responds: "✅ Fixed! Timeout increased to 60s"
```

**Example 3: Git Push (requires approval)**
```
AI: [batch of commits done]
AI: "All changes committed. Ready to push to GitHub. Push now?"
User: "Yes" or "No, wait"
AI: [git push] only after approval
```

### Universal Solution (Multi-Language Projects)

**Tools available:**

1. **Python script** (current project, full control):
   ```bash
   python scripts/generate_changelog.py
   ```

2. **NPM conventional-changelog** (JavaScript projects):
   ```bash
   npm run changelog
   # or
   conventional-changelog -p angular -i CHANGELOG.md -s
   ```

**AI chooses automatically:**
- Python project → use Python script
- JavaScript/TypeScript project → use NPM script
- Both available → prefer Python (more customizable)

### Error Handling in Automation

**If commit fails:**
```bash
# AI should:
1. Show error message
2. Ask user if should retry
3. Suggest fix if known issue
```

**If CHANGELOG generation fails:**
```bash
# AI should:
1. Commits still succeeded (safe state)
2. Notify user: "Commits done, but CHANGELOG generation failed"
3. Offer to retry or skip
```

**If git push fails:**
```bash
# AI should:
1. Show git error (e.g., "rejected - non-fast-forward")
2. Suggest: "Need to pull first? Run git pull --rebase?"
3. Wait for user decision
```

### Summary: AI Agent Responsibilities

**AI always does:**
- Write code based on natural language requests
- Commit with proper Conventional Commits format
- Generate CHANGELOG from commits
- Update TASK files when done
- Show user summary of actions taken

**AI asks before:**
- Git push to remote
- Production database changes
- Environment variable updates
- Destructive operations

**User only does:**
- Speak natural language: "Add feature X"
- Approve critical operations when asked
- Review final results

**Result:**
- User focuses on WHAT to build (strategy)
- AI handles HOW to build (implementation + automation)
