"""
Background worker that continuously scrapes for all users
"""
import asyncio
import time
from typing import List, Dict
from src.database.models import Database, UserManager, ResultManager
from src.api.scraper_service import scrape_for_user
from src.api.notifications import send_pushover_notifications_for_listings
from src.shared.log import logger
from src.shared.config import get_param_limits


class ScrapingWorker:
    """Background worker for continuous scraping"""
    
    def __init__(self, db: Database, scrape_interval: int = 60):
        self.db = db
        self.scrape_interval = scrape_interval
        self.user_manager = UserManager(db)
        self.result_manager = ResultManager(db)
        self.is_running = False
    
    async def process_user(self, user: Dict) -> bool:
        """
        Process a single user: scrape, compare, notify, save.
        
        Returns:
            True if successful, False otherwise
        """
        user_id = user['user_id']
        filters = user['filters']
        pushover_api_token = user['pushover_api_token']
        pushover_user_key = user['pushover_user_key']
        notify_on_first_scrape = user['notify_on_first_scrape']
        
        try:
            logger.info(f"Processing user: {user_id}")
            
            # Scrape with user's filters
            new_listings = await scrape_for_user(filters)
            
            if not new_listings:
                logger.info(f"No listings found for user {user_id} - filters may be too restrictive or no matching cars available")
                # Still save empty results to track that scraping happened
                self.result_manager.save_user_results(user_id, [])
                return True
            
            # Get stored results
            stored_results = self.result_manager.get_user_results(user_id)
            
            if not stored_results:
                # First scrape OR filters were just changed - notify about all results ONLY if flag is set
                logger.info(f"Initial scrape for user {user_id} (first scrape or filters changed). Saving {len(new_listings)} listings.")
                self.result_manager.save_user_results(user_id, new_listings)
                
                # Only notify if flag is set (filter change scenario)
                if notify_on_first_scrape:
                    logger.info(f"Sending notifications for initial scrape with {len(new_listings)} listings (user {user_id} - filters changed)")
                    send_pushover_notifications_for_listings(
                        new_listings,
                        pushover_api_token,
                        pushover_user_key
                    )
                    # Clear the notify flag after sending
                    try:
                        self.user_manager.clear_notify_flag(user_id)
                        logger.info(f"Cleared notify flag for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error clearing notify flag: {e}", exc_info=True)
                else:
                    logger.info(f"No notification sent (first scrape, notify flag not set)")
                return True
            
            # Compare with stored results - only notify about NEW listings
            new_listings_only = self.result_manager.compare_results(user_id, new_listings)
            
            if new_listings_only:
                logger.info(f"Found {len(new_listings_only)} NEW listings for user {user_id} (out of {len(new_listings)} total)")
                
                # Send notifications ONLY for new listings
                send_pushover_notifications_for_listings(
                    new_listings_only,
                    pushover_api_token,
                    pushover_user_key
                )
                
                # Update stored results
                self.result_manager.save_user_results(user_id, new_listings)
            else:
                logger.info(f"No NEW listings for user {user_id} (all {len(new_listings)} listings already seen)")
                # Still update stored results in case listings were removed/changed
                self.result_manager.save_user_results(user_id, new_listings)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing user {user_id}: {e}", exc_info=True)
            return False
    
    async def run_cycle(self):
        """Run one scraping cycle for all users - only if filters are provided"""
        try:
            users = self.user_manager.get_all_active_users()
            
            if not users:
                logger.debug("No active users found. Waiting for registration...")
                return
            
            # Check if any user has filters set (not just empty defaults)
            users_with_filters = []
            for user in users:
                filters = user.get('filters', {})
                # Check if filters have meaningful values (not just empty defaults)
                has_filters = False
                if filters.get('znamka') and filters.get('znamka') != ['']:
                    has_filters = True
                elif filters.get('subcenaMIN') or filters.get('subcenaMAX'):
                    has_filters = True
                elif filters.get('cenaMax') and filters.get('cenaMax') != 100000:
                    has_filters = True
                elif filters.get('model') and filters.get('model') != '':
                    has_filters = True
                
                if has_filters:
                    users_with_filters.append(user)
            
            if not users_with_filters:
                logger.debug("No users with filters configured. Waiting for filters...")
                return
            
            logger.info(f"Starting scraping cycle for {len(users_with_filters)} user(s) with filters")
            
            # Process each user independently
            for user in users_with_filters:
                try:
                    await self.process_user(user)
                except Exception as e:
                    logger.error(f"Failed to process user {user['user_id']}: {e}", exc_info=True)
                    # Continue with next user
                    continue
            
            logger.info("Scraping cycle completed")
            
        except Exception as e:
            logger.error(f"Error in scraping cycle: {e}", exc_info=True)
    
    async def start(self):
        """Start the worker loop - waits for filters before scraping"""
        self.is_running = True
        logger.info(f"Scraping worker started. Waiting for filters to be provided...")
        logger.info(f"Interval: {self.scrape_interval} seconds (once filters are set)")
        
        while self.is_running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
            
            # Wait for next cycle
            logger.debug(f"Waiting {self.scrape_interval} seconds until next cycle...")
            await asyncio.sleep(self.scrape_interval)
    
    def stop(self):
        """Stop the worker loop"""
        logger.info("Stopping scraping worker...")
        self.is_running = False

