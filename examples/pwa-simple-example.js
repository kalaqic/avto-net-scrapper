/**
 * Simple PWA Integration Example - No Polling Required!
 * 
 * This example shows how to register a user with filters.
 * The backend will automatically scrape every 60 seconds and send
 * Pushover notifications when new listings are found.
 */

const API_BASE_URL = 'http://localhost:8000'; // Change to your API URL

/**
 * Register a user with filters and Pushover credentials
 * @param {string} userId - Unique user identifier (e.g., email, username, UUID)
 * @param {string} pushoverApiToken - Your Pushover API token
 * @param {string} pushoverUserKey - Your Pushover user key
 * @param {Object} filters - Search filters
 * @param {boolean} notifyOnFirstScrape - Send notifications on first scrape (default: false)
 * @returns {Promise<Object>} Registration response
 */
async function registerUser(userId, pushoverApiToken, pushoverUserKey, filters, notifyOnFirstScrape = false) {
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
        notify_on_first_scrape: notifyOnFirstScrape
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to register user');
    }

    return await response.json();
  } catch (error) {
    console.error('Error registering user:', error);
    throw error;
  }
}

/**
 * Update user filters or Pushover credentials
 * @param {string} userId - User identifier
 * @param {Object} updates - Updates (filters, pushover keys, etc.)
 * @returns {Promise<Object>} Update response
 */
async function updateUser(userId, updates) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update user');
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating user:', error);
    throw error;
  }
}

/**
 * Get user information
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} User information
 */
async function getUser(userId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get user');
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting user:', error);
    throw error;
  }
}

/**
 * Deactivate a user (stops scraping)
 * @param {string} userId - User identifier
 * @returns {Promise<Object>} Deactivation response
 */
async function deactivateUser(userId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to deactivate user');
    }

    return await response.json();
  } catch (error) {
    console.error('Error deactivating user:', error);
    throw error;
  }
}

// Example usage:
/*
// Register a new user
registerUser(
  'user_123',  // Your unique user ID
  'your_pushover_api_token',  // From Pushover
  'your_pushover_user_key',    // From Pushover
  {
    znamka: ["Volkswagen"],
    model: "Golf",
    cenaMin: 10000,
    cenaMax: 25000,
    letnikMin: 2015,
    letnikMax: 2023,
    kmMax: 100000,
    bencin: 201  // 201=petrol, 202=diesel, 207=electric
  },
  false  // Don't notify on first scrape
)
.then(response => {
  console.log('User registered:', response.message);
  console.log('Scraping will start automatically every 60 seconds!');
})
.catch(error => {
  console.error('Registration failed:', error);
});

// Update filters later
updateUser('user_123', {
  filters: {
    znamka: ["Audi"],
    model: "A4",
    cenaMin: 15000,
    cenaMax: 30000
  }
})
.then(response => {
  console.log('User updated:', response.message);
});

// Get user info
getUser('user_123')
.then(user => {
  console.log('User filters:', user.filters);
});

// Deactivate user (stop scraping)
deactivateUser('user_123')
.then(response => {
  console.log('User deactivated:', response.message);
});
*/

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    registerUser,
    updateUser,
    getUser,
    deactivateUser
  };
}

// Export for browser
if (typeof window !== 'undefined') {
  window.AvtoNetScraperAPI = {
    registerUser,
    updateUser,
    getUser,
    deactivateUser
  };
}

