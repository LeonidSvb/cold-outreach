# Modules Changelog

## 2025-01-15

### Architecture Refactoring
- 🏗️ **MAJOR REFACTOR**: Moved from monolithic scripts to modular architecture
- ✅ **ADDED**: 4 independent modules (link_extractor, link_filter, content_scraper, content_summarizer)  
- ✅ **ADDED**: Flexible CSV processor for any column structure
- ✅ **ADDED**: Auto-logging system with performance tracking
- 🔧 **ARCHITECTURE**: Separated prompts from code for easy editing
- 🔧 **ARCHITECTURE**: Each module completely independent, can work standalone or combined
- 📦 **MIGRATION**: Moved legacy code to legacy/ folder (preserved for reference)

### link_extractor v1.0.0
- ✅ **ADDED**: Extract all links from website with depth control
- ✅ **ADDED**: Automatic duplicate filtering and domain validation
- 🔧 **ARCHITECTURE**: Using requests + BeautifulSoup for HTTP-only scraping per CLAUDE.md

### link_filter v1.0.0  
- ✅ **ADDED**: AI-based relevance filtering using external prompts
- ✅ **ADDED**: Configurable filtering criteria (pages to include/exclude)
- 🔧 **ARCHITECTURE**: Prompt-based filtering via core/prompts/link_filtering.txt

### content_scraper v1.0.0
- ✅ **ADDED**: Scrape multiple URLs to clean JSON format  
- ✅ **ADDED**: HTML parsing with CSS/JS removal
- ✅ **ADDED**: Text extraction and JSON structuring
- 🔧 **ARCHITECTURE**: Combined scraping + conversion in one function for simplicity

### content_summarizer v1.0.0
- ✅ **ADDED**: Extract key facts for personalization from scraped content
- ✅ **ADDED**: Company insights, services, and unique selling points extraction
- 🔧 **ARCHITECTURE**: AI-powered summarization using core/prompts/summarization.txt

## Migration Notes:
- Old processors preserved in legacy/ folder
- All functionality maintained, now more modular and flexible
- CSV processing now works with any column structure
- Auto-logging replaces manual statistics tracking