# Test Setup Guide

## Quick Start - Test PWA

Follow these steps to test the Avto-Net Scraper API with the test PWA:

### Step 1: Install Dependencies

```bash
# Install Python dependencies
pip3 install -r requirements/common.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Start the API Server

Open a terminal and run:

```bash
python3 api_server.py
```

You should see:
```
Starting API server on 0.0.0.0:8000
Scrape interval: 60 seconds
Starting background scraping worker...
```

The API will be available at: **http://localhost:8000**

### Step 3: Start the PWA Server

Open a **new terminal** and run:

```bash
python3 serve_pwa.py
```

Or use Python's built-in server:

```bash
python3 -m http.server 8080 -d test-pwa
```

The PWA will be available at: **http://localhost:8080**

### Step 4: Open the PWA

1. Open your browser and go to: **http://localhost:8080**
2. You should see the registration form
3. The API status indicator should show "API Online" (green dot)

### Step 5: Register a User

Fill in the form:

1. **User ID**: Any unique identifier (e.g., "test_user_123")
2. **Pushover API Token**: Your Pushover API token
   - Get it from: https://pushover.net/apps/build
3. **Pushover User Key**: Your Pushover user key
   - Get it from: https://pushover.net/ (logged in)
4. **Search Filters**: 
   - Brand (optional): e.g., "Volkswagen"
   - Model (optional): e.g., "Golf"
   - Price range, year range, mileage, fuel type
5. Click **"Start Monitoring"**

### Step 6: Verify

After registration:
- ✅ You should see a success message
- ✅ The API health endpoint should show 1 active user
- ✅ Check your Pushover app - you'll receive notifications when new listings are found
- ✅ The backend scrapes automatically every 60 seconds

## Testing Without Pushover

If you don't have Pushover credentials yet, you can still test:

1. Use dummy values for Pushover fields (the registration will succeed)
2. Check the logs: `tail -f logs/scraper.log`
3. Check the database: `sqlite3 data/scraper.db "SELECT * FROM users;"`

## Troubleshooting

### API Server Won't Start

**Error: ModuleNotFoundError**
```bash
pip3 install -r requirements/common.txt
```

**Error: Playwright browser not found**
```bash
playwright install chromium
```

### PWA Can't Connect to API

1. Make sure API server is running on port 8000
2. Check browser console for CORS errors
3. Verify API health: `curl http://localhost:8000/api/health`

### No Notifications

1. Verify Pushover credentials are correct
2. Check user is active: `sqlite3 data/scraper.db "SELECT * FROM users WHERE user_id = 'your_user_id';"`
3. Check logs: `tail -f logs/scraper.log`
4. Wait for the next scraping cycle (60 seconds)

## Quick Test Commands

```bash
# Check API health
curl http://localhost:8000/api/health

# List all users
sqlite3 data/scraper.db "SELECT user_id, is_active FROM users;"

# View logs
tail -f logs/scraper.log

# Check database
sqlite3 data/scraper.db ".tables"
```

## Files Created

- `test-pwa/index.html` - The test PWA interface
- `test-pwa/manifest.json` - PWA manifest
- `serve_pwa.py` - Simple HTTP server for PWA
- `start_test.sh` - Startup script (optional)

## Next Steps

Once testing is complete:
1. Integrate the API into your actual PWA
2. Use the examples in `examples/pwa-simple-example.js`
3. Deploy the API server (see `docs/DEPLOYMENT.md`)

