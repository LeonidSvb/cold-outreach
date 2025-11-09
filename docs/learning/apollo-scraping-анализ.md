# Apollo Scraping: Как работают сервисы типа Leads Rapidly

**Дата:** 2025-11-09
**Тема:** Техническая механика scraping Apollo.io и бизнес-модель сервисов-агрегаторов

---

## 🔍 Краткое резюме

**Суть:** Сервисы типа Leads Rapidly scrape'ят Apollo.io, который сам scrape'ит LinkedIn
**Круговорот шакалов в природе:** LinkedIn → Apollo → Leads Rapidly → Конечные пользователи
**Легальность:** Серая зона (нарушает TOS, но не закон)
**Масштаб Leads Rapidly:** Micro SaaS, $300K-$1M ARR, 1-3 человека

---

## 🧩 Как работает Apollo.io

### Уровни доступа Apollo:

```
FREE АККАУНТ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Поиск компаний/людей
✅ Preview (имя, должность, компания)
❌ Email/телефон СКРЫТЫ (нужны credits)
❌ Экспорт ограничен (25/месяц)
❌ API нет

PAID ПЛАН ($49-99/месяц):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Emails раскрываются (используя credits)
✅ Больше экспортов
✅ API доступ
✅ Email sequences
```

### Откуда Apollo берёт данные:

**1. LinkedIn Scraping (70% данных)**

```javascript
// Упрощённая схема работы Apollo

// Массовые fake аккаунты LinkedIn
const fakeAccounts = [
  { email: 'bot1@apollo.io', password: 'xxx' },
  { email: 'bot2@apollo.io', password: 'xxx' },
  // тысячи таких аккаунтов
];

// Автоматический поиск и сбор
for (let account of fakeAccounts) {
  loginToLinkedIn(account);

  const results = searchLinkedIn({
    title: 'CEO',
    location: 'United States',
    company_size: '11-50'
  });

  // Парсинг профилей
  for (let profile of results) {
    saveToApolloDatabase({
      name: profile.name,
      title: profile.title,
      company: profile.company,
      linkedin_url: profile.url,
      // Email НЕТ на LinkedIn!
    });
  }

  // Ротация аккаунтов
  await sleep(randomDelay());
}
```

**2. Email Enrichment (магия)**

LinkedIn не показывает emails публично. Как Apollo их находит:

```
Техники:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Company domain guess:
   John Smith @ Apple → пробуют:
   - john.smith@apple.com
   - john@apple.com
   - jsmith@apple.com
   - j.smith@apple.com

2. Email verification (SMTP check):
   - Пингуют mail сервер
   - Проверяют существование ящика
   - Не отправляют письмо!

3. Data providers:
   - Покупают базы (Clearbit, Hunter)
   - Обмен данными между конкурентами

4. User contributions:
   - Apollo Chrome extension
   - Собирает emails со страниц которые ты посещаешь
   - Добавляет в их базу
   - ТЫ помогаешь Apollo бесплатно!
```

**3. Другие источники (30%)**

```
- Crunchbase (scraping)
- Company websites (contact pages)
- Public registries (гос. базы)
- News articles
- Social media (Twitter, Facebook)
```

---

## 🔧 Как работает Leads Rapidly

### Техническая схема:

```
ШАГ 1: Пользователь даёт ссылку
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Пример Apollo search URL:
https://app.apollo.io/#/people?
  jobTitles[]=CEO&
  personLocations[]=United%20States&
  organizationNumEmployeesRanges[]=11,20

Это сохранённый поиск в Apollo UI


ШАГ 2: Leads Rapidly запускает браузер
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Используют Puppeteer/Playwright:
- Headless Chrome браузер
- Заходят под СВОИМ Apollo аккаунтом
- Открывают твою ссылку
- Видят результаты с раскрытыми emails


ШАГ 3: Автоматический сбор
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Скрипт:
- Скроллит страницу
- Кликает "Show more"
- Парсит HTML каждого контакта
- Сохраняет в CSV
- Возвращает тебе файл
```

### Бизнес-модель (как зарабатывают):

**Вариант 1: Shared Premium Account (наиболее вероятно)**

```
┌─────────────────────────────────────────────┐
│  СХЕМА "ОДИН АККАУНТ НА ВСЕХ"               │
├─────────────────────────────────────────────┤
│  1. Leads Rapidly покупает:                 │
│     - Apollo Max Plan ($149-199/мес)       │
│     - Unlimited exports                     │
│     - Большой пул credits                   │
│                                             │
│  2. Все клиенты используют ОДИН аккаунт:   │
│     - 100 клиентов × $29/мес = $2,900      │
│     - Платят Apollo: $199/мес              │
│     - Profit: $2,700/мес 💰                │
│                                             │
│  3. Ротация запросов:                       │
│     - Queue система                         │
│     - Rate limiting                         │
│     - Один браузер для всех                │
└─────────────────────────────────────────────┘

Economics:
- 100 клиентов = $2,900/мес revenue
- Apollo cost = $199/мес
- Server cost = $100/мес
- NET: $2,600/мес чистыми
```

**Код (упрощённо):**

```javascript
const SHARED_APOLLO_ACCOUNT = {
  email: 'leadsrapidly@example.com',
  password: 'xxx',
  plan: 'Max ($199/month)'
};

// Queue для клиентских запросов
const requestQueue = [];

async function processClientRequest(clientUrl) {
  // Один браузер для всех
  const page = await getSharedBrowser();

  // Логин (если нужно)
  if (!isLoggedIn) {
    await loginToApollo(SHARED_APOLLO_ACCOUNT);
  }

  // Открыть ссылку клиента
  await page.goto(clientUrl);

  // Собрать данные
  const leads = await scrapeLeads(page);

  return leads;
}

// Rate limiting
setInterval(async () => {
  if (requestQueue.length > 0) {
    const request = requestQueue.shift();
    await processClientRequest(request);
    await sleep(5000); // Delay
  }
}, 5000);
```

---

## 💰 Leads Rapidly: Масштаб бизнеса

### Финансовые показатели (оценка):

```
┌─────────────────────────────────────────────┐
│  LEADS RAPIDLY - METRICS                    │
├─────────────────────────────────────────────┤
│  Pricing: $29-99/мес                        │
│  Average: ~$49/мес                          │
│                                             │
│  Customers: 500-2,000 (оценка)             │
│                                             │
│  MRR: $24,500 - $98,000                    │
│  ARR: $300K - $1.2M                        │
│                                             │
│  Valuation: $1-5M (если продадут)          │
│  Team: 1-3 человека (bootstrap)            │
│                                             │
│  Category: Micro SaaS                       │
└─────────────────────────────────────────────┘
```

### Сравнение с конкурентами:

| Компания | ARR | Valuation | Категория |
|----------|-----|-----------|-----------|
| Apollo.io | $100M+ | $1.6B | Unicorn 🦄 |
| ZoomInfo | $1B+ | $20B+ | Public company 🏢 |
| Hunter.io | $5-10M | $50-100M | Mid-size SaaS 💪 |
| PhantomBuster | $3-5M | $20-30M | Automation tool 🔧 |
| **Leads Rapidly** | **$0.3-1.2M** | **$1-5M** | **Micro SaaS 🐭** |

**Вывод:** Leads Rapidly = ОЧЕНЬ маленькая контора

---

## ⚖️ Легальность и риски

### Юридическая позиция:

```
┌─────────────────────────────────────────────┐
│  ЛЕГАЛЬНО (по закону)                       │
├─────────────────────────────────────────────┤
│  ✅ Scraping публичных данных               │
│  ✅ Использование своего аккаунта           │
│  ✅ Автоматизация для личного использования│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  СЕРАЯ ЗОНА                                  │
├─────────────────────────────────────────────┤
│  ⚠️ Scraping за paywall (Apollo paid data) │
│  ⚠️ Shared accounts                         │
│  ⚠️ Обход rate limits                       │
│  ⚠️ Коммерческое использование              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  НЕЛЕГАЛЬНО                                  │
├─────────────────────────────────────────────┤
│  ❌ Взлом аккаунтов                         │
│  ❌ Кража credentials                       │
│  ❌ DDoS атаки                              │
└─────────────────────────────────────────────┘
```

### Apollo Terms of Service:

```
ЗАПРЕЩЕНО:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Автоматический scraping через ботов
- Обход платных ограничений
- Shared accounts
- Массовый экспорт данных

НАКАЗАНИЕ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Бан аккаунта (instant)
- IP block
- Legal action (редко, но возможно)
```

### Риски для Leads Rapidly:

```
1. APOLLO БЛОКИРОВКА (риск: 60-70%)
   ├─ Apollo обнаружит shared аккаунты
   ├─ Забанит все их аккаунты
   └─ Сервис перестанет работать

2. ЮРИДИЧЕСКИЙ ИСК (риск: 30-40%)
   ├─ Apollo подаёт в суд
   ├─ Leads Rapidly закрывается
   └─ Founders платят штрафы

3. ТЕХНИЧЕСКИЕ ИЗМЕНЕНИЯ (риск: 90%+)
   ├─ Apollo меняет UI (каждые 3-6 мес)
   ├─ Scraper ломается
   ├─ Downtime 1-2 недели
   └─ Клиенты уходят
```

---

## 🎭 Ирония индустрии

### Круговорот шакалов в природе:

```
┌─────────────────────────────────────────────┐
│  LINKEDIN                                    │
│  Говорит: "Защищаем privacy пользователей" │
│  Делает: Продаёт те же данные (Sales Nav)  │
└─────────────────────────────────────────────┘
              ↓ (scraping)
┌─────────────────────────────────────────────┐
│  APOLLO                                      │
│  Говорит: "Aggregate публичные данные"     │
│  Делает: Массовый scraping LinkedIn        │
│  TOS: "Запрещён scraping НАШИХ данных!"    │
└─────────────────────────────────────────────┘
              ↓ (scraping)
┌─────────────────────────────────────────────┐
│  LEADS RAPIDLY                               │
│  Говорит: "Automation tool"                │
│  Делает: Scraping платных данных Apollo    │
│  Позиция: "Если Apollo может scrape        │
│            LinkedIn, почему мы не можем    │
│            scrape Apollo?"                  │
└─────────────────────────────────────────────┘
```

**Каждый уровень:**
- Scrape'ит предыдущий уровень
- Запрещает scraping себя
- Продаёт те же данные дороже
- Жалуется на нарушение TOS

**Итог:** Вся B2B data индустрия построена на гипокрисии 😄

---

## 🤔 Можно ли построить свой Apollo scraper?

### Технически: ДА, возможно

**Простой пример:**

```python
from playwright.sync_api import sync_playwright

def scrape_apollo(search_url, email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Логин в Apollo
        page.goto('https://app.apollo.io/login')
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')

        # Открыть поиск
        page.goto(search_url)
        page.wait_for_selector('.people-list')

        # Скроллинг
        for i in range(10):
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)

        # Парсинг
        contacts = page.evaluate('''() => {
            const rows = document.querySelectorAll('[data-cy="people-row"]');
            return Array.from(rows).map(row => ({
                name: row.querySelector('.name')?.textContent,
                title: row.querySelector('.title')?.textContent,
                company: row.querySelector('.company')?.textContent,
                email: row.querySelector('.email')?.textContent,
            }));
        }''')

        browser.close()
        return contacts
```

### Экономически: НЕТ, не стоит

```
┌─────────────────────────────────────────────┐
│  РАЗРАБОТКА SCRAPER                          │
├─────────────────────────────────────────────┤
│  Время: 15-20 часов                         │
│  Обслуживание: 3-5 часов/месяц             │
│  Opportunity cost: 20ч × $200/ч = $4,000   │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  VS APOLLO SUBSCRIPTION                      │
├─────────────────────────────────────────────┤
│  Apollo Basic: $49/месяц                    │
│  Годовая стоимость: $588                    │
│  Break-even: $4,000 / $49 = 81 месяц!      │
│  Это почти 7 ЛЕТ!                           │
└─────────────────────────────────────────────┘

ВЫВОД: НЕ СТОИТ разработки
```

### Когда имеет смысл:

```
Только если:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ У тебя УЖЕ есть paid Apollo
✅ Автоматизируешь рутину (не обходишь paywall)
✅ Экономишь 10+ часов/месяц
✅ Понимаешь риски бана

НЕ для:
❌ Обхода платных ограничений
❌ Получения бесплатных emails
❌ Коммерческой перепродажи данных
```

---

## 🎯 Рекомендации

### Для получения B2B лидов:

```
BEST STACK (легальный + дешёвый):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Google Maps API
   ├─ 8,000 лидов/мес БЕСПЛАТНО
   ├─ Компании + телефоны + сайты
   └─ 100% легально и стабильно

2. Hunter.io или Apollo Free
   ├─ Email finding по доменам
   ├─ $49/мес или бесплатно (ограниченно)
   └─ Официальный сервис

3. LinkedIn (ручной research)
   ├─ Поиск decision makers
   └─ Дополняет Google Maps данные

ИТОГО: $0-49/месяц
Легально: ✅
Стабильно: ✅
Качество: ⭐⭐⭐⭐⭐
```

### Использовать ли Leads Rapidly?

```
┌─────────────────────────────────────────────┐
│  АНАЛИЗ                                      │
├─────────────────────────────────────────────┤
│  ✅ Плюсы:                                  │
│  - Дёшево ($29-49/мес)                     │
│  - Работает (пока)                          │
│                                             │
│  ❌ Минусы:                                 │
│  - Может закрыться любой момент            │
│  - Нестабильная работа (downtime)          │
│  - Качество ниже чем Apollo direct         │
│  - Этические вопросы                        │
│  - Риск для твоего бизнеса                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  РЕКОМЕНДАЦИЯ                                │
├─────────────────────────────────────────────┤
│  ❌ НЕ ИСПОЛЬЗУЙ для critical операций      │
│     └─ Не строй бизнес на их сервисе       │
│                                             │
│  ⚠️ МОЖНО как временное решение            │
│     └─ Для тестирования market             │
│     └─ Side projects                        │
│                                             │
│  ✅ ЛУЧШЕ:                                  │
│     - Google Maps API (stable)             │
│     - Apollo Free + Hunter.io              │
│     - Sustainable процесс                   │
└─────────────────────────────────────────────┘
```

### Если всё равно хочешь попробовать:

```
ПРАВИЛА БЕЗОПАСНОГО ИСПОЛЬЗОВАНИЯ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. НЕ завязывай критичные процессы
   └─ Держи backup источник лидов

2. Месячная подписка (не годовая)
   └─ Быстрый выход если проблемы

3. Экспортируй данные сразу
   └─ Сохраняй локально
   └─ Не храни только у них

4. Готовность к downtime
   └─ 2-3 дня/мес не работает = норма

5. Диверсификация
   └─ 30% Leads Rapidly
   └─ 70% другие источники
```

---

## 📚 Ключевые инсайты

### 1. Вся индустрия = круговорот scraping

```
LinkedIn → Apollo → Leads Rapidly → Users

Все scrape друг друга
Все запрещают scraping себя
Все продолжают делать бизнес
```

### 2. Leads Rapidly = micro SaaS

```
Размер: $300K-$1M ARR
Команда: 1-3 человека
Риск закрытия: ВЫСОКИЙ
Longevity: 6-24 месяца
```

### 3. Технически возможно, экономически нет

```
Построить свой Apollo scraper:
- Технически: ДА (15-20 часов)
- Экономически: НЕТ (break-even 7 лет)
- Opportunity cost: $4,000
```

### 4. Лучшая альтернатива

```
Google Maps API:
- 8,000 лидов/мес БЕСПЛАТНО
- Легально и стабильно
- Качество ⭐⭐⭐⭐⭐
- No риск бана
```

---

## 🔥 Финальный вердикт

```
APOLLO SCRAPING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Техника: Shared premium accounts + browser automation
Легальность: Серая зона (TOS violation, не закон)
Риски: Бан, нестабильность, юридические иски

LEADS RAPIDLY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Тип: Micro SaaS ($300K-$1M ARR)
Команда: 1-3 человека, bootstrap
Будущее: Либо взлёт, либо закрытие (6-24 мес)

РЕКОМЕНДАЦИЯ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ НЕ строй свой Apollo scraper (not worth it)
❌ НЕ полагайся на Leads Rapidly (unstable)
✅ ИСПОЛЬЗУЙ Google Maps API (best choice)
✅ КОМБИНИРУЙ легальные источники

Bottom line:
"Leads Rapidly = временный костыль,
не фундамент для бизнеса.

Строй на стабильном фундаменте:
Google Maps API + Hunter.io + Apollo Free"
```

---

**Версия документа:** 1.0
**Последнее обновление:** 2025-11-09
**Следующий review:** 2025-05-09 (через 6 месяцев)

## 📅 Когда пересмотреть

```
[ ] Если Leads Rapidly закроется
[ ] Если Apollo изменит политику
[ ] Появятся новые легальные альтернативы
[ ] Через 6 месяцев (плановый review)
```
