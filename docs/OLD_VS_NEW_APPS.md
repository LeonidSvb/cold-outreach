# Old vs New Streamlit Apps - Migration Guide

## 🔴 СТАРЫЕ APPS (НЕ ИСПОЛЬЗОВАТЬ)

### 1. **modules/scraping/homepage_email_scraper/app.py**
**3 таба:**
1. 📤 Upload & Run - загрузка CSV и запуск скрейпинга
2. 📊 View Results - просмотр результатов
3. ✅ Email Validation - валидация email (импортирует streamlit_validator)

**Проблема:** Импорт `from modules.email_verification.streamlit_validator import render_validation_tab` - ломается если запускать не из корня

**→ Заменен на:** `modules/ui/main_app.py` Tab 1 (Email Scraper) + Tab 2 (Email Validator)

---

### 2. **modules/scraping/ui/streamlit_app.py**
**Функции:**
- Universal website scraper
- 2 режима: Personal & Shared
- CSV upload, scraping, results download

**→ Заменен на:** `modules/ui/main_app.py` Tab 1 (Email Scraper)

---

### 3. **modules/scraping/ui/streamlit_homepage_scraper.py**
**Функции:**
- Enhanced homepage scraper
- Live real-time progress
- 2 modes: homepage only vs deep search

**→ Заменен на:** `modules/ui/main_app.py` Tab 1 (Email Scraper)

---

### 4. **modules/scraping/streamlit_website_parser.py**
**Функции:**
- Website content parsing
- Text extraction

**→ Заменен на:** `modules/ui/main_app.py` Tab 1 (можно добавить как 4й таб если нужно)

---

### 5. **modules/openai/streamlit_ai_processor.py**
**Функции:**
- Iterative OpenAI processing
- Column selector
- Prompt library
- Real-time cost tracking

**→ Заменен на:** `modules/ui/main_app.py` Tab 3 (AI Processor) - **ПОЛНОСТЬЮ ПЕРЕНЕСЕН**

---

### 6. **modules/email_verification/streamlit_validator.py**
**Функции:**
- Render validation tab (компонент)
- Can be embedded in other apps

**→ Заменен на:** `modules/ui/tabs/email_validator_tab.py` - **ПЕРЕНЕСЕН КАК ПОЛНОЦЕННЫЙ ТАБ**

---

### 7. **modules/email_verification/app.py**
**Функции:**
- Standalone email validation app

**→ Заменен на:** `modules/ui/main_app.py` Tab 2 (Email Validator)

---

### 8. **modules/google_maps/ui/streamlit_app.py**
**Функции:**
- Google Maps scraping UI

**→ Можно добавить как Tab 4** в `modules/ui/main_app.py` (пока не добавлен)

---

### 9. **website_content_parser/app.py**
**Функции:**
- Standalone website parser

**→ Можно добавить как Tab 4** (пока не добавлен)

---

### 10. **ai_data_processor/app.py**
**Функции:**
- AI data processing

**→ Заменен на:** `modules/ui/main_app.py` Tab 3 (AI Processor)

---

## ✅ НОВЫЙ УНИФИЦИРОВАННЫЙ APP

### **modules/ui/main_app.py**

**3 основных таба:**

#### Tab 1: 📧 Email Scraper
- **Из:** `homepage_email_scraper/app.py` (Upload & Run tab) + `streamlit_app.py` + `streamlit_homepage_scraper.py`
- **Фичи:**
  - CSV upload
  - Homepage + deep search modes
  - Email extraction (3 formats)
  - Real-time progress
  - Results browser
- **Results:** `modules/ui/results/scraper/`

#### Tab 2: ✅ Email Validator
- **Из:** `email_verification/app.py` + `streamlit_validator.py`
- **Фичи:**
  - Auto-load from Tab 1 (session state)
  - Mails.so API integration
  - Batch validation
  - Deliverable/undeliverable split
- **Results:** `modules/ui/results/validator/`

#### Tab 3: 🤖 AI Processor
- **Из:** `openai/streamlit_ai_processor.py`
- **Фичи:**
  - Iterative processing
  - Column selector
  - Prompt library (editable)
  - Cost tracking
  - Multi-column output
- **Results:** `modules/ui/results/ai_processor/`

---

## 🔄 DATA FLOW (Session State)

```
Tab 1 (Scraper)
    ↓
st.session_state['scraped_data']
    ↓
Tab 2 (Validator) ← Auto-loads scraped data
    ↓
st.session_state['validated_data']
    ↓
Tab 3 (AI) ← Auto-loads validated (deliverable) data
    ↓
st.session_state['ai_processed_data']
    ↓
Download campaign-ready CSV
```

**NO FILE RE-UPLOADS NEEDED!**

---

## 📊 COMPARISON

| Feature | Old Apps | New App |
|---------|----------|---------|
| **Number of apps** | 10 разных | 1 унифицированный |
| **Data sharing** | Manual file upload | Session state (auto) |
| **UI consistency** | Разные стили | Единый дизайн |
| **Import issues** | Часто ломаются | Работают всегда |
| **Results location** | Разбросаны | Организованы по табам |
| **Code duplication** | Много дублей | DRY (компоненты) |

---

## 🚀 HOW TO USE

### ❌ DON'T USE:
```bash
streamlit run modules/scraping/homepage_email_scraper/app.py
# Error: ModuleNotFoundError
```

### ✅ USE:
```bash
streamlit run modules/ui/main_app.py
# or
py -m streamlit run modules/ui/main_app.py
```

**Opens:** http://localhost:8501

---

## 📝 MIGRATION CHECKLIST

- [x] Email Scraper → Tab 1
- [x] Email Validator → Tab 2
- [x] AI Processor → Tab 3
- [ ] Google Maps → Tab 4 (TODO)
- [ ] Website Parser → Tab 5 (TODO)
- [ ] Archive old apps

---

## 💡 FUTURE ENHANCEMENTS

**Potential Tab 4: Google Maps Scraper**
- Apify Google Maps integration
- Location-based lead generation

**Potential Tab 5: Website Content Parser**
- Deep content extraction
- Text analysis
- SEO insights

---

## 🗑️ ARCHIVE OLD APPS

После проверки что всё работает, старые apps можно:
1. Переместить в `archive/old_streamlit_apps/`
2. Или удалить совсем

**Не удалять:**
- `streamlit_validator.py` - используется как компонент
- `streamlit_ai_processor.py` - может быть полезен для референса
