# CSV Column Transformer Module

## 🚀 AI-POWERED CSV COLUMN TRANSFORMATION SYSTEM [v1.0.0]

Advanced modular system for analyzing CSV files, detecting columns, applying AI transformations using custom prompts, and generating new enriched columns.

## 📋 KEY FEATURES

### CSV Processing (`src/`)
- **Automatic column detection** and analysis
- **Interactive prompt selection** from markdown library
- **New column generation** with AI transformations
- **Batch processing** support for large CSV files
- **Results tracking** and backup creation

### Prompt Library (`prompts.md`)
- **Centralized prompt management** in markdown format
- **Multiple transformation types** (analysis, enrichment, extraction)
- **Customizable parameters** with placeholder support
- **Easy prompt selection** interface

## 📊 MODULE ARCHITECTURE

### 1. CSV Analyzer
**File:** `src/csv_analyzer.py` (v1.0.0)
- Loads CSV files and detects column structure
- Analyzes data types and content patterns
- Presents interactive column selection interface
- Validates data quality and completeness

### 2. Prompt Manager
**File:** `src/prompt_manager.py` (v1.0.0)
- Loads and parses prompts from `prompts.md`
- Provides interactive prompt selection menu
- Handles prompt parameter substitution
- Validates prompt compatibility with selected columns

### 3. Column Transformer
**File:** `src/column_transformer.py` (v1.0.0)
- Applies AI transformations using OpenAI API
- Processes data in batches for efficiency
- Handles rate limiting and error recovery
- Generates new columns with transformed data

### 4. Results Manager
**File:** `src/results_manager.py` (v1.0.0)
- Saves transformed CSV with new columns
- Creates detailed transformation reports
- Maintains operation history and statistics
- Handles backup and recovery operations

## 🔄 QUICK START

### Standard Pipeline
```bash
# Navigate to module directory
cd modules/csv_transformer

# Run the complete pipeline
python src/csv_analyzer.py      # Step 1: Analyze CSV and select columns
python src/column_transformer.py # Step 2: Apply transformations and generate new column
```

### Interactive Mode (Recommended)
```bash
# Use interactive column transformer
python csv_column_transformer.py
```

## ⚙️ КОНФИГУРАЦИЯ

### Input Files
- **CSV Files:** Any CSV file with headers
- **Prompts:** `prompts.md` with transformation templates
- **Config:** Embedded in main script for easy customization

### Output Files
- **Transformed CSV:** Original + new transformed column
- **Reports:** Detailed transformation statistics
- **Backups:** Original file copies for safety

## 📁 MODULE STRUCTURE [v1.0.0]

```
csv_transformer/
├── src/                          # Core transformation scripts
│   ├── csv_analyzer.py          # CSV analysis and column detection
│   ├── prompt_manager.py        # Prompt loading and selection
│   ├── column_transformer.py    # AI transformation engine
│   └── results_manager.py       # Output handling and reporting
├── csv_column_transformer.py    # Main interactive script
├── prompts.md                   # Transformation prompt library
├── README.md                    # This documentation
├── results/                     # Generated CSV files and reports
└── archive/                     # Legacy versions and backups
```

## 🎯 SUPPORTED TRANSFORMATIONS

### Data Analysis
- **Company Analysis:** Extract insights from company names/domains
- **Content Enrichment:** Add metadata and categorization
- **Text Extraction:** Pull specific information from text fields

### Lead Enhancement
- **Personalization:** Generate personalized messaging
- **Industry Classification:** Categorize companies by industry
- **Priority Scoring:** Rank leads by potential value

### Content Processing
- **Summarization:** Create concise summaries of long text
- **Translation:** Translate content to different languages
- **Sentiment Analysis:** Analyze emotional tone of content

## 💡 USAGE EXAMPLES

### Example 1: Company Analysis
```
Input CSV: companies.csv (columns: company_name, website, industry)
Selected Prompt: "Company Intelligence Analysis"
New Column: company_analysis (JSON with insights, pain points, tech stack)
```

### Example 2: Lead Personalization
```
Input CSV: leads.csv (columns: first_name, last_name, company, title)
Selected Prompt: "Personalized Email Opener"
New Column: personalized_opener (Custom email opening lines)
```

## 🔧 TECHNICAL REQUIREMENTS

- **Python 3.8+** with pandas, openai libraries
- **OpenAI API key** in environment variables
- **CSV files** with proper headers
- **Sufficient API credits** for transformations

## 💰 COST ESTIMATION

- **Analysis:** $0.001 per 100 rows
- **Transformation:** $0.01-0.05 per 100 rows (depends on prompt complexity)
- **Typical cost:** $0.50-5.00 per 1000 row transformation

---

**Status:** ✅ Production Ready
**Last Update:** September 25, 2025
**Next Step:** Run your first CSV transformation