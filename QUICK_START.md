# 🚀 Quick Start - Test PWA

I've created a complete test PWA website for you! Here's how to get everything running:

## 📋 What Was Created

1. **Test PWA** (`test-pwa/index.html`) - Beautiful form to register users
2. **PWA Server** (`serve_pwa.py`) - Simple HTTP server for the PWA
3. **Startup Script** (`start_test.sh`) - Automated startup (optional)

## 🎯 Step-by-Step Setup

### 1. Install Dependencies

```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper

# Install Python packages
pip3 install -r requirements/common.txt

# Install Playwright browser
playwright install chromium
```

**Note**: If you get permission errors, use:
```bash
pip3 install --user -r requirements/common.txt
```

### 2. Start the API Server

**Terminal 1:**
```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper
python3 api_server.py
```

You should see:
```
Starting API server on 0.0.0.0:8000
Scrape interval: 60 seconds
Starting background scraping worker...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Keep this terminal open!**

### 3. Start the PWA Server

**Terminal 2** (new terminal):
```bash
cd /Users/nodi/github-avtonetscraper/avto-net-scrapper
python3 serve_pwa.py
```

You should see:
```
🌐 PWA Server Started!
📱 Open your browser and go to: http://localhost:8080
```

✅ **Keep this terminal open too!**

### 4. Open the PWA

Open your browser and go to: **http://localhost:8080**

You should see:
- 🎨 Beautiful gradient background
- 📝 Registration form
- 🟢 Green API status indicator (if API is running)

## 📝 How to Use the Test PWA

### Fill in the Form:

1. **User ID**: 
   - Any unique identifier
   - Example: `test_user_123` or `your_email@example.com`

2. **Pushover API Token**:
   - Get from: https://pushover.net/apps/build
   - Create an app and copy the API token

3. **Pushover User Key**:
   - Get from: https://pushover.net/
   - Log in and copy your user key

4. **Search Filters**:
   - **Brand**: e.g., "Volkswagen" (or leave empty for all)
   - **Model**: e.g., "Golf" (or leave empty for all)
   - **Price Range**: Min and Max in EUR
   - **Year Range**: Min and Max year
   - **Max Mileage**: Maximum kilometers
   - **Fuel Type**: All, Petrol, Diesel, or Electric

5. **Notify on First Scrape**: 
   - Check if you want notifications on the first scrape
   - Default: unchecked (only new listings trigger notifications)

6. **Click "Start Monitoring"**

### What Happens Next:

✅ **Immediate**: Success message appears  
✅ **Background**: API starts scraping every 60 seconds  
✅ **Notifications**: You'll receive Pushover notifications for new listings  
✅ **No Polling**: Everything is automatic!

## 🧪 Testing Without Pushover

If you don't have Pushover credentials yet:

1. Use dummy values: `test_token` and `test_key`
2. Registration will succeed
3. Check the logs: `tail -f logs/scraper.log`
4. Check the database: `sqlite3 data/scraper.db "SELECT * FROM users;"`

## 🔍 Verify Everything Works

### Check API Status:
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

### Check Database:
```bash
sqlite3 data/scraper.db "SELECT user_id, is_active FROM users;"
```

## 🎨 Features of the Test PWA

- ✅ **Real-time API status** - Shows if API is online/offline
- ✅ **Form validation** - Ensures all required fields are filled
- ✅ **Success/Error messages** - Clear feedback
- ✅ **Responsive design** - Works on mobile and desktop
- ✅ **Beautiful UI** - Modern gradient design
- ✅ **Auto-refresh** - API status updates every 10 seconds

## 🐛 Troubleshooting

### API Server Won't Start

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
pip3 install fastapi uvicorn pydantic playwright
playwright install chromium
```

### PWA Shows "API Offline"

**Problem**: Red status indicator

**Solutions**:
1. Make sure API server is running (Terminal 1)
2. Check API: `curl http://localhost:8000/api/health`
3. Check browser console for errors (F12)

### Port Already in Use

**Problem**: `Address already in use`

**Solution**: 
- Change port in `api_server.py` (line 69): `port = int(os.getenv("PORT", "8001"))`
- Or kill the process: `lsof -ti:8000 | xargs kill`

### CORS Errors

**Problem**: Browser console shows CORS errors

**Solution**: 
- Use the PWA server (`serve_pwa.py`) instead of opening HTML directly
- Or update CORS in `src/api/main.py`

## 📱 Alternative: Open HTML Directly

If you prefer to open the HTML file directly:

```bash
open test-pwa/index.html
```

**Note**: This may have CORS issues. The HTTP server method is recommended.

## 🎉 You're All Set!

Once both servers are running:
1. ✅ API server on http://localhost:8000
2. ✅ PWA server on http://localhost:8080
3. ✅ Open http://localhost:8080 in your browser
4. ✅ Fill in the form and start monitoring!

The system will automatically:
- Scrape every 60 seconds
- Compare results
- Send Pushover notifications for new listings
- Store results in the database

**No polling, no job IDs, just automatic monitoring!** 🚀

