from datetime import datetime
import re

from bs4 import BeautifulSoup
from src.shared.utils import extract_property, collect_car_data, format_price, hash_listing
import pandas as pd
from src.shared.config import get_columns, get_base_url, get_selectors
from src.shared.log import logger

def extract_lastnikov(title, data):
    """Extract number of owners from title or data."""
    if not title:
        return None
    
    # Look for patterns like "2.LASTNICA", "1.LASTNICA", etc.
    match = re.search(r'(\d+)\.LASTNICA', title.upper())
    if match:
        return match.group(1)
    
    # Look for patterns like "2.LASTNIK", "1.LASTNIK", etc.
    match = re.search(r'(\d+)\.LASTNIK', title.upper())
    if match:
        return match.group(1)
    
    # Look for patterns like "2.LASTNIKA", "1.LASTNIKA", etc.
    match = re.search(r'(\d+)\.LASTNIKA', title.upper())
    if match:
        return match.group(1)
    
    return None

def populate_data(html, cars):
    selectors = get_selectors()
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('div', class_=selectors["result_row"])

    logger.info(f"Found {len(results)} car listings")

    for result in results:

        title = extract_property(result, selectors["title"], 'div')
        price = extract_property(result, selectors["price_main"], 'div') or extract_property(result, selectors["price_fallback"], 'div')
        reg_date = extract_property(result, '1.registracija', 'div') or ""

        link_raw = extract_property(result, selectors["link"], 'a')
        link = link_raw.replace("..", get_base_url()) if link_raw else None

        data_block = extract_property(result, selectors["data_block_primary"], 'div')
        if data_block is None:
            data_block = extract_property(result, selectors["data_block_fallback"], 'div')
        data = collect_car_data(data_block) if data_block else None

        if data:
            # Extract number of owners from title or data
            lastnikov = extract_lastnikov(title, data)
            
            listing_hash = hash_listing(title or "", format_price(price or ""), reg_date or "")
            row = {
                'Naziv': title,
                'Cena': format_price(price) if price else '',
                'URL': link,
                'HASH': listing_hash,
                'lastnikov': lastnikov,
                **data
            }
            data_cleaned = {col: row.get(col, None) for col in get_columns()}
            new_row = pd.DataFrame([data_cleaned])
            cars = pd.concat([cars, new_row], ignore_index=True)

    return cars
