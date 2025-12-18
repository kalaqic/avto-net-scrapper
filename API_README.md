# Avto-Net Scraper API

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements/common.txt
```

### 2. Start the API Server

```bash
python api_server.py
```

The API will be available at `http://localhost:8000`

### 3. Test the API

Open your browser and visit:
- `http://localhost:8000` - API information
- `http://localhost:8000/docs` - Interactive API documentation (Swagger UI)
- `http://localhost:8000/redoc` - Alternative API documentation

## API Endpoints

### Start a Scrape Job

```bash
curl -X POST "http://localhost:8000/api/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "znamka": ["Volkswagen"],
    "model": "Golf",
    "cenaMin": 10000,
    "cenaMax": 25000,
    "letnikMin": 2015,
    "letnikMax": 2023
  }'
```

### Check Job Status

```bash
curl "http://localhost:8000/api/scrape/{job_id}"
```

### Get Results

```bash
curl "http://localhost:8000/api/scrape/{job_id}/results"
```

## Usage from PWA

See `docs/API_USAGE.md` for detailed examples including JavaScript/React code.

## Configuration

The API uses the same configuration files as the CLI version:
- `config/selectors.json` - HTML selectors
- `config/scheduler_params.json` - Scheduler settings (not used in API mode)

Filter parameters are provided via the API request body, not from `config/params.json`.

## Differences from CLI Version

1. **Dynamic Filters**: Filters are provided via API request instead of config file
2. **Job-Based**: Uses async job system instead of continuous scheduling
3. **JSON Response**: Returns structured JSON instead of CSV files
4. **No Notifications**: Pushover notifications are not triggered (can be added if needed)
5. **No CSV Storage**: Results are stored in memory only (can be persisted if needed)

## Production Considerations

1. **Persistent Storage**: Implement database storage for jobs and results
2. **Rate Limiting**: Add rate limiting middleware
3. **Authentication**: Add API key or OAuth authentication
4. **CORS**: Restrict CORS to your PWA domain
5. **Error Monitoring**: Add error tracking (Sentry, etc.)
6. **Caching**: Consider caching results for repeated queries
7. **Queue System**: Use Celery or similar for better job management

## Troubleshooting

### Port Already in Use

Change the port in `api_server.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Playwright Browser Not Found

Install Playwright browsers:
```bash
playwright install chromium
```

### Import Errors

Make sure you're running from the project root directory:
```bash
cd /path/to/avto-net-scrapper
python api_server.py
```

