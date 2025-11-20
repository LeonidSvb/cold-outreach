# 🤖 Universal AI Data Processor

**Version:** 1.0.0
**Created:** 2025-01-20

Iterative OpenAI processing with full control over prompts and columns. Process CSV data through customizable AI prompts, add columns progressively, and manage your workflow iteratively.

---

## 🌟 Features

### Core Capabilities

- **Column Selector**: Choose which columns to send to OpenAI (checkboxes above preview table)
- **Editable Prompt Library**: Add/edit/delete prompts directly in UI - NO hardcoded prompts
- **Iterative Processing**: Run multiple times, each run adds NEW columns to DataFrame
- **Column Manager**: Delete unwanted columns between runs
- **Real-time Cost Tracking**: Track OpenAI API costs as you process
- **Session Persistence**: DataFrame persists across runs for iterative work
- **Export/Import**: Backup and share prompt libraries as JSON

### Smart Auto-Pass System

**NO placeholders needed!** Selected columns are automatically prepended to your prompts:

```
=== COMPANY DATA ===
company_name: Acme Corp
website: acme.com
industry: SaaS
===================

[Your custom prompt here]
```

### n8n-Style Preview

See exactly how your prompt will look with real data from the first row before processing.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this folder
cd ai_data_processor

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file in this folder (or use existing one in project root):

```env
OPENAI_API_KEY=sk-your-api-key-here
```

Or enter API key directly in the sidebar when running the app.

### 3. Run Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📖 How to Use

### Workflow Example: Icebreaker Generation

1. **Upload CSV**
   - Click "Choose CSV file" in sidebar
   - Upload your leads CSV with company data

2. **Select Input Columns** (Tab 2)
   - Check the columns you want OpenAI to see
   - Default: all columns selected
   - Use "Select All" / "Clear All" for convenience

3. **Choose or Create Prompt** (Tab 2)
   - Select "Icebreaker Generator" from preset dropdown
   - OR write custom prompt

4. **Review Preview**
   - See exactly how prompt looks with your data
   - Adjust prompt if needed

5. **Configure & Run**
   - Set parallel workers (default: 50)
   - Choose JSON mode if needed
   - Click "🚀 Run Processing"

6. **Review Results** (Tab 3)
   - New column "icebreaker" added to DataFrame
   - Download CSV or run another iteration

### Iterative Processing Example

**Run 1:** Generate icebreakers
→ Adds column: `icebreaker`

**Run 2:** Generate email sequence
→ Adds columns: `email_1`, `email_2`, `email_3`, `subject_line`

**Run 3:** Score leads by priority
→ Adds columns: `priority_score`, `reason`

All data persists in the same DataFrame! Delete unwanted columns anytime in Tab 3.

---

## 📚 Preset Prompts

### 1. Icebreaker Generator

**Output:** `icebreaker`
**Purpose:** Generate short (max 35 words), casual icebreakers for cold emails

### 2. Email Sequence (3 emails)

**Output:** `email_1`, `email_2`, `email_3`, `subject_line`
**Purpose:** Generate complete cold email sequence with subject line

### 3. Content Parser

**Output:** `business_type`, `services`, `value_proposition`, `target_audience`
**Purpose:** Extract business information from website content

---

## 🎨 Prompt Library Management (Tab 1)

### Add Custom Prompts

1. Click "Create New Prompt"
2. Enter:
   - Prompt name (e.g., "Priority Scorer")
   - Prompt instructions (NO placeholders needed!)
   - Description
   - Output columns (comma separated)
3. Click "💾 Save Prompt"

### Edit Prompts

1. Expand any prompt
2. Click "Edit"
3. Modify prompt/description/columns
4. Click "💾 Save Changes"

### Export/Import

**Export:** Download prompt library as JSON for backup
**Import:** Upload JSON to restore or share prompts

---

## ⚙️ Configuration

### OpenAI Settings (Sidebar)

- **API Key**: Enter your OpenAI API key (or use .env)
- **Model**: Choose from gpt-4o-mini (default), gpt-4o, gpt-4-turbo
- **Temperature**: 0.0 (deterministic) to 1.0 (creative)
- **Parallel Workers**: 1-100 (default: 50)

### Processing Options (Tab 2)

- **Process all rows**: Process entire CSV (default)
- **Sample size**: Process subset for testing
- **JSON response format**: Force OpenAI to return valid JSON
- **Real-time progress**: Show live progress updates

---

## 💰 Cost Estimation

The app estimates cost before processing:

- **Time estimate**: Based on workers and row count
- **Cost estimate**: ~$0.002 per row for gpt-4o-mini
- **Real-time cost**: Updates during processing
- **Total cost**: Tracked across all runs in session

**Cost saving tip:** Test with sample size first, then process all rows.

---

## 🌐 Deploy to Streamlit Cloud

### 1. Prepare Repository

Ensure your repo has:

```
ai_data_processor/
├── app.py
├── requirements.txt
├── README.md
└── results/
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Select `ai_data_processor/app.py` as main file
4. Add `OPENAI_API_KEY` to Secrets:

```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```

5. Click "Deploy"

---

## 🔧 Troubleshooting

### Error: "Please provide OpenAI API key"

**Solution:** Add API key in sidebar or create `.env` file with `OPENAI_API_KEY`

### Error: "Please specify output columns"

**Solution:** Enter comma-separated column names (e.g., `icebreaker, score`)

### Error: Rate limit exceeded

**Solution:** Reduce parallel workers (try 10-20 instead of 50)

### Slow processing

**Solution:**
- Increase parallel workers (up to 100)
- Use gpt-4o-mini instead of gpt-4o (faster & cheaper)
- Check your internet connection

### Results look wrong

**Solution:**
- Review prompt preview to ensure data is passed correctly
- Adjust temperature (lower = more consistent)
- Try JSON mode for structured output
- Edit prompt to be more specific

---

## 📊 Results Management (Tab 3)

### Column Manager

- **View added columns**: See which columns were added vs. original
- **Delete columns**: Select and delete unwanted columns
- **Reset to original**: Restore uploaded CSV state

### Download Results

- Download processed CSV with timestamp
- Format: `ai_processed_YYYYMMDD_HHMMSS.csv`
- Includes all columns (original + added)

---

## 🎯 Best Practices

### 1. Test Before Full Processing

- Start with sample size (10-50 rows)
- Review results in preview
- Adjust prompt if needed
- Then process all rows

### 2. Iterative Workflow

- Process one task at a time (e.g., icebreakers first)
- Review results
- Delete bad columns if needed
- Run next task (e.g., email sequence)

### 3. Prompt Writing Tips

- **Be specific**: Tell OpenAI exactly what you want
- **Use JSON mode**: For structured output with multiple fields
- **Set context**: OpenAI sees ALL selected columns automatically
- **Test variations**: Edit and re-run to compare results

### 4. Cost Optimization

- Use gpt-4o-mini (10x cheaper than gpt-4o)
- Process only rows you need
- Lower parallel workers if hitting rate limits
- Test prompts on sample first

---

## 🛠️ Technical Details

### Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **AI**: OpenAI GPT-4o-mini / GPT-4o
- **Concurrency**: ThreadPoolExecutor (parallel processing)
- **State Management**: Streamlit session state

### Processing Flow

1. User selects columns → stored in session state
2. Snapshot created for thread safety
3. For each row:
   - Build data section with selected columns
   - Prepend to user prompt
   - Send to OpenAI API
4. Results parsed and added to DataFrame
5. Session state updated
6. UI reloaded with new data

### File Structure

```
ai_data_processor/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── .env               # OpenAI API key (not in repo)
└── results/           # Auto-created for future use
```

---

## 📝 Version History

### v1.0.0 (2025-01-20)

**Initial release**

- Column selector with checkboxes
- Auto-pass system (no placeholders)
- Editable prompt library
- Iterative processing
- Column manager
- Real-time cost tracking
- Export/import prompts
- n8n-style preview

---

## 📄 License

This tool is part of the Cold Outreach Automation Platform project.

---

## 🤝 Support

For issues or questions:

1. Check **Troubleshooting** section above
2. Review prompt preview to debug issues
3. Test with smaller sample size
4. Adjust OpenAI settings (model, temperature)

---

## 🚀 Next Steps

1. **Upload your CSV** and start processing
2. **Try preset prompts** to see examples
3. **Create custom prompts** for your use case
4. **Process iteratively** - add columns progressively
5. **Download results** when done

**Happy processing!** 🎉
