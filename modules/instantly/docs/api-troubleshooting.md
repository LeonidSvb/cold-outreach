# INSTANTLY API TROUBLESHOOTING GUIDE

## Текущая проблема
Все запросы к Instantly API возвращают ошибку 403 с кодом 1010 (Cloudflare protection)

## Решения по приоритету

### 1. ПРОВЕРЬТЕ API КЛЮЧ В INSTANTLY DASHBOARD

**Шаги:**
1. Войдите в https://app.instantly.ai/
2. Перейдите в Settings → API Keys
3. Проверьте статус вашего API ключа
4. Если неактивен - активируйте
5. Если не работает - создайте новый

**Возможные проблемы:**
- API ключ истек или деактивирован
- Аккаунт не имеет доступа к API
- API ключ создан для другого уровня доступа

### 2. ЗАМЕНИТЕ API КЛЮЧ В .ENV

**Текущий ключ:**
```
INSTANTLY_API_KEY=YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0OnpoTXlidndIZ3JuZQ==
```

**После декодирования:**
```
c6ea1bfd-6fac-4e41-925c-4628477e2954:zhMybvwHgrne
```

**Если получите новый ключ:**
1. Откройте .env файл
2. Замените значение INSTANTLY_API_KEY
3. Сохраните файл
4. Перезапустите тест

### 3. ПРОВЕРЬТЕ ОГРАНИЧЕНИЯ АККАУНТА

**Возможные ограничения:**
- Free план не имеет доступа к API
- Аккаунт заблокирован или приостановлен
- Превышен лимит запросов
- Нужна верификация аккаунта

### 4. ОБРАТИТЕСЬ В ПОДДЕРЖКУ INSTANTLY

**Если ничего не помогает:**
1. Напишите в поддержку: support@instantly.ai
2. Укажите ваш email аккаунта
3. Опишите проблему с API (ошибка 403, код 1010)
4. Попросите проверить статус API доступа

### 5. АЛЬТЕРНАТИВНЫЕ РЕШЕНИЯ

**Если API недоступен:**
1. Экспорт данных вручную из dashboard
2. Использование автоматизации браузера (Selenium)
3. Интеграция через Zapier/n8n webhooks

## Тестирование после исправления

После получения нового API ключа:

```bash
# Перейти в папку модуля
cd "C:\Users\79818\Desktop\Outreach - new\modules\instantly"

# Тест подключения
python test_instantly_connection.py

# Полный сбор данных
python instantly_data_collector.py
```

## Ожидаемые данные после успешного подключения

### Campaigns
- Список всех кампаний
- Статистика отправки
- Open rates, reply rates
- Click-through rates

### Email Accounts
- Список всех email аккаунтов
- Статус аккаунтов
- Health scores
- Warmup статистика

### Analytics
- Детальная аналитика по дням
- Статистика по этапам кампаний
- Метрики deliverability
- A/B test результаты

## Контакты для решения

1. **Instantly Support**: support@instantly.ai
2. **Documentation**: https://docs.instantly.ai/
3. **API Explorer**: https://docs.instantly.ai/api-explorer

---

*Скрипты готовы к работе, как только API ключ будет исправлен.*