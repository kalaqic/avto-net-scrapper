/**
 * React Component Example - No Polling Required!
 * 
 * This component shows how to register a user with filters.
 * The backend handles all scraping automatically.
 */

import React, { useState } from 'react';

const API_BASE_URL = 'http://localhost:8000';

function CarScraperRegistration() {
  const [userId, setUserId] = useState('');
  const [pushoverApiToken, setPushoverApiToken] = useState('');
  const [pushoverUserKey, setPushoverUserKey] = useState('');
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
  const [notifyOnFirstScrape, setNotifyOnFirstScrape] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/users/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          pushover_api_token: pushoverApiToken,
          pushover_user_key: pushoverUserKey,
          filters: filters,
          notify_on_first_scrape: notifyOnFirstScrape,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to register');
      }

      const result = await response.json();
      setMessage(result.message);
      
      // Clear form on success
      setUserId('');
      setPushoverApiToken('');
      setPushoverUserKey('');
      setFilters({
        znamka: [''],
        model: '',
        cenaMin: 0,
        cenaMax: 100000,
        letnikMin: 2015,
        letnikMax: 2023,
        kmMax: 100000,
        bencin: 0,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="car-scraper-registration">
      <h1>🚗 Avto-Net Scraper Registration</h1>
      <p>
        Register your search filters and Pushover credentials.
        The system will automatically scrape every 60 seconds and send
        notifications when new listings are found.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-section">
          <h2>User Information</h2>
          
          <div className="form-group">
            <label>User ID (unique identifier):</label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="e.g., user_123 or your_email@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Pushover API Token:</label>
            <input
              type="text"
              value={pushoverApiToken}
              onChange={(e) => setPushoverApiToken(e.target.value)}
              placeholder="Your Pushover API token"
              required
            />
          </div>

          <div className="form-group">
            <label>Pushover User Key:</label>
            <input
              type="text"
              value={pushoverUserKey}
              onChange={(e) => setPushoverUserKey(e.target.value)}
              placeholder="Your Pushover user key"
              required
            />
          </div>
        </div>

        <div className="form-section">
          <h2>Search Filters</h2>

          <div className="form-group">
            <label>Brand:</label>
            <input
              type="text"
              value={filters.znamka[0] || ''}
              onChange={(e) => setFilters({ ...filters, znamka: [e.target.value] })}
              placeholder="e.g., Volkswagen (empty for all)"
            />
          </div>

          <div className="form-group">
            <label>Model:</label>
            <input
              type="text"
              value={filters.model}
              onChange={(e) => setFilters({ ...filters, model: e.target.value })}
              placeholder="e.g., Golf (empty for all)"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Price (€):</label>
              <input
                type="number"
                value={filters.cenaMin}
                onChange={(e) => setFilters({ ...filters, cenaMin: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div className="form-group">
              <label>Max Price (€):</label>
              <input
                type="number"
                value={filters.cenaMax}
                onChange={(e) => setFilters({ ...filters, cenaMax: parseInt(e.target.value) || 100000 })}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Min Year:</label>
              <input
                type="number"
                value={filters.letnikMin}
                onChange={(e) => setFilters({ ...filters, letnikMin: parseInt(e.target.value) || 2000 })}
              />
            </div>

            <div className="form-group">
              <label>Max Year:</label>
              <input
                type="number"
                value={filters.letnikMax}
                onChange={(e) => setFilters({ ...filters, letnikMax: parseInt(e.target.value) || 2090 })}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Max Mileage:</label>
            <input
              type="number"
              value={filters.kmMax}
              onChange={(e) => setFilters({ ...filters, kmMax: parseInt(e.target.value) || 300000 })}
            />
          </div>

          <div className="form-group">
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
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={notifyOnFirstScrape}
              onChange={(e) => setNotifyOnFirstScrape(e.target.checked)}
            />
            Notify on first scrape (default: false)
          </label>
        </div>

        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}

        {message && (
          <div className="success-message">
            {message}
          </div>
        )}

        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register & Start Scraping'}
        </button>
      </form>

      <div className="info-box">
        <h3>How it works:</h3>
        <ol>
          <li>Register with your filters and Pushover credentials</li>
          <li>The backend automatically scrapes every 60 seconds</li>
          <li>You'll receive Pushover notifications when new listings match your filters</li>
          <li>No polling or manual checking needed!</li>
        </ol>
      </div>
    </div>
  );
}

export default CarScraperRegistration;

