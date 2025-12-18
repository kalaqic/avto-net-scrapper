"""
Scraper service for user-based scraping
"""
import pandas as pd
from typing import Dict, List
from src.api.scraper_api import scrape_with_filters
from src.shared.log import logger


async def scrape_for_user(filters: Dict) -> List[Dict]:
    """
    Scrape car listings for a user with given filters.
    
    Args:
        filters: Dictionary containing search filters
        
    Returns:
        List of car listings as dictionaries
    """
    try:
        logger.info(f"Starting scrape with filters: {filters}")
        logger.info(f"  Brand: {filters.get('znamka', 'ALL')}")
        logger.info(f"  Model: {filters.get('model', 'ALL')}")
        logger.info(f"  Price: {filters.get('cenaMin', 0)}-{filters.get('cenaMax', 'MAX')}€")
        if 'subcenaMIN' in filters:
            logger.info(f"  Price Range: subcenaMIN={filters.get('subcenaMIN')}, subcenaMAX={filters.get('subcenaMAX')}")
        
        # Use the existing scrape_with_filters function
        results_df = await scrape_with_filters(filters)
        
        if results_df is None or results_df.empty:
            logger.info(f"No results found for filters: {filters.get('znamka', 'ALL')} {filters.get('model', '')} - This may indicate filters are too restrictive")
            return []
        
        # Convert DataFrame to list of dictionaries
        listings = []
        for _, row in results_df.iterrows():
            listing = {
                'HASH': row.get('HASH', ''),
                'URL': row.get('URL', ''),
                'Cena': row.get('Cena'),
                'Naziv': row.get('Naziv'),
                '1.registracija': row.get('1.registracija'),
                'Prevoženih': row.get('Prevoženih'),
                'Menjalnik': row.get('Menjalnik'),
                'Motor': row.get('Motor'),
                'lastnikov': row.get('lastnikov')
            }
            listings.append(listing)
        
        logger.info(f"Scrape completed. Found {len(listings)} listings")
        return listings
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
        return []

