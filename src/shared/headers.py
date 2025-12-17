import random
import pytz
from datetime import datetime
from src.shared.log import logger

# List of common User-Agent strings from different browsers and devices
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    
    # Firefox
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:115.0) Gecko/20100101 Firefox/115.0",
    
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    
    # Mobile Chrome Android
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
    
    # Mobile Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
    
    # iPad Safari
    "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
]

# Common Accept-Language values
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "de-DE,de;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "it-IT,it;q=0.9,en;q=0.8",
    "nl-NL,nl;q=0.9,en;q=0.8",
    "sl-SI,sl;q=0.9,en;q=0.8",
    "hr-HR,hr;q=0.9,en;q=0.8",
    "pt-PT,pt;q=0.9,en;q=0.8",
]

# Common Referer values
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://search.yahoo.com/",
    "https://www.google.si/",
    "https://www.google.de/",
    "https://www.google.hr/",
    "https://www.avto.net/",
    "",  # Sometimes no referer
]

# Common screen resolutions and viewports
SCREEN_RESOLUTIONS = [
    {"width": 1920, "height": 1080},  # Full HD
    {"width": 1366, "height": 768},   # Common laptop
    {"width": 1440, "height": 900},   # MacBook Air
    {"width": 1600, "height": 900},   # 16:9 widescreen
    {"width": 1280, "height": 720},   # HD
    {"width": 1536, "height": 864},   # Common Windows
    {"width": 1680, "height": 1050},  # 16:10 ratio
    {"width": 2560, "height": 1440},  # 2K
    {"width": 1024, "height": 768},   # 4:3 ratio
    {"width": 1280, "height": 1024},  # 5:4 ratio
]

# Mobile viewports
MOBILE_VIEWPORTS = [
    {"width": 375, "height": 667},    # iPhone SE
    {"width": 414, "height": 896},    # iPhone 11 Pro Max
    {"width": 360, "height": 640},    # Samsung Galaxy S8
    {"width": 412, "height": 915},    # Pixel 5
    {"width": 768, "height": 1024},   # iPad
    {"width": 820, "height": 1180},   # iPad Air
]

# Common timezones (valid Playwright timezone IDs)
TIMEZONES = [
    "Europe/Ljubljana",  # Slovenia
    "Europe/Zagreb",     # Croatia
    "Europe/Vienna",     # Austria
    "Europe/Berlin",     # Germany (Munich not valid)
    "Europe/Rome",       # Italy
    "Europe/Budapest",   # Hungary
    "Europe/Prague",     # Czech Republic
    "Europe/Warsaw",     # Poland
    "Europe/Zurich",     # Switzerland
    "Europe/Brussels",   # Belgium
]

# Import proxy configuration
try:
    from config.proxy_config import PROXY_SERVERS
    from src.shared.proxy_fetcher import proxy_fetcher
    USE_DYNAMIC_PROXIES = True
except ImportError:
    # Fallback if proxy config doesn't exist
    PROXY_SERVERS = []
    USE_DYNAMIC_PROXIES = False

def get_random_headers():
    """
    Generate a random set of HTTP headers to mimic different browsers and devices.
    
    Returns:
        dict: A dictionary containing randomized headers
    """
    user_agent = random.choice(USER_AGENTS)
    accept_language = random.choice(ACCEPT_LANGUAGES)
    referer = random.choice(REFERERS)
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Only add referer if it's not empty
    if referer:
        headers["Referer"] = referer
    
    return headers

def get_random_viewport():
    """
    Get a random viewport size based on the user agent type.
    
    Returns:
        dict: Viewport dimensions
    """
    # 20% chance of mobile viewport
    if random.random() < 0.2:
        return random.choice(MOBILE_VIEWPORTS)
    else:
        return random.choice(SCREEN_RESOLUTIONS)

def get_random_timezone():
    """
    Get a random timezone from European regions.
    
    Returns:
        str: Timezone string
    """
    return random.choice(TIMEZONES)

def get_random_proxy():
    """
    Get a random proxy server (DISABLED for now).
    
    Returns:
        dict or None: Always returns None (no proxy)
    """
    # Proxy rotation disabled for stability
    return None

def get_playwright_context_options():
    """
    Generate randomized options for Playwright browser context.
    
    Returns:
        dict: A dictionary with user_agent and other context options
    """
    user_agent = random.choice(USER_AGENTS)
    accept_language = random.choice(ACCEPT_LANGUAGES)
    viewport = get_random_viewport()
    timezone = get_random_timezone()
    proxy = get_random_proxy()
    
    context_options = {
        "user_agent": user_agent,
        "viewport": viewport,
        "timezone_id": timezone,
        "locale": accept_language.split(',')[0],  # Extract primary language
        "extra_http_headers": {
            "Accept-Language": accept_language,
            "DNT": "1",
        }
    }
    
    # Add proxy if available
    if proxy:
        context_options["proxy"] = proxy
    
    return context_options

def get_random_schedule_interval():
    """
    Get a random interval between 2-5 minutes with some variance.
    
    Returns:
        int: Random interval in minutes
    """
    return random.randint(2, 5)

def is_night_time():
    """
    Check if current time is between 00:00 and 06:00 in Ljubljana timezone.
    
    Returns:
        bool: True if it's night time
    """
    ljubljana_tz = pytz.timezone('Europe/Ljubljana')
    current_time = datetime.now(ljubljana_tz)
    return current_time.hour >= 0 and current_time.hour < 6
