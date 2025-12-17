import requests
import json
from plyer import notification
from src.shared.utils import check_null_data
from src.shared.log import logger

def load_pushover_config():
    """Load Pushover configuration from config file."""
    try:
        with open('config/pushover.json', 'r') as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load Pushover config")
        return None

def send_pushover_notification(row):
    """Send a single car listing notification via Pushover."""
    config = load_pushover_config()
    if not config:
        logger.error("Pushover config not available")
        return
    
    # Format the message with car details
    title = f"🚗 {check_null_data(row['Naziv'])}"
    message = f"💰 {check_null_data(row['Cena'])} €\n"
    message += f"📅 {check_null_data(row['1.registracija'])}\n"
    message += f"🛣️ {check_null_data(row['Prevoženih'])}\n"
    message += f"🔧 {check_null_data(row['Motor'])}\n"
    
    # Add number of owners if available
    lastnikov = check_null_data(row.get('lastnikov', None))
    if lastnikov and lastnikov != ":x:":
        message += f"👤 Lastnikov: {lastnikov}\n"
    
    message += f"🔗 {check_null_data(row['URL'])}"
    
    payload = {
        "token": config["api_token"],
        "user": config["user_key"],
        "title": title,
        "message": message,
        "sound": config.get("sound", "pushover"),
        "priority": config.get("priority", 0)
    }
    
    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=payload)
        if response.status_code == 200:
            logger.info("Pushover notification sent successfully.")
        else:
            logger.warning(f"Failed to send Pushover notification: {response.status_code} - {response.text}")
    except Exception:
        logger.exception("Exception occurred while sending Pushover notification.")

def send_pushover_notifications(rows):
    """Send notifications for multiple car listings via Pushover."""
    for _, row in rows.iterrows():
        send_pushover_notification(row)

def send_notification():
    try:
        notification.notify(
            title='New listing',
            message='A new car within your search parameters has been listed!',
            app_name='Avto-Net Scraper',
            timeout=10,
        )
        logger.info("Notification sent.")
    except Exception:
        logger.warning("Failed to send desktop notification.")