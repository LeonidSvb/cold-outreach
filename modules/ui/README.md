# Unified Streamlit UI Platform

Single entry point for all cold outreach tools with modular architecture.

## 🚀 Quick Start

```bash
streamlit run modules/ui/main_app.py
```

## 📂 Structure

```
modules/ui/
├── main_app.py              # Main entry point
├── components/              # Reusable UI components
│   ├── file_uploader.py    # Universal CSV uploader with results browser
│   ├── column_selector.py  # Column selection and mapping
│   ├── progress_tracker.py # Live progress tracking
│   ├── results_viewer.py   # Results display with download
│   └── pipeline_status.py  # Sidebar pipeline status tracker
├── tabs/                    # Modular tabs
│   ├── email_scraper_tab.py    # Email scraping (homepage_email_scraper)
│   ├── email_validator_tab.py  # Email validation (mails.so)
│   └── ai_processor_tab.py     # OpenAI processing with prompts
├── results/                 # Saved results
└── prompt_library.json      # Saved AI prompts

## 🔄 Data Flow

1. **Email Scraper Tab**
   - Upload CSV with websites
   - Configure scraping options
   - Extract emails from homepages
   - → Results saved to `st.session_state['scraped_data']`

2. **Email Validator Tab**
   - Auto-loads scraped data OR upload manually
   - Configure mails.so API
   - Validate emails
   - → Results saved to `st.session_state['validated_data']`

3. **AI Processor Tab**
   - Auto-loads validated data OR upload manually
   - Filter deliverable emails
   - Choose/create prompts
   - Generate icebreakers/summaries
   - → Results saved to `st.session_state['ai_processed_data']`

## 💡 Key Features

### Session State Data Sharing
Data flows automatically between tabs via `st.session_state`:
- No need to re-upload files
- Results persist during session
- Pipeline status visible in sidebar

### Reusable Components
All tabs use the same components:
- `render_file_uploader()` - consistent upload experience
- `render_column_selector()` - smart column detection
- `render_progress_tracker()` - unified progress UI
- `render_results_viewer()` - standardized result display

### Flexible Workflow
- Start from any tab (upload manually)
- Skip steps (e.g., scrape → AI, skip validation)
- Iterative AI processing (add multiple columns)
- Download at any step

## 🎨 Component Library

### file_uploader
```python
from modules.ui.components import render_file_uploader

df = render_file_uploader(
    label="Upload CSV",
    with_results_browser=True,
    results_dir="path/to/results",
    key_prefix="unique_key"
)
```

### column_selector
```python
from modules.ui.components import render_column_selector

selected = render_column_selector(
    columns=df.columns.tolist(),
    label="Select columns",
    multiselect=True,
    default_selection=['email', 'name']
)
```

### progress_tracker
```python
from modules.ui.components import render_progress_tracker

render_progress_tracker(
    total=100,
    processed=75,
    success=60,
    failed=15,
    current_item="example.com"
)
```

### results_viewer
```python
from modules.ui.components import render_results_viewer

render_results_viewer(
    df=results_df,
    title="Results",
    show_download=True,
    download_filename="results.csv"
)
```

### pipeline_status
```python
from modules.ui.components import render_pipeline_status

render_pipeline_status()  # Automatically reads session_state
```

## 🔧 Extending the Platform

### Adding a New Tab

1. Create tab file: `modules/ui/tabs/my_new_tab.py`

```python
def render_my_new_tab():
    st.header("My New Feature")

    # Use shared components
    from modules.ui.components import render_file_uploader

    df = render_file_uploader(
        label="Upload data",
        key_prefix="my_tab"
    )

    if df is not None:
        # Your logic here
        results = process_data(df)

        # Save to session state
        st.session_state['my_results'] = results
```

2. Register in `modules/ui/tabs/__init__.py`:

```python
from .my_new_tab import render_my_new_tab

__all__ = [..., 'render_my_new_tab']
```

3. Add to `main_app.py`:

```python
from modules.ui.tabs import render_my_new_tab

tab4 = st.tabs([..., "My New Tab"])

with tab4:
    render_my_new_tab()
```

### Creating a Custom Component

1. Create component file: `modules/ui/components/my_component.py`

```python
def render_my_component(param1, param2):
    """
    Reusable component description
    """
    # Component logic
    pass
```

2. Register in `modules/ui/components/__init__.py`:

```python
from .my_component import render_my_component

__all__ = [..., 'render_my_component']
```

3. Use in any tab:

```python
from modules.ui.components import render_my_component

render_my_component(param1="value", param2="value")
```

## 📊 Pipeline Status Tracking

The sidebar automatically tracks:
- ✅ Scraped data: row count, email count
- ✅ Validated data: deliverable count, rate
- ✅ AI processed data: with icebreakers count

Plus quick actions:
- 🗑️ Clear all data
- 📥 Download final results

## 🎯 Best Practices

1. **Always use key_prefix**: Prevents widget key collisions
   ```python
   render_file_uploader(key_prefix="unique_tab_name")
   ```

2. **Check session_state before using**:
   ```python
   if 'scraped_data' in st.session_state:
       df = st.session_state['scraped_data']
   ```

3. **Provide fallback options**:
   ```python
   # Try to load from session, else manual upload
   if 'data' in st.session_state:
       use_session_data()
   else:
       upload_manually()
   ```

4. **Save results to session_state**:
   ```python
   st.session_state['my_results'] = processed_df
   ```

## 🐛 Troubleshooting

**Tab not loading?**
- Check import in `modules/ui/tabs/__init__.py`
- Ensure `sys.path` includes project root
- Verify all dependencies imported

**Session state not working?**
- Check exact key names (case-sensitive)
- Use `st.rerun()` after state changes
- Clear with `st.session_state.clear()` if stuck

**Components not found?**
- Verify `__init__.py` exports component
- Check import statement matches export
- Ensure project root in `sys.path`

## 📝 Version History

### v1.0.0 (2025-11-21)
- Initial unified platform
- Email scraper tab
- Email validator tab
- AI processor tab
- Reusable component library
- Pipeline status tracking
- Session state data sharing
