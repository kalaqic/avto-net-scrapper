"""
API wrapper for scraper that accepts dynamic filters
"""
import asyncio
from typing import Optional
import pandas as pd
from src.internal.scraper import scrape_with_js_and_cookies
from src.internal.parser import populate_data
from src.shared.config import build_url, get_columns, get_selectors, get_param_limits
from src.shared.log import logger


async def scrape_with_filters(filters: dict) -> pd.DataFrame:
    """
    Scrape car listings with dynamic filters.
    
    Args:
        filters: Dictionary containing search filters
        
    Returns:
        DataFrame containing scraped listings
    """
    logger.info("Starting scrape with dynamic filters...")
    
    # Normalize brand parameter
    brands = filters.get("znamka", [""])
    if isinstance(brands, str):
        if brands == "":
            brands = [""]
        else:
            brands = [brands]
    elif not isinstance(brands, list):
        brands = [""]
    
    # Validate brand count
    param_limits = get_param_limits()
    if len(brands) > param_limits["max_brands"]:
        logger.warning(f"Too many brands ({len(brands)}), limiting to {param_limits['max_brands']}")
        brands = brands[:param_limits["max_brands"]]
    
    # Start with minimal defaults - only what's needed for the URL to work
    # Only include filters that user explicitly set
    base_params = {
        "znamka": "",
        "model": "",
        "stran": 1,
        # PRODAM (for sale) - always include this as default
        "subSELLER": 2,
    }
    
    # Only add filters that user explicitly provided
    # Use None/empty values for filters not set by user
    filter_keys = [
        "cenaMin", "cenaMax", "letnikMin", "letnikMax", 
        "kmMin", "kmMax", "kwMin", "kwMax", 
        "ccmMin", "ccmMax", "mocMin", "mocMax",
        "subLOCATION", "oblika", "bencin",
        "subcenaMIN", "subcenaMAX",  # Price range filters
        "EQ1", "EQ2", "EQ3", "EQ4", "EQ5", "EQ6", "EQ7", "EQ8", "EQ9", "EQ10",
        "sort", "sort_order", "presort", "tipsort", "lastnikov"
    ]
    
    # Only add filters that user explicitly set (not None, not empty defaults)
    for key in filter_keys:
        if key in filters:
            base_params[key] = filters[key]
    
    # Always include user-set filters (but prioritize subcenaMIN/subcenaMAX over cenaMax)
    for k, v in filters.items():
        if k not in filter_keys:
            base_params[k] = v
    
    # If subcenaMIN/subcenaMAX are set, override cenaMax based on them
    if 'subcenaMIN' in base_params and 'subcenaMAX' in base_params:
        subcena_min = base_params['subcenaMIN']
        subcena_max = base_params['subcenaMAX']
        # Map subcena values to actual price ranges
        if subcena_min == 3 and subcena_max == 1000:
            base_params['cenaMax'] = 1000
        elif subcena_min >= 1000:
            base_params['cenaMax'] = subcena_max
        # For other special cases (akcija, brez), keep wide range
    
    all_results = pd.DataFrame(columns=get_columns())
    
    # Scrape each brand
    for brand in brands:
        local_params = base_params.copy()
        local_params["znamka"] = brand
        
        # Apply model if specified
        if filters.get("model"):
            local_params["model"] = filters["model"]
        
        logger.info(f"Scraping: {brand or 'ALL'} {'(' + filters.get('model', '') + ')' if filters.get('model') else ''}")
        
        try:
            brand_data = await scrape_brand_with_pagination_dynamic(
                brand, 
                param_limits["max_pages"],
                local_params
            )
            all_results = pd.concat([all_results, brand_data], ignore_index=True)
        except Exception as e:
            logger.error(f"Error scraping brand {brand}: {e}")
            continue
    
    if all_results.empty:
        logger.warning("No results fetched from any brand/page.")
        return pd.DataFrame(columns=get_columns())
    
    logger.info(f"Scrape complete. Found {len(all_results)} listings.")
    return all_results


async def scrape_brand_with_pagination_dynamic(
    brand: str, 
    max_pages: int, 
    base_params: dict
) -> pd.DataFrame:
    """
    Scrape multiple pages for a brand with dynamic parameters.
    
    Args:
        brand: Brand name (empty string for all)
        max_pages: Maximum number of pages to scrape
        base_params: Base parameters dictionary
        
    Returns:
        DataFrame containing scraped listings
    """
    logger.info(f"Scraping brand: '{brand or 'ALL'}' with {max_pages} pages")
    brand_results = pd.DataFrame(columns=get_columns())
    
    for page in range(1, max_pages + 1):
        local_params = base_params.copy()
        local_params["znamka"] = brand
        local_params["stran"] = page
        
        logger.debug(f"Fetching page {page} for brand '{brand}'")
        result = await scrape_with_js_and_cookies(local_params)
        
        if isinstance(result, int):  # If 500 or error
            logger.warning(f"Skipping page {page} for '{brand}' due to error code {result}")
            continue
        
        if not result:  # Empty result
            logger.debug(f"No results on page {page} for '{brand}'")
            break
        
        page_data = populate_data(result, pd.DataFrame(columns=get_columns()))
        found_count = len(page_data)
        brand_results = pd.concat([brand_results, page_data], ignore_index=True)
        
        max_results_per_page = get_param_limits()["max_results_per_page"]
        if found_count < max_results_per_page:
            logger.debug(f"Less than {max_results_per_page} results on page {page} — assuming last page.")
            break
    
    return brand_results

