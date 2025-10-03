# TASK-009: Instantly Sync Service (Orchestration)

---

## Metadata

```yaml
id: "TASK-009"
title: "Create Instantly Sync Orchestration Service"
status: "done"
priority: "P1"
labels: ["backend", "instantly", "services"]
dependencies: ["TASK-006", "TASK-007", "TASK-008"]
created: "2025-10-03"
completed: "2025-10-03"
assignee: "AI Agent"
```

---

## 1. Цель (High-Level Objective)

Создать сервис-оркестратор который объединяет все модули (sources, transform, supabase) для выполнения полной синхронизации Instantly → Supabase с поддержкой incremental sync.

---

## 2. Контекст (Background)

**Проблема:**
- Есть 3 отдельных модуля (sources, transform, client)
- Нужен оркестратор для полного workflow
- Нужна поддержка upsert (incremental sync)

**Архитектура (Level 3 - Services):**
```
instantly_sync.py (orchestrator)
  |
  ├─ instantly_sources.py (load JSON)
  ├─ instantly_transform.py (transform data)
  └─ supabase_client.py (upload to DB)
```

---

## 3. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- TASK-006, 007, 008 завершены
- RAW tables пустые (первый sync) или содержат старые данные

**ОГРАНИЧЕНИЯ:**
- Upsert по campaign_id / email (может перезаписать данные)
- Нет rollback на ошибках (все-или-ничего не гарантируется)

---

## 4. Зависимости

- [ ] TASK-006 (Supabase Client) завершена
- [ ] TASK-007 (Instantly Sources) завершена
- [ ] TASK-008 (Data Transform) завершена

---

## 5. Plan Контекста

### В начале:
- `backend/lib/supabase_client.py` _(read-only)_
- `modules/instantly/instantly_sources.py` _(read-only)_
- `modules/instantly/instantly_transform.py` _(read-only)_

### В конце:
- `backend/services/instantly_sync.py`
- `backend/services/__init__.py`

---

## 6. Пошаговый План

### Шаг 1: Create services directory

**Действие:**
```bash
mkdir -p backend/services
touch backend/services/__init__.py
```

### Шаг 2: Create sync service

**Файл:** `backend/services/instantly_sync.py`

```python
#!/usr/bin/env python3
"""
Instantly Sync Service
Orchestrates: JSON load → Transform → Supabase upload
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add modules to path
sys.path.append(str(Path(__file__).parent.parent.parent / "modules"))

from instantly.instantly_sources import (
    load_from_json,
    extract_campaigns,
    extract_accounts,
    extract_daily_analytics
)
from instantly.instantly_transform import (
    transform_campaigns,
    transform_accounts,
    transform_daily_analytics,
    validate_transformed_data
)

# Add backend lib to path
sys.path.append(str(Path(__file__).parent.parent))
from lib.supabase_client import upsert_rows

def sync_from_file(file_path: str, sync_options: Dict = None) -> Dict[str, Any]:
    """
    Sync Instantly data from JSON file to Supabase

    Args:
        file_path: Path to JSON file (raw_data or dashboard_data)
        sync_options: Optional dict with:
            - sync_campaigns: bool (default True)
            - sync_accounts: bool (default True)
            - sync_daily: bool (default False - large dataset)

    Returns:
        Dict with sync results

    Example:
        result = sync_from_file('modules/instantly/results/raw_data.json')
    """
    sync_options = sync_options or {}
    sync_campaigns = sync_options.get('sync_campaigns', True)
    sync_accounts = sync_options.get('sync_accounts', True)
    sync_daily = sync_options.get('sync_daily', False)

    results = {
        "success": True,
        "file_path": file_path,
        "campaigns": {"synced": 0, "status": "skipped"},
        "accounts": {"synced": 0, "status": "skipped"},
        "daily_analytics": {"synced": 0, "status": "skipped"},
        "errors": []
    }

    try:
        # Step 1: Load JSON
        load_result = load_from_json(file_path)
        if not load_result['success']:
            results['success'] = False
            results['errors'].append(f"Failed to load JSON: {load_result.get('error')}")
            return results

        data = load_result['data']

        # Step 2: Sync Campaigns
        if sync_campaigns:
            campaigns = extract_campaigns(data)
            if campaigns:
                campaigns_result = _sync_campaigns(campaigns)
                results['campaigns'] = campaigns_result
                if not campaigns_result.get('success'):
                    results['errors'].append(campaigns_result.get('error'))

        # Step 3: Sync Accounts
        if sync_accounts:
            accounts = extract_accounts(data)
            if accounts:
                accounts_result = _sync_accounts(accounts)
                results['accounts'] = accounts_result
                if not accounts_result.get('success'):
                    results['errors'].append(accounts_result.get('error'))

        # Step 4: Sync Daily Analytics (optional - large dataset)
        if sync_daily:
            daily = extract_daily_analytics(data)
            if daily:
                daily_result = _sync_daily_analytics(daily)
                results['daily_analytics'] = daily_result
                if not daily_result.get('success'):
                    results['errors'].append(daily_result.get('error'))

        # Final status
        if results['errors']:
            results['success'] = False

        return results

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        return results

def _sync_campaigns(campaigns: List[Dict]) -> Dict[str, Any]:
    """
    Sync campaigns to instantly_campaigns_raw table

    Args:
        campaigns: List of campaign dicts from Instantly

    Returns:
        Dict with sync result
    """
    try:
        # Transform
        transformed = transform_campaigns(campaigns)

        # Validate
        validation = validate_transformed_data('instantly_campaigns_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "error": f"Validation failed: {validation['error']}",
                "synced": 0,
                "status": "validation_error"
            }

        # Upsert to Supabase
        result = upsert_rows(
            table='instantly_campaigns_raw',
            rows=transformed,
            on_conflict='instantly_campaign_id'
        )

        if result['success']:
            return {
                "success": True,
                "synced": result['upserted'],
                "status": "completed"
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "synced": 0,
                "status": "upload_error"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "synced": 0,
            "status": "error"
        }

def _sync_accounts(accounts: List[Dict]) -> Dict[str, Any]:
    """Sync accounts to instantly_accounts_raw table"""
    try:
        transformed = transform_accounts(accounts)

        validation = validate_transformed_data('instantly_accounts_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "error": validation['error'],
                "synced": 0,
                "status": "validation_error"
            }

        result = upsert_rows(
            table='instantly_accounts_raw',
            rows=transformed,
            on_conflict='email'
        )

        return {
            "success": result['success'],
            "synced": result.get('upserted', 0),
            "status": "completed" if result['success'] else "upload_error",
            "error": result.get('error')
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "synced": 0,
            "status": "error"
        }

def _sync_daily_analytics(daily: List[Dict]) -> Dict[str, Any]:
    """Sync daily analytics to instantly_daily_analytics_raw table"""
    try:
        transformed = transform_daily_analytics(daily)

        validation = validate_transformed_data('instantly_daily_analytics_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "error": validation['error'],
                "synced": 0,
                "status": "validation_error"
            }

        # Note: No upsert for daily analytics (unique constraint on date)
        # Using insert instead
        from lib.supabase_client import get_supabase
        supabase = get_supabase()
        response = supabase.table('instantly_daily_analytics_raw').insert(transformed).execute()

        return {
            "success": True,
            "synced": len(transformed),
            "status": "completed"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "synced": 0,
            "status": "error"
        }

# Test function
if __name__ == "__main__":
    # Test with real file
    test_file = "../../modules/instantly/results/raw_data_20250921_125555.json"

    print("Testing Instantly sync...")
    result = sync_from_file(test_file, sync_options={
        'sync_campaigns': True,
        'sync_accounts': True,
        'sync_daily': False  # Skip large dataset for testing
    })

    print(f"Sync result: {result}")
```

### Шаг 3: Test service

**Команда:**
```bash
cd backend/services
python instantly_sync.py
```

---

## 7. Критерии Приёмки

- [ ] `backend/services/instantly_sync.py` создан
- [ ] `sync_from_file()` загружает и sync campaigns
- [ ] `sync_from_file()` загружает и sync accounts
- [ ] Upsert работает (повторный sync не создаёт дубликаты)
- [ ] Validation errors возвращаются в результате
- [ ] Test с real data проходит
- [ ] Campaigns видны в Supabase table

---

## 8. Стратегия Тестирования

**Manual test:**
```bash
python backend/services/instantly_sync.py
```

**Check Supabase:**
```sql
SELECT COUNT(*) FROM instantly_campaigns_raw;
-- Should return 4

SELECT campaign_name FROM instantly_campaigns_raw;
-- Should show 4 campaign names
```

---

**Task Version:** 1.0


## 9. Testing Results

**Date:** 2025-10-03

**Test Run:**
```
Overall: SUCCESS
Campaigns: 4 synced (completed)
Accounts: 10 synced (completed)
Daily: 17 synced (completed)
No errors
```

**Created Files:**
- `backend/services/instantly_sync.py` - Production-ready sync service
- `backend/services/__init__.py` - Services module init

**Key Features:**
- Orchestrates full sync: sources → transform → upload
- Returns structured results (JSON-serializable)
- Error handling with detailed status codes
- Configurable sync options
- Can be called from FastAPI or CLI

**Usage:**
```python
from backend.services.instantly_sync import sync_from_file

result = sync_from_file(\"path/to/data.json\")
# Returns: {success, campaigns, accounts, daily_analytics, errors}
```

---

**Task Version:** 1.0
