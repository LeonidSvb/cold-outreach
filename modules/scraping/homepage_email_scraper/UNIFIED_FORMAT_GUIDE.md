# Homepage Email Scraper - Unified Format Guide

## 🎯 Унифицированная Система (v4.2.0+)

Система работает **одинаково** независимо от того, включена ли экстракция email или нет.

---

## 📊 Логика Success/Failed

### С Email Extraction (Extract emails = ON)
```
SUCCESS = email найден (на homepage ИЛИ через deep search)
FAILED  = email НЕ найден (но контент scraped)
```

### Без Email Extraction (Extract emails = OFF)
```
SUCCESS = контент успешно scraped с сайта
FAILED  = не удалось scrape контент (timeout, 404, etc)
```

---

## 📁 Output Files (Всегда 3 + 1 Analytics)

### 1. `success.csv` / `success.json` / `success.xlsx`
**Достигли цели**
- С email: содержит все rows где email найден
- Без email: содержит все rows где контент scraped успешно
- **Columns**: все original + `email`, `homepage_content`, `scrape_status`, `site_type`, etc.

### 2. `failed.csv` / `failed.json` / `failed.xlsx`
**Не достигли цели**
- С email: сайты где email НЕ найден (но контент есть!)
- Без email: сайты где scraping failed (timeout, errors)
- **Columns**: все original + `failure_reason`, `error_message`, `site_type`

**failure_reason types:**
- `no_email_found_static` - статичный сайт, email не найден
- `no_email_found_dynamic` - React/Vue сайт, email не найден
- `connection_timeout` - timeout при подключении
- `page_not_found` - 404 error
- `[other error message]` - другие ошибки

### 3. `all_combined.csv` / `all_combined.json` / `all_combined.xlsx`
**Все вместе для анализа**
- Все rows из success + failed
- Удобно для фильтрации и анализа в Excel/Pandas
- **Column `scrape_status`**: `success` или `failed`
- **Column `failure_reason`**: пустая для success, причина для failed

### 4. `scraping_analytics.json`
**Метрики и статистика**
```json
{
  "summary": {
    "total_sites": 1000,
    "success_rate": "85.2%",
    "duration_seconds": 324.5,
    "sites_per_second": 3.08
  },
  "results": {
    "success": { ... },
    "failed": { ... }
  },
  "site_types": {
    "static": 720,
    "dynamic": 280
  }
}
```

---

## 🔧 Columns в Output

### Всегда присутствуют:
- **Original columns** - все колонки из input CSV сохранены
- `scrape_status` - `success` / `failed`
- `site_type` - `static` / `dynamic` / `unknown`
- `homepage_content` - текст с homepage (если `save_content=True`)

### При Extract Emails = ON:
- `email` - найденный email(и)
- `email_source` - `homepage` / `deep_search` / `none`

### При Failed:
- `error_message` - детальное сообщение ошибки
- `failure_reason` - категоризированная причина

### Опциональные (по настройкам):
- `sitemap_links` - если `save_sitemap=True`
- `social_media_links` - если `save_social=True`
- `other_links` - если `save_links=True`
- `deep_pages_content` - если `save_deep_content=True`

---

## 💡 Use Cases

### Case 1: Scraping для Email Outreach
**Settings:**
- Extract emails: ✅ ON
- Save content: ✅ ON (для контекста)

**Output:**
- `success.csv` - используйте для cold outreach (есть email)
- `failed.csv` - можно попробовать найти email вручную (контент есть!)
- `all_combined.csv` - полный анализ coverage

### Case 2: Scraping Website Content для AI Analysis
**Settings:**
- Extract emails: ❌ OFF
- Save content: ✅ ON

**Output:**
- `success.csv` - все сайты где контент scraped (можно передать в AI)
- `failed.csv` - сайты с ошибками (нужно retry)
- `all_combined.csv` - полный dataset для обработки

### Case 3: Research & Data Collection
**Settings:**
- Extract emails: ✅ ON
- Save content: ✅ ON
- Save sitemap: ✅ ON
- Save social: ✅ ON

**Output:**
- Максимум данных в каждом файле
- Используйте `all_combined.xlsx` для анализа в Excel
- Filter по `scrape_status` и `failure_reason`

---

## 📥 Download Formats

### CSV (.csv)
- ✅ Excel compatible
- ✅ Pandas compatible
- ✅ UTF-8 with BOM (русские символы)
- **Best for**: Excel, Google Sheets, Pandas

### JSON (.json)
- ✅ Structured data
- ✅ API integration
- ✅ Pretty printed (indent=2)
- **Best for**: API, JavaScript, data pipelines

### Excel (.xlsx)
- ✅ Native Excel format
- ✅ Multiple sheets support (будущее)
- ✅ Formatting preserved
- **Best for**: Business users, presentations
- **Note**: требует `openpyxl` library

---

## 🎨 UI Navigation

### Upload & Run Tab:
1. Choose mode (Fast / Advanced)
2. Upload CSV
3. Configure settings
4. Run scraper
5. See completion stats with breakdown

### View Results Tab:
1. Select result folder
2. View analytics summary
3. **Download section:**
   - ✅ Success: CSV + JSON + Excel
   - ❌ Failed: CSV + JSON + Excel
   - 📊 All Combined: CSV + JSON + Excel
4. Preview first 10 rows before download

---

## 🔄 Migration from Old Format

### Old Files (v4.1.x):
```
success_emails.csv
failed_static.csv
failed_dynamic.csv
failed_other.csv
```

### New Files (v4.2.0+):
```
success.csv / .json / .xlsx
failed.csv / .json / .xlsx
all_combined.csv / .json / .xlsx
```

**Что изменилось:**
- `success_emails.csv` → `success.csv` (+ JSON + Excel)
- `failed_static.csv` + `failed_dynamic.csv` + `failed_other.csv` → `failed.csv` (с column `failure_reason`)
- **NEW**: `all_combined.csv` - все данные вместе

**Преимущества:**
- ✅ Unified формат для email и no-email режимов
- ✅ Меньше файлов (3 вместо 4)
- ✅ Больше форматов (CSV + JSON + Excel)
- ✅ Easier фильтрация через `failure_reason` column

---

## 🚀 Quick Start Examples

### Example 1: Email Extraction Only
```bash
streamlit run app.py

# Settings:
- Mode: Fast Mode
- Extract emails: ON
- Save content: OFF (faster)
```

### Example 2: Content + Email
```bash
streamlit run app.py

# Settings:
- Mode: Advanced Mode
- Extract emails: ON
- Save content: ON
- Max pages: 5
```

### Example 3: Content Only (No Emails)
```bash
streamlit run app.py

# Settings:
- Mode: Fast Mode
- Extract emails: OFF
- Save content: ON
```

**Result:**
- `success.csv` = все сайты где контент scraped
- `failed.csv` = сайты с ошибками
- Можно передать `success.csv` в AI для анализа

---

## 📊 Excel Analysis Tips

Откройте `all_combined.xlsx` в Excel:

### Filter by Status:
1. Select column `scrape_status`
2. Filter → Show only `success`
3. Результат: все успешные rows

### Analyze Failures:
1. Select column `failure_reason`
2. Pivot Table → Count by reason
3. Результат: breakdown причин failures

### Find Specific Emails:
1. Select column `email`
2. Filter → Contains "@gmail.com"
3. Результат: все Gmail addresses

---

## 🔍 Troubleshooting

### "Excel N/A" - Excel files не генерируются
**Fix**: Install openpyxl
```bash
pip install openpyxl
```

### Empty success.csv когда ожидали результаты
**Check**:
- Если `extract_emails=ON`: проверьте, что сайты действительно содержат email
- Если `extract_emails=OFF`: проверьте `failed.csv` для error messages

### Failure_reason = "unknown_error"
**Check**:
- Откройте `scraping_analytics.json` для detailed stats
- Проверьте debug logs (если доступны)

---

## 📝 Notes

1. **Deduplication**: При `extract_emails=ON`, success.csv автоматически deduplicated по email
2. **Content Size**: `homepage_content` limited to 50,000 chars по умолчанию
3. **Performance**: Fast Mode = 50-100 workers, Advanced Mode = 10-20 workers
4. **Encoding**: Все CSV files saved с UTF-8 BOM (поддержка русских символов)

---

**Version**: 4.2.0
**Last Updated**: 2025-11-20
**Author**: Leo
