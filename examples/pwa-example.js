/**
 * Ready-to-use API client for PWA integration
 * Copy this file into your PWA project
 */

const API_BASE_URL = 'http://localhost:8000'; // Change to your API server URL

class AvtoNetScraperAPI {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Start a scrape job
   */
  async startScrape(filters) {
    const response = await fetch(`${this.baseUrl}/api/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(filters),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start scrape');
    }

    return await response.json();
  }

  /**
   * Check job status
   */
  async checkStatus(jobId) {
    const response = await fetch(`${this.baseUrl}/api/scrape/${jobId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to check status');
    }

    return await response.json();
  }

  /**
   * Get scrape results
   */
  async getResults(jobId) {
    const response = await fetch(`${this.baseUrl}/api/scrape/${jobId}/results`);
    
    if (response.status === 202) {
      throw new Error('Job still running');
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get results');
    }

    return await response.json();
  }

  /**
   * Complete workflow: start scrape and wait for results
   */
  async scrapeAndWait(filters, options = {}) {
    const {
      pollInterval = 2000,
      maxAttempts = 60,
      onStatusUpdate = null,
    } = options;

    // Start the scrape
    const { job_id } = await this.startScrape(filters);

    // Poll for completion
    let attempts = 0;
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, pollInterval));

      const status = await this.checkStatus(job_id);
      
      if (onStatusUpdate) {
        onStatusUpdate(status);
      }

      if (status.status === 'completed') {
        return await this.getResults(job_id);
      } else if (status.status === 'failed') {
        throw new Error(`Scrape failed: ${status.error || 'Unknown error'}`);
      }

      attempts++;
    }

    throw new Error('Scrape timed out');
  }
}

// Example usage:
/*
const api = new AvtoNetScraperAPI();

// Simple usage
api.scrapeAndWait({
  znamka: ["Volkswagen"],
  model: "Golf",
  cenaMin: 10000,
  cenaMax: 25000
})
.then(results => {
  console.log(`Found ${results.total_listings} listings`);
  results.listings.forEach(listing => {
    console.log(`${listing.Naziv} - ${listing.Cena} €`);
  });
})
.catch(error => {
  console.error('Error:', error);
});

// With status updates
api.scrapeAndWait(
  {
    znamka: ["Volkswagen"],
    model: "Golf",
    cenaMin: 10000,
    cenaMax: 25000
  },
  {
    onStatusUpdate: (status) => {
      console.log(`Status: ${status.status}`);
      if (status.total_listings !== null) {
        console.log(`Found so far: ${status.total_listings}`);
      }
    }
  }
)
.then(results => {
  console.log('Results:', results.listings);
});
*/

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AvtoNetScraperAPI;
}

// Export for browser
if (typeof window !== 'undefined') {
  window.AvtoNetScraperAPI = AvtoNetScraperAPI;
}

