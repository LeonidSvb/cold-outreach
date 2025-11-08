# Data Processor - Обработчик данных

## 📋 Что это?

Инструмент для массовой обработки CSV файлов с помощью AI и веб-скрапинга.

Два режима работы:
1. **AI Mass Processor** - обработка любых данных через OpenAI
2. **Web Scraper** - парсинг сайтов (Quick или Full Pipeline с AI)

---

## 🏗️ Как это работает?

### Архитектура (путь данных):

```
┌─────────────────┐
│  1. FRONTEND    │  Пользователь загружает CSV, настраивает параметры
│  (React UI)     │
└────────┬────────┘
         │
         ↓ FormData (file + params)
         │
┌────────┴────────┐
│  2. API ROUTE   │  Next.js API принимает данные, запускает Python скрипт
│  /api/.../stream│
└────────┬────────┘
         │
         ↓ spawn('py', ['script.py', '--param', 'value'])
         │
┌────────┴────────┐
│  3. PYTHON      │  Скрипт обрабатывает CSV, возвращает результат
│  (Backend)      │
└────────┬────────┘
         │
         ↓ CSV output
         │
┌────────┴────────┐
│  4. DOWNLOAD    │  Пользователь скачивает результат
│  (Frontend)     │
└─────────────────┘
```

---

## 🎯 Режимы работы

### 1️⃣ AI Mass Processor (1-я вкладка)

**Что делает:**
- Обрабатывает каждую строку CSV через OpenAI
- Использует ваш кастомный промпт
- Добавляет результаты в новые колонки

**Какой скрипт:**
- `scripts/openai_mass_processor.py`

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `prompt` | Промпт для OpenAI (используйте `{{column_name}}` для подстановки значений) | - |
| `model` | Модель OpenAI | gpt-4o-mini |
| `concurrency` | Сколько запросов одновременно | 25 |
| `temperature` | Креативность AI (0 = строго, 1 = креативно) | 0.3 |

**Пример промпта:**
```
Проанализируй компанию {{company_name}} с сайта {{website}}.
Верни JSON: {"industry": "...", "size": "..."}
```

**Как передаются параметры:**
```typescript
// Frontend (AIProcessorTab.tsx)
const [prompt, setPrompt] = useState('')  // State хранит промпт
formData.append('prompt', prompt)         // Передаем в API

// API (/api/data-processor/stream/route.ts)
const prompt = formData.get('prompt')     // Получаем из FormData
args.push('--prompt', prompt)             // Передаем в Python

// Python (openai_mass_processor.py)
parser.add_argument('--prompt', type=str) // Принимаем как CLI аргумент
custom_prompt = args.prompt               // Используем в скрипте
```

---

### 2️⃣ Web Scraper - Quick Mode (2-я вкладка)

**Что делает:**
- Парсит сайты из CSV
- Извлекает только email адреса
- Быстро, без AI

**Какой скрипт:**
- `scripts/scraping_parallel_website_email_extractor.py`

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `workers` | Количество параллельных потоков | 25 |

**Скорость:**
- ~2-3 сек на сайт
- Без затрат на AI

---

### 3️⃣ Web Scraper - Full Pipeline (2-я вкладка)

**Что делает:**
1. Парсит сайт (извлекает текст)
2. Отправляет текст в OpenAI
3. AI анализирует и извлекает структурированные данные

**Какой скрипт:**
- `scripts/scraping_website_personalization_enricher.py`

**Параметры:**
| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `workers` | Количество параллельных потоков | 25 |
| `model` | Модель OpenAI | gpt-4o-mini |
| `maxContentLength` | Максимальная длина текста для AI | 15000 символов |
| `prompt` | Кастомный промпт (опционально) | Default промпт |

**Кастомный промпт (опционально):**

Если не указан, используется default промпт, который извлекает:
- `owner_name` - имя владельца/основателя
- `business_summary` - краткое описание бизнеса
- `personalization_hook` - фраза для персонализации

**Плейсхолдеры для промпта:**
- `{{company_name}}` - название компании из CSV
- `{{website}}` - URL сайта
- `{{content}}` - спарсенный текст с сайта

**Пример кастомного промпта:**
```
Проанализируй компанию {{company_name}} (сайт: {{website}}).

Из текста: {{content}}

Извлеки JSON:
{
  "owner_name": "имя владельца или null",
  "industry": "отрасль бизнеса",
  "target_audience": "целевая аудитория"
}
```

**Как работает передача промпта:**
```typescript
// Frontend (WebScraperTab.tsx) - только для Full mode
const [customPrompt, setCustomPrompt] = useState('')  // State
if (mode === 'full' && customPrompt.trim()) {
  formData.append('prompt', customPrompt.trim())      // Передаем только если заполнен
}

// API (/api/data-processor/stream/route.ts)
const prompt = formData.get('prompt') || ''           // Получаем (может быть пустым)
if (prompt) {
  args.push('--prompt', prompt)                       // Передаем в Python только если есть
}

// Python (scraping_website_personalization_enricher.py)
custom_prompt = args.prompt                           // None если не передан
if custom_prompt:
    # Используем кастомный
    prompt = custom_prompt.replace('{{company_name}}', company_name)
else:
    # Используем default промпт
    prompt = default_prompt
```

**Скорость и стоимость:**
- ~5-8 сек на сайт
- ~$0.003-0.01 на сайт (зависит от модели)

---

## 📊 Какие файлы задействованы?

### Frontend (React):
```
frontend/src/
├── app/data-processor/
│   ├── page.tsx                              # Главная страница с табами
│   └── README.md                             # 👈 Эта документация
├── components/data-processor/
│   ├── AIProcessorTab.tsx                    # 1-я вкладка (AI Mass Processor)
│   └── WebScraperTab.tsx                     # 2-я вкладка (Web Scraper)
└── app/api/data-processor/
    ├── stream/route.ts                       # API для запуска скриптов
    └── download/[fileId]/route.ts            # API для скачивания результатов
```

### Backend (Python):
```
scripts/
├── openai_mass_processor.py                  # AI обработка любых CSV
├── scraping_parallel_website_email_extractor.py  # Quick mode - только emails
└── scraping_website_personalization_enricher.py  # Full Pipeline - AI анализ сайтов
```

---

## 🔄 Поток данных (детально)

### Пример: Web Scraper Full Pipeline

1. **Пользователь загружает CSV:**
   ```typescript
   // WebScraperTab.tsx
   const handleFileUpload = (e) => {
     const file = e.target.files[0]
     setUploadedFile(file)  // Сохраняем в state
   }
   ```

2. **Настраивает параметры:**
   ```typescript
   // Все параметры хранятся в React state
   const [mode, setMode] = useState('full')
   const [workers, setWorkers] = useState(25)
   const [model, setModel] = useState('gpt-4o-mini')
   const [customPrompt, setCustomPrompt] = useState('')
   ```

3. **Нажимает "Start Processing":**
   ```typescript
   const handleProcess = async () => {
     // Собираем все в FormData
     const formData = new FormData()
     formData.append('file', uploadedFile)
     formData.append('mode', 'web-scraper')
     formData.append('scraperMode', mode)        // 'full'
     formData.append('workers', workers)
     formData.append('model', model)
     formData.append('maxContentLength', maxContentLength)
     if (customPrompt) {
       formData.append('prompt', customPrompt)
     }

     // Отправляем в API
     const response = await fetch('/api/data-processor/stream', {
       method: 'POST',
       body: formData
     })
   }
   ```

4. **API принимает запрос:**
   ```typescript
   // stream/route.ts
   export async function POST(request: NextRequest) {
     const formData = await request.formData()

     // Извлекаем параметры
     const file = formData.get('file')
     const mode = formData.get('mode')
     const scraperMode = formData.get('scraperMode')
     const workers = formData.get('workers')
     const model = formData.get('model')
     const prompt = formData.get('prompt')

     // Сохраняем файл
     const inputPath = path.join(UPLOAD_DIR, `${fileId}_input.csv`)
     await writeFile(inputPath, buffer)

     // Запускаем Python скрипт
     const scriptPath = 'scripts/scraping_website_personalization_enricher.py'
     const args = [
       scriptPath,
       '--input', inputPath,
       '--output', outputPath,
       '--workers', workers,
       '--model', model,
       '--max-content-length', maxContentLength
     ]
     if (prompt) {
       args.push('--prompt', prompt)
     }

     const python = spawn('py', args)
   }
   ```

5. **Python скрипт работает:**
   ```python
   # scraping_website_personalization_enricher.py

   # Парсим аргументы
   args = parse_args()
   custom_prompt = args.prompt

   # Читаем CSV
   rows = read_csv(args.input)

   # Обрабатываем каждый сайт
   for row in rows:
       # 1. Скрапим сайт
       content = scrape_website(row['website'])

       # 2. Отправляем в OpenAI
       if custom_prompt:
           prompt = custom_prompt.replace('{{company_name}}', row['company'])
           prompt = prompt.replace('{{content}}', content)
       else:
           prompt = default_prompt

       result = openai.chat.completions.create(
           model=args.model,
           messages=[{"role": "user", "content": prompt}]
       )

       # 3. Сохраняем результат
       row['ai_result'] = result

   # Сохраняем CSV
   save_csv(rows, args.output)
   ```

6. **Результат возвращается пользователю:**
   ```typescript
   // WebScraperTab.tsx
   // Получаем логи в реальном времени
   python.stdout.on('data', (data) => {
     setLogs(prev => [...prev, { message: data, type: 'info' }])
   })

   // Когда готово
   python.on('close', () => {
     setIsComplete(true)
     setFileId(fileId)  // Можно скачать
   })
   ```

7. **Скачивание результата:**
   ```typescript
   const handleDownload = () => {
     fetch(`/api/data-processor/download/${fileId}`)
       .then(res => res.blob())
       .then(blob => {
         // Скачиваем файл
         const url = window.URL.createObjectURL(blob)
         const a = document.createElement('a')
         a.href = url
         a.download = `result_${fileId}.csv`
         a.click()
       })
   }
   ```

---

## 💡 Важные моменты

### Плейсхолдеры в промптах:

**AI Mass Processor:**
- Используйте `{{column_name}}` для подстановки значений из CSV
- Пример: `{{company_name}}`, `{{website}}`, `{{email}}`

**Web Scraper Full Pipeline:**
- Используйте `{{company_name}}`, `{{website}}`, `{{content}}`
- `{{content}}` - это весь спарсенный текст с сайта

### State Management:

Все параметры хранятся в React state:
```typescript
// Каждое поле имеет:
const [value, setValue] = useState(defaultValue)

// И подключено к UI:
<input value={value} onChange={(e) => setValue(e.target.value)} />

// НЕТ хардкода! Все динамическое.
```

### Логи в реальном времени:

Используем Server-Sent Events (SSE):
```typescript
// Python пишет в stdout/stderr
print("Processing...")

// API стримит через SSE
python.stdout.on('data', (data) => {
  controller.enqueue(`event: log\ndata: ${data}\n\n`)
})

// Frontend получает в реальном времени
const reader = response.body.getReader()
// Обновляем UI
setLogs(prev => [...prev, newLog])
```

---

## 🐛 Troubleshooting

### Логи не показываются:
- Проверьте что скрипт пишет в `stdout` (используйте `print()` в Python)
- Проверьте что API правильно стримит события

### Промпт не работает:
- Проверьте что используете правильные плейсхолдеры
- В AI Processor: `{{column_name}}`
- В Web Scraper Full: `{{company_name}}`, `{{website}}`, `{{content}}`

### Параметры не передаются:
- Проверьте цепочку: State → FormData → API → Python
- Используйте `console.log()` на каждом этапе

---

## 📚 Дополнительные материалы

- Детальные комментарии в коде каждого файла
- Примеры промптов в placeholder'ах UI
- Python скрипты имеют подробные docstring'и
