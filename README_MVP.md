# Script Runner MVP

Веб-интерфейс для запуска и мониторинга Python скриптов.

## Быстрый старт

### 1. Запуск Backend
```bash
# Способ 1: Двойной клик
start_backend.bat

# Способ 2: Вручную
cd api
py main.py
```

### 2. Запуск Frontend
```bash
# Способ 1: Двойной клик
start_frontend.bat

# Способ 2: Вручную
cd frontend
npm run dev
```

### 3. Открыть в браузере
```
http://localhost:3000
```

## Возможности MVP

### ✅ Готово:
- **Выбор скрипта** из dropdown меню
- **Загрузка файлов** через drag & drop
- **Настройка конфигурации** через динамические формы
- **Real-time мониторинг** выполнения
- **Просмотр логов** с возможностью копирования
- **Скачивание результатов** в JSON формате
- **Обработка ошибок** с детальным выводом

### 🎯 Поддерживаемые скрипты:
- `openai_mass_processor.py` - Генерация icebreakers через OpenAI

## Архитектура

```
├── frontend/          # React + TypeScript + Tailwind
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.tsx     # Drag & drop файлов
│   │   │   ├── ConfigForm.tsx     # Динамические формы
│   │   │   └── JobStatus.tsx      # Real-time статус
│   │   └── app/page.tsx           # Главная страница
├── api/               # FastAPI Backend
│   ├── main.py                    # API endpoints
│   └── script_runner.py           # Интеграция со скриптами
└── modules/           # Ваши существующие скрипты (БЕЗ изменений)
```

## Как добавить новый скрипт

1. **Поместите скрипт** в `modules/[category]/script_name.py`
2. **Убедитесь что есть CONFIG** объект в начале файла
3. **Добавьте в script_runner.py** информацию о новом скрипте
4. **Перезапустите backend** - скрипт автоматически появится в UI

## Пример использования

1. Выберите `openai_mass_processor` из списка
2. Загрузите CSV файл с leads (columns: company_name, website, first_name, email)
3. Настройте API ключ OpenAI и параметры обработки
4. Нажмите "Start Processing"
5. Следите за прогрессом в real-time
6. Скачайте результаты с персонализированными icebreakers

## Технические детали

- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python 3.12
- **Real-time**: HTTP polling (2 секунды)
- **File handling**: Multipart upload с валидацией
- **Error handling**: Structured error responses

## Troubleshooting

### Backend не запускается:
```bash
cd api
py -m pip install -r requirements.txt
```

### Frontend не запускается:
```bash
cd frontend
npm install
```

### CORS ошибки:
Убедитесь что backend запущен на порту 8000, frontend на 3000.