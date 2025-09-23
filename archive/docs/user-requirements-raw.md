# User Requirements - Raw Input Data

**Дата создания:** 2025-01-10  
**Контекст:** Создание PRD и задач для Cold Outreach Automation Platform

## Исходные требования пользователя

### Основной пользователь
- Инструмент для внутреннего использования (solo entrepreneur)
- Объем: 10-30K лидов/месяц (постепенное увеличение)
- Цель: максимизировать email reply rate и positive response rate
- Технический уровень: все делается в Claude Code
- Frontend: nice-to-have в будущем, сейчас важна стабильная работа core features

### Входные данные
- **Источники CSV:** LeadMagic, Apollo, Epify, Sales Navigator и другие third-party services
- **Доступная информация:** LinkedIn, иногда website, базовая информация (название, размер компании, контакт)
- **Вариативность:** "sometimes there is this information, sometimes there is another" - нужна динамичность
- **CRM интеграция:** не нужна пока

### Архитектурные требования
- **Модульность:** "different functions that work separately" + master orchestrator
- **Гибкость:** можно собирать в любых комбинациях
- **НЕ hardcoding:** динамическая обработка разных типов данных
- **Apify:** "We will most likely use Apify. Well, we will definitely use Apify."

### Генерация айсбрейкеров
- **Количество:** 10+ опций или "as many options as possible"
- **Стиль:** естественные, короткие (short and sweet), "as if we knew a person for a long time"
- **Финализация:** функция должна использовать ВСЮ доступную информацию о компании

### Хранение и организация
- **Файлы:** "one Icebreaker file" readable by human and machine
- **Google Sheets:** одна таблица с системой именования для хронологического порядка
- **Email sequences:** обычно 2 письма (initial + follow-up)
- **Структура писем:** subject + icebreaker + main offer + CTA

### Офферы и копирайтинг
- **Продукт:** системы для AI automation и lead generation
- **Услуги:** AI automation, lead generation services
- **Цель:** получать booked calls в календарь
- **Секция офферов:** помощь в формулировании офферов и копирайтинга

### Процесс запуска
- **Natural language:** "I give you a table, I tell you how much to process"
- **Массовость:** focus на массовую обработку, максимальные батчи
- **Команды:** обычным языком "you will just tell you, you will run"
- **Валидация:** "validate everything. If there is a mistake, then you need to log all the errors"

### Analytics и логирование
- **Требование:** "Let us log all the errors, all the scripts that are made"
- **Стандарт:** analytics for each script согласно industry standards для small projects
- **Детали:** когда какие скрипты запускались, какие ошибки были, сколько времени заняло
- **Цель:** "so that it was very well done. Detailed information"
- **Улучшения:** "based on this data, our scripts could be improved"

### Интеграции
- **Instantly:** загрузка кампаний пока manually достаточно, интеграция nice-to-have
- **Notifications:** не нужны пока
- **Dashboard:** nice-to-have, не первоочередное
- **Приоритет:** "The main thing is that core features work"

### Философия подхода
- **Простота:** "Let's not complicate things, we have so much on the plate"
- **Фокус:** core functionality сначала, потом productization
- **Реальность:** всегда real data, никаких test data если не просят прямо

## Ключевые цитаты

> "I don't give a shit about the structure. I want it to be just different functions that work separately"

> "I want to say that the function of icebreaker generation finalizes all the information that is about the company"

> "focus on the mass, so that the maximum batch is, so that everything is cool"

> "validate everything. If there is a mistake, then you need to log all the errors"

> "so that based on this data, our scripts could be improved"

> "Let's not complicate things, we have so much on the plate"