# Sprint 01: First Campaign Launch

**Дата:** 2025-10-02
**Статус:** Planning
**Цель:** Запустить первую реальную Instantly кампанию с 1500 лидами через полный pipeline

---

## 🎯 Executive Summary

### Что делаем
Создаём полный pipeline для обработки лидов и запуска email кампаний:
```
CSV Upload → Parse → Normalize → Icebreakers → Batches → Upload to Instantly
```

### Ключевые решения
1. **Модульная архитектура** вместо wizard UI
2. **Raw data layer first** - сначала сохраняем всё как есть, потом нормализуем
3. **Backend orchestration** - Python FastAPI объединяет модульные скрипты

### Прогресс
- [ ] Database schema created (0/2 migrations)
- [ ] Supabase integration (0/3 components)
- [ ] Processing scripts (0/6 scripts)
- [ ] Frontend pages (0/2 pages)

**Общий прогресс:** 0/13 tasks completed

---

## 📂 Структура спринта

### `/docs` - Документация и решения
- `architecture-levels-and-data-flow.md` - 5-уровневая архитектура системы
- `modular-vs-wizard-decision-and-implementation-plan.md` - Архитектурные решения + полный план на 4 дня

### `/tasks` - Задачи для выполнения
- `_template.md` - Шаблон для создания новых задач
- (Задачи будут добавляться по ходу реализации)

### `sprint-plan.md` - Оригинальный план спринта

---

## 🚀 Быстрый старт

### Прочитать сначала:
1. `docs/modular-vs-wizard-decision-and-implementation-plan.md` - Полный контекст и план
2. `docs/architecture-levels-and-data-flow.md` - Понять архитектуру системы
3. `sprint-plan.md` - Детальные требования спринта

### Начать работу:
1. Взять шаблон из `tasks/_template.md`
2. Создать первую задачу (например, `01-setup-supabase-database.md`)
3. Следовать плану из документации

---

## 📊 Ключевые метрики

### Технические:
- **Database tables:** 0/8 created
- **Python scripts:** 0/6 implemented
- **API endpoints:** 0/7 created
- **Frontend pages:** 1/3 ready (`/script-runner` exists)

### Бизнес:
- **Target:** 1500 leads через pipeline
- **Timeline:** 3-4 дня
- **Success:** Campaign launched in Instantly

---

## 🔗 Связанные документы

- **CHANGELOG:** `../../../CHANGELOG.md` (секция [Unreleased])
- **PRD:** `../../PRD.md`
- **ADR:** `../../ADR.md`
- **SQL Migrations:** `../../sql/`

---

**Last Updated:** 2025-10-02
**Sprint Status:** Planning → Execution
