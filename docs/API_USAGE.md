# Avto-Net Scraper API Documentation

## Overview

The Avto-Net Scraper API provides a RESTful interface to scrape car listings from avto.net with dynamic filters. The API uses an asynchronous job-based approach where you submit a scrape request and poll for results.

## Starting the API Server

```bash
# Install dependencies
pip install -r requirements/common.txt

# Start the API server
python api_server.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Root Endpoint

**GET** `/`

Returns API information and available endpoints.

**Response:**
```json
{
  "message": "Avto-Net Scraper API",
  "version": "1.0.0",
  "endpoints": {
    "POST /api/scrape": "Start a new scrape job with filters",
    "GET /api/scrape/{job_id}": "Get scrape job status",
    "GET /api/scrape/{job_id}/results": "Get scrape results"
  }
}
```

### 2. Start Scrape Job

**POST** `/api/scrape`

Starts a new scrape job with the provided filters. Returns immediately with a job ID.

**Request Body:**
```json
{
  "znamka": ["Volkswagen"],
  "model": "Golf",
  "cenaMin": 10000,
  "cenaMax": 25000,
  "letnikMin": 2015,
  "letnikMax": 2023,
  "kmMin": 0,
  "kmMax": 100000,
  "bencin": 201
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scrape job started. Use the job_id to check status and retrieve results.",
  "created_at": "2025-01-20T10:30:00"
}
```

**Filter Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `znamka` | `string[]` | `[""]` | Brand(s) - empty string for all brands |
| `model` | `string` | `""` | Model name - empty string for all models |
| `cenaMin` | `int` | `0` | Minimum price in EUR |
| `cenaMax` | `int` | `100000` | Maximum price in EUR |
| `letnikMin` | `int` | `2000` | Minimum registration year |
| `letnikMax` | `int` | `2090` | Maximum registration year |
| `kmMin` | `int` | `0` | Minimum mileage |
| `kmMax` | `int` | `300000` | Maximum mileage |
| `kwMin` | `int` | `0` | Minimum engine power (kW) |
| `kwMax` | `int` | `999` | Maximum engine power (kW) |
| `ccmMin` | `int` | `0` | Minimum engine displacement (ccm) |
| `ccmMax` | `int` | `99999` | Maximum engine displacement (ccm) |
| `bencin` | `int` | `0` | Fuel type: 0=all, 201=petrol, 202=diesel, 207=electric |
| `EQ1-EQ10` | `int` | Various | Equipment flags (see search_parameters.md) |

**Limitations:**
- Maximum 2 brands per request
- Maximum 1 page per brand

### 3. Get Job Status

**GET** `/api/scrape/{job_id}`

Returns the current status of a scrape job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-01-20T10:30:00",
  "completed_at": "2025-01-20T10:32:15",
  "total_listings": 42,
  "error": null
}
```

**Status Values:**
- `pending`: Job is queued but not started
- `running`: Job is currently scraping
- `completed`: Job finished successfully
- `failed`: Job encountered an error

### 4. Get Scrape Results

**GET** `/api/scrape/{job_id}/results`

Returns the car listings found during the scrape. Only available when job status is `completed`.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "total_listings": 2,
  "listings": [
    {
      "HASH": "abc123...",
      "URL": "https://www.avto.net/Ads/details.asp?id=12345",
      "Cena": "15000",
      "Naziv": "Volkswagen Golf 2.0 TDI",
      "1.registracija": "2018",
      "Prevoženih": "50000",
      "Menjalnik": "Avtomatski",
      "Motor": "2.0 TDI, 110kW",
      "lastnikov": "1"
    },
    {
      "HASH": "def456...",
      "URL": "https://www.avto.net/Ads/details.asp?id=67890",
      "Cena": "18000",
      "Naziv": "Volkswagen Golf 1.4 TSI",
      "1.registracija": "2019",
      "Prevoženih": "40000",
      "Menjalnik": "Ročni",
      "Motor": "1.4 TSI, 110kW",
      "lastnikov": "2"
    }
  ],
  "created_at": "2025-01-20T10:30:00",
  "completed_at": "2025-01-20T10:32:15"
}
```

**Error Responses:**

- **404**: Job not found
- **202**: Job still running (not completed yet)
- **500**: Job failed

### 5. Health Check

**GET** `/api/health`

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-20T10:30:00"
}
```

## Usage Example (JavaScript/PWA)

```javascript
// Start a scrape job
async function startScrape(filters) {
  const response = await fetch('http://localhost:8000/api/scrape', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(filters)
  });
  
  const job = await response.json();
  return job.job_id;
}

// Check job status
async function checkStatus(jobId) {
  const response = await fetch(`http://localhost:8000/api/scrape/${jobId}`);
  return await response.json();
}

// Get results
async function getResults(jobId) {
  const response = await fetch(`http://localhost:8000/api/scrape/${jobId}/results`);
  if (response.status === 202) {
    throw new Error('Job still running');
  }
  return await response.json();
}

// Complete workflow
async function scrapeCars(filters) {
  // Start job
  const jobId = await startScrape({
    znamka: ["Volkswagen"],
    model: "Golf",
    cenaMin: 10000,
    cenaMax: 25000,
    letnikMin: 2015,
    letnikMax: 2023,
    kmMax: 100000,
    bencin: 201
  });
  
  console.log(`Job started: ${jobId}`);
  
  // Poll for completion
  let status;
  do {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
    status = await checkStatus(jobId);
    console.log(`Status: ${status.status}`);
  } while (status.status === 'pending' || status.status === 'running');
  
  if (status.status === 'completed') {
    // Get results
    const results = await getResults(jobId);
    console.log(`Found ${results.total_listings} listings`);
    return results.listings;
  } else {
    throw new Error(`Job failed: ${status.error}`);
  }
}

// Usage
scrapeCars({})
  .then(listings => {
    console.log('Listings:', listings);
  })
  .catch(error => {
    console.error('Error:', error);
  });
```

## React Example

```jsx
import { useState } from 'react';

function CarScraper() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);

  const startScrape = async (filters) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
      });
      const job = await response.json();
      setJobId(job.job_id);
      pollStatus(job.job_id);
    } catch (error) {
      console.error('Failed to start scrape:', error);
      setLoading(false);
    }
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/scrape/${id}`);
        const statusData = await response.json();
        setStatus(statusData);

        if (statusData.status === 'completed') {
          clearInterval(interval);
          fetchResults(id);
        } else if (statusData.status === 'failed') {
          clearInterval(interval);
          setLoading(false);
          alert(`Scrape failed: ${statusData.error}`);
        }
      } catch (error) {
        clearInterval(interval);
        console.error('Failed to check status:', error);
        setLoading(false);
      }
    }, 2000);
  };

  const fetchResults = async (id) => {
    try {
      const response = await fetch(`http://localhost:8000/api/scrape/${id}/results`);
      const results = await response.json();
      setListings(results.listings);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch results:', error);
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={() => startScrape({
          znamka: ["Volkswagen"],
          model: "Golf",
          cenaMin: 10000,
          cenaMax: 25000
        })}
        disabled={loading}
      >
        {loading ? 'Scraping...' : 'Start Scrape'}
      </button>

      {status && (
        <div>
          <p>Status: {status.status}</p>
          {status.total_listings !== null && (
            <p>Found: {status.total_listings} listings</p>
          )}
        </div>
      )}

      {listings.length > 0 && (
        <div>
          <h2>Results ({listings.length})</h2>
          {listings.map((listing, index) => (
            <div key={listing.HASH}>
              <h3>{listing.Naziv}</h3>
              <p>Price: {listing.Cena} €</p>
              <p>Year: {listing['1.registracija']}</p>
              <p>Mileage: {listing.Prevoženih}</p>
              <a href={listing.URL} target="_blank" rel="noopener noreferrer">
                View Listing
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default CarScraper;
```

## CORS Configuration

The API includes CORS middleware configured to allow requests from any origin. For production, update the `allow_origins` in `src/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-pwa-domain.com"],  # Your PWA domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **202**: Accepted (job started or still running)
- **404**: Resource not found
- **500**: Internal server error

Error responses include a JSON body with error details:

```json
{
  "detail": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

## Rate Limiting

Currently, there are no built-in rate limits. However, the scraper itself has safety limits:
- Maximum 2 brands per request
- Maximum 1 page per brand
- Minimum 2-minute intervals between scrapes (if using scheduler)

Consider implementing rate limiting for production use.

## Notes

- Jobs are stored in memory and will be lost on server restart
- For production, consider persisting jobs to a database
- Scraping may take 30 seconds to 2 minutes depending on the number of brands/pages
- The API uses background tasks, so jobs continue even if the client disconnects

