# Deployment Guide - User-Based Persistent Scraping System

## Overview

This guide explains how to deploy the refactored Avto-Net Scraper API with persistent background scraping.

## Architecture

- **FastAPI Server**: Handles user registration and management
- **Background Worker**: Continuously scrapes for all users every 60 seconds
- **SQLite Database**: Stores users, filters, and results
- **Pushover Integration**: Sends notifications for new listings

## Prerequisites

- Python 3.8+
- pip
- Playwright browsers installed (`playwright install chromium`)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements/common.txt
playwright install chromium
```

### 2. Environment Variables

Create a `.env` file (optional, or use system environment variables):

```bash
# Database
DB_PATH=data/scraper.db

# Server
HOST=0.0.0.0
PORT=8000

# Scraping
SCRAPE_INTERVAL=60  # Seconds between scraping cycles

# CORS (comma-separated for multiple origins)
CORS_ORIGINS=https://your-pwa-domain.com,https://www.your-pwa-domain.com
```

### 3. Start the Server

```bash
python api_server.py
```

The server will:
- Initialize the database
- Start the background worker
- Begin scraping every 60 seconds for all registered users

## Database Structure

### Users Table
- `id`: Auto-increment primary key
- `user_id`: Unique user identifier
- `pushover_api_token`: Pushover API token
- `pushover_user_key`: Pushover user key
- `filters`: JSON string of search filters
- `is_active`: Boolean (1 = active, 0 = inactive)
- `notify_on_first_scrape`: Boolean
- `created_at`: Timestamp
- `updated_at`: Timestamp

### User Results Table
- `id`: Auto-increment primary key
- `user_id`: Foreign key to users
- `listing_hash`: SHA256 hash of listing
- `listing_data`: JSON string of listing data
- `created_at`: Timestamp

## API Endpoints

### POST `/api/users/register`
Register a new user with filters and Pushover credentials.

**Request:**
```json
{
  "user_id": "user_123",
  "pushover_api_token": "your_token",
  "pushover_user_key": "your_key",
  "filters": {
    "znamka": ["Volkswagen"],
    "model": "Golf",
    "cenaMin": 10000,
    "cenaMax": 25000
  },
  "notify_on_first_scrape": false
}
```

### GET `/api/users/{user_id}`
Get user information and current filters.

### PUT `/api/users/{user_id}`
Update user filters or Pushover credentials.

### DELETE `/api/users/{user_id}`
Deactivate a user (stops scraping for this user).

### GET `/api/health`
Health check endpoint.

## Deployment Options

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/avto-net-scraper.service`:

```ini
[Unit]
Description=Avto-Net Scraper API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/avto-net-scrapper
Environment="DB_PATH=/path/to/data/scraper.db"
Environment="SCRAPE_INTERVAL=60"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
ExecStart=/usr/bin/python3 /path/to/avto-net-scrapper/api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable avto-net-scraper
sudo systemctl start avto-net-scraper
sudo systemctl status avto-net-scraper
```

### Option 2: Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/common.txt .
RUN pip install --no-cache-dir -r common.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run server
CMD ["python", "api_server.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  scraper-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_PATH=/app/data/scraper.db
      - SCRAPE_INTERVAL=60
      - HOST=0.0.0.0
      - PORT=8000
      - CORS_ORIGINS=https://your-pwa-domain.com
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

Run:
```bash
docker-compose up -d
```

### Option 3: Shared Hosting (PythonAnywhere, Heroku, etc.)

1. **PythonAnywhere**:
   - Upload code via Git or files
   - Create a Web app
   - Set up a scheduled task for the worker (or use Always-On task)
   - Configure environment variables

2. **Heroku**:
   - Create `Procfile`:
     ```
     web: python api_server.py
     ```
   - Deploy via Git
   - Set environment variables in Heroku dashboard

3. **VPS (DigitalOcean, Linode, etc.)**:
   - Use systemd service (Option 1)
   - Or use PM2:
     ```bash
     npm install -g pm2
     pm2 start api_server.py --interpreter python3 --name avto-scraper
     pm2 save
     pm2 startup
     ```

## Monitoring

### Logs

Logs are written to:
- Console (stdout)
- `logs/scraper.log` (rotating, max 5MB, 3 backups)

### Health Check

Monitor the health endpoint:
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "active_users": 5
}
```

### Database Backup

Backup SQLite database:
```bash
# Simple copy
cp data/scraper.db data/scraper.db.backup

# Or use sqlite3
sqlite3 data/scraper.db ".backup 'data/scraper.db.backup'"
```

## Troubleshooting

### Worker Not Running

Check logs:
```bash
tail -f logs/scraper.log
```

Verify database:
```bash
sqlite3 data/scraper.db "SELECT COUNT(*) FROM users WHERE is_active = 1;"
```

### No Notifications

1. Verify Pushover credentials are correct
2. Check Pushover API token and user key
3. Verify user is active: `SELECT * FROM users WHERE user_id = 'your_user_id';`
4. Check logs for notification errors

### High Memory Usage

- Reduce scrape interval if needed
- Limit number of brands per user (enforced: max 2)
- Limit pages per brand (enforced: max 1)

### Database Locked Errors

SQLite can have locking issues with high concurrency. For production with many users, consider:
- Migrating to PostgreSQL
- Using connection pooling
- Implementing retry logic

## Production Checklist

- [ ] Set up proper CORS origins
- [ ] Use HTTPS (reverse proxy with nginx/Apache)
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring/alerting
- [ ] Use environment variables for secrets
- [ ] Set up process manager (systemd/PM2)
- [ ] Test Pushover notifications
- [ ] Verify scraping works correctly
- [ ] Set up firewall rules
- [ ] Document your deployment

## Scaling Considerations

For high-scale deployments:

1. **Database**: Migrate to PostgreSQL for better concurrency
2. **Worker**: Run multiple worker processes (one per user group)
3. **Caching**: Cache Pushover API responses
4. **Rate Limiting**: Implement rate limiting for API endpoints
5. **Queue System**: Use Celery/RQ for distributed task processing

## Security Notes

- Never commit `.env` files or database files
- Use strong user IDs (UUIDs recommended)
- Validate all user inputs
- Implement API authentication if exposing publicly
- Use HTTPS in production
- Regularly update dependencies

