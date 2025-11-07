# Стратегии деплоймента агентов Claude Code

**Дата создания:** 2025-11-03
**Источник:** Беседа с Claude Code

---

## Оглавление
1. [4 способа деплоймента](#4-способа-деплоймента)
2. [Markdown файл + скрипты](#вариант-1-markdown-файл--скрипты)
3. [Claude Code Plugin](#вариант-2-claude-code-plugin)
4. [MCP Server](#вариант-3-mcp-server)
5. [Standalone SaaS](#вариант-4-standalone-saas)
6. [Сравнительная таблица](#сравнительная-таблица)
7. [Рекомендации](#рекомендации)

---

## 4 способа деплоймента

Если вы хотите:
- ✅ Использовать агента в других проектах
- ✅ Передать клиенту
- ✅ Продать как продукт
- ✅ Опубликовать в marketplace

Есть 4 основных подхода с разной сложностью и возможностями.

---

## Вариант 1: Markdown файл + скрипты

### САМЫЙ ПРОСТОЙ способ

**Что передаёте:**

```bash
apollo-icp-analyzer-package/
├─ README.md                      # Инструкция по установке
├─ .claude/
│   └─ agents/
│       └─ apollo-icp-analyzer.md  # Агент
├─ modules/
│   └─ apollo/
│       ├─ apollo_icp_validator.py
│       ├─ analyze_icp_results.py
│       └─ tools/
│           ├─ email_validator.py
│           └─ company_normalizer.py
└─ requirements.txt                # pip install pandas, etc.
```

### Инструкция для клиента:

```markdown
# Установка Apollo ICP Analyzer

## Требования:
- Claude Code установлен
- Python 3.8+
- Git (опционально)

## Установка:

1. Скопируйте папку `.claude/agents/` в ваш проект:
   ```bash
   cp -r .claude/agents/apollo-icp-analyzer.md /path/to/your/project/.claude/agents/
   ```

2. Скопируйте `modules/apollo/` в ваш проект:
   ```bash
   cp -r modules/apollo /path/to/your/project/modules/
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Готово! Используйте в Claude Code:
   ```
   "Проанализируй мой Apollo CSV файл"
   ```

## Использование:

Поместите ваш CSV файл в проект и скажите Claude:
- "Validate this Apollo CSV against call center ICP"
- "Normalize company names and locations in this file"
- "Score these companies by ICP fit"

Агент автоматически обработает файл и создаст отчёт.
```

### Плюсы:

```
✅ Очень просто распространять (просто файлы)
✅ Работает сразу после копирования
✅ Нет технических сложностей
✅ Клиент видит весь код (прозрачность)
✅ Легко модифицировать под свои нужды
✅ Не требует особых знаний для установки
```

### Минусы:

```
❌ Клиент видит весь код (можно скопировать/украсть)
❌ Нужно вручную копировать файлы
❌ Нет автообновлений
❌ Нужна установка Python и зависимостей
❌ Нет защиты интеллектуальной собственности
```

### Когда использовать:

- Делитесь с коллегами/командой
- Open source проект
- Прозрачность важнее защиты кода
- Простота установки критична
- Не планируете коммерциализацию

### Пример продажи:

```markdown
# Apollo ICP Analyzer - $49

## Что включено:
- Агент для Claude Code
- 5 готовых Python скриптов
- Документация и примеры
- Email поддержка 30 дней

## Доставка:
- ZIP файл с полным пакетом
- Инструкция по установке
- Обновления бесплатно в течение года

## Покупка:
[Buy on Gumroad - $49] [Buy with Stripe]
```

---

## Вариант 2: Claude Code Plugin

### РЕКОМЕНДУЕМЫЙ для коммерческих продуктов

**Что это:**

Claude Code Plugins = пакеты с агентами + скриптами + tools
Работают как VS Code extensions

### Структура плагина:

```bash
apollo-icp-analyzer-plugin/
├─ .claude-plugin/
│   └─ plugin.json              # Метаданные (ОБЯЗАТЕЛЬНО)
├─ agents/
│   └─ apollo-icp-analyzer.md
├─ skills/                       # Опционально
│   └─ apollo-skills.md
├─ commands/                     # Опционально
│   └─ validate-icp.md
├─ hooks/                        # Опционально
│   └─ hooks.json
└─ scripts/
    ├─ apollo_icp_validator.py
    ├─ analyze_icp_results.py
    └─ requirements.txt
```

### plugin.json:

```json
{
  "name": "apollo-icp-analyzer",
  "version": "1.0.0",
  "description": "Validates Apollo leads against ICP criteria and normalizes data",
  "author": "Your Name",
  "license": "Commercial",
  "homepage": "https://your-website.com/apollo-analyzer",
  "repository": "https://github.com/your-name/apollo-analyzer-plugin",

  "agents": ["agents/apollo-icp-analyzer.md"],
  "skills": ["skills/apollo-skills.md"],
  "commands": ["commands/validate-icp.md"],

  "scripts": {
    "postinstall": "pip install -r scripts/requirements.txt"
  },

  "dependencies": {
    "python": ">=3.8",
    "pip": [
      "pandas>=2.0.0",
      "requests>=2.31.0"
    ]
  },

  "pricing": {
    "model": "one-time",
    "price": 49,
    "currency": "USD"
  }
}
```

### Как клиент устанавливает:

```bash
# Вариант 1: Через Claude Code CLI
claude-code plugin install apollo-icp-analyzer-plugin.zip

# Вариант 2: В интерактивном режиме
# В Claude Code:
/plugin install apollo-icp-analyzer-plugin

# Вариант 3: Из marketplace
/plugin marketplace add https://your-marketplace.com/plugins
/plugin install apollo-icp-analyzer
```

### Автоматическая установка зависимостей:

```json
// plugin.json с postinstall скриптом
{
  "scripts": {
    "postinstall": "pip install -r scripts/requirements.txt && echo 'Apollo ICP Analyzer ready!'"
  }
}
```

При установке плагина автоматически:
1. Распаковывается в `.claude/plugins/apollo-icp-analyzer/`
2. Запускается `postinstall` скрипт
3. Устанавливаются Python зависимости
4. Агент становится доступен

### Плюсы:

```
✅ Профессиональная упаковка
✅ Легкая установка для клиента (одна команда)
✅ Автоматическая установка зависимостей
✅ Можно продавать через marketplace
✅ Версионирование и обновления
✅ Можно защитить код (обфускация Python)
✅ Централизованное управление (marketplace)
✅ Автообновления (если настроить)
```

### Минусы:

```
❌ Нужно создать plugin структуру
❌ Требует больше времени на подготовку
⚠️ Claude Code plugin system в активной разработке
⚠️ Marketplace пока не полностью публичен
```

### Создание marketplace для продажи:

```bash
# my-plugins-marketplace/
├─ marketplace.json
├─ apollo-icp-analyzer/
│   └─ (plugin files)
├─ instantly-optimizer/
│   └─ (plugin files)
└─ linkedin-scraper/
    └─ (plugin files)
```

**marketplace.json:**

```json
{
  "name": "Outreach Automation Plugins",
  "description": "Professional Claude Code plugins for cold outreach",
  "url": "https://github.com/your-name/claude-plugins",
  "author": "Your Name",

  "plugins": [
    {
      "id": "apollo-icp-analyzer",
      "name": "Apollo ICP Analyzer",
      "description": "Validate Apollo leads against ICP",
      "version": "1.0.0",
      "price": 49,
      "path": "./apollo-icp-analyzer"
    },
    {
      "id": "instantly-optimizer",
      "name": "Instantly Campaign Optimizer",
      "description": "Optimize Instantly.ai campaigns",
      "version": "1.2.0",
      "price": 79,
      "path": "./instantly-optimizer"
    }
  ]
}
```

### Клиент добавляет ваш marketplace:

```bash
# В Claude Code:
/plugin marketplace add https://github.com/your-name/claude-plugins

# Видит список:
Apollo ICP Analyzer - $49
Instantly Campaign Optimizer - $79
LinkedIn Scraper - $39

# Устанавливает:
/plugin install apollo-icp-analyzer
```

### Система оплаты (интеграция):

```json
// plugin.json
{
  "pricing": {
    "model": "one-time",
    "price": 49,
    "payment": {
      "gumroad": "https://gumroad.com/l/apollo-analyzer",
      "stripe": "price_xxxxxxxxxxxxx",
      "license_key_required": true
    }
  }
}
```

При установке:
1. Клиент покупает через Gumroad/Stripe
2. Получает license key
3. Вводит при установке плагина
4. Плагин активируется

---

## Вариант 3: MCP Server

### Для API-based tools и сервисов

**Что это:**

MCP (Model Context Protocol) = способ создать **НАСТОЯЩИЕ Claude Code Tools**
Это единственный способ добавить новые tools помимо встроенных!

### Когда использовать MCP:

```
✅ Нужен НОВЫЙ Claude Code Tool (не Python скрипт)
✅ Tool должен работать быстро (без subprocess)
✅ Интеграция с внешними API (Apollo, Instantly, Hunter.io)
✅ Реалтайм операции (websockets, streaming)
✅ Сложная логика требующая TypeScript/Node.js
```

**НЕ используйте для:**
```
❌ Простая обработка CSV с pandas → используйте Python скрипт
❌ Анализ данных → используйте Python скрипт
❌ Одноразовые задачи → используйте Python скрипт
```

### Пример: Apollo MCP Server

```typescript
// apollo-mcp-server/src/index.ts

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({
  name: "apollo-api",
  version: "1.0.0",
});

// Регистрируем НОВЫЙ Claude Code Tool
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "apollo_search_companies",
      description: "Search companies in Apollo.io database",
      inputSchema: {
        type: "object",
        properties: {
          industry: {
            type: "string",
            description: "Target industry (e.g., 'call centers')"
          },
          employee_count: {
            type: "string",
            description: "Employee range (e.g., '10-100')"
          },
          location: {
            type: "string",
            description: "Geographic location"
          }
        },
        required: ["industry"]
      }
    },
    {
      name: "apollo_enrich_company",
      description: "Enrich company data with Apollo.io",
      inputSchema: {
        type: "object",
        properties: {
          domain: {
            type: "string",
            description: "Company website domain"
          }
        },
        required: ["domain"]
      }
    }
  ]
}));

// Обработка вызова tools
server.setRequestHandler("tools/call", async (request) => {
  const apiKey = process.env.APOLLO_API_KEY;

  if (request.params.name === "apollo_search_companies") {
    const { industry, employee_count, location } = request.params.arguments;

    const response = await fetch("https://api.apollo.io/v1/mixed_companies/search", {
      method: "POST",
      headers: {
        "X-Api-Key": apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        q_organization_keyword_tags: [industry],
        organization_num_employees_ranges: [employee_count],
        q_organization_locations: [location],
        page: 1,
        per_page: 50
      })
    });

    const data = await response.json();

    return {
      content: [{
        type: "text",
        text: JSON.stringify(data.accounts, null, 2)
      }]
    };
  }

  if (request.params.name === "apollo_enrich_company") {
    const { domain } = request.params.arguments;

    const response = await fetch(`https://api.apollo.io/v1/organizations/enrich?domain=${domain}`, {
      headers: { "X-Api-Key": apiKey }
    });

    const data = await response.json();

    return {
      content: [{
        type: "text",
        text: JSON.stringify(data.organization, null, 2)
      }]
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### package.json:

```json
{
  "name": "apollo-mcp-server",
  "version": "1.0.0",
  "description": "MCP server for Apollo.io API integration",
  "type": "module",
  "bin": {
    "apollo-mcp-server": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "prepare": "npm run build"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^0.5.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0"
  }
}
```

### Клиент устанавливает:

```bash
# 1. Установка MCP сервера
npm install -g apollo-mcp-server

# 2. Конфигурация в Claude Code
# .claude/settings.json
{
  "mcpServers": {
    "apollo-api": {
      "command": "apollo-mcp-server",
      "env": {
        "APOLLO_API_KEY": "client-api-key-here"
      }
    }
  }
}
```

### Теперь Claude видит новые tools:

```xml
<!-- В Claude Code автоматически доступны: -->

<invoke name="apollo_search_companies">
  <parameter name="industry">call centers</parameter>
  <parameter name="employee_count">10-100</parameter>
  <parameter name="location">United States</parameter>
</invoke>

<invoke name="apollo_enrich_company">
  <parameter name="domain">example.com</parameter>
</invoke>
```

### Плюсы MCP:

```
✅ Создаёт НАСТОЯЩИЕ Claude Code Tools
✅ Быстро (нет Python subprocess overhead)
✅ Claude видит их как встроенные tools
✅ Интеграция с любыми API
✅ TypeScript/Node.js экосистема
✅ Профессиональный подход
✅ Можно стримить данные
✅ Websockets, real-time обновления
```

### Минусы MCP:

```
❌ Сложнее создавать (TypeScript)
❌ Нужна установка Node.js
❌ Требует технических знаний
❌ Для простых задач - overkill
❌ Дольше разрабатывать
```

### Продажа MCP Server:

```markdown
# Apollo API MCP Server - $99

Профессиональный MCP сервер для интеграции Apollo.io с Claude Code.

## Включает:
- 5 готовых tools: search, enrich, contacts, export, validate
- Автоматическая rate limiting
- Кэширование запросов
- Error handling и retry логика
- Документация и примеры

## Установка:
```bash
npm install -g apollo-mcp-server
```

## Лицензия:
- Одноразовая оплата $99
- Обновления бесплатно
- Коммерческое использование
```

---

## Вариант 4: Standalone SaaS

### Для монетизации через подписку

**Бизнес-модель:**

```
Вы создаёте облачный сервис → клиенты платят подписку
```

### Архитектура:

```bash
apollo-icp-analyzer-saas/
├─ frontend/                # React/Next.js UI
│   ├─ src/
│   │   ├─ pages/
│   │   │   ├─ dashboard.tsx
│   │   │   ├─ validate.tsx
│   │   │   └─ pricing.tsx
│   │   └─ components/
├─ backend/                 # FastAPI с вашей логикой
│   ├─ main.py
│   ├─ api/
│   │   ├─ validate.py      # Ваш apollo_icp_validator
│   │   ├─ normalize.py
│   │   └─ analyze.py
│   └─ db/
│       └─ models.py
└─ claude-integration/      # MCP server для Claude Code
    └─ mcp-server/
        └─ index.ts
```

### MCP Server вызывает ваш API:

```typescript
// claude-integration/mcp-server/index.ts

server.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "apollo_icp_validate") {
    const { csv_data, api_key } = request.params.arguments;

    // Вызов ВАШЕГО API (код на вашем сервере)
    const response = await fetch("https://your-saas.com/api/validate", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${api_key}`,  // Клиентский API key
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ csv_data })
    });

    if (!response.ok) {
      throw new Error("Validation failed");
    }

    const result = await response.json();
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  }
});
```

### Backend API (ваш сервер):

```python
# backend/api/validate.py

from fastapi import APIRouter, Depends, HTTPException
from ..auth import verify_api_key, check_usage_limits
from ..core.apollo_icp_validator import validate_icp

router = APIRouter()

@router.post("/validate")
async def validate_apollo_data(
    csv_data: str,
    api_key: str = Depends(verify_api_key)
):
    # Проверка лимитов подписки
    user = await check_usage_limits(api_key)
    if not user.has_credits():
        raise HTTPException(status_code=402, detail="Upgrade plan")

    # Ваша логика (защищена на сервере!)
    result = validate_icp(csv_data)

    # Списание кредита
    await user.deduct_credit(1)

    # Аналитика
    await log_usage(user.id, "validate", len(csv_data))

    return result
```

### Pricing plans:

```python
# backend/db/models.py

class Subscription(BaseModel):
    plan: Literal["free", "pro", "enterprise"]
    validations_per_month: int
    price: int

PLANS = {
    "free": Subscription(
        plan="free",
        validations_per_month=100,
        price=0
    ),
    "pro": Subscription(
        plan="pro",
        validations_per_month=5000,
        price=29
    ),
    "enterprise": Subscription(
        plan="enterprise",
        validations_per_month=-1,  # unlimited
        price=199
    )
}
```

### Клиент использует:

```bash
# 1. Регистрируется на your-saas.com
# 2. Выбирает план: Free / Pro ($29/мес) / Enterprise ($199/мес)
# 3. Получает API key
# 4. Устанавливает ваш MCP server:

npm install -g apollo-icp-saas-connector

# 5. Конфигурирует Claude Code:
# .claude/settings.json
{
  "mcpServers": {
    "apollo-icp": {
      "command": "apollo-icp-saas-connector",
      "env": {
        "API_KEY": "client-api-key-from-your-saas"
      }
    }
  }
}

# 6. Использует в Claude:
"Validate this Apollo CSV against ICP"
```

### Преимущества SaaS модели:

```
✅ Защита кода (клиент НЕ видит логику)
✅ Recurring revenue (ежемесячная подписка)
✅ Можно обновлять без действий клиента
✅ Аналитика использования (метрики)
✅ Масштабируется
✅ Можно добавлять фичи без обновления у клиента
✅ Контроль доступа (отключить неплательщиков)
✅ A/B тестирование
```

### Недостатки SaaS:

```
❌ Сложная инфраструктура (сервер, база, мониторинг)
❌ Нужен хостинг ($50-500/месяц)
❌ Нужна поддержка клиентов
❌ Больше ответственности (uptime, security)
❌ Дольше разрабатывать (фронтенд, авторизация, billing)
❌ Требует DevOps знаний
```

---

## Сравнительная таблица

| Критерий | Markdown + Scripts | Plugin | MCP Server | SaaS |
|----------|-------------------|--------|------------|------|
| **Сложность создания** | ⭐ Очень просто | ⭐⭐ Средне | ⭐⭐⭐ Сложно | ⭐⭐⭐⭐⭐ Очень сложно |
| **Простота установки** | ⭐⭐⭐ (копировать файлы) | ⭐⭐⭐⭐⭐ (одна команда) | ⭐⭐⭐⭐ (npm + config) | ⭐⭐⭐⭐⭐ (только API key) |
| **Защита кода** | ❌ Клиент видит всё | ⚠️ Можно обфусцировать | ⚠️ TypeScript виден | ✅ Код на сервере |
| **Автообновления** | ❌ Вручную | ✅ Через marketplace | ⚠️ npm update | ✅ Автоматически |
| **Монетизация** | Одноразовая продажа | Одноразовая/$лицензия | Одноразовая | Подписка (MRR) |
| **Цена продажи** | $19-49 | $49-99 | $99-199 | $29-199/месяц |
| **Требования у клиента** | Python, pip | Claude Code | Node.js, npm | Только Claude Code |
| **Скорость работы** | 🐌 Python subprocess | 🐌 Python subprocess | ⚡ Native speed | ⚡ API (зависит от сети) |
| **Offline работа** | ✅ Да | ✅ Да | ✅ Да | ❌ Нужен интернет |
| **Поддержка** | Email support | Email support | Email support | Тикет-система, чат |
| **Время разработки** | 1-2 дня | 3-5 дней | 1-2 недели | 1-3 месяца |

---

## Рекомендации

### Для вашего Apollo ICP Analyzer:

#### Если хотите быстро начать продавать:

**Используйте Plugin подход:**

```bash
1. Создайте структуру плагина (1 день)
2. Опубликуйте на Gumroad за $49
3. Маркетинг через Twitter, Reddit
4. Собирайте feedback и улучшайте

Potential revenue: $49 × 20 продаж/месяц = ~$1,000/месяц
```

#### Если хотите масштабировать и защитить код:

**Используйте SaaS подход:**

```bash
1. Создайте простой MCP server (1 неделя)
2. Backend API с вашей логикой (1 неделя)
3. Простой лендинг + Stripe (3 дня)
4. Запуск с Free планом для роста

Pricing:
- Free: 100 validations/месяц
- Pro: $29/месяц - 5,000 validations
- Enterprise: $199/месяц - unlimited

Potential revenue: $29 × 50 клиентов = $1,450 MRR
```

#### Если это для команды/open source:

**Используйте Markdown + Scripts:**

```bash
1. Создайте README (2 часа)
2. Опубликуйте на GitHub
3. Поделитесь в сообществе

Free для всех, reputation++
```

---

## Следующие шаги

### Хотите создать Plugin?

Я могу помочь:
1. Создать правильную структуру папок
2. Написать `plugin.json` с метаданными
3. Подготовить README для клиентов
4. Упаковать в .zip для продажи

### Хотите MCP Server?

Я могу:
1. Конвертировать ваш Python код в TypeScript MCP server
2. Создать Apollo API integration
3. Настроить автоматический rate limiting
4. Подготовить npm package

### Хотите SaaS?

Я могу помочь спланировать:
1. Архитектуру (backend + frontend + MCP)
2. Pricing strategy
3. MVP scope (что делать первым)
4. Tech stack recommendations

---

## Связанные материалы

- [Агенты - полное руководство](./agents-explained.md)
- [Tools vs Scripts - фундаментальная разница](./tools-vs-scripts.md)
- [MCP Servers Guide](./mcp-servers-guide.md)

---

**Обновлено:** 2025-11-03
**Статус:** Актуально для Claude Code latest
