#!/bin/bash
# Hostinger VPS Setup Script for Streamlit App

echo "=== Setting up Homepage Scraper on Hostinger VPS ==="

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.11+ and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx supervisor git

# 3. Create app directory
APP_DIR="/opt/homepage-scraper"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 4. Clone repository
cd $APP_DIR
git clone https://github.com/LeonidSvb/cold-outreach.git .

# 5. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 7. Create supervisor config for auto-restart
sudo tee /etc/supervisor/conf.d/homepage-scraper.conf > /dev/null <<EOF
[program:homepage-scraper]
directory=$APP_DIR
command=$APP_DIR/venv/bin/streamlit run modules/scraping/homepage_email_scraper/app.py --server.port 8501 --server.address 0.0.0.0
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/homepage-scraper.err.log
stdout_logfile=/var/log/homepage-scraper.out.log
EOF

# 8. Create nginx reverse proxy config
sudo tee /etc/nginx/sites-available/homepage-scraper > /dev/null <<'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 9. Enable nginx site
sudo ln -s /etc/nginx/sites-available/homepage-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 10. Start supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start homepage-scraper

echo "=== Setup complete! ==="
echo "App running on http://your-domain.com"
echo "Check status: sudo supervisorctl status homepage-scraper"
