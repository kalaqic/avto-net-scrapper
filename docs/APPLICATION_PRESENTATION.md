# 🚗 Avto-Net Scraper - Technical Presentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Breakdown](#component-breakdown)
4. [Application Flow](#application-flow)
5. [Configuration System](#configuration-system)
6. [Key Features](#key-features)
7. [Technical Implementation Details](#technical-implementation-details)
8. [Data Flow](#data-flow)
9. [Anti-Detection Mechanisms](#anti-detection-mechanisms)
10. [Notification System](#notification-system)

---

## Overview

The **Avto-Net Scraper** is an automated web scraping application designed to monitor car listings on [avto.net](https://www.avto.net/), a Slovenian automotive marketplace. The application continuously checks for new listings matching user-defined criteria and sends notifications when new cars are found.

### Purpose
- Automatically monitor car listings based on customizable search parameters
- Detect new listings that match specific criteria (brand, model, price, year, mileage, etc.)
- Send real-time notifications via Pushover when new listings are discovered
- Store listing data in CSV format for historical tracking

### Technology Stack
- **Python 3.x** - Core programming language
- **Playwright** - Browser automation for JavaScript-rendered content
- **BeautifulSoup4** - HTML parsing and data extraction
- **Pandas** - Data manipulation and CSV handling
- **APScheduler** - Task scheduling and automation
- **Requests** - HTTP requests for notifications

---

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
avto-net-scrapper/
├── main.py                    # Entry point
├── src/
│   ├── internal/              # Core business logic
│   │   ├── scraper.py        # Web scraping orchestration
│   │   ├── parser.py         # HTML parsing and data extraction
│   │   ├── data_handler.py   # Data comparison and storage
│   │   ├── notifier.py       # Notification system
│   │   └── scheduler.py      # Task scheduling
│   └── shared/               # Shared utilities
│       ├── config.py         # Configuration management
│       ├── headers.py        # Browser fingerprinting
│       ├── proxy_fetcher.py  # Proxy management
│       ├── utils.py          # Helper functions
│       └── log.py           # Logging setup
├── config/                   # Configuration files
│   ├── params.json          # Search parameters
│   ├── scheduler_params.json # Scheduler settings
│   ├── selectors.json       # HTML selectors
│   └── pushover.json        # Pushover API config
└── data/                     # Data storage
    └── listings.csv         # Stored listings
```

---

## Component Breakdown

### 1. **main.py** - Application Entry Point

**Purpose**: Initializes the application and coordinates the initial scrape and scheduler startup.

**Key Functions**:
- `main()`: Async entry point that:
  1. Loads and validates configuration parameters
  2. Displays startup information (brands, models, estimated requests)
  3. Performs an initial scrape to populate the database
  4. Starts the scheduler if initial scrape succeeds

**Flow**:
```
Start → Load Config → Display Info → Initial Scrape → Start Scheduler → Run Continuously
```

---

### 2. **scraper.py** - Web Scraping Engine

**Purpose**: Orchestrates the web scraping process using Playwright to handle JavaScript-rendered content.

**Key Functions**:

#### `scrape(init=False)`
- Main scraping orchestrator
- Iterates through configured brands
- Calls `scrape_brand_with_pagination()` for each brand
- Handles initial data save vs. comparison logic

#### `scrape_brand_with_pagination(brand, max_pages)`
- Scrapes multiple pages for a single brand
- Stops early if fewer results than expected (indicates last page)
- Aggregates results into a pandas DataFrame

#### `scrape_with_js_and_cookies(params)`
- **Core scraping function** that:
  1. Builds the search URL from parameters
  2. Launches a headless Chromium browser via Playwright
  3. Applies randomized browser fingerprinting (user agent, viewport, timezone)
  4. Navigates to the search results page
  5. Waits for content to load
  6. Extracts HTML content
  7. Cleans HTML (removes scripts/styles)
  8. Returns cleaned HTML for parsing

**Anti-Bot Features**:
- Random delays (2-5 seconds) before page load
- Randomized browser fingerprints
- Headless mode with automation flags disabled
- Timeout handling for slow-loading pages

---

### 3. **parser.py** - Data Extraction

**Purpose**: Parses HTML content and extracts structured car listing data.

**Key Functions**:

#### `populate_data(html, cars)`
- Parses HTML using BeautifulSoup
- Finds all listing rows using CSS selectors
- Extracts data for each listing:
  - **Title** (Naziv)
  - **Price** (Cena) - with fallback selectors
  - **Registration Date** (1.registracija)
  - **Link** (URL) - normalized to full URL
  - **Data Block** - contains multiple car attributes
  - **Number of Owners** (lastnikov) - extracted from title using regex

#### `extract_lastnikov(title, data)`
- Uses regex patterns to extract owner count from title
- Handles Slovenian variations: "LASTNICA", "LASTNIK", "LASTNIKA"
- Returns number of owners or None

**Data Structure**:
Each listing is converted to a dictionary with:
- `HASH`: Unique identifier (SHA256 of title + price + registration)
- `URL`: Full listing URL
- `Cena`: Formatted price
- `Naziv`: Car title
- `1.registracija`: Registration date
- `Prevoženih`: Mileage
- `Menjalnik`: Transmission type
- `Motor`: Engine details
- `lastnikov`: Number of owners

---

### 4. **data_handler.py** - Data Management

**Purpose**: Compares new scraped data with existing data and manages CSV storage.

**Key Functions**:

#### `compare_data(new_cars)`
- Loads existing listings from `data/listings.csv`
- Performs outer merge on `HASH` column to find differences
- Identifies:
  - **New listings** (`right_only`): Not in existing data
  - **Removed listings** (`left_only`): No longer in new data
- Calls `handle_data()` for new listings

#### `handle_data(new_rows)`
- Appends new listings to CSV file
- Triggers notifications via `send_pushover_notifications()`
- Logs the number of new listings found

**Data Comparison Logic**:
- Uses pandas merge with `HASH` as unique identifier
- `HASH` is generated from: `title + price + registration_date`
- This ensures listings are uniquely identified even if URLs change

---

### 5. **notifier.py** - Notification System

**Purpose**: Sends notifications to users when new listings are found.

**Key Functions**:

#### `send_pushover_notifications(rows)`
- Iterates through new listings
- Calls `send_pushover_notification()` for each listing

#### `send_pushover_notification(row)`
- Formats car details into a readable message:
  - 🚗 Car title
  - 💰 Price
  - 📅 Registration date
  - 🛣️ Mileage
  - 🔧 Engine details
  - 👤 Number of owners (if available)
  - 🔗 Listing URL
- Sends POST request to Pushover API
- Handles errors gracefully

**Configuration**:
- Loads API credentials from `config/pushover.json`
- Supports custom sound and priority settings

---

### 6. **scheduler.py** - Task Scheduling

**Purpose**: Manages periodic execution of scraping tasks with intelligent scheduling.

**Key Functions**:

#### `start_scheduler()`
- Initializes AsyncIOScheduler
- Sets up error handling listener
- Configures timezone (default: Europe/Ljubljana)
- Schedules first run dynamically
- Runs indefinitely until interrupted

#### `schedule_next_run(scheduler, time_zone)`
- **Intelligent scheduling** based on time of day:
  - **Night Mode (00:00-06:00)**: Every 60 minutes
  - **Day Mode (06:00-00:00)**: Random interval between 2-5 minutes
- Removes existing jobs before scheduling new one
- Uses `date` trigger for precise timing

#### `run_scrape_job_and_reschedule(scheduler, time_zone)`
- Executes the scrape job
- Logs execution time
- Automatically schedules the next run
- Handles errors via event listener

**Scheduling Strategy**:
- **Adaptive intervals**: Less frequent at night when fewer new listings appear
- **Randomization**: Prevents predictable patterns that could be detected
- **Error recovery**: Continues scheduling even if a job fails

---

### 7. **config.py** - Configuration Management

**Purpose**: Centralized configuration loading and validation.

**Key Functions**:

#### `get_param_limits()`
Returns hardcoded safety limits:
- `max_pages`: 1 (prevents excessive requests)
- `max_brands`: 2 (limits brand iterations)
- `min_scrape_interval_m`: 2 minutes (minimum delay)
- `max_results_per_page`: 48 (Avto.net maximum)

#### `build_url(params)`
- Constructs the Avto.net search URL
- Handles all search parameters:
  - Brand (znamka)
  - Model
  - Price range (cenaMin, cenaMax)
  - Year range (letnikMin, letnikMax)
  - Mileage (kmMin, kmMax)
  - Engine power (kwMin, kwMax, ccmMin, ccmMax)
  - Fuel type (bencin)
  - Equipment flags (EQ1-EQ10)
  - Pagination (stran)
  - Sorting options

#### `validate_params(params)`
- Ensures brand count doesn't exceed `MAX_BRANDS`
- Validates scrape interval is above minimum
- Converts single brand string to list format
- Handles empty string (all brands) case

**Configuration Files**:
- `params.json`: Search criteria
- `scheduler_params.json`: Scheduling settings
- `selectors.json`: HTML CSS selectors
- `webhook.json`: Discord webhook (legacy, not actively used)
- `pushover.json`: Pushover API credentials

---

### 8. **headers.py** - Browser Fingerprinting

**Purpose**: Generates randomized browser fingerprints to avoid detection.

**Key Functions**:

#### `get_playwright_context_options()`
Returns randomized browser context options:
- **User-Agent**: Random selection from 20+ real browser UAs
- **Viewport**: Random screen resolution (desktop or mobile)
- **Timezone**: Random European timezone
- **Locale**: Random language preference
- **Extra HTTP Headers**: Accept-Language, DNT

#### `get_random_schedule_interval()`
- Returns random interval between 2-5 minutes
- Adds variance to prevent pattern detection

#### `is_night_time()`
- Checks if current time is 00:00-06:00 in Ljubljana timezone
- Used for adaptive scheduling

**Fingerprinting Strategy**:
- **20+ User-Agents**: Chrome, Firefox, Safari (desktop/mobile)
- **10 Screen Resolutions**: Common desktop and mobile sizes
- **10 European Timezones**: Realistic geographic distribution
- **10 Language Preferences**: European languages including Slovenian
- **9 Referer URLs**: Search engines and avto.net itself

---

### 9. **utils.py** - Utility Functions

**Purpose**: Helper functions for data processing.

**Key Functions**:

#### `extract_property(result, property_class, tag_type)`
- Safely extracts text or href from HTML elements
- Handles missing elements gracefully

#### `collect_car_data(text_block)`
- Parses key-value pairs from data block
- Converts newline-separated text to dictionary

#### `format_price(price)`
- Extracts numeric price from formatted string
- Removes thousands separators and currency symbols

#### `hash_listing(title, price, registration)`
- Generates SHA256 hash from listing identifiers
- Creates unique fingerprint for comparison

#### `check_null_data(value)`
- Returns ":x:" emoji for null values
- Used in notification formatting

---

### 10. **proxy_fetcher.py** - Proxy Management

**Purpose**: Fetches and manages proxy servers (currently disabled but infrastructure exists).

**Key Features**:
- Fetches proxies from geonode.com API
- Filters by uptime (>80%) and protocol
- Caches proxies for 30 minutes
- Prefers HTTP and SOCKS5 protocols
- Currently disabled in `headers.py` for stability

---

### 11. **log.py** - Logging System

**Purpose**: Centralized logging configuration.

**Features**:
- Logs to both console and file
- Rotating file handler (5MB max, 3 backups)
- Timestamped log entries
- DEBUG level logging for detailed troubleshooting

---

## Application Flow

### Initialization Phase

```
1. main.py starts
   ↓
2. Load configuration files
   - params.json (search criteria)
   - scheduler_params.json (scheduling)
   - selectors.json (HTML selectors)
   ↓
3. Validate parameters
   - Check brand count ≤ MAX_BRANDS
   - Check interval ≥ MIN_INTERVAL
   ↓
4. Display startup information
   - Brands to scrape
   - Models to filter
   - Estimated requests
   ↓
5. Perform initial scrape
   - scrape(init=True)
   ↓
6. Save initial data to CSV
   - data/listings.csv
   ↓
7. Start scheduler
   - start_scheduler()
```

### Scraping Cycle

```
1. Scheduler triggers scrape job
   ↓
2. scrape(init=False) called
   ↓
3. For each brand in params["znamka"]:
   ↓
4. scrape_brand_with_pagination(brand, max_pages)
   ↓
5. For each page (1 to max_pages):
   ↓
6. scrape_with_js_and_cookies(params)
   - Build URL
   - Launch Playwright browser
   - Apply randomized fingerprint
   - Navigate to page
   - Wait for content
   - Extract HTML
   ↓
7. populate_data(html, cars)
   - Parse HTML with BeautifulSoup
   - Extract listing data
   - Generate HASH for each listing
   ↓
8. Aggregate all results
   ↓
9. compare_data(new_results)
   - Load existing CSV
   - Merge on HASH
   - Identify new listings
   ↓
10. handle_data(new_listings)
    - Append to CSV
    - Send notifications
    ↓
11. Schedule next run
    - Calculate next interval
    - Schedule job
```

### Data Processing Pipeline

```
HTML Content
    ↓
BeautifulSoup Parsing
    ↓
CSS Selector Extraction
    ↓
Data Structure Creation
    ↓
HASH Generation
    ↓
DataFrame Assembly
    ↓
Comparison with Existing Data
    ↓
New Listings Identification
    ↓
CSV Storage
    ↓
Notification Dispatch
```

---

## Configuration System

### Search Parameters (`config/params.json`)

**Core Parameters**:
- `znamka`: Brand(s) - empty string for all, or array like `["Audi", "BMW"]`
- `model`: Model name - empty string for all models
- `cenaMin`/`cenaMax`: Price range in EUR
- `letnikMin`/`letnikMax`: Year range
- `kmMin`/`kmMax`: Mileage range
- `kwMin`/`kwMax`: Engine power (kW)
- `ccmMin`/`ccmMax`: Engine displacement
- `bencin`: Fuel type (0=all, 201=petrol, 202=diesel, 207=electric)

**Equipment Flags (EQ1-EQ10)**:
- Binary-encoded feature flags
- Example: `EQ3` = Transmission (1001000000 = automatic, 1002000000 = manual)
- Example: `EQ7` = Status (1110100120 = new/test/used)

**Sorting**:
- `sort`: Sort field
- `sort_order`: Sort direction
- `presort`/`tipsort`: Pre-sorting options

### Scheduler Parameters (`config/scheduler_params.json`)

- `timezone`: Timezone for scheduling (default: "Europe/Ljubljana")
- `interval_minute`: Base interval in minutes (used as reference)
- Note: Actual intervals are dynamically calculated

### HTML Selectors (`config/selectors.json`)

CSS class selectors for extracting data:
- `result_row`: Container for each listing
- `title`: Listing title
- `price_main`/`price_fallback`: Price elements
- `data_block_primary`/`data_block_fallback`: Car details container
- `link`: Listing URL link

**Why Selectors File?**
- Avto.net may change HTML structure
- Easy to update without code changes
- Supports fallback selectors for reliability

---

## Key Features

### 1. **Intelligent Scheduling**
- **Adaptive Intervals**: Slower at night (60 min), faster during day (2-5 min)
- **Randomization**: Prevents pattern detection
- **Error Recovery**: Continues scheduling after failures

### 2. **Anti-Detection Mechanisms**
- **Browser Fingerprinting**: Randomized user agents, viewports, timezones
- **Request Delays**: Random 2-5 second delays
- **Limited Scope**: Max 1 page, max 2 brands to reduce footprint
- **Headless Automation**: Disables automation detection flags

### 3. **Robust Data Handling**
- **Unique Identification**: SHA256 hash prevents duplicates
- **Incremental Updates**: Only processes new listings
- **CSV Storage**: Simple, human-readable data format
- **Data Validation**: Handles missing/null values gracefully

### 4. **Comprehensive Notifications**
- **Pushover Integration**: Real-time mobile/desktop notifications
- **Rich Formatting**: Emojis and structured data
- **Error Handling**: Graceful failure if notification service unavailable

### 5. **Modular Architecture**
- **Separation of Concerns**: Each module has single responsibility
- **Easy Maintenance**: Update selectors/config without code changes
- **Extensible**: Easy to add new notification channels or data sources

---

## Technical Implementation Details

### Browser Automation Strategy

**Why Playwright?**
- Handles JavaScript-rendered content (Avto.net uses dynamic loading)
- Better automation detection evasion than Selenium
- Supports headless mode with full browser features
- Can set custom browser fingerprints

**Browser Context Options**:
```python
{
    "user_agent": "Random UA",
    "viewport": {"width": 1920, "height": 1080},
    "timezone_id": "Europe/Ljubljana",
    "locale": "sl-SI",
    "extra_http_headers": {...}
}
```

### Data Deduplication

**HASH Generation**:
```python
hash = SHA256(title + price + registration_date)
```

**Why This Approach?**
- Title + price + registration uniquely identifies a listing
- More reliable than URL (URLs can change)
- Handles price updates (new hash = new listing)

### Error Handling

**Graceful Degradation**:
- Missing HTML elements → Returns None, continues processing
- Network errors → Logs error, continues with next page/brand
- Notification failures → Logs warning, doesn't stop scraping
- CSV read errors → Creates empty DataFrame, treats all as new

**Logging Levels**:
- **DEBUG**: Detailed execution info (selectors, fingerprints)
- **INFO**: Normal operations (scraping start, results found)
- **WARNING**: Non-critical issues (missing data, notification failures)
- **ERROR**: Critical failures (scraping errors, configuration issues)

---

## Data Flow

### Input → Processing → Output

```
Configuration Files
    ↓
Search Parameters
    ↓
URL Construction
    ↓
Web Request (Playwright)
    ↓
HTML Response
    ↓
BeautifulSoup Parsing
    ↓
Data Extraction
    ↓
Pandas DataFrame
    ↓
HASH Generation
    ↓
Comparison with CSV
    ↓
New Listings Filter
    ↓
CSV Update
    ↓
Pushover Notification
```

### Data Structure Example

**CSV Columns**:
- `HASH`: Unique identifier
- `URL`: Listing URL
- `Cena`: Price (formatted)
- `Naziv`: Car title
- `1.registracija`: Registration date
- `Prevoženih`: Mileage
- `Menjalnik`: Transmission
- `Motor`: Engine details
- `lastnikov`: Number of owners

**Example Row**:
```
HASH: a1b2c3d4...
URL: https://www.avto.net/Ads/details.asp?id=12345
Cena: 15000
Naziv: Volkswagen Golf 2.0 TDI
1.registracija: 2018
Prevoženih: 50000
Menjalnik: Avtomatski
Motor: 2.0 TDI, 110kW
lastnikov: 1
```

---

## Anti-Detection Mechanisms

### 1. **Request Rate Limiting**
- Maximum 1 page per brand
- Maximum 2 brands per scrape
- Minimum 2-minute intervals
- Random delays (2-5 seconds) before requests

### 2. **Browser Fingerprinting**
- **20+ User-Agents**: Rotates through real browser signatures
- **Viewport Randomization**: Different screen sizes
- **Timezone Variation**: European timezones
- **Language Headers**: Multiple Accept-Language values
- **Referer Rotation**: Search engines and avto.net

### 3. **Behavioral Patterns**
- **Adaptive Scheduling**: Slower at night (less suspicious)
- **Random Intervals**: 2-5 minute variance prevents patterns
- **Headless Mode**: Runs without visible browser window

### 4. **Error Handling**
- Graceful failures don't expose scraping behavior
- Timeout handling prevents hanging requests
- Early termination on empty results

---

## Notification System

### Pushover Integration

**Message Format**:
```
🚗 [Car Title]
💰 [Price] €
📅 [Registration Date]
🛣️ [Mileage]
🔧 [Engine Details]
👤 Lastnikov: [Number of Owners]
🔗 [Listing URL]
```

**Configuration** (`config/pushover.json`):
```json
{
    "api_token": "your_api_token",
    "user_key": "your_user_key",
    "sound": "pushover",
    "priority": 0
}
```

**Features**:
- Per-listing notifications (one notification per new car)
- Rich formatting with emojis
- Clickable URLs
- Customizable sound and priority

---

## Limitations & Considerations

### Built-in Limitations
1. **Pagination**: Maximum 1 page per brand (safety limit)
2. **Brands**: Maximum 2 brands per scrape
3. **Models**: Single model filter (multiple models not supported)
4. **Interval**: Minimum 2 minutes between scrapes

### Technical Limitations
1. **HTML Structure Dependency**: Relies on CSS selectors (may break if Avto.net changes structure)
2. **JavaScript Rendering**: Requires Playwright (slower than simple HTTP requests)
3. **No Proxy Rotation**: Proxy system exists but is disabled
4. **Single Notification Channel**: Only Pushover (Discord webhook code exists but unused)

### Maintenance Considerations
1. **Selector Updates**: May need to update `selectors.json` if Avto.net changes HTML
2. **URL Parameter Changes**: Search URL construction may need updates
3. **API Changes**: Pushover API changes could break notifications
4. **Rate Limiting**: Avto.net may implement stricter rate limiting

---

## Summary

The Avto-Net Scraper is a sophisticated web scraping application that:

1. **Monitors** car listings on avto.net based on customizable search criteria
2. **Detects** new listings by comparing scraped data with stored CSV
3. **Notifies** users via Pushover when new matching listings are found
4. **Stores** listing data in CSV format for historical tracking
5. **Schedules** automatic periodic checks with intelligent timing
6. **Evades** detection through browser fingerprinting and rate limiting

The application is designed for **personal use** with built-in safety limits to prevent excessive requests. It uses modern web scraping techniques (Playwright, BeautifulSoup) combined with intelligent scheduling and notification systems to provide a seamless monitoring experience.

---

## Future Enhancement Possibilities

1. **Multi-Channel Notifications**: Add Discord, Email, SMS support
2. **Database Storage**: Replace CSV with SQLite/PostgreSQL
3. **Web Dashboard**: Web interface for viewing listings and configuring searches
4. **Price Tracking**: Track price changes over time
5. **Image Download**: Download and store listing images
6. **Advanced Filtering**: Machine learning for listing relevance scoring
7. **Proxy Rotation**: Re-enable and improve proxy management
8. **Distributed Scraping**: Multiple instances with load balancing

---

*Document generated from codebase analysis - Last Updated: 2025*

