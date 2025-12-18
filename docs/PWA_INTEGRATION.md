# PWA Integration Guide

This guide shows you how to integrate the Avto-Net Scraper API into your Progressive Web App.

## Quick Start

### 1. API Server Setup

Make sure your API server is running and accessible:

```bash
# On your server/development machine
python api_server.py
```

The API will be available at `http://localhost:8000` (or your server's IP/domain).

### 2. Update CORS Settings (Production)

For production, update CORS in `src/api/main.py` to allow only your PWA domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-pwa-domain.com", "https://www.your-pwa-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Basic Integration

### Vanilla JavaScript Example

```javascript
// api.js - API client for your PWA

const API_BASE_URL = 'http://localhost:8000'; // Change to your API URL

class AvtoNetScraperAPI {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Start a scrape job
   * @param {Object} filters - Search filters
   * @returns {Promise<Object>} Job information with job_id
   */
  async startScrape(filters) {
    try {
      const response = await fetch(`${this.baseUrl}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start scrape');
      }

      return await response.json();
    } catch (error) {
      console.error('Error starting scrape:', error);
      throw error;
    }
  }

  /**
   * Check job status
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Job status
   */
  async checkStatus(jobId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/scrape/${jobId}`);
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to check status');
      }

      return await response.json();
    } catch (error) {
      console.error('Error checking status:', error);
      throw error;
    }
  }

  /**
   * Get scrape results
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} Scrape results with listings
   */
  async getResults(jobId) {
    try {
      const response = await fetch(`${this.baseUrl}/api/scrape/${jobId}/results`);
      
      if (response.status === 202) {
        throw new Error('Job still running');
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to get results');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting results:', error);
      throw error;
    }
  }

  /**
   * Complete workflow: start scrape and wait for results
   * @param {Object} filters - Search filters
   * @param {Object} options - Options for polling
   * @param {number} options.pollInterval - Polling interval in ms (default: 2000)
   * @param {number} options.maxAttempts - Maximum polling attempts (default: 60)
   * @param {Function} options.onStatusUpdate - Callback for status updates
   * @returns {Promise<Object>} Final results
   */
  async scrapeAndWait(filters, options = {}) {
    const {
      pollInterval = 2000,
      maxAttempts = 60,
      onStatusUpdate = null,
    } = options;

    // Start the scrape
    const { job_id } = await this.startScrape(filters);
    console.log(`Scrape started: ${job_id}`);

    // Poll for completion
    let attempts = 0;
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, pollInterval));

      const status = await this.checkStatus(job_id);
      
      // Call status update callback if provided
      if (onStatusUpdate) {
        onStatusUpdate(status);
      }

      if (status.status === 'completed') {
        // Get results
        const results = await this.getResults(job_id);
        return results;
      } else if (status.status === 'failed') {
        throw new Error(`Scrape failed: ${status.error || 'Unknown error'}`);
      }

      attempts++;
    }

    throw new Error('Scrape timed out');
  }
}

// Export for use in your PWA
export default AvtoNetScraperAPI;
```

### Usage in Your PWA

```javascript
// app.js
import AvtoNetScraperAPI from './api.js';

const api = new AvtoNetScraperAPI('http://localhost:8000');

// Example: Search for cars
async function searchCars() {
  try {
    const results = await api.scrapeAndWait(
      {
        znamka: ["Volkswagen"],
        model: "Golf",
        cenaMin: 10000,
        cenaMax: 25000,
        letnikMin: 2015,
        letnikMax: 2023,
        kmMax: 100000,
        bencin: 201 // Petrol
      },
      {
        pollInterval: 2000, // Check every 2 seconds
        maxAttempts: 60, // Max 2 minutes
        onStatusUpdate: (status) => {
          console.log(`Status: ${status.status}, Found: ${status.total_listings || 0}`);
          // Update UI with status
          updateUI(status);
        }
      }
    );

    console.log(`Found ${results.total_listings} listings`);
    displayResults(results.listings);
  } catch (error) {
    console.error('Search failed:', error);
    showError(error.message);
  }
}

function updateUI(status) {
  const statusElement = document.getElementById('status');
  statusElement.textContent = `Status: ${status.status}`;
  
  if (status.total_listings !== null) {
    const countElement = document.getElementById('count');
    countElement.textContent = `Found: ${status.total_listings} listings`;
  }
}

function displayResults(listings) {
  const resultsContainer = document.getElementById('results');
  resultsContainer.innerHTML = listings.map(listing => `
    <div class="listing-card">
      <h3>${listing.Naziv || 'N/A'}</h3>
      <p class="price">${listing.Cena || 'N/A'} €</p>
      <p>Year: ${listing['1.registracija'] || 'N/A'}</p>
      <p>Mileage: ${listing.Prevoženih || 'N/A'}</p>
      <p>Transmission: ${listing.Menjalnik || 'N/A'}</p>
      <p>Engine: ${listing.Motor || 'N/A'}</p>
      ${listing.lastnikov ? `<p>Owners: ${listing.lastnikov}</p>` : ''}
      <a href="${listing.URL}" target="_blank" rel="noopener noreferrer">
        View on Avto.net
      </a>
    </div>
  `).join('');
}
```

## React Integration

### React Hook Example

```jsx
// useScraper.js
import { useState, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';

export function useScraper() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startScrape = useCallback(async (filters) => {
    setLoading(true);
    setError(null);
    setListings([]);
    
    try {
      // Start scrape
      const response = await fetch(`${API_BASE_URL}/api/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start scrape');
      }

      const job = await response.json();
      setJobId(job.job_id);
      setStatus({ ...job, total_listings: null });

      // Start polling
      pollStatus(job.job_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/scrape/${id}`);
        const statusData = await response.json();
        setStatus(statusData);

        if (statusData.status === 'completed') {
          clearInterval(interval);
          fetchResults(id);
        } else if (statusData.status === 'failed') {
          clearInterval(interval);
          setError(statusData.error || 'Scrape failed');
          setLoading(false);
        }
      } catch (err) {
        clearInterval(interval);
        setError(err.message);
        setLoading(false);
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(interval);
  }, []);

  const fetchResults = useCallback(async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/scrape/${id}/results`);
      
      if (response.status === 202) {
        // Still running, continue polling
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch results');
      }

      const results = await response.json();
      setListings(results.listings);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, []);

  return {
    startScrape,
    jobId,
    status,
    listings,
    loading,
    error,
  };
}
```

### React Component Example

```jsx
// CarScraper.jsx
import React, { useState } from 'react';
import { useScraper } from './useScraper';

function CarScraper() {
  const { startScrape, status, listings, loading, error } = useScraper();
  const [filters, setFilters] = useState({
    znamka: [''],
    model: '',
    cenaMin: 0,
    cenaMax: 100000,
    letnikMin: 2015,
    letnikMax: 2023,
    kmMax: 100000,
    bencin: 0,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    startScrape(filters);
  };

  return (
    <div className="car-scraper">
      <form onSubmit={handleSubmit}>
        <div>
          <label>Brand:</label>
          <input
            type="text"
            value={filters.znamka[0] || ''}
            onChange={(e) => setFilters({ ...filters, znamka: [e.target.value] })}
            placeholder="e.g., Volkswagen (empty for all)"
          />
        </div>

        <div>
          <label>Model:</label>
          <input
            type="text"
            value={filters.model}
            onChange={(e) => setFilters({ ...filters, model: e.target.value })}
            placeholder="e.g., Golf (empty for all)"
          />
        </div>

        <div>
          <label>Min Price:</label>
          <input
            type="number"
            value={filters.cenaMin}
            onChange={(e) => setFilters({ ...filters, cenaMin: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label>Max Price:</label>
          <input
            type="number"
            value={filters.cenaMax}
            onChange={(e) => setFilters({ ...filters, cenaMax: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label>Min Year:</label>
          <input
            type="number"
            value={filters.letnikMin}
            onChange={(e) => setFilters({ ...filters, letnikMin: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label>Max Year:</label>
          <input
            type="number"
            value={filters.letnikMax}
            onChange={(e) => setFilters({ ...filters, letnikMax: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label>Max Mileage:</label>
          <input
            type="number"
            value={filters.kmMax}
            onChange={(e) => setFilters({ ...filters, kmMax: parseInt(e.target.value) })}
          />
        </div>

        <div>
          <label>Fuel Type:</label>
          <select
            value={filters.bencin}
            onChange={(e) => setFilters({ ...filters, bencin: parseInt(e.target.value) })}
          >
            <option value={0}>All</option>
            <option value={201}>Petrol</option>
            <option value={202}>Diesel</option>
            <option value={207}>Electric</option>
          </select>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Scraping...' : 'Search Cars'}
        </button>
      </form>

      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}

      {status && (
        <div className="status">
          <p>Status: <strong>{status.status}</strong></p>
          {status.total_listings !== null && (
            <p>Found: <strong>{status.total_listings}</strong> listings</p>
          )}
        </div>
      )}

      {listings.length > 0 && (
        <div className="results">
          <h2>Results ({listings.length})</h2>
          <div className="listings-grid">
            {listings.map((listing) => (
              <div key={listing.HASH} className="listing-card">
                <h3>{listing.Naziv || 'N/A'}</h3>
                <p className="price">{listing.Cena || 'N/A'} €</p>
                <div className="details">
                  <p><strong>Year:</strong> {listing['1.registracija'] || 'N/A'}</p>
                  <p><strong>Mileage:</strong> {listing.Prevoženih || 'N/A'}</p>
                  <p><strong>Transmission:</strong> {listing.Menjalnik || 'N/A'}</p>
                  <p><strong>Engine:</strong> {listing.Motor || 'N/A'}</p>
                  {listing.lastnikov && (
                    <p><strong>Owners:</strong> {listing.lastnikov}</p>
                  )}
                </div>
                <a
                  href={listing.URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="view-listing"
                >
                  View on Avto.net →
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CarScraper;
```

## Vue.js Integration

```vue
<!-- CarScraper.vue -->
<template>
  <div class="car-scraper">
    <form @submit.prevent="handleSubmit">
      <div>
        <label>Brand:</label>
        <input v-model="filters.znamka[0]" placeholder="e.g., Volkswagen" />
      </div>
      <div>
        <label>Model:</label>
        <input v-model="filters.model" placeholder="e.g., Golf" />
      </div>
      <div>
        <label>Min Price:</label>
        <input type="number" v-model.number="filters.cenaMin" />
      </div>
      <div>
        <label>Max Price:</label>
        <input type="number" v-model.number="filters.cenaMax" />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'Scraping...' : 'Search Cars' }}
      </button>
    </form>

    <div v-if="error" class="error">{{ error }}</div>
    
    <div v-if="status">
      <p>Status: {{ status.status }}</p>
      <p v-if="status.total_listings !== null">
        Found: {{ status.total_listings }} listings
      </p>
    </div>

    <div v-if="listings.length > 0" class="results">
      <h2>Results ({{ listings.length }})</h2>
      <div v-for="listing in listings" :key="listing.HASH" class="listing-card">
        <h3>{{ listing.Naziv }}</h3>
        <p class="price">{{ listing.Cena }} €</p>
        <a :href="listing.URL" target="_blank">View Listing</a>
      </div>
    </div>
  </div>
</template>

<script>
const API_BASE_URL = 'http://localhost:8000';

export default {
  data() {
    return {
      filters: {
        znamka: [''],
        model: '',
        cenaMin: 0,
        cenaMax: 100000,
      },
      jobId: null,
      status: null,
      listings: [],
      loading: false,
      error: null,
      pollInterval: null,
    };
  },
  methods: {
    async handleSubmit() {
      this.loading = true;
      this.error = null;
      this.listings = [];

      try {
        const response = await fetch(`${API_BASE_URL}/api/scrape`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.filters),
        });

        const job = await response.json();
        this.jobId = job.job_id;
        this.status = job;
        this.startPolling(job.job_id);
      } catch (error) {
        this.error = error.message;
        this.loading = false;
      }
    },
    startPolling(jobId) {
      this.pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/api/scrape/${jobId}`);
          const statusData = await response.json();
          this.status = statusData;

          if (statusData.status === 'completed') {
            clearInterval(this.pollInterval);
            this.fetchResults(jobId);
          } else if (statusData.status === 'failed') {
            clearInterval(this.pollInterval);
            this.error = statusData.error || 'Scrape failed';
            this.loading = false;
          }
        } catch (error) {
          clearInterval(this.pollInterval);
          this.error = error.message;
          this.loading = false;
        }
      }, 2000);
    },
    async fetchResults(jobId) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/scrape/${jobId}/results`);
        const results = await response.json();
        this.listings = results.listings;
        this.loading = false;
      } catch (error) {
        this.error = error.message;
        this.loading = false;
      }
    },
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  },
};
</script>
```

## Service Worker Integration (Offline Support)

```javascript
// sw.js - Service Worker for caching API responses

const CACHE_NAME = 'avto-net-scraper-v1';
const API_BASE_URL = 'http://localhost:8000';

// Cache API responses
self.addEventListener('fetch', (event) => {
  // Only cache GET requests for job status/results
  if (event.request.method === 'GET' && event.request.url.includes('/api/scrape/')) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return fetch(event.request)
          .then((response) => {
            // Cache successful responses
            if (response.ok) {
              cache.put(event.request, response.clone());
            }
            return response;
          })
          .catch(() => {
            // Return cached version if network fails
            return cache.match(event.request);
          });
      })
    );
  }
});
```

## Error Handling Best Practices

```javascript
class ScraperError extends Error {
  constructor(message, code, details) {
    super(message);
    this.name = 'ScraperError';
    this.code = code;
    this.details = details;
  }
}

async function handleScrapeRequest(filters) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new ScraperError(
        errorData.detail || 'Request failed',
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ScraperError) {
      // Handle API errors
      console.error(`API Error [${error.code}]:`, error.message);
    } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
      // Handle network errors
      console.error('Network error: API server unreachable');
      throw new ScraperError('Cannot connect to API server', 'NETWORK_ERROR');
    } else {
      // Handle other errors
      console.error('Unexpected error:', error);
      throw error;
    }
  }
}
```

## Environment Configuration

```javascript
// config.js
const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000',
  },
  production: {
    API_BASE_URL: 'https://api.yourdomain.com',
  },
};

const env = process.env.NODE_ENV || 'development';
export const API_BASE_URL = config[env].API_BASE_URL;
```

## Testing the Integration

```javascript
// test-api.js
async function testAPI() {
  const api = new AvtoNetScraperAPI('http://localhost:8000');

  console.log('Testing API...');

  try {
    // Test 1: Start scrape
    console.log('1. Starting scrape...');
    const { job_id } = await api.startScrape({
      znamka: ["Volkswagen"],
      model: "Golf",
      cenaMin: 10000,
      cenaMax: 25000,
    });
    console.log('✓ Scrape started:', job_id);

    // Test 2: Check status
    console.log('2. Checking status...');
    const status = await api.checkStatus(job_id);
    console.log('✓ Status:', status.status);

    // Test 3: Wait for completion
    console.log('3. Waiting for results...');
    const results = await api.scrapeAndWait(
      { znamka: ["Volkswagen"], model: "Golf" },
      { onStatusUpdate: (s) => console.log('  Status update:', s.status) }
    );
    console.log('✓ Results received:', results.total_listings, 'listings');

    console.log('All tests passed!');
  } catch (error) {
    console.error('Test failed:', error);
  }
}

testAPI();
```

## Production Checklist

- [ ] Update CORS settings to allow only your PWA domain
- [ ] Use HTTPS for API server
- [ ] Add API authentication (API keys or OAuth)
- [ ] Implement rate limiting on client side
- [ ] Add error monitoring (Sentry, etc.)
- [ ] Cache results appropriately
- [ ] Handle network failures gracefully
- [ ] Add loading states and progress indicators
- [ ] Test on mobile devices
- [ ] Optimize polling intervals based on usage

## Common Issues

### CORS Errors
- Make sure CORS is configured in `src/api/main.py`
- Check that your PWA domain is in the `allow_origins` list

### Network Errors
- Verify API server is running
- Check firewall/network settings
- Ensure correct API_BASE_URL

### Job Timeout
- Increase `maxAttempts` in `scrapeAndWait()`
- Check API server logs for errors
- Verify filters are valid

### Empty Results
- Check if filters are too restrictive
- Verify selectors haven't changed (check `config/selectors.json`)
- Check API server logs for scraping errors

