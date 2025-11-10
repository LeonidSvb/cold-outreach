# Universal Website Scraper - Streamlit UI

Interactive web interface for the Universal Website Scraper.

## Features

- CSV upload with URL validation
- Flexible scraping configuration (quick/standard/full/custom modes)
- Real-time progress tracking
- Results preview and download
- Time estimation calculator
- Past results browser

## Local Development

### Run locally:

```bash
streamlit run modules/scraping/ui/streamlit_app.py
```

### Access:
Browser will open automatically at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Community Cloud (Recommended - FREE)

**Best for:** Simple deployment, free hosting, automatic updates from GitHub

**Steps:**

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select:
   - Repository: `your-repo`
   - Branch: `main` or `master`
   - Main file path: `modules/scraping/ui/streamlit_app.py`
6. Click "Deploy"

**Free tier limits:**
- Unlimited public apps
- 1 GB RAM per app
- Community support

**Pros:**
- Completely free
- Zero configuration
- Auto-deploys on git push
- Perfect for Streamlit apps

**Cons:**
- Apps go to sleep after inactivity
- Public by default (can request private with paid plan)

---

### Option 2: Vercel (NOT recommended for this app)

**Why not Vercel:**
- Vercel is optimized for Next.js/frontend apps
- Streamlit requires Python runtime (not ideal on Vercel)
- More complex configuration needed
- Better alternatives exist for Python apps

---

### Option 3: Railway.app (Good alternative - FREE tier)

**Best for:** More control, private apps, better performance

**Steps:**

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Login and deploy:
   ```bash
   railway login
   railway init
   railway up
   ```

3. Set start command in Railway dashboard:
   ```
   streamlit run modules/scraping/ui/streamlit_app.py --server.port $PORT
   ```

**Free tier:**
- $5 credit/month
- 500 hours execution time
- Private apps by default

---

### Option 4: Render.com (FREE)

**Steps:**

1. Create `render.yaml`:
   ```yaml
   services:
     - type: web
       name: website-scraper
       env: python
       buildCommand: pip install -r modules/scraping/ui/requirements.txt
       startCommand: streamlit run modules/scraping/ui/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
   ```

2. Connect GitHub repo at [render.com](https://render.com)
3. Select "New" -> "Blueprint"
4. Deploy

**Free tier:**
- Unlimited apps
- 750 hours/month
- Sleeps after inactivity

---

### Option 5: Hugging Face Spaces (FREE)

**Best for:** ML/AI apps, great community

**Steps:**

1. Create Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Select "Streamlit" SDK
3. Push code:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
   git push hf main
   ```

**Pros:**
- Free forever
- Good for data/AI apps
- Community-focused

---

## Recommended: Streamlit Community Cloud

**For this project, use Streamlit Community Cloud because:**

1. **Zero configuration** - just connect GitHub
2. **Completely free** - no credit card required
3. **Auto-deploy** - push to GitHub = instant update
4. **Built for Streamlit** - optimized performance
5. **Easy sharing** - get public URL instantly

## Configuration Files Needed for Deployment

### For Streamlit Cloud:

No extra files needed! Just:
- `streamlit_app.py` (main file)
- `requirements.txt` (dependencies)

### For Railway/Render:

Add `Procfile`:
```
web: streamlit run modules/scraping/ui/streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

## Environment Variables

If using API keys or secrets:

1. **Streamlit Cloud:** Add in app settings -> Secrets
2. **Railway/Render:** Add in dashboard -> Environment variables

Format in Streamlit secrets (`.streamlit/secrets.toml`):
```toml
OPENAI_API_KEY = "sk-..."
GOOGLE_MAPS_KEY = "AIza..."
```

## Performance Notes

- **Local:** Best performance, no limits
- **Streamlit Cloud:** Good for <1000 URLs per job
- **Railway/Render:** Better for larger jobs (more RAM)

## Cost Comparison

| Platform | Free Tier | Best For |
|----------|-----------|----------|
| Streamlit Cloud | Unlimited apps | Public demos, portfolios |
| Railway.app | $5/month | Private apps, more control |
| Render.com | 750h/month | Production apps |
| Vercel | ❌ Not suitable | Frontend apps only |
| Hugging Face | Unlimited | ML/AI community |

## Recommendation

**Start with Streamlit Community Cloud** - it's the easiest and most suitable for this type of app. If you need:
- Private hosting → Railway.app
- More performance → Railway.app or Render.com
- Community features → Hugging Face Spaces
