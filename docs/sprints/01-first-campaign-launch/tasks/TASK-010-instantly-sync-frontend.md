# TASK-010: Instantly Sync Frontend Page & API Endpoints

---

## Metadata

```yaml
id: "TASK-010"
title: "Create Instantly Sync Frontend Page with File Upload"
status: "planned"
priority: "P1"
labels: ["frontend", "backend", "instantly", "ui"]
dependencies: ["TASK-009"]
created: "2025-10-03"
assignee: "AI Agent"
```

---

## 1. Цель (High-Level Objective)

Создать отдельную frontend страницу `/instantly-sync` с двумя режимами: загрузка JSON файла и будущая API синхронизация, + FastAPI endpoint для обработки.

---

## 2. Контекст (Background)

**Требования:**
1. Новая страница `/instantly-sync` (отдельно от dashboard)
2. **Режим 1:** File upload - загрузка JSON файлов
3. **Режим 2:** API sync button (placeholder для будущего)
4. Результаты синхронизации (campaigns synced, accounts synced)

**Существующий паттерн:**
- `/script-runner` уже есть с file upload
- Используем shadcn/ui компоненты
- Backend на FastAPI port 8002

---

## 3. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- TASK-009 (Sync Service) завершена
- shadcn/ui components установлены
- Backend FastAPI работает

**ОГРАНИЧЕНИЯ:**
- Только JSON files (не CSV)
- File size limit 50MB
- Desktop-first (не mobile)

---

## 4. Зависимости

- [ ] TASK-009 (Instantly Sync Service) завершена
- [ ] `backend/main.py` существует
- [ ] shadcn/ui Button, Card, Alert components installed

---

## 5. Plan Контекста

### В начале:
- `frontend/src/app/script-runner/page.tsx` _(reference для file upload pattern)_
- `backend/main.py` _(будет изменён - добавить endpoints)_
- `backend/services/instantly_sync.py` _(read-only)_

### В конце:
- `frontend/src/app/instantly-sync/page.tsx`
- `backend/main.py` - с новыми endpoints
- `backend/routers/instantly.py` - FastAPI router

---

## 6. Пошаговый План

### Шаг 1: Create FastAPI router

**Файл:** `backend/routers/instantly.py`

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from services.instantly_sync import sync_from_file

router = APIRouter(prefix="/api/instantly", tags=["instantly"])

class SyncResponse(BaseModel):
    success: bool
    campaigns_synced: int
    accounts_synced: int
    daily_synced: int
    errors: list
    message: str

@router.post("/sync-from-file", response_model=SyncResponse)
async def sync_json_file(file: UploadFile = File(...)):
    """
    Upload JSON file and sync to Supabase

    Accepts: raw_data or dashboard_data JSON format
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files accepted")

    try:
        # Save uploaded file temporarily
        temp_dir = Path("uploads/instantly")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / file.filename

        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        # Sync using service
        result = sync_from_file(str(temp_file), sync_options={
            'sync_campaigns': True,
            'sync_accounts': True,
            'sync_daily': False  # Skip large dataset
        })

        # Clean up temp file
        temp_file.unlink()

        return SyncResponse(
            success=result['success'],
            campaigns_synced=result['campaigns'].get('synced', 0),
            accounts_synced=result['accounts'].get('synced', 0),
            daily_synced=result['daily_analytics'].get('synced', 0),
            errors=result.get('errors', []),
            message="Sync completed successfully" if result['success'] else "Sync failed"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-from-api")
async def sync_from_api():
    """
    Future: Sync from Instantly API (not implemented yet)
    """
    return {
        "success": False,
        "message": "API sync not implemented yet - use file upload"
    }
```

### Шаг 2: Register router in main.py

**Файл:** `backend/main.py`

```python
# Add import
from routers import instantly

# Register router
app.include_router(instantly.router)
```

### Шаг 3: Create frontend page

**Файл:** `frontend/src/app/instantly-sync/page.tsx`

```typescript
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface SyncResult {
  success: boolean
  campaigns_synced: number
  accounts_synced: number
  daily_synced: number
  errors: string[]
  message: string
}

export default function InstantlySyncPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<SyncResult | null>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
      setResult(null)
    }
  }

  const handleSyncFromFile = async () => {
    if (!selectedFile) return

    setSyncing(true)
    setResult(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('http://localhost:8002/api/instantly/sync-from-file', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      setResult(data)

    } catch (error) {
      setResult({
        success: false,
        campaigns_synced: 0,
        accounts_synced: 0,
        daily_synced: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        message: 'Sync failed'
      })
    } finally {
      setSyncing(false)
    }
  }

  const handleSyncFromAPI = async () => {
    alert('API sync not implemented yet. Use file upload instead.')
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Instantly Data Sync</h1>
        <p className="text-gray-600 mt-2">
          Synchronize Instantly campaign data to Supabase database
        </p>
      </div>

      {/* Mode 1: File Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Mode 1: Upload JSON File</CardTitle>
          <CardDescription>
            Upload raw_data or dashboard_data JSON files from Instantly
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <input
              type="file"
              accept=".json"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-600">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          <Button
            onClick={handleSyncFromFile}
            disabled={!selectedFile || syncing}
            className="w-full"
          >
            {syncing ? 'Syncing...' : 'Sync to Database'}
          </Button>
        </CardContent>
      </Card>

      {/* Mode 2: API Sync (Future) */}
      <Card>
        <CardHeader>
          <CardTitle>Mode 2: Sync from Instantly API</CardTitle>
          <CardDescription>
            Live synchronization from Instantly API (coming soon)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleSyncFromAPI}
            disabled
            variant="outline"
            className="w-full"
          >
            Sync from API (Not Implemented)
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <Alert variant={result.success ? "default" : "destructive"}>
          <AlertDescription>
            <div className="space-y-2">
              <p className="font-semibold">{result.message}</p>
              <div className="text-sm">
                <p>Campaigns synced: {result.campaigns_synced}</p>
                <p>Accounts synced: {result.accounts_synced}</p>
                {result.daily_synced > 0 && (
                  <p>Daily analytics synced: {result.daily_synced}</p>
                )}
              </div>
              {result.errors.length > 0 && (
                <div className="mt-2 text-sm">
                  <p className="font-semibold">Errors:</p>
                  <ul className="list-disc list-inside">
                    {result.errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}
```

### Шаг 4: Add to navigation

**Файл:** `frontend/src/app/page.tsx`

Add link to `/instantly-sync` in main navigation.

---

## 7. Критерии Приёмки

- [ ] `backend/routers/instantly.py` создан
- [ ] Router registered in `backend/main.py`
- [ ] `POST /api/instantly/sync-from-file` works
- [ ] `frontend/src/app/instantly-sync/page.tsx` создан
- [ ] File upload UI works
- [ ] Sync button triggers backend sync
- [ ] Results display (campaigns/accounts synced)
- [ ] Error messages показываются при ошибках
- [ ] Test with real JSON file passes

---

## 8. Стратегия Тестирования

**Manual E2E Test:**
1. Start backend: `cd backend && uvicorn main:app --reload --port 8002`
2. Start frontend: `cd frontend && npm run dev`
3. Navigate to `http://localhost:3000/instantly-sync`
4. Upload `raw_data_20250921_125555.json`
5. Click "Sync to Database"
6. Check results show: "Campaigns synced: 4, Accounts synced: 10"
7. Verify in Supabase:
```sql
SELECT COUNT(*) FROM instantly_campaigns_raw; -- Should be 4
SELECT COUNT(*) FROM instantly_accounts_raw;  -- Should be 10
```

---

**Task Version:** 1.0
