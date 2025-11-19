#!/bin/bash
# Auto-update script for GitHub webhook or manual execution

APP_DIR="/opt/homepage-scraper"

echo "=== Updating Homepage Scraper from GitHub ==="

cd $APP_DIR

# Pull latest changes
git pull origin master

# Activate venv
source venv/bin/activate

# Install/update dependencies
pip install --upgrade -r requirements.txt

# Restart app
sudo supervisorctl restart homepage-scraper

echo "=== Update complete! ==="
echo "App restarted with latest code"
