# TASK-007: Instantly JSON Sources Module

---

## Metadata

```yaml
id: "TASK-007"
title: "Create Instantly JSON Data Loader Module"
status: "planned"
priority: "P1"
labels: ["backend", "instantly", "data-processing"]
dependencies: ["TASK-006"]
created: "2025-10-03"
assignee: "AI Agent"
```

---

## 1. Цель (High-Level Objective)

Создать модуль для загрузки JSON данных из файлов Instantly (как raw_data, так и dashboard_data) с валидацией структуры и поддержкой разных форматов.

---

## 2. Контекст (Background)

**Проблема:**
- Есть готовые JSON файлы с данными Instantly (`raw_data_20250921_125555.json`, `dashboard_data_20250921_125555.json`)
- Нет модуля для загрузки и валидации этих данных
- Структура JSON может быть разной (raw vs dashboard)

**Почему важно:**
- Первый шаг в pipeline: JSON → Transform → Supabase
- Нужна валидация данных перед трансформацией

---

## 3. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- JSON файлы в `modules/instantly/results/`
- Структура JSON соответствует Instantly API format

**ОГРАНИЧЕНИЯ:**
- Только file-based (API sync - в будущем)
- JSON может быть большим (10MB+)

---

## 4. Зависимости

- [ ] TASK-006 (Supabase Client) - завершена
- [ ] JSON файлы существуют в `modules/instantly/results/`

---

## 5. Plan Контекста

### В начале:
- `modules/instantly/results/raw_data_20250921_125555.json` _(read-only)_
- `modules/instantly/results/dashboard_data_20250921_125555.json` _(read-only)_

### В конце:
- `modules/instantly/instantly_sources.py`

---

## 6. Пошаговый План

### Шаг 1: Create sources module

**Файл:** `modules/instantly/instantly_sources.py`

```python
#!/usr/bin/env python3
"""
Instantly JSON Data Sources
Loads data from JSON files (raw_data or dashboard_data)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_from_json(file_path: str) -> Dict[str, Any]:
    """
    Load Instantly data from JSON file

    Args:
        file_path: Path to JSON file (raw_data or dashboard_data)

    Returns:
        Dict with parsed JSON data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "success": True,
            "data": data,
            "file_path": str(file_path),
            "data_type": detect_data_type(data)
        }

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def detect_data_type(data: Dict) -> str:
    """
    Detect if JSON is raw_data or dashboard_data format

    Args:
        data: Parsed JSON data

    Returns:
        'raw_data' or 'dashboard_data'
    """
    # Dashboard data has 'metadata' and 'campaigns' keys
    if 'metadata' in data and 'campaigns' in data:
        return 'dashboard_data'

    # Raw data has direct keys like 'campaigns_overview'
    if 'campaigns_overview' in data:
        return 'raw_data'

    return 'unknown'

def extract_campaigns(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract campaigns from JSON (handles both formats)

    Args:
        data: Parsed JSON data

    Returns:
        List of campaign dictionaries
    """
    data_type = detect_data_type(data)

    if data_type == 'dashboard_data':
        return data.get('campaigns', [])
    elif data_type == 'raw_data':
        # Use campaigns_detailed if available, else campaigns_overview
        return data.get('campaigns_detailed', data.get('campaigns_overview', []))

    return []

def extract_accounts(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract email accounts from JSON

    Args:
        data: Parsed JSON data

    Returns:
        List of account dictionaries
    """
    accounts_data = data.get('accounts', {})

    # Accounts might be in 'items' array
    if isinstance(accounts_data, dict):
        return accounts_data.get('items', [])

    # Or directly as array
    if isinstance(accounts_data, list):
        return accounts_data

    return []

def extract_daily_analytics(data: Dict) -> List[Dict[str, Any]]:
    """
    Extract daily analytics from JSON

    Args:
        data: Parsed JSON data

    Returns:
        List of daily analytics dictionaries
    """
    # Dashboard format
    if 'daily_trends' in data:
        return data['daily_trends']

    # Raw format
    if 'daily_analytics_all' in data:
        return data['daily_analytics_all']

    return []

def get_file_stats(file_path: str) -> Dict[str, Any]:
    """
    Get statistics about JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Dict with file stats
    """
    result = load_from_json(file_path)
    data = result['data']

    campaigns = extract_campaigns(data)
    accounts = extract_accounts(data)
    daily = extract_daily_analytics(data)

    return {
        "file_path": file_path,
        "data_type": result['data_type'],
        "campaigns_count": len(campaigns),
        "accounts_count": len(accounts),
        "daily_records": len(daily)
    }

# Test function
if __name__ == "__main__":
    # Test with real file
    test_file = "results/raw_data_20250921_125555.json"

    if Path(test_file).exists():
        stats = get_file_stats(test_file)
        print(f"File stats: {stats}")
    else:
        print(f"Test file not found: {test_file}")
```

### Шаг 2: Test with real data

**Команда:**
```bash
cd modules/instantly
python instantly_sources.py
```

**Expected output:**
```
File stats: {
  'file_path': 'results/raw_data_20250921_125555.json',
  'data_type': 'raw_data',
  'campaigns_count': 4,
  'accounts_count': 10,
  'daily_records': 45
}
```

---

## 7. Критерии Приёмки

- [ ] `modules/instantly/instantly_sources.py` создан
- [ ] `load_from_json()` загружает оба формата (raw_data, dashboard_data)
- [ ] `extract_campaigns()` возвращает 4 кампании
- [ ] `extract_accounts()` возвращает 10 аккаунтов
- [ ] Test script проходит с реальным JSON файлом
- [ ] Error handling для missing files работает

---

## 8. Стратегия Тестирования

**Test with real files:**
```python
from instantly_sources import load_from_json, get_file_stats

# Test raw_data format
stats = get_file_stats('results/raw_data_20250921_125555.json')
assert stats['campaigns_count'] == 4
assert stats['accounts_count'] == 10

# Test dashboard_data format
stats = get_file_stats('results/dashboard_data_20250921_125555.json')
assert stats['campaigns_count'] == 4
```

---

**Task Version:** 1.0
