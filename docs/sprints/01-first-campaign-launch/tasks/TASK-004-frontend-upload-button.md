# TASK-004: Frontend Upload to Supabase Button

---

## Metadata

```yaml
id: "TASK-004"
title: "Add Upload to Supabase Button in Frontend"
status: "planned"
priority: "P1"
labels: ["frontend", "react", "nextjs", "ui"]
dependencies: ["TASK-003"]
created: "2025-10-03"
assignee: "AI Agent"
```

---

## 1. Цель (High-Level Objective)

Добавить кнопку "Upload to Supabase" в Lead Processing Center UI с прогресс-индикатором, success/error уведомлениями и отображением результатов загрузки.

---

## 2. Контекст (Background)

**Текущая ситуация:**
- Есть Lead Processing Center UI (`frontend/src/app/script-runner/page.tsx`)
- Можно загружать CSV и видеть preview
- Можно видеть detected columns
- НЕТ кнопки для загрузки в Supabase
- НЕТ feedback после успешной загрузки

**Проблема:**
- После upload CSV в frontend - он остаётся только в `backend/uploads/` (temporary)
- Пользователь не может загрузить данные в Supabase через UI
- Нет визуального feedback о процессе загрузки

**Почему важно:**
- One-click загрузка CSV → Supabase
- User-friendly UX с прогрессом и результатами
- Preparation для campaign launch (данные в БД)

---

## 3. 🤔 ВОПРОСЫ ДЛЯ ДЕТАЛИЗАЦИИ (ответить перед началом)

### Перед началом выполнения ответь на эти вопросы:

**Q1: Место размещения кнопки**
Где показывать кнопку "Upload to Supabase"?
- **Вариант A:** После file preview (после таблицы с последними 15 rows)
- **Вариант B:** В file manager dropdown (рядом с файлом)
- **Вариант C:** Отдельная секция "Actions" с multiple buttons
- **Рекомендация:** Вариант A - логичный flow (upload → preview → upload to DB)

**Q2: UI/UX для прогресса**
Как показывать процесс загрузки?
- **Вариант A:** Loading spinner в кнопке
- **Вариант B:** Progress bar (0-100%)
- **Вариант C:** Modal dialog с steps (companies → leads → done)
- **Рекомендация:** Вариант A для MVP, Вариант C для production

**Q3: Success notification**
Как показать успешную загрузку?
- **Вариант A:** Toast notification (shadcn/ui Sonner)
- **Вариант B:** Alert component под кнопкой
- **Вариант C:** Modal dialog с detailed results
- **Рекомендация:** Вариант A (Toast) + Вариант C (optional detailed view)

**Q4: Отображение результатов**
Какие метрики показывать после загрузки?
- Companies created/updated
- Leads created/updated
- Errors (если есть)
- **Показывать в:**
  - Toast (краткая инфа)?
  - Expandable section (детали)?
  - **Рекомендация:** Toast с summary + expandable details

**Q5: Error handling**
Что показывать если загрузка failed?
- **Вариант A:** Error toast с retry button
- **Вариант B:** Error alert с error details
- **Вариант C:** Modal с error log
- **Рекомендация:** Вариант A + Вариант B (show errors list)

**Q6: Повторная загрузка**
Можно ли загружать один файл несколько раз?
- **Вариант A:** Кнопка disabled после успешной загрузки
- **Вариант B:** Кнопка always enabled (для re-upload)
- **Вариант C:** Show warning "Already uploaded, re-upload?"
- **Рекомендация:** Вариант B (re-upload для обновления данных)

**Q7: Validation перед загрузкой**
Проверять что-то перед отправкой в Supabase?
- Проверить что detected_columns содержит минимум email?
- Проверить что detected_columns содержит company_name?
- Показать warning если нет website (не будет company deduplication)?
- **Рекомендация:** Show warning, но allow upload anyway

**Q8: shadcn/ui компоненты**
Какие компоненты использовать?
- Button (уже есть)
- Toast/Sonner (для notifications)
- Alert (для результатов)
- Badge (для stats)
- **Нужно установить новые компоненты?**

---

## 4. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- TASK-003 выполнен - endpoint `POST /api/supabase/upload-csv` работает
- shadcn/ui уже настроен в проекте
- File preview уже показывается в UI
- User понимает что такое "upload to Supabase"

**ОГРАНИЧЕНИЯ:**
- Next.js 15 + React Server Components
- No manual column mapping UI (используем auto-detection)
- No batch upload (one file at a time)

---

## 5. Plan Контекста (Context Plan)

### В начале (добавить в контекст AI):
- `frontend/src/app/script-runner/page.tsx` _(main UI file)_
- `backend/main.py` endpoint _(для понимания API response)_
- Existing shadcn/ui components (Button, Toast, Alert)

### В конце (должно быть создано/изменено):
- `frontend/src/app/script-runner/page.tsx` - добавлена кнопка + upload logic
- Возможно новые shadcn/ui components (Sonner toast)
- Возможно новый компонент `UploadResults.tsx` (для детального отображения)

---

## 6. Пошаговый План (Low-Level Steps)

### Шаг 1: Установка Toast component (если нужен)

**Команда:**
```bash
cd frontend
npx shadcn@latest add sonner
```

**Проверить:**
- `frontend/src/components/ui/sonner.tsx` создан
- Toast provider добавлен в layout

---

### Шаг 2: State management для upload

**Файл:** `frontend/src/app/script-runner/page.tsx`

**Действие:**
```typescript
'use client';

import { useState } from 'react';
import { toast } from 'sonner';

// Добавить state
const [isUploading, setIsUploading] = useState(false);
const [uploadResults, setUploadResults] = useState<{
  success: boolean;
  companies_created: number;
  companies_updated: number;
  leads_created: number;
  leads_updated: number;
  errors: string[];
} | null>(null);
```

---

### Шаг 3: Upload function

**Файл:** `frontend/src/app/script-runner/page.tsx`

**Действие:**
```typescript
async function handleUploadToSupabase(fileId: string) {
  setIsUploading(true);
  setUploadResults(null);

  try {
    const response = await fetch(`http://localhost:8002/api/supabase/upload-csv?file_id=${fileId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Upload failed');
    }

    const data = await response.json();

    setUploadResults(data);

    // Success toast
    toast.success('CSV uploaded to Supabase!', {
      description: `Created ${data.companies_created} companies, ${data.leads_created} leads`,
    });

  } catch (error) {
    console.error('Upload error:', error);

    toast.error('Upload failed', {
      description: error instanceof Error ? error.message : 'Unknown error',
    });

  } finally {
    setIsUploading(false);
  }
}
```

---

### Шаг 4: Upload Button UI

**Файл:** `frontend/src/app/script-runner/page.tsx`

**Действие:**
```tsx
{/* After file preview section */}
{selectedFile && (
  <div className="mt-6 flex flex-col gap-4">
    <Button
      onClick={() => handleUploadToSupabase(selectedFile.id)}
      disabled={isUploading}
      className="w-full max-w-md"
    >
      {isUploading ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Uploading to Supabase...
        </>
      ) : (
        <>
          <Database className="mr-2 h-4 w-4" />
          Upload to Supabase
        </>
      )}
    </Button>

    {/* Results summary */}
    {uploadResults && uploadResults.success && (
      <Alert className="max-w-md">
        <CheckCircle2 className="h-4 w-4" />
        <AlertTitle>Upload Successful</AlertTitle>
        <AlertDescription>
          <div className="mt-2 space-y-1">
            <div className="flex justify-between">
              <span>Companies created:</span>
              <Badge variant="default">{uploadResults.companies_created}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Companies updated:</span>
              <Badge variant="secondary">{uploadResults.companies_updated}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Leads created:</span>
              <Badge variant="default">{uploadResults.leads_created}</Badge>
            </div>
            <div className="flex justify-between">
              <span>Leads updated:</span>
              <Badge variant="secondary">{uploadResults.leads_updated}</Badge>
            </div>
          </div>
        </AlertDescription>
      </Alert>
    )}

    {/* Error display */}
    {uploadResults && uploadResults.errors.length > 0 && (
      <Alert variant="destructive" className="max-w-md">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Some errors occurred</AlertTitle>
        <AlertDescription>
          <ul className="mt-2 list-disc pl-4">
            {uploadResults.errors.slice(0, 5).map((error, i) => (
              <li key={i} className="text-sm">{error}</li>
            ))}
          </ul>
          {uploadResults.errors.length > 5 && (
            <p className="mt-2 text-sm">... and {uploadResults.errors.length - 5} more</p>
          )}
        </AlertDescription>
      </Alert>
    )}
  </div>
)}
```

**Детали:**
- Loading state в кнопке (spinner icon)
- Success Alert с detailed stats
- Error Alert с first 5 errors
- Icons: Database, Loader2, CheckCircle2, AlertCircle

---

### Шаг 5: Imports

**Файл:** `frontend/src/app/script-runner/page.tsx`

**Добавить:**
```typescript
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { Database, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
```

---

### Шаг 6: Validation (optional)

**Файл:** `frontend/src/app/script-runner/page.tsx`

**Действие:**
```typescript
// Before handleUploadToSupabase
function validateBeforeUpload(file: UploadedFile): string | null {
  const hasEmail = Object.values(file.detected_columns).includes('email');
  const hasCompany = Object.values(file.detected_columns).includes('company_name');

  if (!hasEmail) {
    return 'Warning: No email column detected. Leads may not be created properly.';
  }

  if (!hasCompany) {
    return 'Warning: No company column detected. Company deduplication may not work.';
  }

  return null; // No warnings
}

// In Button onClick
const warning = validateBeforeUpload(selectedFile);
if (warning) {
  const proceed = window.confirm(`${warning}\n\nContinue anyway?`);
  if (!proceed) return;
}

handleUploadToSupabase(selectedFile.id);
```

---

## 7. Типы и Интерфейсы

```typescript
interface UploadResults {
  success: boolean;
  file_name: string;
  total_rows: number;
  companies_created: number;
  companies_updated: number;
  leads_created: number;
  leads_updated: number;
  errors: string[];
}

interface UploadedFile {
  id: string;
  filename: string;
  rows: number;
  columns: string[];
  detected_columns: Record<string, string>;
}
```

---

## 8. Критерии Приёмки (Acceptance Criteria)

- [ ] Кнопка "Upload to Supabase" добавлена после file preview
- [ ] Кнопка показывает loading state (spinner) во время upload
- [ ] Success toast появляется при успешной загрузке
- [ ] Success Alert показывает детальные результаты:
  - [ ] Companies created/updated
  - [ ] Leads created/updated
- [ ] Error toast появляется при неудачной загрузке
- [ ] Error Alert показывает список ошибок (до 5)
- [ ] UI остаётся responsive во время загрузки
- [ ] Можно загружать файл несколько раз (re-upload)
- [ ] Test на реальном CSV:
  - [ ] Upload 10 leads CSV
  - [ ] Проверить что toast появился
  - [ ] Проверить что results отобразились
  - [ ] Проверить в Supabase что данные загружены

---

## 9. Стратегия Тестирования (Testing Strategy)

**Manual UI Testing:**
1. Upload CSV через file upload
2. Click "Upload to Supabase"
3. Verify loading spinner shows
4. Verify toast notification appears
5. Verify results Alert shows stats
6. Test re-upload same file
7. Test upload different file

**Error Testing:**
1. Stop backend server
2. Try upload → verify error toast
3. Start backend, try again → verify success

**Integration Testing:**
1. Upload CSV with 10 rows
2. Check Supabase Dashboard:
   - Companies table has records
   - Leads table has records
3. Re-upload same CSV
4. Verify no duplicate companies created

**Visual Testing:**
1. Check button styling (icons, spacing)
2. Check toast positioning
3. Check Alert layout (stats grid)
4. Test on mobile (responsive design)

---

## 10. Заметки / Ссылки (Notes / Links)

**Документация:**
- shadcn/ui Button: https://ui.shadcn.com/docs/components/button
- shadcn/ui Toast: https://ui.shadcn.com/docs/components/sonner
- shadcn/ui Alert: https://ui.shadcn.com/docs/components/alert
- Lucide Icons: https://lucide.dev

**Связанные задачи:**
- TASK-003: Backend endpoint (dependency)
- TASK-005: E2E testing (будет использовать этот UI)

**Референсы:**
- `frontend/src/app/script-runner/page.tsx` - existing UI
- `backend/main.py` - endpoint `/api/supabase/upload-csv`

**UI Components to install:**
```bash
npx shadcn@latest add sonner  # Toast notifications
npx shadcn@latest add alert   # Results display
npx shadcn@latest add badge   # Stats numbers
```

---

## ✅ Pre-Execution Checklist

Перед началом выполнения ОБЯЗАТЕЛЬНО ответь на вопросы в секции 3:

- [ ] Определено место размещения кнопки (Q1: after preview/dropdown/separate section)
- [ ] Выбран UI для прогресса (Q2: spinner/progress bar/modal)
- [ ] Решено как показывать success (Q3: Toast/Alert/Modal)
- [ ] Определены метрики для отображения (Q4: какие stats показывать)
- [ ] Решено как обрабатывать errors (Q5: Toast/Alert/Modal)
- [ ] Решено про re-upload (Q6: disable/enable/warning)
- [ ] Определена validation logic (Q7: какие проверки перед upload)
- [ ] Проверены доступные shadcn/ui компоненты (Q8: что уже есть, что нужно добавить)

**После ответов на вопросы → начинать выполнение задачи!**

---

**Task Status:** Готова к детализации → Жду ответов на вопросы из секции 3
