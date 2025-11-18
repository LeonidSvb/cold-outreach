# 🚀 VPS Deployment Guide

## Автоматический деплой скриптов на Hostinger VPS

### 📋 Что ты получишь:

- ✅ Все Python скрипты на VPS
- ✅ Автоматическая установка зависимостей
- ✅ Готовая структура папок
- ✅ Cron jobs для автозапуска (опционально)

---

## 🎯 Шаг 1: Найди данные VPS в Hostinger

### Где найти:

1. Зайди в **Hostinger hPanel**
2. Перейди в **VPS → SSH Access**
3. Найди:
   - **IP адрес** (например: `185.123.45.67`)
   - **Username** (обычно `root`)
   - **SSH Port** (обычно `22`)

---

## 🚀 Шаг 2: Запусти автоматический деплой

### Одна команда делает все:

```cmd
deploy_to_vps.bat [IP_АДРЕС] [USERNAME]
```

### Пример:

```cmd
deploy_to_vps.bat 185.123.45.67 root
```

### Что происходит автоматически:

1. ✅ Проверяет SSH подключение
2. ✅ Создает структуру папок на VPS
3. ✅ Загружает все Python скрипты
4. ✅ Загружает .env файл (API ключи)
5. ✅ Устанавливает Python зависимости
6. ✅ Готово к использованию!

---

## 📱 Шаг 3: Запусти скрипт на VPS

### Подключись к VPS:

```bash
ssh -i C:Users79818.sshhostinger_key root@185.123.45.67
```

### Запусти любой скрипт:

```bash
cd /root/cold-outreach

# Apollo lead collection
python3 modules/apollo/scripts/apollo_lead_collector.py

# Email scraping
python3 modules/scraping/scripts/simple_homepage_scraper.py --input data/raw/websites.csv

# Instantly sync
python3 modules/instantly/scripts/instantly_sync.py
```

### Скачай результаты обратно:

```cmd
scp -i C:Users79818.sshhostinger_key root@185.123.45.67:/root/cold-outreach/modules/apollo/results/*.json ./local-results/
```

---

## ⏰ Шаг 4: Настрой автозапуск (Cron Jobs)

### Автоматический запуск скриптов по расписанию:

1. **Загрузи setup скрипт на VPS:**
   ```cmd
   scp -i C:Users79818.sshhostinger_key setup_cron_jobs.sh root@185.123.45.67:/root/
   ```

2. **Подключись к VPS:**
   ```bash
   ssh -i C:Users79818.sshhostinger_key root@185.123.45.67
   ```

3. **Запусти setup:**
   ```bash
   chmod +x /root/setup_cron_jobs.sh
   /root/setup_cron_jobs.sh
   ```

### Автоматическое расписание:

- **Apollo leads:** Каждый день в 9:00 утра
- **Instantly sync:** Каждые 6 часов
- **Email scraping:** Каждый понедельник в 10:00
- **Backup результатов:** Ежедневно в полночь

---

## 🔧 Troubleshooting

### Ошибка: "Permission denied (publickey)"

**Решение:**
```bash
# Установи правильные права на SSH ключ
icacls "C:Users79818.sshhostinger_key" /inheritance:r
icacls "C:Users79818.sshhostinger_key" /grant:r "%USERNAME%:R"
```

### Ошибка: "Python3 not found"

**Решение (на VPS):**
```bash
ssh -i C:Users79818.sshhostinger_key root@185.123.45.67

# Установи Python
apt update
apt install python3 python3-pip -y
```

### Ошибка: "Module not found"

**Решение (переустанови зависимости):**
```bash
ssh -i C:Users79818.sshhostinger_key root@185.123.45.67
cd /root/cold-outreach
pip3 install -r requirements.txt --upgrade
```

---

## 📊 Проверка логов на VPS

### Смотри логи в реальном времени:

```bash
# Apollo logs
tail -f /root/cold-outreach/logs/apollo_$(date +%Y%m%d).log

# Instantly logs
tail -f /root/cold-outreach/logs/instantly_$(date +%Y%m%d).log

# Все логи
ls -lh /root/cold-outreach/logs/
```

---

## 🎯 Полезные команды

### Проверить статус cron jobs:

```bash
crontab -l
```

### Редактировать расписание:

```bash
crontab -e
```

### Посмотреть запущенные процессы:

```bash
ps aux | grep python
```

### Очистить старые результаты:

```bash
cd /root/cold-outreach
rm modules/*/results/*.json
```

---

## 🔄 Обновление скриптов

### Когда изменил код локально - обновляешь на VPS:

```cmd
# Просто запусти деплой еще раз
deploy_to_vps.bat 185.123.45.67 root
```

Скрипт автоматически перезапишет файлы новыми версиями!

---

## 💡 Tips & Tricks

### 1. Alias для быстрого подключения

Создай alias в Windows Terminal:

```cmd
# Добавь в PowerShell profile
Set-Alias vps "ssh -i C:Users79818.sshhostinger_key root@185.123.45.67"

# Теперь просто пиши:
vps
```

### 2. Мониторинг через Telegram bot

Можешь добавить Telegram уведомления в скрипты:

```python
import requests

def send_telegram(message):
    bot_token = "YOUR_BOT_TOKEN"
    chat_id = "YOUR_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": message})

# В конце скрипта:
send_telegram(f"✅ Apollo: Collected {len(leads)} leads")
```

### 3. Auto-backup в Google Drive

Настрой rclone для автобэкапа результатов в облако.

---

## ❓ FAQ

**Q: Можно ли запускать несколько скриптов одновременно?**
A: Да! Используй `nohup` для фоновых процессов:
```bash
nohup python3 script1.py > output1.log 2>&1 &
nohup python3 script2.py > output2.log 2>&1 &
```

**Q: Как посмотреть использование ресурсов?**
A:
```bash
htop  # Интерактивный мониторинг
df -h  # Место на диске
free -h  # RAM
```

**Q: Что делать если VPS перезагрузился?**
A: Cron jobs автоматически восстанавливаются. Проверь: `crontab -l`

**Q: Как удалить все с VPS?**
A:
```bash
ssh -i C:Users79818.sshhostinger_key root@185.123.45.67
rm -rf /root/cold-outreach
crontab -r  # Удалить cron jobs
```

---

## 🎉 Готово!

Теперь твои скрипты работают на VPS 24/7 без участия твоего компьютера!

**Нужна помощь?** Пиши в Claude Code 😉
