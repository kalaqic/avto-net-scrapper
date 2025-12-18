# Refactoring Guide - User-Based Persistent Scraping System

## Overview

The API has been completely refactored from a job-based polling system to a persistent, user-based scraping system with automatic background processing.

## Key Changes

### Before (Job-Based System)
- Frontend sends filters → receives job_id
- Frontend polls for status
- Frontend fetches results when complete
- One-time scraping per request

### After (Persistent System)
- Frontend sends filters + Pushover credentials → receives confirmation
- Backend continuously scrapes every 60 seconds
- Backend sends Pushover notifications automatically
- No polling required

## Architecture

### Components

1. **Database Layer** (`src/database/models.py`)
   - `Database`: SQLite database manager
   - `UserManager`: User CRUD operations
   - `ResultManager`: Result storage and comparison

2. **API Layer** (`src/api/main.py`)
   - User registration endpoint
   - User update endpoint
   - User deactivation endpoint
   - Health check endpoint

3. **Worker Layer** (`src/api/worker.py`)
   - `ScrapingWorker`: Background loop that processes all users
   - Runs every 60 seconds (configurable)
   - Isolated error handling per user

4. **Scraper Service** (`src/api/scraper_service.py`)
   - Wraps existing scraper with user-specific filters
   - Returns listings as dictionaries

5. **Notification Service** (`src/api/notifications.py`)
   - Sends Pushover notifications per user
   - Uses user's own Pushover credentials

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    pushover_api_token TEXT NOT NULL,
    pushover_user_key TEXT NOT NULL,
    filters TEXT NOT NULL,  -- JSON string
    is_active INTEGER DEFAULT 1,
    notify_on_first_scrape INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### User Results Table
```sql
CREATE TABLE user_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    listing_hash TEXT NOT NULL,
    listing_data TEXT NOT NULL,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, listing_hash)
);
```

## Workflow

### 1. User Registration
```
Frontend → POST /api/users/register
  ↓
Backend stores user + filters
  ↓
Returns success confirmation
  ↓
User is automatically included in scraping loop
```

### 2. Background Scraping Loop
```
Every 60 seconds:
  ↓
For each active user:
  ↓
  Fetch user filters
  ↓
  Scrape Avto.net
  ↓
  Compare with stored results
  ↓
  If new listings found:
    ↓
    Send Pushover notifications
    ↓
  Save updated results
```

### 3. Result Comparison
```
New listings from scrape
  ↓
Compare HASH with stored results
  ↓
Filter out duplicates
  ↓
Return only new listings
  ↓
Send notifications for new listings
```

## API Endpoints

### POST `/api/users/register`
Register a new user.

**Request:**
```json
{
  "user_id": "user_123",
  "pushover_api_token": "token",
  "pushover_user_key": "key",
  "filters": {
    "znamka": ["Volkswagen"],
    "model": "Golf",
    "cenaMin": 10000,
    "cenaMax": 25000
  },
  "notify_on_first_scrape": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "User user_123 registered successfully. Scraping will start automatically."
}
```

### GET `/api/users/{user_id}`
Get user information.

### PUT `/api/users/{user_id}`
Update user filters or Pushover credentials.

### DELETE `/api/users/{user_id}`
Deactivate user (stops scraping).

## Frontend Integration

### Simple Registration
```javascript
const response = await fetch('http://localhost:8000/api/users/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'user_123',
    pushover_api_token: 'your_token',
    pushover_user_key: 'your_key',
    filters: {
      znamka: ["Volkswagen"],
      model: "Golf",
      cenaMin: 10000,
      cenaMax: 25000
    }
  })
});

const result = await response.json();
console.log(result.message); // "User registered successfully..."
```

**That's it!** No polling, no job IDs, no status checks. The backend handles everything.

## Configuration

### Environment Variables

- `DB_PATH`: Database file path (default: `data/scraper.db`)
- `SCRAPE_INTERVAL`: Seconds between scraping cycles (default: `60`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `CORS_ORIGINS`: Comma-separated allowed origins (default: `*`)

### Example `.env` file:
```
DB_PATH=data/scraper.db
SCRAPE_INTERVAL=60
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://your-pwa.com,https://www.your-pwa.com
```

## Error Handling

### User Isolation
- Each user's scraping is isolated
- Failure for one user doesn't affect others
- Errors are logged and the loop continues

### Error Types
1. **Scraping Errors**: Logged, user skipped, continue with next user
2. **Notification Errors**: Logged, continue processing
3. **Database Errors**: Logged, user skipped, continue with next user

## Migration from Old System

If you have existing code using the old job-based system:

1. **Remove polling logic** from frontend
2. **Replace job registration** with user registration
3. **Remove status checking** endpoints
4. **Remove result fetching** endpoints
5. **Add Pushover credentials** to registration

## Testing

### Test User Registration
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "pushover_api_token": "test_token",
    "pushover_user_key": "test_key",
    "filters": {
      "znamka": ["Volkswagen"],
      "model": "Golf"
    }
  }'
```

### Check Health
```bash
curl http://localhost:8000/api/health
```

### View Logs
```bash
tail -f logs/scraper.log
```

## Performance Considerations

- **Scrape Interval**: Default 60 seconds. Adjust based on:
  - Number of users
  - Server resources
  - Avto.net rate limits

- **Database**: SQLite is fine for small-medium deployments. For large scale:
  - Consider PostgreSQL
  - Implement connection pooling
  - Add database indexes

- **Memory**: Each user's results are stored in memory during processing. For many users:
  - Process users in batches
  - Clear results after processing
  - Monitor memory usage

## Security

- User IDs should be unique and not guessable (use UUIDs)
- Pushover credentials are stored in database (encrypt if needed)
- Validate all user inputs
- Implement rate limiting for API endpoints
- Use HTTPS in production

## Monitoring

### Logs
- All operations logged to `logs/scraper.log`
- Rotating logs (5MB max, 3 backups)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Health Endpoint
- Returns database status
- Returns active user count
- Use for monitoring/alerting

### Database Queries
```sql
-- Count active users
SELECT COUNT(*) FROM users WHERE is_active = 1;

-- View user filters
SELECT user_id, filters FROM users WHERE is_active = 1;

-- Check results per user
SELECT user_id, COUNT(*) as listing_count 
FROM user_results 
GROUP BY user_id;
```

## Troubleshooting

### Worker Not Running
- Check logs: `tail -f logs/scraper.log`
- Verify database exists: `ls -la data/scraper.db`
- Check for errors in startup logs

### No Notifications
- Verify Pushover credentials are correct
- Check user is active: `SELECT * FROM users WHERE user_id = 'your_user';`
- Check logs for notification errors
- Test Pushover API directly

### Database Locked
- SQLite can lock with high concurrency
- Consider PostgreSQL for production
- Implement retry logic
- Reduce scrape frequency

## Future Enhancements

Possible improvements:
- WebSocket notifications instead of Pushover
- Multiple notification channels (Email, SMS, etc.)
- User dashboard to view stored results
- Scheduled scraping (different intervals per user)
- Result caching and deduplication
- Analytics and statistics

