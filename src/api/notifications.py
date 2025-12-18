"""
Pushover notification system for user-based scraping
"""
import requests
from src.shared.utils import check_null_data
from src.shared.log import logger
from typing import List, Dict


def send_pushover_notification_for_listing(
    listing: Dict,
    pushover_api_token: str,
    pushover_user_key: str,
    sound: str = "pushover",
    priority: int = 0
) -> bool:
    """Send a single car listing notification via Pushover"""
    try:
        # Format the message with car details
        title = f"🚗 {check_null_data(listing.get('Naziv', 'N/A'))}"
        message = f"💰 {check_null_data(listing.get('Cena', 'N/A'))} €\n"
        message += f"📅 {check_null_data(listing.get('1.registracija', 'N/A'))}\n"
        message += f"🛣️ {check_null_data(listing.get('Prevoženih', 'N/A'))}\n"
        message += f"🔧 {check_null_data(listing.get('Motor', 'N/A'))}\n"
        
        # Add number of owners if available
        lastnikov = listing.get('lastnikov')
        if lastnikov and lastnikov != ":x:":
            message += f"👤 Lastnikov: {lastnikov}\n"
        
        message += f"🔗 {check_null_data(listing.get('URL', 'N/A'))}"
        
        payload = {
            "token": pushover_api_token,
            "user": pushover_user_key,
            "title": title,
            "message": message,
            "sound": sound,
            "priority": priority
        }
        
        response = requests.post("https://api.pushover.net/1/messages.json", data=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Pushover notification sent successfully for listing {listing.get('HASH', 'unknown')[:8]}")
            return True
        else:
            logger.warning(f"Failed to send Pushover notification: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.exception(f"Exception occurred while sending Pushover notification: {e}")
        return False


def send_pushover_notifications_for_listings(
    listings: List[Dict],
    pushover_api_token: str,
    pushover_user_key: str,
    sound: str = "pushover",
    priority: int = 0
) -> int:
    """Send notifications for multiple car listings via Pushover"""
    success_count = 0
    for listing in listings:
        if send_pushover_notification_for_listing(listing, pushover_api_token, pushover_user_key, sound, priority):
            success_count += 1
            # Small delay between notifications to avoid rate limiting
            import time
            time.sleep(0.5)
    
    logger.info(f"Sent {success_count}/{len(listings)} Pushover notifications")
    return success_count

