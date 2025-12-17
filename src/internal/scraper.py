import random

from playwright.async_api import async_playwright
from src.internal.parser import populate_data
from src.internal.data_handler import compare_data
import pandas as pd
import asyncio
import os
from bs4 import BeautifulSoup
from src.shared.config import (
    params, build_url, get_columns, get_selectors, get_param_limits
)
from src.shared.headers import get_playwright_context_options, get_random_headers
from src.shared.log import logger

async def scrape_with_js_and_cookies(params):
    url = build_url(params)
    logger.info(f"Built search URL: {url}")
    
    try:
        # Get randomized context options for this request
        context_options = get_playwright_context_options()
        
        # Log the randomized settings being used for debugging
        logger.debug(f"Using User-Agent: {context_options['user_agent'][:50]}...")
        logger.debug(f"Viewport: {context_options['viewport']['width']}x{context_options['viewport']['height']}")
        logger.debug(f"Timezone: {context_options['timezone_id']}")
        logger.debug(f"Locale: {context_options['locale']}")
        if 'proxy' in context_options:
            logger.debug(f"Using proxy: {context_options['proxy']['server']}")
        else:
            logger.debug("No proxy configured")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(**context_options)
            page = await context.new_page()

            await asyncio.sleep(random.uniform(2, 5))  # anti-bot cooldown
            await page.goto(url, timeout=60000)

            content = await page.content()

            # Check for empty result message
            if "Ni zadetkov" in content or "ni rezultatov" in content:
                logger.info(f"No results on page {params['stran']} for '{params['znamka']}' — skipping.")
                return ""

            await page.wait_for_selector("div." + get_selectors()["result_row"], timeout=15000)

            soup = BeautifulSoup(content, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            cleaned_content = str(soup)

            return cleaned_content

    except KeyboardInterrupt:
        logger.warning("Scraping manually interrupted by user.")
        return 500
    except Exception:
        logger.exception("Error during scraping.")
        return 500


async def scrape_brand_with_pagination(brand: str, max_pages: int) -> pd.DataFrame:
    logger.info(f"Scraping brand: '{brand or 'ALL'}' with {max_pages} pages")
    brand_results = pd.DataFrame(columns=get_columns())

    for page in range(1, max_pages + 1):
        local_params = params.copy()
        local_params["znamka"] = brand
        local_params["stran"] = page

        logger.debug(f"Fetching page {page} for brand '{brand}'")
        result = await scrape_with_js_and_cookies(local_params)
        if isinstance(result, int):  # If 500 or error
            logger.warning(f"Skipping page {page} for '{brand}' due to error code {result}")
            continue

        page_data = populate_data(result, pd.DataFrame(columns=get_columns()))
        found_count = len(page_data)
        brand_results = pd.concat([brand_results, page_data], ignore_index=True)

        max_results_per_page = get_param_limits()["max_results_per_page"]
        if found_count < max_results_per_page:
            logger.debug(f"Less than {max_results_per_page} results on page {page} — assuming last page.")
            break

    return brand_results

async def scrape(init=False):
    logger.info("Starting scrape process...")

    param_limits = get_param_limits()
    all_results = pd.DataFrame(columns=get_columns())

    for brand in params["znamka"]:
        local_params = params.copy()
        local_params["znamka"] = brand

        # Always apply the model (if it exists) — Avto.net will skip invalid combos
        if params["model"]:
            local_params["model"] = params["model"]

        logger.info(f"Scraping: {brand} {'(' + params['model'] + ')' if params['model'] else ''}")
        brand_data = await scrape_brand_with_pagination(brand, param_limits["max_pages"])
        all_results = pd.concat([all_results, brand_data], ignore_index=True)

    if all_results.empty:
        logger.warning("No results fetched from any brand/page.")
        return None

    if init:
        os.makedirs("data", exist_ok=True)
        all_results.to_csv("data/listings.csv", sep=';', index=False)
        logger.info("Initial listings saved to data/listings.csv")
    else:
        compare_data(all_results)

    logger.info("Scrape complete")
    return all_results