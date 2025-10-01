# Supabase Setup Guide

## 🎯 **Быстрая настройка Supabase для CSV Storage**

### **Шаг 1: Настройка Supabase проекта**

1. Зайди в свой существующий Supabase проект
2. Перейди в **SQL Editor**
3. Скопируй и выполни весь SQL из файла `supabase-setup.sql`

### **Шаг 2: Получение API ключей**

1. Перейди в **Settings** → **API**
2. Скопируй следующие ключи:
   - **Project URL** (начинается с https://xxx.supabase.co)
   - **anon public** ключ
   - **service_role** ключ (секретный)

### **Шаг 3: Настройка .env файла**

Замени placeholders в `.env` файле:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://ваш-проект-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=ваш-anon-ключ
SUPABASE_SERVICE_ROLE_KEY=ваш-service-role-ключ
```

### **Шаг 4: Проверка настройки**

После настройки выполни SQL для проверки:

```sql
-- Проверить таблицу
SELECT COUNT(*) FROM file_metadata;

-- Проверить bucket
SELECT * FROM storage.buckets WHERE name = 'csv-files';

-- Проверить policies
SELECT * FROM storage.policies WHERE bucket_id = 'csv-files';
```

## 📁 **Как работает File Storage**

### **Архитектура:**

1. **Upload CSV** → Frontend форма
2. **Analysis** → Python анализ структуры
3. **Supabase Storage** → Файл сохраняется как blob
4. **Supabase Database** → Метаданные в таблице `file_metadata`

### **Структура данных:**

```typescript
interface FileMetadata {
  id: string                           // UUID файла
  filename: string                     // Имя файла в storage
  original_name: string                // Оригинальное имя
  upload_date: string                  // Дата загрузки
  total_rows: number                   // Количество строк
  total_columns: number                // Количество колонок
  column_types: Record<string, string> // Типы колонок
  detected_key_columns: Record<string, string> // Ключевые колонки
  file_size: number                    // Размер файла
  storage_path: string                 // Путь в storage
}
```

### **Storage Structure:**

```
csv-files bucket:
├── uploads/
│   ├── uuid1.csv
│   ├── uuid2.csv
│   └── uuid3.csv
```

## 🔧 **API Endpoints**

### **POST /api/upload**
- Загружает CSV файл
- Анализирует структуру
- Сохраняет в Supabase
- Возвращает метаданные

### **GET /api/uploaded-files**
- Возвращает список всех файлов
- Данные из таблицы `file_metadata`

### **GET /api/files/[fileId]/preview**
- Возвращает preview CSV файла
- Загружает контент из Supabase Storage

## 💾 **Storage Limits**

- **Free Tier**: 1GB storage
- **Pricing**: $0.021/GB после лимита
- **Практически**: 1GB = ~20,000 CSV файлов по 50KB

## 🛠 **Troubleshooting**

### **Ошибка: "File not found"**
```bash
# Проверь существование файла в storage
SELECT storage_path FROM file_metadata WHERE id = 'your-file-id';
```

### **Ошибка: "Upload failed"**
```bash
# Проверь policies
SELECT * FROM storage.policies WHERE bucket_id = 'csv-files';
```

### **Ошибка: "Database insert failed"**
```bash
# Проверь таблицу
\d file_metadata
```

## 🚀 **Готово!**

После настройки файлы будут:
- ✅ Сохраняться постоянно в Supabase
- ✅ Доступны через API
- ✅ С полными метаданными
- ✅ Работать на Vercel deployment