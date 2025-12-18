# Test PWA for Avto-Net Scraper

This is a simple test Progressive Web App to test the Avto-Net Scraper API.

## Quick Start

### Option 1: Using the startup script (Recommended)

```bash
# From the project root
./start_test.sh
```

This will:
1. Check and install dependencies
2. Start the API server on http://localhost:8000
3. Provide instructions for accessing the PWA

### Option 2: Manual Start

1. **Start the API server:**
   ```bash
   python api_server.py
   ```

2. **Serve the PWA:**
   ```bash
   # Option A: Python HTTP server
   python3 -m http.server 8080 -d test-pwa
   # Then open http://localhost:8080 in your browser
   
   # Option B: Open directly (may have CORS issues)
   open test-pwa/index.html
   ```

## Usage

1. Open the PWA in your browser
2. Fill in the form:
   - **User ID**: Any unique identifier (e.g., "test_user_123")
   - **Pushover API Token**: Your Pushover API token
   - **Pushover User Key**: Your Pushover user key
   - **Search Filters**: Brand, model, price range, etc.
3. Click "Start Monitoring"
4. The system will automatically start scraping every 60 seconds
5. You'll receive Pushover notifications when new listings are found

## Features

- ✅ Real-time API status indicator
- ✅ Form validation
- ✅ Success/error messages
- ✅ Responsive design
- ✅ PWA manifest (can be installed as app)

## Notes

- Make sure the API server is running before using the PWA
- The API status indicator will show green when connected
- First scrape stores results but doesn't send notifications (unless enabled)
- Subsequent scrapes only notify for NEW listings

