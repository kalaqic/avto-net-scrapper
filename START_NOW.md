# 🚀 Start Now - Quick Instructions

## Step 1: Install Dependencies (if needed)

Open Terminal and run:

```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper
pip3 install fastapi uvicorn pydantic playwright
playwright install chromium
```

## Step 2: Start API Server

**Open Terminal 1** and run:

```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper
python3 api_server.py
```

**Keep this terminal open!** You should see:
```
Starting API server on 0.0.0.0:8000
Scrape interval: 60 seconds
Starting background scraping worker...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 3: Start PWA Server

**Open Terminal 2** (new terminal) and run:

```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper
python3 serve_pwa.py
```

**Keep this terminal open!** It will automatically open your browser to:
**http://localhost:8080**

## Step 4: Use the Form

1. **Open**: http://localhost:8080 (if browser didn't open automatically)

2. **Fill in**:
   - **User ID**: Your unique identifier (e.g., "my_user_123")
   - **Pushover API Token**: Your token from Pushover
   - **Pushover User Key**: Your user key from Pushover
   - **Filters**: Brand, model, price range, etc.

3. **Click**: "🚀 Start Monitoring"

4. **Done!** The system will:
   - ✅ Register your user
   - ✅ Start scraping every 60 seconds automatically
   - ✅ Send Pushover notifications for new listings

## ✅ Verify It's Working

### Check API:
```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "active_users": 1
}
```

### Check Logs:
```bash
tail -f logs/scraper.log
```

You'll see scraping activity every 60 seconds!

## 🎉 That's It!

No polling, no job IDs - just register and receive automatic notifications!

