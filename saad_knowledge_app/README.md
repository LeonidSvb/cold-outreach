# 🎯 Saad Knowledge Base - Interactive Q&A

Ask questions about Saad Belcaid's YouTube content and get answers with:
- ✅ **Direct quotes** from multiple videos
- ✅ **Saad's tone of voice** (no-BS, actionable)
- ✅ **Approximate timestamps** to jump directly to relevant parts
- ✅ **Grouped sources** showing all relevant quotes per video

Built from **125 YouTube videos** covering sales systems, automation, and AI freelancing.

---

## 🚀 Try It Live

👉 **[Launch App](https://your-app-name.streamlit.app)** (Deploy first!)

---

## 💡 Example Questions

- What are the best niches for sales systems agencies?
- How can I get my first client in 2 weeks?
- What cold email strategies does Saad use?
- How to price automation services?
- What's the connector business model?
- How did Saad build a $100K/month business?

---

## 📊 What's Inside

- **125 YouTube videos** transcribed and vectorized
- **855 text chunks** with semantic embeddings
- **Semantic search** using OpenAI embeddings
- **GPT-4o-mini** for generating answers in Saad's style

---

## 🛠️ Deploy to Streamlit Cloud (FREE)

### Prerequisites

1. **OpenAI API Key** - Get yours at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. **GitHub account**
3. **Streamlit Cloud account** (free) at [share.streamlit.io](https://share.streamlit.io)

### Step 1: Fork or Clone This Repo

```bash
git clone https://github.com/yourusername/saad-knowledge-base
cd saad-knowledge-base
```

### Step 2: Push to Your GitHub

```bash
git add .
git commit -m "Initial commit: Saad Knowledge Base"
git push origin main
```

### Step 3: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Connect your GitHub repository
4. Settings:
   - **Repository:** `yourusername/saad-knowledge-base`
   - **Branch:** `main`
   - **Main file path:** `saad_knowledge_app/app.py`
5. Click **"Deploy!"**

### Step 4: You're Live! 🎉

Your app will be available at: `https://your-app-name.streamlit.app`

**Note:** Users will need to provide their own OpenAI API key when using the app.

---

## 💻 Run Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install streamlit openai numpy
```

### 2. Run the App

```bash
streamlit run app.py
```

### 3. Open in Browser

Automatically opens at: `http://localhost:8501`

---

## 💰 Cost Breakdown

### One-Time Costs (Already Done)
- **Vectorization:** $0.02 (using `text-embedding-3-small`)

### Per-Question Costs
- **Embedding creation:** ~$0.00002
- **GPT-4o-mini answer:** ~$0.0003
- **Total per question:** ~$0.0003 (less than a penny!)

### Monthly Estimate
- **100 questions/day:** ~$9/month
- **500 questions/day:** ~$45/month

**Streamlit Cloud Hosting:** FREE on Community tier

---

## 🎨 Features

### 1. Multiple Quotes Per Video
Unlike basic RAG systems, this app groups all relevant quotes from the same video together, giving you comprehensive context.

```
Video 1: "Best Niches for 2025" (3 relevant quotes)
├─ Quote 1 (~2:30): "Recruiting is one of the best..."
├─ Quote 2 (~5:40): "SaaS companies need..."
└─ Quote 3 (~8:15): "Financial services have..."
```

### 2. Saad's Tone of Voice
Answers are generated in Saad's signature style:
- Direct and no-BS
- Specific numbers and examples
- Actionable steps
- Real stories from his experience

### 3. Approximate Timestamps
Each quote includes an estimated timestamp linking directly to the YouTube video at that point.

### 4. User's Own API Key
Privacy-first: users provide their own OpenAI API key (stored only in browser session).

---

## 📂 Project Structure

```
saad_knowledge_app/
├── app.py                  # Main Streamlit application
├── saad_vectors.json       # Vector database (855 chunks, ~35MB)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🔧 Technical Details

### How It Works

1. **User asks a question**
   ↓
2. **Create embedding** of the question (OpenAI `text-embedding-3-small`)
   ↓
3. **Cosine similarity search** against 855 pre-computed vectors
   ↓
4. **Group top-K results by video** (default: 12 chunks)
   ↓
5. **GPT-4o-mini generates answer** in Saad's tone with direct quotes
   ↓
6. **Display answer + sources** with timestamps

### Vector Database Schema

```json
{
  "metadata": {
    "total_videos": 125,
    "total_chunks": 855,
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 800
  },
  "vectors": [
    {
      "video_title": "How I Built $100K/Mo...",
      "video_url": "https://youtube.com/...",
      "chunk_index": 0,
      "text": "Transcript text...",
      "embedding": [1536 floats]
    }
  ]
}
```

---

## 🛡️ Privacy & Security

- **API Keys:** Stored only in browser session (not saved to disk)
- **Questions:** Not logged or stored anywhere
- **Data:** All processing happens client-side or via OpenAI API

---

## 📈 Roadmap

Potential improvements:

- [ ] Add filters (by date, topic, video duration)
- [ ] Export answers to PDF/Markdown
- [ ] Trending questions analytics
- [ ] Most cited videos dashboard
- [ ] Exact timestamps (requires video duration metadata)
- [ ] Multi-language support
- [ ] Custom tone of voice (user can choose style)

---

## 🐛 Troubleshooting

### "Vector database not found"
**Solution:** Ensure `saad_vectors.json` is in the same folder as `app.py`

### "Invalid API key"
**Solution:**
- Check your key starts with `sk-`
- Verify it's active at platform.openai.com
- Make sure you have credits

### App is slow
**Solution:**
- Reduce "Number of sources" in settings (5-8 is faster)
- Use a faster OpenAI model (already using the fastest: gpt-4o-mini)

### Timestamps seem off
**Solution:** Timestamps are approximate estimates. Click the link and scan ±1 minute for the exact quote.

---

## 🙏 Credits

- **Content:** All credit to [Saad Belcaid](https://www.youtube.com/@SaadBelcaid) for his amazing YouTube videos
- **Tech Stack:** OpenAI, Streamlit, NumPy
- **Built by:** [Your Name]

---

## 📝 License

This project is for educational purposes. All video content belongs to Saad Belcaid.

---

## 🔗 Links

- **Saad's YouTube:** [@SaadBelcaid](https://www.youtube.com/@SaadBelcaid)
- **Saad's Community:** [SSSMasters](https://www.skool.com/ssmasters)
- **OpenAI Platform:** [platform.openai.com](https://platform.openai.com)
- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)

---

**Made with ❤️ for the sales systems community**
