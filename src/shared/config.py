import json
import sys

# Config limits
# Change these at your own discretion.
# This is as far as I'd go, you might arouse suspicion with too many requests per scrape
MAX_PAGES = 1
MAX_BRANDS = 2
MIN_SCRAPE_INTERVAL_MINUTES = 2
MAX_RESULTS_PER_PAGE = 48 # Max displayed listings on Avto net, as of April 2025

with open('config/params.json') as f:
    params = json.load(f)

with open('config/webhook.json') as f:
    webhook = json.load(f)

with open('config/scheduler_params.json') as f:
    scheduler_params = json.load(f)

def get_param_limits() -> dict:
    return {
        "max_pages": MAX_PAGES,
        "max_brands": MAX_BRANDS,
        "min_scrape_interval_m": MIN_SCRAPE_INTERVAL_MINUTES,
        "max_results_per_page": MAX_RESULTS_PER_PAGE
    }

def get_selectors() -> dict:
    with open('config/selectors.json') as f:
        return json.load(f)

def get_base_url():
    return 'https://www.avto.net'

def build_url(params: dict) -> str:
    sort = params.get("sort", "")
    sort_order = params.get("sort_order", "")
    presort = params.get("presort", "2")  # Default presort=2 (matching user's URL)
    tipsort = params.get("tipsort", "ASC")  # Default tipsort=ASC (matching user's URL)
    page_num = params.get("stran", 1)
    
    # PRODAM (for sale) - default to 2 if not specified
    subSELLER = params.get("subSELLER", 2)

    # Build URL with only explicitly set parameters
    # Use empty strings or 0 for parameters not set (means "all" or "no filter")
    url = get_base_url() + f"/Ads/results.asp?znamka={params.get('znamka', '')}&model={params.get('model', '')}&modelID=&tip=&znamka2=&model2=&tip2=&znamka3=&model3=&tip3="
    
    # Price filters - use subcenaMIN/subcenaMAX if provided (this is the primary filter)
    # When subcenaMIN/subcenaMAX are used, we should set cenaMin/cenaMax to match the range
    if 'subcenaMIN' in params and 'subcenaMAX' in params:
        subcena_min = params['subcenaMIN']
        subcena_max = params['subcenaMAX']
        url += f"&subcenaMIN={subcena_min}&subcenaMAX={subcena_max}"
        
        # Map subcena values to actual price ranges for cenaMin/cenaMax
        # subcenaMIN=3, subcenaMAX=1000 means "up to 1000€"
        if subcena_min == 3 and subcena_max == 1000:
            # "Up to 1000€"
            url += f"&cenaMin=0&cenaMax=1000"
        elif subcena_min == 1 and subcena_max == 1:
            # "With discount price" - use wide range
            url += f"&cenaMin=0&cenaMax=999999"
        elif subcena_min == 2 and subcena_max == 2:
            # "Without price" - use wide range
            url += f"&cenaMin=0&cenaMax=999999"
        elif subcena_min >= 1000:
            # Regular price range (e.g., 1000-2500)
            url += f"&cenaMin={subcena_min}&cenaMax={subcena_max}"
        else:
            # Default fallback
            url += f"&cenaMin=0&cenaMax={subcena_max if subcena_max < 100000 else 999999}"
    else:
        # Fallback to cenaMin/cenaMax if subcena not provided
        cenaMin = params.get('cenaMin', 0)
        cenaMax = params.get('cenaMax', 999999)
        url += f"&cenaMin={cenaMin}&cenaMax={cenaMax}"
    
    # Handle special price filters
    if params.get('akcija'):
        url += "&akcija=1"
    if params.get('brezCene'):
        url += "&brezCene=1"
    
    # Only add year filters if explicitly set, otherwise use "all" values
    if 'letnikMin' in params:
        url += f"&letnikMin={params['letnikMin']}"
    else:
        url += "&letnikMin=0"  # 0 = all years from beginning
    if 'letnikMax' in params:
        url += f"&letnikMax={params['letnikMax']}"
    else:
        url += "&letnikMax=2090"  # 2090 = all years to future
    
    # Fuel type
    url += f"&bencin={params.get('bencin', 0)}"
    
    # Standard parameters (always needed)
    url += "&starost2=999"
    
    # Body type
    url += f"&oblika={params.get('oblika', '0')}"
    
    # Engine filters - only if set
    if 'ccmMin' in params:
        url += f"&ccmMin={params['ccmMin']}"
    else:
        url += "&ccmMin=0"
    if 'ccmMax' in params:
        url += f"&ccmMax={params['ccmMax']}"
    else:
        url += "&ccmMax=99999"
    
    url += f"&mocMin={params.get('mocMin', '0')}&mocMax={params.get('mocMax', '999999')}"
    
    # Mileage filters - only if set, otherwise use "all" values
    if 'kmMin' in params:
        url += f"&kmMin={params['kmMin']}"
    else:
        url += "&kmMin=0"  # 0 = no minimum
    if 'kmMax' in params:
        url += f"&kmMax={params['kmMax']}"
    else:
        url += "&kmMax=9999999"  # Very high = no maximum filter
    
    # Power filters - only if set
    if 'kwMin' in params:
        url += f"&kwMin={params['kwMin']}"
    else:
        url += "&kwMin=0"
    if 'kwMax' in params:
        url += f"&kwMax={params['kwMax']}"
    else:
        url += "&kwMax=999"
    
    # Standard parameters (matching user's working URL format exactly)
    url += "&motortakt=0&motorvalji=0&lokacija=0&sirina=0&dolzina=&dolzinaMIN=0&dolzinaMAX=100&nosilnostMIN=0&nosilnostMAX=999999"
    url += "&sedezevMIN=0&sedezevMAX=9&lezisc=&presek=0&premer=0&col=0&vijakov=0&EToznaka=0&vozilo=&airbag=&barva=&barvaint=&doseg=0&BkType=0&BkOkvir=0&BkOkvirType=0&Bk4=0"
    
    # Equipment flags - use "all" defaults that don't restrict results
    # EQ7=1110100120 means "new, test, used" (matching user's working URL)
    # Only include EQ values if explicitly set, otherwise use neutral "all" values
    eq_defaults = {
        'EQ1': '1000000000', 'EQ2': '1000000000', 'EQ3': '1000000000',  # All transmissions
        'EQ4': '1000000000', 'EQ5': '1000000000', 'EQ6': '1000000000',
        'EQ7': '1110100120',  # All statuses (new, test, used) - matches user's URL
        'EQ8': '100000000', 'EQ9': '1000000020', 'EQ10': '1000000000'
    }
    for eq in ['EQ1', 'EQ2', 'EQ3', 'EQ4', 'EQ5', 'EQ6', 'EQ7', 'EQ8', 'EQ9', 'EQ10']:
        if eq in params:
            url += f"&{eq}={params[eq]}"
        else:
            url += f"&{eq}={eq_defaults.get(eq, '1000000000')}"
    
    # Standard parameters
    # PIA parameter controls VAT/DDV display - set to 0 to show prices with VAT (removes "cena brez DDV" text)
    url += "&KAT=1010000000&PIA=&PIAzero=&PIAOut=&PSLO=&akcija=0&paketgarancije=&broker=0&prikazkategorije=0&kategorija=0&ONLvid=0&ONLnak=0&zaloga=10&arhiv=0"
    
    # Sorting
    url += f"&presort={presort}&tipsort={tipsort}&stran={page_num}&subSORT={sort}&subTIPSORT={sort_order}"
    
    # Location
    url += f"&subLOCATION={params.get('subLOCATION', '')}"
    
    # PRODAM (for sale) - always include
    url += f"&subSELLER={subSELLER}"
    
    # Number of owners
    url += f"&lastnikov={params.get('lastnikov', '')}"
    
    return url

def get_columns():
    return ['HASH', 'URL', 'Cena', 'Naziv', '1.registracija', 'Prevoženih', 'Menjalnik', 'Motor', 'lastnikov']

def validate_params(params: dict) -> None:
    brand = params.get("znamka")

    if isinstance(brand, list):
        if len(brand) > MAX_BRANDS:
            print(f"[ERROR] Too many brands provided. Max allowed is {MAX_BRANDS}. You gave: {len(brand)}")
            sys.exit(1)
    elif isinstance(brand, str):
        if brand == "":
            # Allow empty string → all brands
            params["znamka"] = [""]
        else:
            # Convert single string into list, for consistency
            params["znamka"] = [brand]
    else:
        print("[ERROR] 'znamka' must be either a string, an empty string, or a list of strings.")
        sys.exit(1)

    interval = scheduler_params.get("interval_minute", 1)
    if int(interval) < MIN_SCRAPE_INTERVAL_MINUTES:
        print(f"[ERROR] Scrape interval too short. Must be at least {MIN_SCRAPE_INTERVAL_MINUTES} minute(s).")
        sys.exit(1)

# Run validation on import
validate_params(params)