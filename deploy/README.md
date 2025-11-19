# Homepage Scraper Deployment Guide

## Option 1: Streamlit Community Cloud (Recommended - FREE)

### Pros:
- ✅ Free
- ✅ Auto-deploy from GitHub (no setup needed!)
- ✅ HTTPS included
- ✅ 2-minute setup

### Cons:
- ❌ 1GB RAM limit
- ❌ May sleep when inactive
- ❌ Public access (or Streamlit auth)

### Setup Steps:

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: `LeonidSvb/cold-outreach`
   - Branch: `master`
   - Main file: `modules/scraping/homepage_email_scraper/app.py`
5. Click "Deploy"

**That's it!** Every `git push` will auto-update your app.

---

## Option 2: Hostinger VPS (If you need more resources)

### Pros:
- ✅ More RAM/CPU
- ✅ Never sleeps
- ✅ Full control
- ✅ Can add custom domain

### Cons:
- ❌ Costs ~$4-10/month
- ❌ Requires setup

### Setup Steps:

#### 1. Initial Setup (One-time)

SSH into your Hostinger VPS:
```bash
ssh user@your-hostinger-ip
```

Download and run setup script:
```bash
wget https://raw.githubusercontent.com/LeonidSvb/cold-outreach/master/deploy/hostinger_setup.sh
chmod +x hostinger_setup.sh
./hostinger_setup.sh
```

Edit nginx config to add your domain:
```bash
sudo nano /etc/nginx/sites-available/homepage-scraper
# Replace "your-domain.com" with actual domain
sudo systemctl restart nginx
```

#### 2. Auto-Deploy Setup

**Option A: GitHub Actions (Automatic on every push)**

Add secrets to GitHub repository:
1. Go to: https://github.com/LeonidSvb/cold-outreach/settings/secrets/actions
2. Add these secrets:
   - `HOSTINGER_HOST`: Your VPS IP address
   - `HOSTINGER_USER`: SSH username (usually `root` or your username)
   - `HOSTINGER_SSH_KEY`: Your SSH private key

Generate SSH key if you don't have one:
```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions"
# Copy public key to VPS
ssh-copy-id user@your-hostinger-ip
# Copy private key content to GitHub secret
cat ~/.ssh/id_ed25519
```

**Option B: Manual Update (when you want)**

SSH into VPS and run:
```bash
/opt/homepage-scraper/deploy/auto_update.sh
```

#### 3. Monitoring

Check app status:
```bash
sudo supervisorctl status homepage-scraper
```

View logs:
```bash
sudo tail -f /var/log/homepage-scraper.out.log
```

Restart app:
```bash
sudo supervisorctl restart homepage-scraper
```

---

## Comparison

| Feature | Streamlit Cloud | Hostinger VPS |
|---------|----------------|---------------|
| Cost | FREE | $4-10/month |
| Setup time | 2 minutes | 30 minutes |
| RAM | 1GB | 2-8GB+ |
| Auto-deploy | Built-in | GitHub Actions |
| Custom domain | Limited | Full control |
| Always on | No (sleeps) | Yes |
| Best for | Demos, testing | Production |

## Recommendation

1. **Start with Streamlit Cloud** - it's free and instant!
2. **Upgrade to Hostinger** if you hit limits or need more control

---

## Troubleshooting

### Streamlit Cloud

**App won't start:**
- Check `requirements.txt` has all dependencies
- Check logs in Streamlit dashboard

**App is slow:**
- You might be hitting RAM limits
- Consider Hostinger VPS

### Hostinger VPS

**App not accessible:**
```bash
# Check if app is running
sudo supervisorctl status homepage-scraper

# Check nginx
sudo systemctl status nginx

# Check firewall
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
```

**Auto-deploy not working:**
- Check GitHub Actions logs
- Verify SSH secrets are correct
- Test SSH connection manually

---

Need help? Check the main README or create an issue!
