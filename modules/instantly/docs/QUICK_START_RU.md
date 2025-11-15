# Быстрый старт - Загрузка CSV в Instantly

## Шаг 1: Получи API ключ и Campaign ID

### API Key:
1. Зайди в Instantly.ai → Settings → API
2. Скопируй API key

### Campaign ID:
1. Открой нужную кампанию
2. Посмотри на URL: `https://app.instantly.ai/app/campaigns/[ВОТ_ЭТОТ_ID]`
3. Скопируй ID из URL

## Шаг 2: Настрой скрипт

Открой файл: `modules/instantly/scripts/upload_csv_to_campaign.py`

Найди секцию CONFIG и заполни:

```python
CONFIG = {
    "API": {
        "api_key": "твой-api-ключ-сюда",  # API key из Step 1
    },
    "CAMPAIGN": {
        "campaign_id": "твой-campaign-id-сюда",  # Campaign ID из Step 1
    },
    "INPUT": {
        "csv_path": r"C:\путь\к\твоему\файлу.csv",  # Путь к CSV
    }
}
```

**Для твоего файла CSV уже прописан правильный путь:**
```python
"csv_path": r"C:\Users\79818\Desktop\Outreach - new\modules\openai\results\museum_emails_20251115_153331.csv"
```

## Шаг 3: Запусти скрипт

```bash
python modules/instantly/scripts/upload_csv_to_campaign.py
```

## Шаг 4: Создай sequence steps в Instantly

После загрузки лидов, иди в Instantly UI и создай steps:

### Step 1:
- **Subject:** `{{Subject_Line}}`
- **Body:** `{{Email_1}}`
- Wait: 0 days (отправляется сразу)

### Step 2:
- **Subject:** (оставь пустым - продолжит тред)
- **Body:** `{{Email_2}}`
- Wait: 3-5 дней

### Step 3:
- **Subject:** (оставь пустым)
- **Body:** `{{Email_3}}`
- Wait: 3-5 дней

## Доступные переменные

После загрузки в Instantly будут доступны:

- `{{Name}}` - название музея
- `{{Website}}` - сайт
- `{{Short_Museum_Name}}` - короткое название
- `{{Specific_Section}}` - секция музея
- `{{Subject_Line}}` - тема письма
- `{{Email_1}}` - текст первого email
- `{{Email_2}}` - текст второго email
- `{{Email_3}}` - текст третьего email
- `{{Language}}` - язык (en/fr/de/nl/es)
- `{{Summary}}` - описание музея
- `{{Focus_Wars}}` - фокус на войнах
- `{{Focus_Periods}}` - временные периоды

## Что делает скрипт

1. ✅ Читает твой CSV файл
2. ✅ Очищает email адреса (убирает "remove-this" и т.д.)
3. ✅ Проверяет валидность emails
4. ✅ Маппит все колонки в custom variables
5. ✅ Загружает через Instantly API
6. ✅ Сохраняет результаты в `modules/instantly/results/`

## Важно

### Про sequences:
- ❌ Нельзя загрузить лид сразу на Step 2 или Step 3
- ✅ Все лиды начинают с Step 1
- ✅ Разные тексты для разных лидов = используй {{Email_1}}, {{Email_2}}, {{Email_3}}

### Про языки:
- У тебя лиды на разных языках (nl, de, es, fr)
- Вариант 1: Загрузи всех в одну кампанию, используй {{Email_1}} (там уже правильный язык)
- Вариант 2: Создай отдельные кампании для каждого языка

### Очистка emails:
Скрипт автоматически исправит:
- `info@remove-this.museum.com` → `info@museum.com`
- `contact@museum.nliban` → `contact@museum.nl`

## Пример вывода

```
==========================================================
UPLOAD SUMMARY
==========================================================
Total rows processed: 10
Valid leads uploaded: 9
Skipped (invalid): 1
Execution time: 2.34s
Results saved to: modules/instantly/results/upload_campaign_20251115_153500.json
==========================================================
```

## Если что-то пошло не так

### "API key not configured"
→ Добавь API key в `CONFIG["API"]["api_key"]`

### "Campaign ID not configured"
→ Добавь Campaign ID в `CONFIG["CAMPAIGN"]["campaign_id"]`

### "401 Unauthorized"
→ API key неправильный, проверь в Instantly settings

### "No valid leads to upload"
→ Проверь, что в CSV есть колонка `email` с валидными адресами

## Полная документация

Детальная инструкция: `modules/instantly/docs/CSV_UPLOAD_GUIDE.md`
